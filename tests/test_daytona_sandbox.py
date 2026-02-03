import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock daytona module if not present (though it is installed in this env)
# But verifying we can mock it is good practice.

class TestDaytonaSandbox(unittest.TestCase):

    @patch("app.sandbox.daytona.Daytona")
    @patch("app.sandbox.daytona.DaytonaConfig")
    @patch("app.sandbox.daytona.CreateSandboxFromImageParams")
    def test_setup_creates_sandbox(self, mock_params, mock_config, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        from app.config import settings

        sandbox = DaytonaSandbox("test-session")

        with patch.object(settings, 'DAYTONA_SNAPSHOT_NAME', ''):
            # Mock Daytona instance
            from daytona import DaytonaNotFoundError
            mock_daytona_instance = mock_daytona_cls.return_value
            mock_daytona_instance.find_one.side_effect = DaytonaNotFoundError("No sandbox found")
            mock_sandbox_obj = MagicMock()
            mock_daytona_instance.create.return_value = mock_sandbox_obj

            # Run setup
            sandbox.setup()

            # Check config init
            mock_config.assert_called_with(
                api_key=settings.DAYTONA_API_KEY
            )

            # Check params creation
            mock_params.assert_called()
            args, kwargs = mock_params.call_args
            self.assertEqual(kwargs['image'], settings.DAYTONA_TARGET_IMAGE)
            self.assertEqual(kwargs['labels'], {"session_id": "test-session"})

            # Check create called
            mock_daytona_instance.create.assert_called_once()
            self.assertEqual(sandbox.sandbox, mock_sandbox_obj)

    @patch("app.sandbox.daytona.Daytona")
    @patch("app.sandbox.daytona.DaytonaConfig")
    @patch("app.sandbox.daytona.CreateSandboxFromImageParams")
    def test_setup_with_repo_metadata(self, mock_params, mock_config, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        from app.config import settings
        from app.common.credentials import GitCredentials

        repo_url = "https://github.com/test/repo"
        base_branch = "develop"
        git_credentials = GitCredentials(
            token="test-token",
            username="x-access-token",
            author_name="swe-agent",
            author_email="swe-agent@example.com",
            co_author_name="John Doe",
            co_author_email="john@example.com"
        )
        sandbox = DaytonaSandbox("test-session", repo_url=repo_url, base_branch=base_branch, git_credentials=git_credentials)

        with patch.object(settings, 'DAYTONA_SNAPSHOT_NAME', ''):
            from daytona import DaytonaNotFoundError
            mock_daytona_instance = mock_daytona_cls.return_value
            mock_daytona_instance.find_one.side_effect = DaytonaNotFoundError("No sandbox found")
            
            sandbox.setup()

            # Check labels
            args, kwargs = mock_params.call_args
            expected_labels = {
                "session_id": "test-session",
                "repo_url": repo_url,
                "base_branch": base_branch,
                "git_co_author_name": "John Doe",
                "git_co_author_email": "john@example.com"
            }
            self.assertEqual(kwargs['labels'], expected_labels)

    @patch("app.sandbox.daytona.Daytona")
    @patch("app.sandbox.daytona.DaytonaConfig")
    @patch("app.sandbox.daytona.CreateSandboxFromSnapshotParams")
    def test_setup_creates_sandbox_from_snapshot(self, mock_params, mock_config, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        from app.config import settings

        sandbox = DaytonaSandbox("test-session-snapshot")

        with patch.object(settings, 'DAYTONA_SNAPSHOT_NAME', 'test-snapshot'):
            # Mock Daytona instance
            from daytona import DaytonaNotFoundError
            mock_daytona_instance = mock_daytona_cls.return_value
            mock_daytona_instance.find_one.side_effect = DaytonaNotFoundError("No sandbox found")
            mock_sandbox_obj = MagicMock()
            mock_daytona_instance.create.return_value = mock_sandbox_obj

            # Run setup
            sandbox.setup()

            # Check create called with snapshot params
            mock_daytona_instance.create.assert_called_once()
            args, kwargs = mock_params.call_args
            self.assertEqual(kwargs['snapshot'], "test-snapshot")
            self.assertEqual(sandbox.sandbox, mock_sandbox_obj)

    @patch("app.sandbox.daytona.Daytona")
    def test_setup_resumes_sandbox(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        sandbox = DaytonaSandbox("test-resume")

        mock_daytona_instance = mock_daytona_cls.return_value
        mock_sandbox_obj = MagicMock()
        mock_sandbox_obj.id = "existing-id"
        mock_sandbox_obj.state = "stopped"
        mock_daytona_instance.find_one.return_value = mock_sandbox_obj

        # Run setup
        sandbox.setup()

        # Check if find_one was called
        mock_daytona_instance.find_one.assert_called_once()
        # Check if start was called since it was stopped
        mock_sandbox_obj.start.assert_called_once()
        self.assertEqual(sandbox.sandbox, mock_sandbox_obj)

    @patch("app.sandbox.daytona.Daytona")
    def test_run_command(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        from app.common.credentials import GitCredentials
        
        git_credentials = GitCredentials(
            token="test-token",
            username="x-access-token",
            author_name="swe-agent",
            author_email="swe-agent@example.com",
            co_author_name="John Doe",
            co_author_email="john@example.com"
        )
        sandbox = DaytonaSandbox("test-cmd", git_credentials=git_credentials)
        mock_sandbox_obj = MagicMock()
        sandbox.sandbox = mock_sandbox_obj

        # Mock execution response
        mock_resp = MagicMock()
        mock_resp.result = "output"
        mock_resp.exit_code = 0
        mock_sandbox_obj.process.exec.return_value = mock_resp

        res = sandbox.run_command("echo hello")
        self.assertEqual(res, "output")
        # Check if default env (including user meta) was passed
        kwargs = mock_sandbox_obj.process.exec.call_args.kwargs
        self.assertEqual(kwargs['env']['COREPACK_ENABLE_DOWNLOAD_PROMPT'], "0")
        self.assertEqual(kwargs['env']['GIT_CO_AUTHOR_NAME'], "John Doe")
        self.assertEqual(kwargs['env']['GIT_CO_AUTHOR_EMAIL'], "john@example.com")

    @patch("app.sandbox.daytona.Daytona")
    def test_file_ops(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        sandbox = DaytonaSandbox("test-files")
        mock_sandbox_obj = MagicMock()
        sandbox.sandbox = mock_sandbox_obj
        mock_sandbox_obj.get_work_dir.return_value = "/workspace"
        sandbox.set_cwd("/workspace/repo")

        # Test read_file with relative path
        mock_sandbox_obj.fs.download_file.return_value = b"content"
        content = sandbox.read_file("file.txt")
        self.assertEqual(content, "content")
        mock_sandbox_obj.fs.download_file.assert_called_with("/workspace/repo/file.txt")

        # Test write_file with relative path
        res = sandbox.write_file("file.txt", "new content")
        self.assertIn("Successfully", res)
        mock_sandbox_obj.fs.upload_file.assert_called_with(b"new content", "/workspace/repo/file.txt")

        # Test list_files with '.'
        file1 = MagicMock()
        file1.name = "file1"
        file1.is_dir = False
        mock_sandbox_obj.fs.list_files.return_value = [file1]

        listing = sandbox.list_files(".")
        self.assertIn("file1", listing)
        mock_sandbox_obj.fs.list_files.assert_called_with("/workspace/repo")

    @patch("app.sandbox.daytona.Daytona")
    def test_git_ops(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        sandbox = DaytonaSandbox("test-git")
        mock_sandbox_obj = MagicMock()
        sandbox.sandbox = mock_sandbox_obj
        mock_sandbox_obj.get_work_dir.return_value = "/workspace"

        # Test clone_repo
        sandbox.clone_repo("https://github.com/test/repo.git", branch="main")
        mock_sandbox_obj.git.clone.assert_called_with(
            "https://github.com/test/repo.git", "/workspace/repo", branch="main", token=None
        )
        self.assertEqual(sandbox.get_cwd(), "/workspace/repo")

        # Test pull_latest_changes
        sandbox.pull_latest_changes()
        mock_sandbox_obj.git.pull.assert_called_with("/workspace/repo", token=None)

    @patch("app.sandbox.daytona.Daytona")
    def test_tree_generation(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        sandbox = DaytonaSandbox("test-tree")
        mock_sandbox_obj = MagicMock()
        sandbox.sandbox = mock_sandbox_obj
        mock_sandbox_obj.get_work_dir.return_value = "/workspace"
        sandbox.set_cwd("/workspace/repo")

        mock_resp = MagicMock()
        mock_resp.result = "tree structure"
        mock_sandbox_obj.process.exec.return_value = mock_resp

        res = sandbox.generate_codebase_tree(depth=2)
        self.assertEqual(res, "tree structure")
        
        # Verify it used the repo CWD
        kwargs = mock_sandbox_obj.process.exec.call_args.kwargs
        self.assertEqual(kwargs['cwd'], "/workspace/repo")
        self.assertIn("-L 2", mock_sandbox_obj.process.exec.call_args.args[0])

if __name__ == "__main__":
    unittest.main()
