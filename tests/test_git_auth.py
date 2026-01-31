import unittest
from unittest.mock import patch, MagicMock
import json
from app.git_tools import _add_auth_to_url

class TestGitAuth(unittest.TestCase):

    @patch('app.git_tools.settings')
    def test_git_host_token_priority(self, mock_settings):
        # Setup
        mock_settings.GIT_USERNAME = "myuser"
        mock_settings.GIT_TOKEN = "legacy_token"
        mock_settings.GIT_HOST_TOKENS = json.dumps({"gitlab.com": "gl_token"})

        url = "https://gitlab.com/user/repo.git"
        expected = "https://myuser:gl_token@gitlab.com/user/repo.git"

        self.assertEqual(_add_auth_to_url(url), expected)

    @patch('app.git_tools.settings')
    def test_fallback_to_git_token(self, mock_settings):
        # Setup
        mock_settings.GIT_USERNAME = "myuser"
        mock_settings.GIT_TOKEN = "legacy_token"
        mock_settings.GIT_HOST_TOKENS = ""

        url = "https://github.com/user/repo.git"
        expected = "https://myuser:legacy_token@github.com/user/repo.git"

        self.assertEqual(_add_auth_to_url(url), expected)

    @patch('app.git_tools.settings')
    def test_self_hosted_token(self, mock_settings):
        # Setup
        mock_settings.GIT_USERNAME = "corpuser"
        mock_settings.GIT_TOKEN = "legacy_token"
        mock_settings.GIT_HOST_TOKENS = json.dumps({"git.mycorp.com": "corp_token"})

        url = "https://git.mycorp.com/user/repo.git"
        expected = "https://corpuser:corp_token@git.mycorp.com/user/repo.git"

        self.assertEqual(_add_auth_to_url(url), expected)

    @patch('app.git_tools.settings')
    def test_pre_authenticated_url(self, mock_settings):
        # Setup
        mock_settings.GIT_TOKEN = "legacy_token"
        mock_settings.GIT_USERNAME = "myuser"

        url = "https://user:pass@github.com/user/repo.git"
        # Should not change
        self.assertEqual(_add_auth_to_url(url), url)

    @patch('app.git_tools.settings')
    def test_default_username_fallback(self, mock_settings):
        # Setup
        mock_settings.GIT_USERNAME = "" # Empty
        mock_settings.GIT_TOKEN = "generic_token"
        mock_settings.GIT_HOST_TOKENS = ""

        url = "https://bitbucket.org/user/repo.git"
        # Fallback to "oauth2" if GIT_USERNAME is missing
        expected = "https://oauth2:generic_token@bitbucket.org/user/repo.git"

        self.assertEqual(_add_auth_to_url(url), expected)

    @patch('app.git_tools.settings')
    def test_no_tokens(self, mock_settings):
        mock_settings.GIT_HOST_TOKENS = ""
        mock_settings.GIT_TOKEN = ""
        mock_settings.GIT_USERNAME = "myuser"

        url = "https://github.com/user/repo.git"
        self.assertEqual(_add_auth_to_url(url), url)

if __name__ == "__main__":
    unittest.main()
