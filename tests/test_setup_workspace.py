import unittest
from unittest.mock import MagicMock
from app.git_tools import create_git_tools

class TestSetupWorkspace(unittest.TestCase):
    def test_setup_workspace_success(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox/repo"

        def side_effect(cmd, *args, **kwargs):
            if "test -d" in cmd:
                return "" # Not exists
            if "git clone" in cmd:
                return "Cloning into 'repo'..."
            if "git checkout develop" in cmd:
                return "Switched to branch 'develop'"
            return ""

        mock_sandbox.run_command.side_effect = side_effect
        mock_sandbox.list_files.return_value = "repo/\n"

        tools = create_git_tools(mock_sandbox)
        setup_tool = next(t for t in tools if t.name == "setup_workspace")

        result = setup_tool.invoke({"repo_url": "https://github.com/test/repo.git", "base_branch": "develop"})

        # clone_repo returns "Successfully cloned..." if "Error" not in res
        self.assertIn("Successfully cloned", result)
        self.assertIn("Checked out base branch 'develop'", result)

    def test_setup_workspace_already_exists(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox/repo"

        def side_effect(cmd, *args, **kwargs):
            if "test -d" in cmd:
                return "EXISTS"
            if "git checkout develop" in cmd:
                return "Switched to branch 'develop'"
            if "git fetch" in cmd:
                return ""
            return ""

        mock_sandbox.run_command.side_effect = side_effect
        mock_sandbox.list_files.return_value = "repo/\n"

        tools = create_git_tools(mock_sandbox)
        setup_tool = next(t for t in tools if t.name == "setup_workspace")

        result = setup_tool.invoke({"repo_url": "https://github.com/test/repo.git", "base_branch": "develop"})

        self.assertIn("Repository already exists", result)
        self.assertIn("Checked out base branch 'develop'", result)

    def test_setup_workspace_branch_not_found(self):
        mock_sandbox = MagicMock()
        mock_sandbox.get_root_path.return_value = "/tmp/sandbox"
        mock_sandbox.get_cwd.return_value = "/tmp/sandbox/repo"

        def side_effect(cmd, *args, **kwargs):
            if "test -d" in cmd:
                return ""
            if "git clone" in cmd:
                return "Cloning into 'repo'..."
            if "git checkout bad-branch" in cmd:
                return "error: pathspec 'bad-branch' did not match any file(s) known to git"
            return ""

        mock_sandbox.run_command.side_effect = side_effect
        mock_sandbox.list_files.return_value = "repo/\n"

        tools = create_git_tools(mock_sandbox)
        setup_tool = next(t for t in tools if t.name == "setup_workspace")

        result = setup_tool.invoke({"repo_url": "https://github.com/test/repo.git", "base_branch": "bad-branch"})

        self.assertIn("Successfully cloned", result)
        self.assertIn("Warning: Base branch 'bad-branch' not found", result)

if __name__ == "__main__":
    unittest.main()
