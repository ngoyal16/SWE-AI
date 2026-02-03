"""
Apply Patch Tool - Git-based diff application with fallback.

Inspired by open-swe apply-patch implementation.
"""
import uuid
from langchain_core.tools import StructuredTool
from typing import Optional
from ..sandbox.base import Sandbox


def _apply_patch_with_git(sandbox: Sandbox, workdir: str, diff_content: str, file_path: str) -> dict:
    """
    Attempts to apply a patch using Git CLI.
    Returns dict with success status and output/error.
    """
    # Generate temp patch file path
    temp_patch_file = f"/tmp/patch_{uuid.uuid4().hex}.diff"
    
    try:
        # Create the patch file
        # Use a heredoc to handle special characters in diff
        create_result = sandbox.run_command(
            f"cat > \"{temp_patch_file}\" << 'ENDOFPATCH'\n{diff_content}\nENDOFPATCH"
        )
        
        if "Error" in create_result:
            return {
                "success": False,
                "output": f"Failed to create patch file: {create_result}"
            }
        
        # Execute git apply with --verbose
        result = sandbox.run_command(f"cd {workdir} && git apply --verbose \"{temp_patch_file}\"", workdir)
        
        if "error" in result.lower() or "fatal" in result.lower():
            return {
                "success": False,
                "output": f"Git apply failed: {result}"
            }
        
        return {
            "success": True,
            "output": result if result else "Patch applied successfully"
        }
        
    finally:
        # Clean up temp file
        sandbox.run_command(f"rm -f \"{temp_patch_file}\"")


def _apply_patch_manual(sandbox: Sandbox, file_path: str, diff_content: str) -> dict:
    """
    Manual patch application as fallback when git apply fails.
    Parses unified diff format and applies changes.
    """
    try:
        # Read current file content
        current_content = sandbox.read_file(file_path)
        if "Error:" in current_content and len(current_content) < 200:
            # File might not exist - try to create
            if "No such file" in current_content or "does not exist" in current_content.lower():
                # Extract new content from diff for new file creation
                new_lines = []
                for line in diff_content.split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        new_lines.append(line[1:])  # Remove the leading +
                
                if new_lines:
                    new_content = '\n'.join(new_lines)
                    result = sandbox.write_file(file_path, new_content)
                    return {"success": True, "output": f"Created new file {file_path}"}
            
            return {"success": False, "output": current_content}
        
        lines = current_content.splitlines()
        
        # Parse the diff
        hunks = []
        current_hunk = None
        
        for line in diff_content.split('\n'):
            if line.startswith('@@'):
                # Parse hunk header: @@ -start,count +start,count @@
                import re
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    if current_hunk:
                        hunks.append(current_hunk)
                    current_hunk = {
                        'old_start': int(match.group(1)),
                        'old_count': int(match.group(2) or 1),
                        'new_start': int(match.group(3)),
                        'new_count': int(match.group(4) or 1),
                        'changes': []
                    }
            elif current_hunk is not None:
                if line.startswith('-') and not line.startswith('---'):
                    current_hunk['changes'].append(('remove', line[1:]))
                elif line.startswith('+') and not line.startswith('+++'):
                    current_hunk['changes'].append(('add', line[1:]))
                elif line.startswith(' ') or line == '':
                    current_hunk['changes'].append(('context', line[1:] if line.startswith(' ') else ''))
        
        if current_hunk:
            hunks.append(current_hunk)
        
        if not hunks:
            return {"success": False, "output": "Could not parse diff: no hunks found"}
        
        # Apply hunks in reverse order to maintain line numbers
        for hunk in reversed(hunks):
            line_idx = hunk['old_start'] - 1  # 0-indexed
            
            for change_type, content in hunk['changes']:
                if change_type == 'remove':
                    if line_idx < len(lines) and lines[line_idx] == content:
                        lines.pop(line_idx)
                    else:
                        # Line doesn't match, try to find it nearby
                        found = False
                        for offset in range(-3, 4):
                            check_idx = line_idx + offset
                            if 0 <= check_idx < len(lines) and lines[check_idx] == content:
                                lines.pop(check_idx)
                                found = True
                                break
                        if not found:
                            return {"success": False, "output": f"Could not find line to remove: {content[:50]}..."}
                elif change_type == 'add':
                    lines.insert(line_idx, content)
                    line_idx += 1
                elif change_type == 'context':
                    line_idx += 1
        
        # Write the patched content
        new_content = '\n'.join(lines)
        result = sandbox.write_file(file_path, new_content)
        
        if "Error" in result:
            return {"success": False, "output": result}
        
        return {"success": True, "output": "Patch applied successfully via manual parsing"}
        
    except Exception as e:
        return {"success": False, "output": f"Manual patch failed: {str(e)}"}


def apply_patch(sandbox: Sandbox, diff: str, file_path: str) -> str:
    """
    Apply a diff patch to a file.
    Tries git apply first, then falls back to manual application.
    """
    workdir = sandbox.get_cwd()
    
    # First try git apply
    git_result = _apply_patch_with_git(sandbox, workdir, diff, file_path)
    
    if git_result["success"]:
        return f"Successfully applied patch to `{file_path}` using git apply."
    
    # Fall back to manual patch
    manual_result = _apply_patch_manual(sandbox, file_path, diff)
    
    if manual_result["success"]:
        return f"Successfully applied patch to `{file_path}` (manual fallback)."
    
    # Both failed
    return (
        f"Failed to apply patch to `{file_path}`.\n\n"
        f"Git error: {git_result['output']}\n\n"
        f"Manual fallback error: {manual_result['output']}"
    )


def create_apply_patch_tool(sandbox: Sandbox) -> StructuredTool:
    """Creates an apply_patch tool bound to the given sandbox."""
    
    def tool_apply_patch(diff: str, file_path: str) -> str:
        """
        Apply a diff patch to a file.
        
        Args:
            diff: The diff content in unified diff format. Include proper headers (+++ ---).
            file_path: The path to the file to patch.
        
        Returns:
            Success message or detailed error information.
        """
        return apply_patch(sandbox, diff, file_path)
    
    return StructuredTool.from_function(
        func=tool_apply_patch,
        name="apply_patch",
        description=(
            "Apply a unified diff patch to a file. Use standard diff format with +/- markers. "
            "This is useful for making complex multi-line changes. The tool first tries git apply, "
            "then falls back to manual patch parsing. Ensure the diff content accurately reflects "
            "the current file content for best results."
        )
    )
