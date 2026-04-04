import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from langchain_core.documents import Document

# Handle Pydantic validation on import
with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-test-key"}):
    from ingest.build_index import run_indexing, register_repo, settings


class TestBuildIndex(unittest.TestCase):

    def setUp(self):
        self.data_path = "data/fake_repo_agent"
        self.repo_name = "fake_repo_agent"
        # Reset settings for isolated testing
        settings.vectorstore_root = Path("test_vectorstore")
        settings.repo_registry_path = Path("test_data/repos.txt")

    @patch("ingest.build_index.shutil.rmtree")
    @patch("ingest.build_index.GenericLoader")
    @patch("ingest.build_index.FAISS")
    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    def test_run_indexing(self, mock_embeddings, mock_faiss, mock_loader, mock_rmtree):
        """Tests that existing indexes are wiped and recreated fresh."""
        mock_doc = Document(page_content="def hello(): pass",
                            metadata={"source": "hello.py"})
        mock_loader.return_value.load.return_value = [mock_doc]

        mock_db = MagicMock()
        mock_faiss.from_documents.return_value = mock_db

        with patch.object(Path, "exists", return_value=True):
            result = run_indexing(self.data_path)

        # Assertions
        mock_rmtree.assert_called_once()
        mock_faiss.from_documents.assert_called_once()
        mock_db.save_local.assert_called_once()
        self.assertIsNotNone(result)

    @patch("ingest.build_index.GenericLoader")
    @patch("ingest.build_index.FAISS.from_documents")
    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    def test_metadata_injection(self, mock_embeddings, mock_faiss_from, mock_loader):
        """Verify that chunking adds 'repo' and 'source_file' to metadata using AST loader."""
        mock_loader.return_value.load.return_value = [
            Document(page_content="code", metadata={
                     "source": "path/to/script.py"})
        ]

        with patch.object(Path, "exists", return_value=False):
            run_indexing(self.data_path)

        # Inspect the chunks passed to FAISS.from_documents
        passed_chunks = mock_faiss_from.call_args[0][0]
        self.assertEqual(passed_chunks[0].metadata["repo"], self.repo_name)
        self.assertEqual(passed_chunks[0].metadata["source_file"], "script.py")

    @patch("ingest.build_index.Path.read_text")
    def test_register_repo_deduplication(self, mock_read):
        """Ensures we don't write the same repo name twice."""
        mock_read.return_value = "fake_repo_agent\nother_repo\n"

        # Patching Path.exists specifically for the registry file
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open()) as mocked_file:
                register_repo(self.repo_name)
                mocked_file.assert_not_called()

    @patch("ingest.build_index.GenericLoader")
    def test_empty_repo_handling(self, mock_loader):
        """Ensure None is returned if no documents are found."""
        mock_loader.return_value.load.return_value = []

        result = run_indexing(self.data_path)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
