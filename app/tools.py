import os
import subprocess
from langchain_core.tools import StructuredTool
from typing import List

def create_filesystem_tools(workspace_root: str) -> List[StructuredTool]:

    def get_safe_path(filepath: str) -> str:
        abs_path = os.path.abspath(os.path.join(workspace_root, filepath))
        if not abs_path.startswith(os.path.abspath(workspace_root)):
            raise ValueError("Access outside workspace is denied.")
        return abs_path

    def read_file(filepath: str) -> str:
        """Reads the content of a file."""
        try:
            path = get_safe_path(filepath)
            if not os.path.exists(path):
                return f"Error: File {filepath} does not exist."
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(filepath: str, content: str) -> str:
        """Writes content to a file. Overwrites if it exists."""
        try:
            path = get_safe_path(filepath)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def list_files(path: str = ".") -> str:
        """Lists files in a directory."""
        try:
            target_path = get_safe_path(path)
            if not os.path.exists(target_path):
                 return f"Error: Path {path} does not exist."

            files = os.listdir(target_path)
            # Add trailing slash for directories for clarity
            formatted_files = []
            for f in files:
                if os.path.isdir(os.path.join(target_path, f)):
                    formatted_files.append(f + "/")
                else:
                    formatted_files.append(f)
            return "\n".join(formatted_files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def run_command(command: str) -> str:
        """Runs a shell command and returns the output."""
        try:
            # Running in the workspace directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=60 # Safety timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out."
        except Exception as e:
            return f"Error running command: {str(e)}"

    return [
        StructuredTool.from_function(
            func=read_file,
            name="read_file",
            description="Reads the content of a file."
        ),
        StructuredTool.from_function(
            func=write_file,
            name="write_file",
            description="Writes content to a file. Overwrites if it exists."
        ),
        StructuredTool.from_function(
            func=list_files,
            name="list_files",
            description="Lists files in a directory."
        ),
        StructuredTool.from_function(
            func=run_command,
            name="run_command",
            description="Runs a shell command and returns the output."
        )
    ]

# Backward compatibility for existing tests/code until fully refactored
from app.config import settings
def get_tools():
    return create_filesystem_tools(settings.WORKSPACE_DIR)
