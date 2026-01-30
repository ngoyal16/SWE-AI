import unittest
from unittest.mock import MagicMock, patch
from app.sandbox.k8s import K8sSandbox
from app.sandbox.local import LocalSandbox
from app.config import settings

class TestSandbox(unittest.TestCase):

    @patch("app.sandbox.k8s.kubernetes.config")
    @patch("app.sandbox.k8s.kubernetes.client.CoreV1Api")
    def test_k8s_sandbox_init(self, mock_v1, mock_config):
        sandbox = K8sSandbox("test-task")
        self.assertEqual(sandbox.pod_name, "swe-agent-worker-test-task")
        mock_v1.assert_called_once()

    @patch("app.sandbox.k8s.kubernetes.config")
    @patch("app.sandbox.k8s.kubernetes.client.CoreV1Api")
    def test_k8s_runtime_class(self, mock_v1, mock_config):
        # Mock settings.K8S_RUNTIME_CLASS
        with patch.object(settings, 'K8S_RUNTIME_CLASS', 'kata'):
            sandbox = K8sSandbox("test-runtime")
            # We need to mock create_namespaced_pod to check the body
            mock_v1_instance = mock_v1.return_value
            # Make read_namespaced_pod return Running so wait loop exits
            mock_pod = MagicMock()
            mock_pod.status.phase = "Running"
            mock_v1_instance.read_namespaced_pod.return_value = mock_pod

            sandbox.setup()

            mock_v1_instance.create_namespaced_pod.assert_called_once()
            args, kwargs = mock_v1_instance.create_namespaced_pod.call_args
            body = kwargs['body']
            self.assertEqual(body['spec']['runtimeClassName'], 'kata')

    @patch("app.sandbox.k8s.kubernetes.config")
    @patch("app.sandbox.k8s.kubernetes.client.CoreV1Api")
    @patch("app.sandbox.k8s.stream")
    def test_k8s_write_optimization(self, mock_stream, mock_v1, mock_config):
        # Test that write_file uses the optimized single command
        mock_v1_instance = mock_v1.return_value
        sandbox = K8sSandbox("test-opt")
        sandbox.v1 = mock_v1_instance

        # Mock stream response
        mock_stream.return_value = "Success"

        sandbox.write_file("path/to/file.txt", "content")

        # Verify call arguments
        # stream(connect, name, ns, command=[...])
        args, kwargs = mock_stream.call_args
        cmd_list = kwargs['command']
        cmd_str = cmd_list[2] # The actual shell command string

        print(f"Executed command: {cmd_str}")
        self.assertIn("mkdir -p /workspace/path/to", cmd_str) # Full path used
        self.assertIn("base64 -d > /workspace/path/to/file.txt", cmd_str)
        self.assertIn("&&", cmd_str) # Combined

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

import os
if __name__ == "__main__":
    unittest.main()
