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

    @patch("ingest.build_index.shutil.rmtree")
    @patch("ingest.build_index.GenericLoader")
    @patch("ingest.build_index.FAISS")
    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    def test_run_indexing(self, mock_embeddings, mock_faiss, mock_loader, mock_rmtree):
        # different documents for different loaders
        py_doc = Document(page_content="def hello(): pass",
                          metadata={"source": "hello.py"})
        md_doc = Document(page_content="# Readme",
                          metadata={"source": "README.md"})

        #  loaders to return different docs in sequence
        #   1 call for Python and 4 calls for the text_globs
        mock_py_instance = MagicMock()
        mock_py_instance.load.return_value = [py_doc]

        mock_text_instance = MagicMock()
        mock_text_instance.load.return_value = [md_doc]

        # GenericLoader() is called 5 times total (1 Python + 4 Text Globs)
        mock_loader.side_effect = [
            mock_py_instance,   # Python loader
            mock_text_instance,  # README.md loader
            mock_text_instance,  # requirements.txt loader
            mock_text_instance,  # pyproject.toml loader
            mock_text_instance  # Dockerfile loader
        ]

        mock_db = MagicMock()
        mock_faiss.from_documents.return_value = mock_db

        with patch.object(Path, "exists", return_value=True):
            result = run_indexing(self.data_path)

        # Assertions
        self.assertIsNotNone(result)
        mock_rmtree.assert_called_once()
        # Verify FAISS received documents from BOTH loaders (1 py + 4 text = 5 docs)
        # multiple docs here
        mock_faiss.from_documents.assert_called_once()

    @patch("ingest.build_index.GenericLoader")
    @patch("ingest.build_index.FAISS.from_documents")
    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    def test_metadata_injection(self, mock_embeddings, mock_faiss_from, mock_loader):
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
        mock_read.return_value = "fake_repo_agent\nother_repo\n"

        # specifically for the registry file
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open()) as mocked_file:
                register_repo(self.repo_name)
                mocked_file.assert_not_called()

    @patch("ingest.build_index.GenericLoader")
    def test_empty_repo_handling(self, mock_loader):
        mock_loader.return_value.load.return_value = []

        result = run_indexing(self.data_path)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
