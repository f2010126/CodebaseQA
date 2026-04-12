import unittest
import shutil
import pickle
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ingest.build_index import (
    register_repo, load_repo_documents, process_chunks,
    save_hybrid_index, run_indexing, settings
)


class FakeEmbeddings(Embeddings):
    """ fake embedding model for testing."""

    def embed_documents(self, texts):
        #  dummy vectors of length 768
        return [[0.1] * 768 for _ in texts]

    def embed_query(self, text):
        return [0.1] * 768


# Handle Pydantic validation on import
with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-test-key"}):
    from ingest.build_index import run_indexing, register_repo, settings


class TestBuildIndex(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("./test_repo").resolve()
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # dummy repo
        self.fake_repo_path = self.test_dir / "fake_agent"
        self.fake_repo_path.mkdir()
        (self.fake_repo_path / "main.py").write_text("def add(a, b): return a + b")
        (self.fake_repo_path / "README.md").write_text("# Fake Agent Testing")

        # point to the tests
        settings.vectorstore_root = self.test_dir / "vectorstore"
        settings.repo_registry_path = self.test_dir / "repos.txt"

        self.fake_embeddings = FakeEmbeddings()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_load_repo_documents(self):
        """Load files"""
        docs = load_repo_documents(self.fake_repo_path)

        # 2 files expected: .py, .md
        filenames = [Path(d.metadata['source']).name for d in docs]
        self.assertIn("main.py", filenames)
        self.assertIn("README.md", filenames)
        self.assertGreaterEqual(len(docs), 2)

    def test_process_chunks_metadata(self):
        raw_docs = [
            Document(page_content="some code", metadata={
                     "source": str(self.fake_repo_path / "main.py")})
        ]

        chunks = process_chunks(raw_docs, self.fake_repo_path, "fake_agent")

        for chunk in chunks:
            self.assertEqual(chunk.metadata["source_file"], "main.py")
            self.assertEqual(chunk.metadata["repo"], "fake_agent")

    def test_save_hybrid_index(self):
        """Verify FAISS and BM25"""
        chunks = [Document(page_content="test content",
                           metadata={"source_file": "test.py"})]
        save_path = settings.vectorstore_root / "fake_agent"
        save_path.mkdir(parents=True, exist_ok=True)

        # send fake embedding model instead of real Google API call
        db = save_hybrid_index(chunks, "fake_agent", save_path)

        # Check FAISS files
        self.assertTrue((save_path / "index.faiss").exists())
        self.assertTrue((save_path / "index.pkl").exists())

        # Check BM25 file
        self.assertTrue((save_path / "bm25_retriever.pkl").exists())

        # Verify it can be unpickled
        with open(save_path / "bm25_retriever.pkl", "rb") as f:
            retriever = pickle.load(f)
            self.assertIsNotNone(retriever)

    def test_register_repo_deduplication(self):
        """make sure repo.txt is unique"""
        register_repo("fake_agent")
        register_repo("fake_agent")  # duplicate accident
        register_repo("other_app")

        content = settings.repo_registry_path.read_text().splitlines()
        self.assertEqual(len(content), 2)
        self.assertIn("fake_agent", content)
        self.assertIn("other_app", content)

    def test_run_indexing_cleanup(self):
        """full workflow"""
        save_path = settings.vectorstore_root / "fake_agent"
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "stale_file.txt").write_text("should be gone")

        # re index
        #  mock for the embedding model to avoid API error
        with unittest.mock.patch('ingest.build_index.get_embeddings_model', return_value=self.fake_embeddings):
            run_indexing(data_path=str(self.fake_repo_path))

        #  stale file  gone because rmtree was called
        self.assertFalse((save_path / "stale_file.txt").exists())


if __name__ == "__main__":
    unittest.main()
