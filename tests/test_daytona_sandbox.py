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

        # Mock Daytona instance
        mock_daytona_instance = mock_daytona_cls.return_value
        mock_sandbox_obj = MagicMock()
        mock_daytona_instance.create.return_value = mock_sandbox_obj

        # Run setup
        sandbox.setup()

        # Check config init
        mock_config.assert_called_with(
            api_key=settings.DAYTONA_API_KEY,
            server_url=settings.DAYTONA_SERVER_URL
        )

        # Check params creation
        mock_params.assert_called_with(
            name="swe-agent-test-session",
            image=settings.DAYTONA_TARGET_IMAGE
        )

        # Check create called
        mock_daytona_instance.create.assert_called_once()
        self.assertEqual(sandbox.sandbox, mock_sandbox_obj)

    @patch("app.sandbox.daytona.Daytona")
    def test_run_command(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        sandbox = DaytonaSandbox("test-cmd")
        mock_sandbox_obj = MagicMock()
        sandbox.sandbox = mock_sandbox_obj

        # Mock execution response
        mock_resp = MagicMock()
        mock_resp.result = "output"
        mock_resp.exit_code = 0
        mock_sandbox_obj.process.exec.return_value = mock_resp

        res = sandbox.run_command("echo hello")
        self.assertEqual(res, "output")
        mock_sandbox_obj.process.exec.assert_called_with("echo hello", cwd=None)

    @patch("app.sandbox.daytona.Daytona")
    def test_file_ops(self, mock_daytona_cls):
        from app.sandbox.daytona import DaytonaSandbox
        sandbox = DaytonaSandbox("test-files")
        mock_sandbox_obj = MagicMock()
        sandbox.sandbox = mock_sandbox_obj

        # Test read_file
        mock_sandbox_obj.fs.download_file.return_value = b"content"
        content = sandbox.read_file("file.txt")
        self.assertEqual(content, "content")
        mock_sandbox_obj.fs.download_file.assert_called_with("file.txt")

        # Test write_file
        res = sandbox.write_file("file.txt", "new content")
        self.assertIn("Successfully", res)
        mock_sandbox_obj.fs.upload_file.assert_called_with(b"new content", "file.txt")

        # Test list_files
        file1 = MagicMock()
        file1.name = "file1"
        file1.is_dir = False
        file2 = MagicMock()
        file2.name = "dir1"
        file2.is_dir = True

        mock_sandbox_obj.fs.list_files.return_value = [file1, file2]

        listing = sandbox.list_files(".")
        self.assertIn("file1", listing)
        self.assertIn("dir1/", listing)

if __name__ == "__main__":
    unittest.main()
