import os
import shutil
import subprocess
from app.sandbox.base import Sandbox
from app.config import settings

class LocalSandbox(Sandbox):
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.workspace_path = os.path.join(settings.WORKSPACE_DIR, task_id)

    def setup(self):
        os.makedirs(self.workspace_path, exist_ok=True)
        return self

    def teardown(self):
        # Optional: cleanup workspace
        # shutil.rmtree(self.workspace_path)
        pass

    def get_root_path(self) -> str:
        return self.workspace_path

    def _get_safe_path(self, filepath: str) -> str:
        cwd = self.workspace_path
        abs_path = os.path.abspath(os.path.join(cwd, filepath))
        if not abs_path.startswith(os.path.abspath(cwd)):
            raise ValueError("Access outside workspace is denied.")
        return abs_path

    def run_command(self, command: str, cwd: str = None) -> str:
        target_cwd = self.workspace_path
        if cwd:
            # Handle relative path joining
            if not os.path.isabs(cwd):
                target_cwd = os.path.join(self.workspace_path, cwd)
            else:
                target_cwd = cwd

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out."
        except Exception as e:
            return f"Error running command: {str(e)}"

    def read_file(self, filepath: str) -> str:
        try:
            path = self._get_safe_path(filepath)
            if not os.path.exists(path):
                return f"Error: File {filepath} does not exist."
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, filepath: str, content: str) -> str:
        try:
            path = self._get_safe_path(filepath)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def list_files(self, path: str) -> str:
        try:
            target_path = self._get_safe_path(path)
            if not os.path.exists(target_path):
                 return f"Error: Path {path} does not exist."

            files = os.listdir(target_path)
            formatted_files = []
            for f in files:
                if os.path.isdir(os.path.join(target_path, f)):
                    formatted_files.append(f + "/")
                else:
                    formatted_files.append(f)
            return "\n".join(formatted_files)
        except Exception as e:
            return f"Error listing files: {str(e)}"
