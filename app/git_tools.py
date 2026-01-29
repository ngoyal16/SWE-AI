import os
import subprocess
from langchain_core.tools import tool
from app.config import settings
from typing import Optional

def run_git_command(command: str, cwd: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            return f"Error (Code {result.returncode}): {result.stderr}"
        return result.stdout.strip()
    except Exception as e:
        return f"Exception: {str(e)}"

@tool
def clone_repo(repo_url: str) -> str:
    """Clones a git repository into the workspace. Returns the path to the cloned repo."""
    # Assuming repo_url is something like https://github.com/user/repo.git
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    target_path = os.path.join(settings.WORKSPACE_DIR, repo_name)

    if os.path.exists(target_path):
        return f"Repository already exists at {target_path}"

    # Securely inject token if provided and url is https
    final_url = repo_url
    if settings.GIT_TOKEN and repo_url.startswith("https://"):
        # Very basic injection, handle with care in logs
        final_url = repo_url.replace("https://", f"https://oauth2:{settings.GIT_TOKEN}@")

    res = run_git_command(f"git clone {final_url} {repo_name}", settings.WORKSPACE_DIR)

    # Configure local git user
    if "Error" not in res:
        run_git_command(f"git config user.name '{settings.GIT_USERNAME}'", target_path)
        run_git_command(f"git config user.email '{settings.GIT_EMAIL}'", target_path)
        return f"Successfully cloned to {target_path}"
    return res

@tool
def create_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
    """Creates and switches to a new branch."""
    if not repo_path:
        # Try to find the first directory in workspace
        items = os.listdir(settings.WORKSPACE_DIR)
        dirs = [d for d in items if os.path.isdir(os.path.join(settings.WORKSPACE_DIR, d))]
        if not dirs:
            return "No repository found in workspace."
        repo_path = os.path.join(settings.WORKSPACE_DIR, dirs[0])

    return run_git_command(f"git checkout -b {branch_name}", repo_path)

@tool
def commit_changes(message: str, repo_path: Optional[str] = None) -> str:
    """Stages all changes and commits them."""
    if not repo_path:
         # Try to find the first directory in workspace
        items = os.listdir(settings.WORKSPACE_DIR)
        dirs = [d for d in items if os.path.isdir(os.path.join(settings.WORKSPACE_DIR, d))]
        if not dirs:
            return "No repository found in workspace."
        repo_path = os.path.join(settings.WORKSPACE_DIR, dirs[0])

    add_res = run_git_command("git add .", repo_path)
    if "Error" in add_res:
        return f"Failed to add files: {add_res}"

    commit_res = run_git_command(f"git commit -m '{message}'", repo_path)
    return commit_res

@tool
def push_changes(remote: str = "origin", branch: str = "main", repo_path: Optional[str] = None) -> str:
    """Pushes changes to the remote repository."""
    if not repo_path:
         # Try to find the first directory in workspace
        items = os.listdir(settings.WORKSPACE_DIR)
        dirs = [d for d in items if os.path.isdir(os.path.join(settings.WORKSPACE_DIR, d))]
        if not dirs:
            return "No repository found in workspace."
        repo_path = os.path.join(settings.WORKSPACE_DIR, dirs[0])

    return run_git_command(f"git push {remote} {branch}", repo_path)

def get_git_tools():
    return [clone_repo, create_branch, commit_changes, push_changes]
