import unittest
from unittest.mock import MagicMock
from app.git_tools import create_git_tools

class TestGitCheckout(unittest.TestCase):
    def test_checkout_branch(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox/repo"
        mock_sandbox.list_files.return_value = "repo/\n"

        tools = create_git_tools(mock_sandbox)
        checkout_tool = next(t for t in tools if t.name == "checkout_branch")

        # Test valid checkout
        mock_sandbox.run_command.return_value = "Switched to branch 'feature'"
        result = checkout_tool.invoke({"branch_name": "feature"})

        mock_sandbox.run_command.assert_called_with("git checkout feature", "/tmp/sandbox/repo")
        self.assertEqual(result, "Switched to branch 'feature'")

    def test_checkout_branch_no_repo(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox"
        mock_sandbox.list_files.return_value = ""

        tools = create_git_tools(mock_sandbox)
        checkout_tool = next(t for t in tools if t.name == "checkout_branch")

        result = checkout_tool.invoke({"branch_name": "feature"})
        self.assertIn("No repository found", result)

if __name__ == "__main__":
    unittest.main()
