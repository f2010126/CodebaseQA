import unittest
from unittest.mock import patch, MagicMock
import main


class TestMain(unittest.TestCase):

    @patch("main.build_agent")
    def test_agent_invocation(self, mock_build_agent):
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"output": "test answer"}

        mock_build_agent.return_value = mock_agent

        agent = mock_build_agent()

        result = agent.invoke({"input": "test"})

        self.assertEqual(result["output"], "test answer")
        mock_agent.invoke.assert_called_once()


if __name__ == "__main__":
    unittest.main()
