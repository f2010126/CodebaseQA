import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import os
from app.agent import build_agent


import unittest
from unittest.mock import patch, MagicMock
#  dummy environment
with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
    from app.agent import build_agent, build_llm, get_session_history
    from langchain_core.runnables.history import RunnableWithMessageHistory


class TestBuildAgent(unittest.TestCase):
    # Order matters
    @patch("app.agent.AgentExecutor")
    @patch("app.agent.create_tool_calling_agent")
    @patch("app.agent.ChatGoogleGenerativeAI")
    @patch("app.agent.os.listdir")
    @patch("app.agent.os.path.isdir")
    def test_build_agent_success(self, mock_isdir, mock_listdir, mock_llm_class, mock_create, mock_executor):
        mock_listdir.return_value = ["repo_a"]
        mock_isdir.return_value = True

        fake_llm = MagicMock()
        mock_llm_class.return_value = fake_llm

        fake_agent = MagicMock()
        mock_create.return_value = fake_agent

        fake_executor_instance = MagicMock()
        mock_executor.return_value = fake_executor_instance

        result = build_agent()

        self.assertIsInstance(result, RunnableWithMessageHistory)

        mock_executor.assert_called_once()
        _, kwargs = mock_executor.call_args
        self.assertEqual(kwargs["agent"], fake_agent)
        self.assertEqual(kwargs["max_iterations"], 4)
        self.assertEqual(kwargs["early_stopping_method"], "generate")

    # FAILURE expected here.

    @patch("app.agent.ChatGoogleGenerativeAI", side_effect=Exception("API Key Error"))
    def test_build_agent_llm_failure(self, mock_llm):
        with self.assertRaises(Exception) as ctx:
            build_llm()
        self.assertIn("API Key Error", str(ctx.exception))

    def test_session_history(self):
        """ different session IDs get different history objects."""
        id_a = "test_user_a"
        id_b = "test_user_b"

        hist1 = get_session_history(id_a)
        hist2 = get_session_history(id_b)
        hist1_again = get_session_history(id_a)

        self.assertIsNot(
            hist1, hist2, "different sessions need different memory addresses")
        self.assertIs(hist1, hist1_again,
                      "Same session same instance")


if __name__ == "__main__":
    unittest.main()
