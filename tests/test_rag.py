import unittest
from unittest.mock import patch, MagicMock
import pickle
import shutil
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever
from langchain_core.embeddings import Embeddings

# Setup fake environment for Pydantic/Settings
with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
    from app.rag import load_hybrid_retriever, get_context
    from app.config import settings


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts): return [[0.1] * 768 for _ in texts]
    def embed_query(self, text): return [0.1] * 768


class TestRAG(unittest.TestCase):

    def setUp(self):
        # Point settings to a dedicated test directory
        self.test_root = Path("test_vectorstore").resolve()
        settings.vectorstore_root = self.test_root
        self.repo_name = "fake_agent"
        self.repo_path = self.test_root / self.repo_name
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.fake_embeddings = FakeEmbeddings()

    def tearDown(self):
        # Clean up
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    @patch("app.rag.FAISS")
    @patch("app.rag.GoogleGenerativeAIEmbeddings")
    def test_load_hybrid_retriever_full_success(self, mock_emb_class, mock_faiss):
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
        mock_emb_class.return_value = self.fake_embeddings
        mock_vector_retriever = MagicMock(spec=BaseRetriever)

        mock_vs = MagicMock()
        mock_faiss.load_local.return_value = mock_vs
        mock_vs.as_retriever.return_value = mock_vector_retriever

        retriever = load_hybrid_retriever(self.repo_name)
        from langchain_classic.retrievers import EnsembleRetriever
        self.assertIsInstance(retriever, EnsembleRetriever)
        self.assertEqual(len(retriever.retrievers), 2)  # need both

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
            Document(page_content="def func1(): print('hi')",
                     metadata={"source_file": "utils.py", "content_type": "function_definition"}),
            Document(
                page_content="class MyClass: pass",
                metadata={"source_file": "utils.py",
                          "content_type": "class_definition"}
            )
        ]
        mock_load.return_value = mock_retriever

        context = get_context(self.repo_name, "how does utils work?")
        self.assertIn("--- FILE: utils.py (function_definition) ---", context)
        self.assertIn(
            "--- CONTINUED: FILE: utils.py (class_definition) ---", context)
        self.assertIn("def func1(): print('hi')", context)
        self.assertIn("class MyClass: pass", context)


if __name__ == "__main__":
    unittest.main()
