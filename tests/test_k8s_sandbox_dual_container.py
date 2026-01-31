import unittest
from unittest.mock import MagicMock, patch
from app.sandbox.k8s import K8sSandbox
from app.config import settings

class TestK8sSandboxUpdate(unittest.TestCase):

    @patch("app.sandbox.k8s.kubernetes.config")
    @patch("app.sandbox.k8s.kubernetes.client.CoreV1Api")
    def test_k8s_setup_dual_containers(self, mock_v1, mock_config):
        # Setup mocks
        mock_v1_instance = mock_v1.return_value
        mock_pod = MagicMock()
        mock_pod.status.phase = "Running"
        mock_v1_instance.read_namespaced_pod.return_value = mock_pod

        # Instantiate Sandbox
        sandbox = K8sSandbox("test-dual-container")
        sandbox.setup()

        # Check create_namespaced_pod call
        mock_v1_instance.create_namespaced_pod.assert_called_once()
        args, kwargs = mock_v1_instance.create_namespaced_pod.call_args
        body = kwargs['body']

        containers = body['spec']['containers']
        self.assertEqual(len(containers), 2)

        worker = next(c for c in containers if c['name'] == 'worker')
        sandbox_c = next(c for c in containers if c['name'] == 'sandbox')

        self.assertEqual(worker['image'], settings.WORKER_IMAGE)
        self.assertEqual(sandbox_c['image'], settings.SANDBOX_IMAGE)
        self.assertEqual(sandbox_c['command'], ['sleep', 'infinity'])

    @patch("app.sandbox.k8s.kubernetes.config")
    @patch("app.sandbox.k8s.kubernetes.client.CoreV1Api")
    @patch("app.sandbox.k8s.stream")
    def test_k8s_run_command_targets_sandbox(self, mock_stream, mock_v1, mock_config):
        # Setup mocks
        mock_v1_instance = mock_v1.return_value
        sandbox = K8sSandbox("test-exec")
        sandbox.v1 = mock_v1_instance

        # Call run_command
        sandbox.run_command("echo hello")

        # Check stream call
        mock_stream.assert_called_once()
        args, kwargs = mock_stream.call_args

        self.assertEqual(kwargs['container'], "sandbox")

if __name__ == "__main__":
    unittest.main()
