import unittest
from unittest.mock import MagicMock
from app.git_tools import create_git_tools

class TestGitToolsExpansion(unittest.TestCase):
    def test_create_git_tools_length(self):
        mock_sandbox = MagicMock()
        tools = create_git_tools(mock_sandbox)
        tool_names = [t.name for t in tools]
        
        expected_tools = [
            "clone_repo", "create_branch", "checkout_branch", "commit_changes", 
            "push_changes", "git_status", "git_diff", "git_log", "git_restore", "git_blame"
        ]
        
        for name in expected_tools:
            self.assertIn(name, tool_names)
        
        self.assertEqual(len(tools), 10)

if __name__ == "__main__":
    unittest.main()
