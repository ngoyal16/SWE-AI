from langchain_core.tools import StructuredTool
from typing import List
from app.sandbox.base import Sandbox

def create_filesystem_tools(sandbox: Sandbox) -> List[StructuredTool]:

    def read_file(filepath: str) -> str:
        """Reads the content of a file."""
        return sandbox.read_file(filepath)

    def write_file(filepath: str, content: str) -> str:
        """Writes content to a file. Overwrites if it exists."""
        return sandbox.write_file(filepath, content)

    def list_files(path: str = ".") -> str:
        """Lists files in a directory."""
        return sandbox.list_files(path)

    def run_command(command: str) -> str:
        """Runs a shell command and returns the output."""
        return sandbox.run_command(command)

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

# Backward compatibility (only if settings still available, but we need sandbox now)
# We remove the backward compat get_tools that used settings directly to force migration.
