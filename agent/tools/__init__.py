"""
SWE-AI Agent Tools Package

This package contains all agent tools. Import from here for clean access.
"""
from .base import (
    create_filesystem_tools,
    create_text_editor_tool,
    create_shell_tool,
    create_enhanced_tools,
)
from .grep_tool import create_grep_tool
from .editor_tool import create_editor_tools
from .patch_tool import create_apply_patch_tool
from .install_tool import create_install_dependencies_tool
from .url_tool import create_url_content_tool
from .scratchpad_tool import create_scratchpad_tool, get_scratchpad_notes, format_scratchpad_context
from .human_help_tool import (
    create_request_human_help_tool,
    create_session_plan_tool,
    create_update_plan_tool,
    create_mark_task_completed_tool,
)
from .git_tools import create_git_tools

__all__ = [
    # Base tools
    "create_filesystem_tools",
    "create_text_editor_tool",
    "create_shell_tool",
    "create_enhanced_tools",
    # Search
    "create_grep_tool",
    # Editor
    "create_editor_tools",
    # File operations
    "create_apply_patch_tool",
    # Dependencies
    "create_install_dependencies_tool",
    # Web
    "create_url_content_tool",
    # Workflow
    "create_scratchpad_tool",
    "get_scratchpad_notes",
    "format_scratchpad_context",
    "create_request_human_help_tool",
    "create_session_plan_tool",
    "create_update_plan_tool",
    "create_mark_task_completed_tool",
    # Git
    "create_git_tools",
]
