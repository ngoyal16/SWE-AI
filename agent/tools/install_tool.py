"""
Install Dependencies Tool - Package manager aware dependency installation.

Inspired by open-swe install-dependencies implementation.
"""
from langchain_core.tools import StructuredTool
from typing import List, Optional
from ..sandbox.base import Sandbox


# Environment variables to prevent interactive prompts
DEFAULT_ENV = {
    "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0",  # Prevents corepack y/n prompt
    "CI": "true",  # Many tools behave non-interactively in CI
    "DEBIAN_FRONTEND": "noninteractive",  # For apt-get
}


def install_dependencies(
    sandbox: Sandbox,
    command: List[str],
    workdir: Optional[str] = None,
    timeout: int = 150  # 2.5 minutes default
) -> str:
    """
    Install dependencies using the specified package manager command.
    """
    try:
        # Join command parts
        cmd_str = " ".join(command)
        
        # Prepend environment variables
        env_prefix = " ".join(f"{k}={v}" for k, v in DEFAULT_ENV.items())
        full_cmd = f"{env_prefix} {cmd_str}"
        
        # Use workdir if specified
        if workdir:
            full_cmd = f"cd {workdir} && {full_cmd}"
        
        result = sandbox.run_command(full_cmd)
        
        # Check for common error patterns
        error_patterns = [
            "ERR!",
            "error:",
            "Error:",
            "ENOENT",
            "EACCES",
            "EPERM",
            "failed",
            "not found",
        ]
        
        is_error = any(pattern.lower() in result.lower() for pattern in error_patterns)
        
        if is_error and "error" in result.lower():
            return f"Dependency installation may have failed:\n{result}"
        
        return f"Successfully ran: {cmd_str}\n\nOutput:\n{result}"
        
    except Exception as e:
        return f"Error installing dependencies: {str(e)}"


def create_install_dependencies_tool(sandbox: Sandbox) -> StructuredTool:
    """Creates an install_dependencies tool bound to the given sandbox."""
    
    def tool_install_deps(
        command: List[str],
        workdir: Optional[str] = None
    ) -> str:
        """
        Install dependencies for the project using a package manager.
        
        Args:
            command: The install command as a list, e.g., ["npm", "install"] or ["pip", "install", "-r", "requirements.txt"]
            workdir: Optional working directory to run the command in.
        
        Returns:
            Installation output or error message.
        """
        return install_dependencies(sandbox, command, workdir)
    
    return StructuredTool.from_function(
        func=tool_install_deps,
        name="install_dependencies",
        description=(
            "Install dependencies for a project using the appropriate package manager. "
            "Pass the command as a list of strings (e.g., ['npm', 'install'] or ['pip', 'install', '-r', 'requirements.txt']). "
            "The tool sets environment variables to prevent interactive prompts. "
            "Use this after discovering what package manager the project uses."
        )
    )
