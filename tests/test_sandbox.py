import unittest
from unittest.mock import MagicMock, patch
from app.sandbox.local import LocalSandbox
from app.config import settings
import os

class TestSandbox(unittest.TestCase):

    def test_local_sandbox(self):
        # We can test local sandbox logic without mocking too much
        sandbox = LocalSandbox("test-local")
        sandbox.setup()

        sandbox.write_file("test.txt", "hello")
        content = sandbox.read_file("test.txt")
        self.assertEqual(content, "hello")

        ls = sandbox.list_files(".")
        self.assertIn("test.txt", ls)

        # Test CWD tracking
        root = sandbox.get_root_path()
        self.assertEqual(sandbox.get_cwd(), root)

        new_cwd = os.path.join(root, "subdir")
        sandbox.set_cwd(new_cwd)
        self.assertEqual(sandbox.get_cwd(), new_cwd)

        sandbox.teardown()
        import shutil
        if os.path.exists(sandbox.workspace_path):
            shutil.rmtree(sandbox.workspace_path)

if __name__ == "__main__":
    unittest.main()
