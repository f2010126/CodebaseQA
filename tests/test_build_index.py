import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from langchain_core.documents import Document

#  use patch.dict to ensure Pydantic doesn't crash on import if GOOGLE_API_KEY is missing
with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-test-key"}):
    from ingest.build_index import run_indexing, register_repo, settings


class TestBuildIndex(unittest.TestCase):

    def setUp(self):
        self.data_path = "data/fake_repo_agent"
        self.repo_name = "fake_repo_agent"
        # Reset settings paths for testing consistency
        settings.vectorstore_root = Path("test_vectorstore")
        settings.repo_registry_path = Path("test_data/repos.txt")

    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    @patch("ingest.build_index.FAISS")
    @patch("ingest.build_index.DirectoryLoader")
    @patch("ingest.build_index.register_repo")
    def test_run_indexing_new_repo(self, mock_register, mock_loader, mock_faiss, mock_embeddings):
        """Tests the logic for creating a brand new vectorstore."""
        # Setup mock document
        mock_doc = Document(page_content="def hello(): pass",
                            metadata={"source": "hello.py"})
        mock_loader.return_value.load.return_value = [mock_doc]

        # Mock FAISS return
        mock_db = MagicMock()
        mock_faiss.from_documents.return_value = mock_db

        # Use patch.object to mock the Path.exists call specifically for the save_path
        with patch.object(Path, "exists", return_value=False):
            result = run_indexing(self.data_path)

        self.assertIsNotNone(result)
        mock_faiss.from_documents.assert_called_once()
        mock_db.save_local.assert_called_once()
        mock_register.assert_called_once_with(self.repo_name)

    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    @patch("ingest.build_index.FAISS")
    @patch("ingest.build_index.DirectoryLoader")
    def test_run_indexing_update_repo(self, mock_loader, mock_faiss, mock_embeddings):
        """Tests the logic for appending to an existing vectorstore."""
        mock_loader.return_value.load.return_value = [
            Document(page_content="v2", metadata={"source": "a.py"})]

        mock_db = MagicMock()
        mock_faiss.load_local.return_value = mock_db

        # Simulate that the directory exists
        with patch.object(Path, "exists", return_value=True):
            run_indexing(self.data_path)

        mock_faiss.load_local.assert_called_once()
        mock_db.add_documents.assert_called_once()
        mock_db.save_local.assert_called_once()

    def test_metadata_injection(self):
        """Verify that chunking adds 'repo' and 'source_file' to metadata."""
        # logic inside run_indexing
        with patch("ingest.build_index.DirectoryLoader") as mock_loader:
            mock_loader.return_value.load.return_value = [
                Document(page_content="code", metadata={
                         "source": "path/to/script.py"})
            ]
            with patch("ingest.build_index.FAISS.from_documents") as mock_faiss_from:
                with patch("ingest.build_index.GoogleGenerativeAIEmbeddings"):
                    with patch.object(Path, "exists", return_value=False):
                        run_indexing(self.data_path)

        # Inspect the chunks passed to FAISS
        passed_chunks = mock_faiss_from.call_args[0][0]
        self.assertEqual(passed_chunks[0].metadata["repo"], self.repo_name)
        self.assertEqual(passed_chunks[0].metadata["source_file"], "script.py")

    @patch("ingest.build_index.Path.read_text")
    @patch("ingest.build_index.Path.exists")
    def test_register_repo_deduplication(self, mock_exists, mock_read):
        """Ensures we don't write the same repo name twice."""
        mock_exists.return_value = True
        mock_read.return_value = "my_repo\nother_repo\n"

        with patch("builtins.open", mock_open()) as mocked_file:
            register_repo("my_repo")
            # don't open in append mode because it's already there
            mocked_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
