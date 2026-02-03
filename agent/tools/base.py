from langchain_core.tools import StructuredTool
from typing import List, Optional, Tuple
from ..sandbox.base import Sandbox


def create_filesystem_tools(sandbox: Sandbox) -> List[StructuredTool]:
    """Create basic filesystem tools for backward compatibility."""

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

    def edit_file(filepath: str, old_str: str, new_str: str) -> str:
        """Replaces old_str with new_str in the file. Returns success message or error."""
        try:
            content = sandbox.read_file(filepath)
        except Exception as e:
            return f"Error reading file: {str(e)}"

        if "Error:" in content and len(content) < 200:
            return content

        if old_str not in content:
            return f"Error: '{old_str}' not found in {filepath}."

        if content.count(old_str) > 1:
            return f"Error: '{old_str}' found multiple times in {filepath}. Please be more specific."

        new_content = content.replace(old_str, new_str)
        return sandbox.write_file(filepath, new_content)

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
            func=edit_file,
            name="edit_file",
            description="Replaces old_str with new_str in the file. Returns success message or error. Ensure old_str is unique."
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


# ============================================================================
# ENHANCED TOOLS (Inspired by open-swe)
# ============================================================================

def _view_file_with_range(sandbox: Sandbox, path: str, view_range: Optional[Tuple[int, int]] = None) -> str:
    """View a file with optional line range."""
    try:
        content = sandbox.read_file(path)
        
        if not content:
            return f"Error: File '{path}' is empty or could not be read."
        
        lines = content.splitlines()
        total_lines = len(lines)
        
        if view_range:
            start, end = view_range
            # Validate range
            if start < 1:
                start = 1
            if end == -1 or end > total_lines:
                end = total_lines
            if start > end:
                return f"Error: Invalid range. start ({start}) > end ({end})"
            
            # Convert to 0-indexed
            selected_lines = lines[start-1:end]
            # Add line numbers
            numbered = [f"{start + i}: {line}" for i, line in enumerate(selected_lines)]
            return f"File: {path} (lines {start}-{end} of {total_lines})\n" + "\n".join(numbered)
        else:
            # Add line numbers to all lines
            numbered = [f"{i+1}: {line}" for i, line in enumerate(lines)]
            return f"File: {path} ({total_lines} lines)\n" + "\n".join(numbered)
            
    except Exception as e:
        return f"Error reading file: {str(e)}"


def _str_replace(sandbox: Sandbox, path: str, old_str: str, new_str: str) -> str:
    """Replace exact string in file."""
    try:
        content = sandbox.read_file(path)
        
        if "Error:" in content and len(content) < 200:
            return content
        
        if old_str not in content:
            return f"Error: The old_str was not found in {path}. Make sure it matches exactly, including whitespace."
        
        count = content.count(old_str)
        if count > 1:
            return f"Error: old_str appears {count} times in {path}. Please make it more specific to match only once."
        
        new_content = content.replace(old_str, new_str, 1)
        result = sandbox.write_file(path, new_content)
        
        if "Error" in result:
            return result
        
        return f"Successfully replaced text in {path}."
        
    except Exception as e:
        return f"Error replacing text: {str(e)}"


def _create_file(sandbox: Sandbox, path: str, file_text: str) -> str:
    """Create a new file with content."""
    try:
        # Check if file exists
        existing = sandbox.read_file(path)
        if existing and "Error:" not in existing:
            return f"Error: File {path} already exists. Use str_replace command to modify existing files."
        
        result = sandbox.write_file(path, file_text)
        
        if "Error" in result:
            return result
        
        return f"Successfully created file {path}."
        
    except Exception as e:
        return f"Error creating file: {str(e)}"


def _insert_line(sandbox: Sandbox, path: str, insert_line: int, new_str: str) -> str:
    """Insert text after a specific line number."""
    try:
        content = sandbox.read_file(path)
        
        if "Error:" in content and len(content) < 200:
            return content
        
        lines = content.splitlines()
        total_lines = len(lines)
        
        if insert_line < 0 or insert_line > total_lines:
            return f"Error: insert_line {insert_line} is out of range (0-{total_lines})."
        
        # Insert after the specified line (0 means beginning)
        new_lines = new_str.splitlines()
        lines = lines[:insert_line] + new_lines + lines[insert_line:]
        
        new_content = "\n".join(lines)
        result = sandbox.write_file(path, new_content)
        
        if "Error" in result:
            return result
        
        return f"Successfully inserted {len(new_lines)} line(s) after line {insert_line} in {path}."
        
    except Exception as e:
        return f"Error inserting text: {str(e)}"


def _list_directory(sandbox: Sandbox, path: str) -> str:
    """List directory contents with details."""
    try:
        result = sandbox.run_command(f"ls -la {path}")
        return f"Directory listing of {path}:\n{result}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def create_text_editor_tool(sandbox: Sandbox) -> StructuredTool:
    """Creates an enhanced text editor tool with multiple commands."""
    
    def text_editor(
        command: str,
        path: str,
        view_range: Optional[List[int]] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        file_text: Optional[str] = None,
        insert_line: Optional[int] = None
    ) -> str:
        """
        A powerful text editor tool with multiple commands.
        
        Args:
            command: One of 'view', 'str_replace', 'create', 'insert'
            path: Path to the file or directory
            view_range: [start, end] line numbers for view command (1-indexed, -1 for end of file)
            old_str: Text to replace (for str_replace command)
            new_str: Replacement text (for str_replace and insert commands)
            file_text: Content for new file (for create command)
            insert_line: Line number after which to insert (for insert command, 0 for beginning)
        
        Returns:
            Result of the operation or file content
        """
        command = command.lower().strip()
        
        if command == "view":
            # Check if path is a directory
            check_dir = sandbox.run_command(f"test -d {path} && echo 'DIR' || echo 'FILE'")
            if "DIR" in check_dir:
                return _list_directory(sandbox, path)
            
            range_tuple = None
            if view_range and len(view_range) == 2:
                range_tuple = (view_range[0], view_range[1])
            return _view_file_with_range(sandbox, path, range_tuple)
        
        elif command == "str_replace":
            if old_str is None or new_str is None:
                return "Error: str_replace requires both old_str and new_str parameters."
            return _str_replace(sandbox, path, old_str, new_str)
        
        elif command == "create":
            if file_text is None:
                return "Error: create requires file_text parameter."
            return _create_file(sandbox, path, file_text)
        
        elif command == "insert":
            if insert_line is None or new_str is None:
                return "Error: insert requires both insert_line and new_str parameters."
            return _insert_line(sandbox, path, insert_line, new_str)
        
        else:
            return f"Error: Unknown command '{command}'. Use: view, str_replace, create, insert"
    
    return StructuredTool.from_function(
        func=text_editor,
        name="text_editor",
        description=(
            "A text editor tool with multiple commands:\n"
            "- view: Read file content with optional line range [start, end]. Can also view directory listings.\n"
            "- str_replace: Replace old_str with new_str in a file. old_str must match exactly once.\n"
            "- create: Create a new file with file_text content.\n"
            "- insert: Insert new_str after insert_line (0 for beginning of file).\n"
            "This tool is more reliable than write_file for code modifications."
        )
    )


def create_shell_tool(sandbox: Sandbox, timeout: int = 60) -> StructuredTool:
    """Creates an enhanced shell tool with timeout support."""
    
    def shell(command: str, workdir: Optional[str] = None, timeout_sec: int = 60) -> str:
        """
        Run a shell command with timeout support.
        
        Args:
            command: The shell command to execute
            workdir: Optional working directory for the command
            timeout_sec: Maximum time to wait (default 60 seconds)
        
        Returns:
            Command output or error message
        """
        try:
            full_cmd = command
            if workdir:
                full_cmd = f"cd {workdir} && {command}"
            
            result = sandbox.run_command(full_cmd)
            return result
            
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    return StructuredTool.from_function(
        func=shell,
        name="shell",
        description=(
            "Execute a shell command and return its output. "
            "Use for running tests, builds, git commands, or any shell operation. "
            "Optionally specify a working directory."
        )
    )


def create_enhanced_tools(sandbox: Sandbox) -> List[StructuredTool]:
    """Creates the enhanced tool set with text_editor, shell, and basic tools."""
    from .grep_tool import create_grep_tool
    
    return [
        create_text_editor_tool(sandbox),
        create_shell_tool(sandbox),
        create_grep_tool(sandbox),
        StructuredTool.from_function(
            func=lambda path=".": sandbox.list_files(path),
            name="list_files",
            description="Lists files in a directory."
        ),
    ]


# Backward compatibility
# We keep the old create_filesystem_tools for migration period
