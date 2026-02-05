from langchain_core.tools import StructuredTool
from ..sandbox.base import Sandbox
from typing import List, Optional
import shlex

def create_navigation_tools(sandbox: Sandbox) -> List[StructuredTool]:
    """Creates navigation tools: list_directory and find_file."""

    def list_directory(path: str = ".", depth: int = 1) -> str:
        """
        Lists files and directories in the given path.

        Args:
            path: The directory path to list. Defaults to current directory.
            depth: How deep to traverse. Default is 1 (immediate children).
                   Use higher values with caution to avoid massive output.
        """
        try:
            # Validate depth to prevent token explosion
            if depth > 3:
                return "Error: Max depth is 3. For deeper searches, use find_file."

            # Escape path for safety
            safe_path = shlex.quote(path)

            if depth == 1:
                cmd = f"ls -F {safe_path}"
            else:
                # Basic emulation of depth with ls if tree isn't guaranteed
                # But typically 'find' is better for depth.
                # Let's stick to ls for depth=1 and find for depth>1
                cmd = f"find {safe_path} -maxdepth {depth} -not -path '*/.*'"

            result = sandbox.run_command(cmd)

            # Simple output filtering
            if not result or result.strip() == "":
                return "Directory is empty or path does not exist."

            return result

        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def find_file(filename: str, path: str = ".") -> str:
        """
        Finds a file by name (exact or wildcard) starting from the given path.

        Args:
            filename: The filename to search for (e.g. 'user.py' or '*.json').
            path: The starting directory. Defaults to root (.).
        """
        try:
            # Sanitize filename to prevent injection (basic)
            # We use shlex.quote for the path, and careful quoting for the name pattern
            # Note: We want to preserve wildcards in filename if they are intended,
            # but usually the user just passes a name.
            # find -name 'pattern' handles wildcards safely if the pattern itself is quoted.

            # Escape the pattern itself for the shell, so '*' isn't expanded by the shell before find sees it
            safe_filename = shlex.quote(filename)
            safe_path = shlex.quote(path)

            # Exclude common noise directories
            excludes = "-not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*'"

            cmd = f"find {safe_path} -name {safe_filename} {excludes}"
            result = sandbox.run_command(cmd)

            if not result or result.strip() == "":
                return f"No files found matching '{filename}'."

            return result

        except Exception as e:
            return f"Error finding file: {str(e)}"

    return [
        StructuredTool.from_function(
            func=list_directory,
            name="list_directory",
            description="List files in a directory. Use this to explore the file structure. supports depth."
        ),
        StructuredTool.from_function(
            func=find_file,
            name="find_file",
            description="Find a file by name. Use this to locate specific files instantly."
        )
    ]
