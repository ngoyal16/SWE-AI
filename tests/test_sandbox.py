import unittest
from unittest.mock import MagicMock, patch
from app.sandbox.k8s import K8sSandbox
from app.sandbox.local import LocalSandbox

class TestSandbox(unittest.TestCase):

    @patch("app.sandbox.k8s.kubernetes.config")
    @patch("app.sandbox.k8s.kubernetes.client.CoreV1Api")
    def test_k8s_sandbox_init(self, mock_v1, mock_config):
        sandbox = K8sSandbox("test-task")
        self.assertEqual(sandbox.pod_name, "swe-agent-worker-test-task")
        mock_v1.assert_called_once()

    def test_local_sandbox(self):
        # We can test local sandbox logic without mocking too much
        sandbox = LocalSandbox("test-local")
        sandbox.setup()

        sandbox.write_file("test.txt", "hello")
        content = sandbox.read_file("test.txt")
        self.assertEqual(content, "hello")

        ls = sandbox.list_files(".")
        self.assertIn("test.txt", ls)

        sandbox.teardown()
        import shutil
        if os.path.exists(sandbox.workspace_path):
            shutil.rmtree(sandbox.workspace_path)

import os
if __name__ == "__main__":
    unittest.main()
