import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
from app.tools import list_indexed_repos, get_file_content, search_codebase, settings


class TestTools(unittest.TestCase):
    def setUp(self):
        # testing
        self.test_root = Path("test_tool_data").resolve()
        self.repo_name = "test_repo"
        self.repo_dir = self.test_root / self.repo_name
        self.repo_dir.mkdir(parents=True, exist_ok=True)

        #  settings
        settings.data_path = self.test_root
        settings.repo_registry_path = self.test_root / "repos.txt"

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_get_file_content_success(self):
        """sucess"""
        file_rel_path = "src/logic.py"
        full_path = self.repo_dir / file_rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("print('hello world')")

        result = get_file_content.invoke({
            "repo_name": self.repo_name,
            "relative_path": file_rel_path
        })

        self.assertIn("--- CONTENT OF src/logic.py ---", result)
        self.assertIn("print('hello world')", result)

    def test_security_block(self):
        # Attempt to read the registry file from outside the repo root
        result = get_file_content.invoke({
            "repo_name": self.repo_name,
            "relative_path": "../repos.txt"
        })

        self.assertIn("Error: Access denied", result)
        self.assertIn("outside repository boundaries", result)

    def test_content_missing(self):
        """no files"""
        result = get_file_content.invoke({
            "repo_name": self.repo_name,
            "relative_path": "i_dont_exist.py"
        })
        self.assertEqual(result, "Error: File 'i_dont_exist.py' not found.")

    def test_codebase_empty_query(self):
        """ blocks empty strings."""
        result = search_codebase.invoke({
            "repo_name": self.repo_name,
            "query": "   "
        })
        self.assertIn("Error: Query was empty", result)

    @patch("app.tools.get_context")
    def test_search_codebase(self, mock_get_context):
        mock_get_context.return_value = "Fake context from RAG"

        result = search_codebase.invoke({
            "repo_name": self.repo_name,
            "query": "how to login"
        })

        mock_get_context.assert_called_once_with(
            self.repo_name, "how to login")
        self.assertEqual(result, "Fake context from RAG")


if __name__ == "__main__":
    unittest.main()
