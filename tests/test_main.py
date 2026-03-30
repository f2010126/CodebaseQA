import unittest
from unittest.mock import patch, MagicMock
from main import get_agent, run_query, start_agent


class TestMain(unittest.TestCase):

    @patch("main.build_agent")
    def test_get_agent(self, mock_build_agent):
        mock_agent = MagicMock()
        mock_build_agent.return_value = mock_agent

        result = get_agent()

        mock_build_agent.assert_called_once()
        self.assertEqual(result, mock_agent)

    def test_run_query_success(self):
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"output": "hello world"}

        result = run_query(mock_agent, "test query")

        mock_agent.invoke.assert_called_once_with(
            {"input": "test query"}
        )

        self.assertEqual(result["output"], "hello world")

    def test_run_query_error(self):
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = Exception("fail")

        with self.assertRaises(Exception):
            run_query(mock_agent, "test")

    @patch("main.get_agent")
    @patch("main.run_query")
    @patch("builtins.print")
    @patch("builtins.input", side_effect=["hello", "quit"])
    def test_start_agent_normal_flow(
        self, mock_input, mock_print, mock_run_query, mock_get_agent
    ):
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        mock_run_query.return_value = {"output": "response"}

        start_agent()

        mock_run_query.assert_called_once_with(mock_agent, "hello")

    @patch("main.get_agent")
    @patch("main.run_query")
    @patch("main.logger")
    @patch("builtins.print")
    @patch("builtins.input", side_effect=["hello"])
    def test_start_agent_runtime_exception(
        self, mock_input, mock_print, mock_logger, mock_run_query, mock_get_agent
    ):
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent

        # force exception inside loop
        mock_run_query.side_effect = Exception("boom")

        # force exit after first iteration by raising KeyboardInterrupt
        with patch("builtins.input", side_effect=["hello", KeyboardInterrupt()]):
            start_agent()

        # ensure error path triggered
        mock_logger.error.assert_called()

        # ensure fallback print executed
        mock_print.assert_any_call("Something went wrong. Check logs.")

    @patch("main.get_agent")
    @patch("builtins.input", side_effect=KeyboardInterrupt())
    @patch("builtins.print")
    def test_start_agent_keyboard_interrupt(
        self, mock_print, mock_input, mock_get_agent
    ):
        mock_get_agent.return_value = MagicMock()

        start_agent()

        mock_print.assert_any_call("\nExiting...")


if __name__ == "__main__":
    unittest.main()
