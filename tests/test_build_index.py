import unittest
from unittest.mock import patch

from langchain_core.documents import Document
from ingest import build_index


class TestBuildIndex(unittest.TestCase):

    @patch("ingest.build_index.FAISS")
    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    @patch("ingest.build_index.DirectoryLoader")
    def test_successful_index_build(self, mock_loader, mock_embeddings, mock_faiss):

        mock_doc = Document(
            page_content="def foo(): pass",
            metadata={"source": "main.py"}
        )

        mock_loader.return_value.load.return_value = [mock_doc]

        mock_db = mock_faiss.from_documents.return_value

        result = build_index.run_indexing(
            data_path="data/fake_repo_agent",
            save_path="vectorstore"
        )

        mock_loader.assert_called_once()
        mock_faiss.from_documents.assert_called_once()
        mock_db.save_local.assert_called_once()

        self.assertIsNotNone(result)

    @patch("ingest.build_index.DirectoryLoader")
    def test_empty_repo(self, mock_loader):

        mock_loader.return_value.load.return_value = []

        result = build_index.run_indexing(
            data_path="data/fake_repo_agent"
        )

        self.assertIsNone(result)

    @patch("ingest.build_index.DirectoryLoader")
    def test_loader_failure(self, mock_loader):

        mock_loader.return_value.load.side_effect = Exception("Loader error")

        with self.assertRaises(Exception):
            build_index.run_indexing(
                data_path="data/fake_repo_agent"
            )

    # expect an error stack here.
    @patch("ingest.build_index.FAISS")
    @patch("ingest.build_index.GoogleGenerativeAIEmbeddings")
    @patch("ingest.build_index.DirectoryLoader")
    def test_faiss_failure(self, mock_loader, mock_embeddings, mock_faiss):

        mock_doc = Document(
            page_content="def foo(): pass",
            metadata={"source": "main.py"}
        )

        mock_loader.return_value.load.return_value = [mock_doc]

        mock_faiss.from_documents.side_effect = Exception("FAISS failed")

        with self.assertRaises(Exception):
            build_index.run_indexing(
                data_path="data/fake_repo_agent"
            )


if __name__ == "__main__":
    unittest.main()
