import unittest
from unittest.mock import patch, MagicMock

from app.agent import build_agent


import unittest
from unittest.mock import patch, MagicMock

from app.agent import build_agent


class TestBuildAgent(unittest.TestCase):
    # Order matters
    @patch("app.agent.AgentExecutor")
    @patch("app.agent.create_react_agent")
    @patch("app.agent.build_tools")
    @patch("app.agent.build_llm")
    def test_build_agent_success(
        self,
        mock_llm,
        mock_tools,
        mock_create_agent,
        mock_executor
    ):
        fake_llm = MagicMock()
        mock_llm.return_value = fake_llm

        fake_tools = [MagicMock()]
        mock_tools.return_value = fake_tools

        fake_agent = MagicMock()
        mock_create_agent.return_value = fake_agent

        fake_executor_instance = MagicMock()
        mock_executor.return_value = fake_executor_instance
        result = build_agent()

        # Asserts
        mock_llm.assert_called_once()
        mock_tools.assert_called_once()
        mock_create_agent.assert_called_once()
        mock_executor.assert_called_once()

        # Validate
        _, kwargs = mock_create_agent.call_args
        self.assertEqual(kwargs["llm"], fake_llm)
        self.assertEqual(kwargs["tools"], fake_tools)

        self.assertEqual(result, fake_executor_instance)

    # FAILURE expected here.
    @patch("app.agent.build_llm", side_effect=Exception("LLM crash"))
    def test_build_agent_llm_failure(self, mock_llm):
        with self.assertRaises(Exception) as ctx:
            build_agent()

        self.assertIn("LLM crash", str(ctx.exception))

    @patch("app.agent.build_tools", side_effect=Exception("Tools crash"))
    @patch("app.agent.build_llm")
    def test_build_agent_tools_failure(self, mock_llm, mock_tools):
        mock_llm.return_value = MagicMock()

        with self.assertRaises(Exception) as ctx:
            build_agent()

        self.assertIn("Tools crash", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
