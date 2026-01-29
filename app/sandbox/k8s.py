import time
import kubernetes.client
import kubernetes.config
from kubernetes.stream import stream
from app.sandbox.base import Sandbox
from app.config import settings
import base64
import os

class K8sSandbox(Sandbox):
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.pod_name = f"swe-agent-worker-{task_id}"
        self.namespace = settings.K8S_NAMESPACE
        self.workspace_root = "/workspace" # Inside the pod

        # Initialize client (assumes running in-cluster or kubeconfig is set)
        try:
            kubernetes.config.load_incluster_config()
        except:
            try:
                kubernetes.config.load_kube_config()
            except:
                print("Warning: Could not load kubernetes config")

        self.v1 = kubernetes.client.CoreV1Api()

    def setup(self):
        # Define Pod
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": self.pod_name,
                "labels": {"app": "swe-agent-worker", "task_id": self.task_id}
            },
            "spec": {
                "containers": [{
                    "name": "worker",
                    "image": settings.WORKER_IMAGE,
                    "command": ["/bin/sh", "-c", "sleep infinity"], # Keep alive
                    "volumeMounts": [{
                        "name": "workspace",
                        "mountPath": self.workspace_root
                    }]
                }],
                "volumes": [{
                    "name": "workspace",
                    "emptyDir": {} # Ephemeral storage for the task
                }],
                "restartPolicy": "Never"
            }
        }

        try:
            self.v1.create_namespaced_pod(body=pod_manifest, namespace=self.namespace)
            self._wait_for_pod_ready()
        except Exception as e:
            # If pod already exists (e.g. retry), check status
            print(f"Error creating pod: {e}")
            self._wait_for_pod_ready()

        return self

    def _wait_for_pod_ready(self):
        print(f"Waiting for pod {self.pod_name} to be ready...")
        while True:
            resp = self.v1.read_namespaced_pod(name=self.pod_name, namespace=self.namespace)
            if resp.status.phase == 'Running':
                break
            if resp.status.phase in ['Failed', 'Succeeded']:
                raise Exception(f"Pod failed or finished unexpectedly: {resp.status.phase}")
            time.sleep(1)

    def teardown(self):
        try:
            self.v1.delete_namespaced_pod(name=self.pod_name, namespace=self.namespace)
        except Exception as e:
            print(f"Error deleting pod: {e}")

    def get_root_path(self) -> str:
        return self.workspace_root

    def run_command(self, command: str, cwd: str = None) -> str:
        if not cwd:
            cwd = self.workspace_root

        # Wrap command to run in specific cwd
        # Note: 'cd' only affects the shell, so we wrap in sh
        full_command = f"cd {cwd} && {command}"

        try:
            resp = stream(self.v1.connect_get_namespaced_pod_exec,
                          self.pod_name,
                          self.namespace,
                          command=['/bin/sh', '-c', full_command],
                          stderr=True, stdin=False,
                          stdout=True, tty=False)
            return resp
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def read_file(self, filepath: str) -> str:
        path = f"{self.workspace_root}/{filepath}"
        if filepath.startswith("/"):
            path = filepath

        return self.run_command(f"cat {path}")

    def write_file(self, filepath: str, content: str) -> str:
        path = f"{self.workspace_root}/{filepath}"
        if filepath.startswith("/"):
            path = filepath

        # Optimize: Combined mkdir and write to save a network RTT
        dir_path = os.path.dirname(path)
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        # Single command: mkdir -p dir && echo base64 | base64 -d > file
        cmd = f"mkdir -p {dir_path} && echo {encoded} | base64 -d > {path}"

        res = self.run_command(cmd)
        if "Error" in res:
             return res
        return f"Successfully wrote to {filepath}"

    def list_files(self, path: str) -> str:
        target_path = f"{self.workspace_root}/{path}"
        if path.startswith("/"):
            target_path = path

        return self.run_command(f"ls -F {target_path}")
