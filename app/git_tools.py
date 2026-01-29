import os
import subprocess
from langchain_core.tools import StructuredTool
from app.config import settings
from typing import Optional, List

def create_git_tools(workspace_root: str) -> List[StructuredTool]:

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

    def clone_repo(repo_url: str) -> str:
        """Clones a git repository into the workspace. Returns the path to the cloned repo."""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_path = os.path.join(workspace_root, repo_name)

        if os.path.exists(target_path):
            return f"Repository already exists at {target_path}"

        final_url = repo_url
        if settings.GIT_TOKEN and repo_url.startswith("https://"):
            final_url = repo_url.replace("https://", f"https://oauth2:{settings.GIT_TOKEN}@")

        res = run_git_command(f"git clone {final_url} {repo_name}", workspace_root)

        if "Error" not in res:
            run_git_command(f"git config user.name '{settings.GIT_USERNAME}'", target_path)
            run_git_command(f"git config user.email '{settings.GIT_EMAIL}'", target_path)
            return f"Successfully cloned to {target_path}"
        return res

    def create_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
        """Creates and switches to a new branch."""
        if not repo_path:
            items = os.listdir(workspace_root)
            dirs = [d for d in items if os.path.isdir(os.path.join(workspace_root, d))]
            if not dirs:
                return "No repository found in workspace."
            repo_path = os.path.join(workspace_root, dirs[0])
        else:
            # Check if repo_path is relative or absolute, if relative join with workspace_root
            if not os.path.isabs(repo_path):
                 repo_path = os.path.join(workspace_root, repo_path)

        return run_git_command(f"git checkout -b {branch_name}", repo_path)

    def commit_changes(message: str, repo_path: Optional[str] = None) -> str:
        """Stages all changes and commits them."""
        if not repo_path:
            items = os.listdir(workspace_root)
            dirs = [d for d in items if os.path.isdir(os.path.join(workspace_root, d))]
            if not dirs:
                return "No repository found in workspace."
            repo_path = os.path.join(workspace_root, dirs[0])
        else:
             if not os.path.isabs(repo_path):
                 repo_path = os.path.join(workspace_root, repo_path)

        add_res = run_git_command("git add .", repo_path)
        if "Error" in add_res:
            return f"Failed to add files: {add_res}"

        commit_res = run_git_command(f"git commit -m '{message}'", repo_path)
        return commit_res

    def push_changes(remote: str = "origin", branch: str = "main", repo_path: Optional[str] = None) -> str:
        """Pushes changes to the remote repository."""
        if not repo_path:
            items = os.listdir(workspace_root)
            dirs = [d for d in items if os.path.isdir(os.path.join(workspace_root, d))]
            if not dirs:
                return "No repository found in workspace."
            repo_path = os.path.join(workspace_root, dirs[0])
        else:
             if not os.path.isabs(repo_path):
                 repo_path = os.path.join(workspace_root, repo_path)

        return run_git_command(f"git push {remote} {branch}", repo_path)

    return [
        StructuredTool.from_function(clone_repo, name="clone_repo", description="Clones a git repository into the workspace."),
        StructuredTool.from_function(create_branch, name="create_branch", description="Creates and switches to a new branch."),
        StructuredTool.from_function(commit_changes, name="commit_changes", description="Stages all changes and commits them."),
        StructuredTool.from_function(push_changes, name="push_changes", description="Pushes changes to the remote repository.")
    ]

# Backward compatibility
def get_git_tools():
    return create_git_tools(settings.WORKSPACE_DIR)
