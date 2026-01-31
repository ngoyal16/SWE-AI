import os
import re
from langchain_core.tools import StructuredTool
from app.config import settings
from app.sandbox.base import Sandbox
from typing import Optional, List

def validate_branch_name(branch_name: str) -> tuple[bool, str]:
    # Regex: strict "type/kebab-case"
    pattern = r"^(feature|bugfix|hotfix|chore|docs)\/[a-z0-9-]+$"

    if not re.match(pattern, branch_name):
        return False, f"ERROR: Branch '{branch_name}' violates convention. Format must be 'type/kebab-case'. Allowed types: feature, bugfix, hotfix, chore, docs."
    return True, "OK"

def clone_repo(sandbox: Sandbox, repo_url: str) -> str:
    """Clones a git repository into the workspace. Returns the path to the cloned repo."""
    # Use sandbox root
    workspace_root = sandbox.get_root_path()

    # Check if exists (requires list_files or check command)
    # Check for .git directory in root
    check = sandbox.run_command("test -d .git && echo EXISTS")
    if "EXISTS" in check:
         # Optimization: Set CWD
         sandbox.set_cwd(workspace_root)
         return f"Repository already exists at {workspace_root}"

    final_url = repo_url
    if settings.GIT_TOKEN and repo_url.startswith("https://"):
        final_url = repo_url.replace("https://", f"https://oauth2:{settings.GIT_TOKEN}@")

    # Clone directly into current directory (root)
    res = sandbox.run_command(f"git clone {final_url} .", workspace_root)

    # Handle "directory already exists and is not an empty directory" if .git didn't exist but files did
    if "already exists" in res and "not an empty directory" in res:
         # This implies files are there but maybe not .git, or .git check failed.
         # But if we want to be safe and assume it might be a valid repo or just artifact files:
         # For now, let's treat it as failure if it's not a git repo, or success if we decide so.
         # But the user request specifically says "clone should be at session id root".
         # If files exist, git clone . fails.
         return f"Failed to clone: {res}"

    if "Error" not in res and "fatal" not in res:
        sandbox.run_command(f"git config user.name '{settings.GIT_USERNAME}'", workspace_root)
        sandbox.run_command(f"git config user.email '{settings.GIT_EMAIL}'", workspace_root)
        # Optimization: Update sandbox CWD to repo path
        sandbox.set_cwd(workspace_root)
        return f"Successfully cloned to {workspace_root}"
    return res

def get_repo_path(sandbox: Sandbox, provided_path: Optional[str] = None) -> str:
    # Use provided path if valid
    if provided_path:
         return provided_path

    # Always return root path as we clone into root
    return sandbox.get_root_path()

def create_branch(sandbox: Sandbox, branch_name: str, repo_path: Optional[str] = None) -> str:
    """Creates and switches to a new branch."""
    is_valid, error_msg = validate_branch_name(branch_name)
    if not is_valid:
        return error_msg

    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command(f"git checkout -b {branch_name}", target)

def checkout_branch(sandbox: Sandbox, branch_name: str, repo_path: Optional[str] = None) -> str:
    """Switches to an existing branch."""
    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command(f"git checkout {branch_name}", target)

def commit_changes(sandbox: Sandbox, message: str, repo_path: Optional[str] = None) -> str:
    """Stages all changes and commits them."""
    target = get_repo_path(sandbox, repo_path)

    add_res = sandbox.run_command("git add .", target)
    if "Error" in add_res:
        return f"Failed to add files: {add_res}"

    commit_res = sandbox.run_command(f"git commit -m '{message}'", target)
    return commit_res

def push_changes(sandbox: Sandbox, base_branch: Optional[str], remote: str = "origin", branch: str = "main", repo_path: Optional[str] = None) -> str:
    """Pushes changes to the remote repository."""
    # Protection: Do not allow pushing to base_branch or protected branches
    protected_branches = ["main", "master", "develop"]
    if base_branch:
        protected_branches.append(base_branch)

    if branch in protected_branches:
        return f"Error: Cannot push to protected or base branch '{branch}'. Please push to your feature branch."

    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command(f"git push {remote} {branch}", target)

def init_workspace(sandbox: Sandbox, repo_url: str, base_branch: Optional[str] = None) -> str:
    """
    Sets up the workspace by cloning the repository and checking out the base branch.
    """
    # 1. Clone
    clone_res = clone_repo(sandbox, repo_url)
    if ("Error" in clone_res or "fatal" in clone_res or "Failed" in clone_res) and "Repository already exists" not in clone_res:
        return clone_res

    output = [clone_res]

    # 2. Checkout Base Branch
    if base_branch:
         # Ensure we are in the repo
         repo_path = get_repo_path(sandbox)
         if "No repository" in repo_path:
             return f"{clone_res}\nError: Could not find repository path."

         # Fetch to ensure remote branches are visible
         if "Repository already exists" in clone_res:
             sandbox.run_command("git fetch --all", repo_path)

         checkout_res = sandbox.run_command(f"git checkout {base_branch}", repo_path)

         if "error" in checkout_res.lower() or "fatal" in checkout_res.lower() or "did not match any file" in checkout_res.lower():
              output.append(f"Warning: Base branch '{base_branch}' not found or could not be checked out. Keeping default branch.")
         else:
              output.append(f"Checked out base branch '{base_branch}'.")

    return "\n".join(output)

def create_git_tools(sandbox: Sandbox, base_branch: Optional[str] = None) -> List[StructuredTool]:
    # Define tool functions using the module-level helpers
    # We bind the sandbox to them.

    def tool_clone(repo_url: str) -> str:
        return clone_repo(sandbox, repo_url)

    def tool_create_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
        return create_branch(sandbox, branch_name, repo_path)

    def tool_checkout_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
        return checkout_branch(sandbox, branch_name, repo_path)

    def tool_commit_changes(message: str, repo_path: Optional[str] = None) -> str:
        return commit_changes(sandbox, message, repo_path)

    def tool_push_changes(remote: str = "origin", branch: str = "main", repo_path: Optional[str] = None) -> str:
        return push_changes(sandbox, base_branch, remote, branch, repo_path)

    return [
        StructuredTool.from_function(tool_clone, name="clone_repo", description="Clones a git repository into the workspace."),
        StructuredTool.from_function(tool_create_branch, name="create_branch", description="Creates and switches to a new branch."),
        StructuredTool.from_function(tool_checkout_branch, name="checkout_branch", description="Switches to an existing branch."),
        StructuredTool.from_function(tool_commit_changes, name="commit_changes", description="Stages all changes and commits them."),
        StructuredTool.from_function(tool_push_changes, name="push_changes", description="Pushes changes to the remote repository.")
    ]
