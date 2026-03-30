import unittest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from app.tools import search_codebase


class TestTools(unittest.TestCase):

    @patch("app.tools.get_retriever")
    def test_search_codebase_success(self, mock_get_retriever):
        mock_retriever = mock_get_retriever.return_value  # the actual value
        mock_doc = Document(
            page_content="def foo(): pass",
            metadata={"source": "main.py"}
        )
        mock_retriever.invoke.return_value = [mock_doc]

        result = search_codebase("foo")

        self.assertIn("main.py", result)
        self.assertIn("def foo()", result)

    @patch("app.tools.get_retriever")  # its a call now
    def test_search_codebase_empty(self, mock_get_retriever):
        mock_retriever = mock_get_retriever.return_value  # the actual value
        mock_retriever.invoke.return_value = []

        result = search_codebase("nothing")

        self.assertIn("No relevant code", result)

    @patch("app.tools.get_retriever")
    def test_search_codebase_error(self, mock_get_retriever):
        mock_retriever = mock_get_retriever.return_value  # the actual value
        mock_retriever.invoke.side_effect = Exception("fail")

        result = search_codebase("error")

        self.assertIn("Error retrieving", result)


if __name__ == "__main__":
    unittest.main()
