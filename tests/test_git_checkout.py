import unittest
from unittest.mock import MagicMock
from app.git_tools import create_git_tools

class TestGitCheckout(unittest.TestCase):
    def test_checkout_branch(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox"
        mock_sandbox.list_files.return_value = ".git/\n"

        tools = create_git_tools(mock_sandbox)
        checkout_tool = next(t for t in tools if t.name == "checkout_branch")

        # Test valid checkout
        mock_sandbox.run_command.return_value = "Switched to branch 'feature'"
        result = checkout_tool.invoke({"branch_name": "feature"})

        mock_sandbox.run_command.assert_called_with("git checkout feature", "/tmp/sandbox")
        self.assertEqual(result, "Switched to branch 'feature'")

    def test_checkout_branch_no_repo(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox"
        mock_sandbox.list_files.return_value = ""

        # With the new changes, get_repo_path simply returns root path.
        # It relies on the command failing if it's not a git repo, or checks inside logic?
        # create_git_tools wraps checkout_branch which calls get_repo_path(sandbox, repo_path)
        # In the new code:
        # target = get_repo_path(sandbox, repo_path)
        # if "No repository" in target: return target  <-- This check was removed from get_repo_path!

        # Wait, the refactor removed the "No repository" check from get_repo_path.
        # Now get_repo_path always returns the path.
        # The tool functions (checkout_branch) still have:
        # if "No repository" in target: return target

        # But target is just a path string now. So "No repository" will likely NOT be in target unless the path itself contains it (unlikely).
        # So the tool will proceed to run the command.

        # We need to verify how `checkout_branch` handles this.
        # It runs `git checkout ...` in the target dir.
        # If it's not a git repo, git will fail.

        tools = create_git_tools(mock_sandbox)
        checkout_tool = next(t for t in tools if t.name == "checkout_branch")

        mock_sandbox.run_command.return_value = "fatal: not a git repository"

        result = checkout_tool.invoke({"branch_name": "feature"})
        self.assertIn("fatal", result)

if __name__ == "__main__":
    unittest.main()
