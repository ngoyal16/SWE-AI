import unittest
from unittest.mock import MagicMock
from app.git_tools import create_git_tools

class TestGitValidation(unittest.TestCase):
    def setUp(self):
        self.mock_sandbox = MagicMock()
        self.mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        self.mock_sandbox.get_cwd.return_value = "/tmp/sandbox/repo"
        self.mock_sandbox.list_files.return_value = "repo/\n"
        self.tools = create_git_tools(self.mock_sandbox)
        self.create_branch_tool = next(t for t in self.tools if t.name == "create_branch")

    def test_valid_branch_names(self):
        valid_names = [
            "feature/user-login-12345",
            "bugfix/fix-crash-67890",
            "hotfix/urgent-patch-111",
            "chore/cleanup-999",
            "docs/update-readme-000",
            "feature/new-feature", # Technically valid by regex even without ID, strict regex didn't enforce ID presence, just format
        ]

        for name in valid_names:
            self.mock_sandbox.run_command.reset_mock()
            self.mock_sandbox.run_command.return_value = f"Switched to a new branch '{name}'"

            result = self.create_branch_tool.invoke({"branch_name": name})

            self.mock_sandbox.run_command.assert_called_with(f"git checkout -b {name}", "/tmp/sandbox/repo")
            self.assertEqual(result, f"Switched to a new branch '{name}'")

    def test_invalid_branch_names(self):
        invalid_names = [
            "feat/login", # Wrong type (should be feature)
            "fix/crash",  # Wrong type (should be bugfix)
            "random-branch", # Missing type
            "feature/User-Login", # Uppercase not allowed
            "feature/user_login", # Underscore not allowed (kebab-case)
            "feature:user-login", # Colon not allowed
        ]

        for name in invalid_names:
            self.mock_sandbox.run_command.reset_mock()

            result = self.create_branch_tool.invoke({"branch_name": name})

            self.mock_sandbox.run_command.assert_not_called()
            self.assertTrue(result.startswith("ERROR: Branch"))

if __name__ == "__main__":
    unittest.main()
