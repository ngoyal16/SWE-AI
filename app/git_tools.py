import os
from langchain_core.tools import StructuredTool
from app.config import settings
from app.sandbox.base import Sandbox
from typing import Optional, List

def create_git_tools(sandbox: Sandbox) -> List[StructuredTool]:

    def clone_repo(repo_url: str) -> str:
        """Clones a git repository into the workspace. Returns the path to the cloned repo."""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        # Use sandbox root
        workspace_root = sandbox.get_root_path()
        target_path = os.path.join(workspace_root, repo_name)

        # Check if exists (requires list_files or check command)
        # Using command is safer across sandbox types
        check = sandbox.run_command(f"test -d {repo_name} && echo EXISTS")
        if "EXISTS" in check:
             return f"Repository already exists at {target_path}"

        final_url = repo_url
        if settings.GIT_TOKEN and repo_url.startswith("https://"):
            final_url = repo_url.replace("https://", f"https://oauth2:{settings.GIT_TOKEN}@")

        res = sandbox.run_command(f"git clone {final_url} {repo_name}", workspace_root)

        if "Error" not in res:
            sandbox.run_command(f"git config user.name '{settings.GIT_USERNAME}'", target_path)
            sandbox.run_command(f"git config user.email '{settings.GIT_EMAIL}'", target_path)
            return f"Successfully cloned to {target_path}"
        return res

    def create_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
        """Creates and switches to a new branch."""
        if not repo_path:
            # Try to auto-detect
            ls = sandbox.list_files(".")
            # Parse output of ls -F (directories have /)
            dirs = [d.strip("/") for d in ls.splitlines() if d.strip().endswith("/")]
            if not dirs:
                return "No repository found in workspace."
            repo_path = dirs[0] # Relative path

        return sandbox.run_command(f"git checkout -b {branch_name}", repo_path)

    def commit_changes(message: str, repo_path: Optional[str] = None) -> str:
        """Stages all changes and commits them."""
        if not repo_path:
            ls = sandbox.list_files(".")
            dirs = [d.strip("/") for d in ls.splitlines() if d.strip().endswith("/")]
            if not dirs:
                return "No repository found in workspace."
            repo_path = dirs[0]

        add_res = sandbox.run_command("git add .", repo_path)
        if "Error" in add_res:
            return f"Failed to add files: {add_res}"

        commit_res = sandbox.run_command(f"git commit -m '{message}'", repo_path)
        return commit_res

    def push_changes(remote: str = "origin", branch: str = "main", repo_path: Optional[str] = None) -> str:
        """Pushes changes to the remote repository."""
        if not repo_path:
            ls = sandbox.list_files(".")
            dirs = [d.strip("/") for d in ls.splitlines() if d.strip().endswith("/")]
            if not dirs:
                return "No repository found in workspace."
            repo_path = dirs[0]

        return sandbox.run_command(f"git push {remote} {branch}", repo_path)

    return [
        StructuredTool.from_function(clone_repo, name="clone_repo", description="Clones a git repository into the workspace."),
        StructuredTool.from_function(create_branch, name="create_branch", description="Creates and switches to a new branch."),
        StructuredTool.from_function(commit_changes, name="commit_changes", description="Stages all changes and commits them."),
        StructuredTool.from_function(push_changes, name="push_changes", description="Pushes changes to the remote repository.")
    ]
