import unittest
from unittest.mock import MagicMock
from app.git_tools import create_git_tools

class TestGitPushProtection(unittest.TestCase):
    def setUp(self):
        self.mock_sandbox = MagicMock()
        self.mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        self.mock_sandbox.get_cwd.return_value = "/tmp/sandbox/repo"
        self.mock_sandbox.list_files.return_value = "repo/\n"

    def test_push_to_base_branch_fails(self):
        base_branch = "feature/stable-1"
        tools = create_git_tools(self.mock_sandbox, base_branch=base_branch)
        push_tool = next(t for t in tools if t.name == "push_changes")

        # Test pushing to explicitly provided base branch
        result = push_tool.invoke({"branch": "feature/stable-1"})
        self.assertIn("Error: Cannot push to protected or base branch", result)
        self.mock_sandbox.run_command.assert_not_called()

    def test_push_to_protected_branch_fails(self):
        tools = create_git_tools(self.mock_sandbox) # No base branch, but main/master protected
        push_tool = next(t for t in tools if t.name == "push_changes")

        # Test pushing to main
        result = push_tool.invoke({"branch": "main"})
        self.assertIn("Error: Cannot push to protected or base branch", result)

        # Test pushing to develop
        result = push_tool.invoke({"branch": "develop"})
        self.assertIn("Error: Cannot push to protected or base branch", result)

        self.mock_sandbox.run_command.assert_not_called()

    def test_push_to_valid_branch_succeeds(self):
        base_branch = "main"
        tools = create_git_tools(self.mock_sandbox, base_branch=base_branch)
        push_tool = next(t for t in tools if t.name == "push_changes")

        # Test pushing to a valid feature branch
        feature_branch = "feature/new-stuff"
        self.mock_sandbox.run_command.return_value = "Pushed successfully"

        result = push_tool.invoke({"branch": feature_branch})

        self.mock_sandbox.run_command.assert_called_with(f"git push origin {feature_branch}", "/tmp/sandbox/repo")
        self.assertEqual(result, "Pushed successfully")

if __name__ == "__main__":
    unittest.main()
