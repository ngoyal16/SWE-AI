"""
Grep Tool - Ripgrep-based codebase search with advanced filtering.

Inspired by open-swe grep implementation but adapted for Python/sandbox model.
"""
from langchain_core.tools import StructuredTool
from typing import List, Optional
from ..sandbox.base import Sandbox


def _escape_shell_arg(arg: str) -> str:
    """Escapes a string for safe use in shell commands."""
    return "'" + arg.replace("'", "'\\''") + "'"


def _format_grep_command(
    query: str,
    match_string: bool = False,
    case_sensitive: bool = False,
    context_lines: int = 0,
    exclude_files: Optional[str] = None,
    include_files: Optional[str] = None,
    max_results: int = 0,
    file_types: Optional[List[str]] = None,
    follow_symlinks: bool = False
) -> List[str]:
    """Formats a ripgrep command with the given options."""
    args = ["rg", "--color=never", "--line-number", "--heading"]
    
    # Case sensitivity
    if not case_sensitive:
        args.append("-i")
    
    # Regex vs fixed string
    if match_string:
        args.append("--fixed-strings")
    
    # Context lines
    if context_lines and context_lines > 0:
        args.extend(["-C", str(context_lines)])
    
    # File globs
    if include_files:
        args.extend(["--glob", _escape_shell_arg(include_files)])
    
    if exclude_files:
        args.extend(["--glob", _escape_shell_arg(f"!{exclude_files}")])
    
    # File types (extensions)
    if file_types:
        for ext in file_types:
            normalized_ext = ext if ext.startswith(".") else f".{ext}"
            args.extend(["--glob", _escape_shell_arg(f"**/*{normalized_ext}")])
    
    # Follow symlinks
    if follow_symlinks:
        args.append("-L")
    
    # Max results
    if max_results and max_results > 0:
        args.extend(["--max-count", str(max_results)])
    
    # The search query
    if query:
        args.append(_escape_shell_arg(query))
    
    return args


def grep_search(
    sandbox: Sandbox,
    query: str,
    match_string: bool = False,
    case_sensitive: bool = False,
    context_lines: int = 0,
    exclude_files: Optional[str] = None,
    include_files: Optional[str] = None,
    max_results: int = 50,
    file_types: Optional[List[str]] = None,
    follow_symlinks: bool = False
) -> str:
    """Executes a ripgrep search in the repository."""
    try:
        command_parts = _format_grep_command(
            query=query,
            match_string=match_string,
            case_sensitive=case_sensitive,
            context_lines=context_lines,
            exclude_files=exclude_files,
            include_files=include_files,
            max_results=max_results,
            file_types=file_types,
            follow_symlinks=follow_symlinks
        )
        
        command = " ".join(command_parts)
        result = sandbox.run_command(command)
        
        # Handle exit codes
        # rg returns 1 when no matches found, which is not an error
        if not result or result.strip() == "":
            return "No matches found."
        
        if "command not found" in result.lower() or "not found" in result.lower():
            # Fallback to grep if ripgrep not available
            fallback_cmd = f"grep -rn {_escape_shell_arg(query)} ."
            if include_files:
                fallback_cmd = f"grep -rn --include={_escape_shell_arg(include_files)} {_escape_shell_arg(query)} ."
            result = sandbox.run_command(fallback_cmd)
            if not result or result.strip() == "":
                return "No matches found."
        
        return result
        
    except Exception as e:
        return f"Error running grep search: {str(e)}"


def create_grep_tool(sandbox: Sandbox) -> StructuredTool:
    """Creates a grep search tool bound to the given sandbox."""
    
    def tool_grep(
        query: str,
        match_string: bool = False,
        case_sensitive: bool = False,
        context_lines: int = 0,
        exclude_files: Optional[str] = None,
        include_files: Optional[str] = None,
        max_results: int = 50,
        file_types: Optional[List[str]] = None,
        follow_symlinks: bool = False
    ) -> str:
        """
        Search the codebase using ripgrep (rg). Supports regex patterns, file filtering, and context lines.
        
        Args:
            query: The string or regex pattern to search for.
            match_string: If True, treat query as literal string (not regex). Default False.
            case_sensitive: If True, search is case-sensitive. Default False.
            context_lines: Number of context lines before/after matches. Default 0.
            exclude_files: Glob pattern for files to exclude (e.g., "*.test.py").
            include_files: Glob pattern for files to include (e.g., "*.py").
            max_results: Maximum number of results to return. Default 50.
            file_types: List of file extensions to search (e.g., [".py", ".js"]).
            follow_symlinks: Whether to follow symbolic links. Default False.
        
        Returns:
            Search results with file paths, line numbers, and matching content.
        """
        return grep_search(
            sandbox=sandbox,
            query=query,
            match_string=match_string,
            case_sensitive=case_sensitive,
            context_lines=context_lines,
            exclude_files=exclude_files,
            include_files=include_files,
            max_results=max_results,
            file_types=file_types,
            follow_symlinks=follow_symlinks
        )
    
    return StructuredTool.from_function(
        func=tool_grep,
        name="grep_search",
        description=(
            "Search the codebase using ripgrep. Use this to find code patterns, function definitions, "
            "imports, or any text content in the repository. Supports regex patterns by default. "
            "Set match_string=True for literal string matching. Use file_types or include_files to "
            "limit search scope. Results include file paths, line numbers, and matching content."
        )
    )
