import unittest
from unittest.mock import patch, MagicMock
import pickle
import shutil
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever

# Setup fake environment for Pydantic/Settings
with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
    from app.rag import load_hybrid_retriever, get_context
    from app.config import settings


class TestRAG(unittest.TestCase):

    def setUp(self):
        # Point settings to a dedicated test directory
        self.test_root = Path("test_vectorstore")
        settings.vectorstore_root = self.test_root
        self.repo_name = "test_repo"
        self.repo_path = self.test_root / self.repo_name
        self.repo_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    @patch("app.rag.FAISS")
    @patch("app.rag.GoogleGenerativeAIEmbeddings")
    def test_load_hybrid_retriever_full_success(self, mock_emb, mock_faiss):
        """Full success"""
        # mock fake data
        (self.repo_path / "index.faiss").write_text("fake binary")

        # fake pickle file for BM25
        dummy_doc = Document(page_content="test", metadata={
                             "source": "test.py"})
        real_bm25 = BM25Retriever.from_documents([dummy_doc])

        bm25_path = self.repo_path / "bm25_retriever.pkl"
        with open(bm25_path, "wb") as f:
            pickle.dump(real_bm25, f)

        # 3. Mock FAISS behavior
        mock_vector_retriever = MagicMock(spec=BaseRetriever)
        mock_vs = MagicMock()
        mock_faiss.load_local.return_value = mock_vs
        mock_vs.as_retriever.return_value = mock_vector_retriever

        retriever = load_hybrid_retriever(self.repo_name)

        self.assertIsInstance(retriever, EnsembleRetriever)

    @patch("app.rag.FAISS")
    @patch("app.rag.GoogleGenerativeAIEmbeddings")
    def test_load_hybrid_retriever_fallback(self, mock_emb, mock_faiss):
        """fallback when only FAISS files exist."""
        (self.repo_path / "index.faiss").write_text("fake binary")
        mock_vs = MagicMock()
        mock_faiss.load_local.return_value = mock_vs
        mock_vs.as_retriever.return_value = "vector_only"
        retriever = load_hybrid_retriever(self.repo_name)
        self.assertEqual(retriever, "vector_only")

    def test_load_hybrid_retriever_missing_directory(self):
        # unknown repo here
        retriever = load_hybrid_retriever("ghost_repo")
        self.assertIsNone(retriever)

    @patch("app.rag.load_hybrid_retriever")
    def test_get_context_formatting(self, mock_load):
        """Tests the string formatting logic using real Document objects."""
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="print('hi')",
                     metadata={"source_file": "main.py"})
        ]
        mock_load.return_value = mock_retriever

        context = get_context(self.repo_name, "query")
        self.assertEqual(context, "[main.py]: print('hi')")


if __name__ == "__main__":
    unittest.main()
