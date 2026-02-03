from langchain_core.tools import StructuredTool
from ..sandbox.base import Sandbox
from typing import List

def create_editor_tools(sandbox: Sandbox) -> List[StructuredTool]:
    """Creates file editing tools: view_file and replace_in_file."""

    def view_file(filepath: str, start_line: int = 1, end_line: int = -1) -> str:
        """
        Reads a file and returns the content with line numbers.

        Args:
            filepath: The path to the file.
            start_line: The first line to read (1-indexed). Default is 1.
            end_line: The last line to read (1-indexed). Default is -1 (end of file).
        """
        try:
            content = sandbox.read_file(filepath)
            # Check for error message from sandbox (usually short)
            if content.startswith("Error") and len(content) < 200:
                 return content

            lines = content.splitlines()
            total_lines = len(lines)

            if start_line < 1:
                start_line = 1
            if end_line == -1 or end_line > total_lines:
                end_line = total_lines

            if start_line > end_line:
                return f"Error: start_line ({start_line}) is greater than end_line ({end_line})."

            # 0-indexed slicing
            selected_lines = lines[start_line-1 : end_line]

            output = []
            output.append(f"File: {filepath} ({total_lines} lines)")
            output.append(f"Showing lines {start_line} to {end_line}:")
            output.append("```")
            for i, line in enumerate(selected_lines):
                output.append(f"{start_line + i}: {line}")
            output.append("```")

            return "\n".join(output)

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def replace_in_file(filepath: str, search_block: str, replace_block: str) -> str:
        """
        Replaces a block of text in a file with a new block.
        The search_block must match exactly (including whitespace and indentation).
        """
        try:
            content = sandbox.read_file(filepath)
            if content.startswith("Error") and len(content) < 200:
                return content

            if search_block not in content:
                # Provide a helpful error message
                return (
                    f"Error: `search_block` not found in {filepath}.\n"
                    "Please ensure you have captured the exact content including correct indentation.\n"
                    "Use `view_file` to verify the exact content."
                )

            if content.count(search_block) > 1:
                return (
                    f"Error: `search_block` matches multiple locations in {filepath}.\n"
                    "Please provide more context in your `search_block` to make it unique."
                )

            new_content = content.replace(search_block, replace_block)
            result = sandbox.write_file(filepath, new_content)

            if "Error" in result:
                return result

            return f"Successfully replaced block in {filepath}."

        except Exception as e:
            return f"Error replacing in file: {str(e)}"

    return [
        StructuredTool.from_function(
            func=view_file,
            name="view_file",
            description="Read a file with line numbers. Supports optional start_line and end_line range."
        ),
        StructuredTool.from_function(
            func=replace_in_file,
            name="replace_in_file",
            description="Replace an exact block of text in a file with a new block. search_block must match exactly."
        )
    ]
