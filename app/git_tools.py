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
             # Optimization: Set CWD if it exists
             sandbox.set_cwd(target_path)
             return f"Repository already exists at {target_path}"

        final_url = repo_url
        if settings.GIT_TOKEN and repo_url.startswith("https://"):
            final_url = repo_url.replace("https://", f"https://oauth2:{settings.GIT_TOKEN}@")

        res = sandbox.run_command(f"git clone {final_url} {repo_name}", workspace_root)

        if "Error" not in res:
            sandbox.run_command(f"git config user.name '{settings.GIT_USERNAME}'", target_path)
            sandbox.run_command(f"git config user.email '{settings.GIT_EMAIL}'", target_path)
            # Optimization: Update sandbox CWD to repo path
            sandbox.set_cwd(target_path)
            return f"Successfully cloned to {target_path}"
        return res

    def get_repo_path(provided_path: Optional[str] = None) -> str:
        # Use provided path if valid
        if provided_path:
             return provided_path

        # Optimization: Use sandbox CWD if explicitly set and distinct from root
        cwd = sandbox.get_cwd()
        root = sandbox.get_root_path()
        if cwd and cwd != root:
            return cwd

        # Fallback: List files (network call)
        ls = sandbox.list_files(".")
        dirs = [d.strip("/") for d in ls.splitlines() if d.strip().endswith("/")]
        if not dirs:
            return "No repository found in workspace."
        return dirs[0] # Assume first dir is repo

    def create_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
        """Creates and switches to a new branch."""
        target = get_repo_path(repo_path)
        if "No repository" in target: return target
        return sandbox.run_command(f"git checkout -b {branch_name}", target)

    def checkout_branch(branch_name: str, repo_path: Optional[str] = None) -> str:
        """Switches to an existing branch."""
        target = get_repo_path(repo_path)
        if "No repository" in target: return target
        return sandbox.run_command(f"git checkout {branch_name}", target)

    def commit_changes(message: str, repo_path: Optional[str] = None) -> str:
        """Stages all changes and commits them."""
        target = get_repo_path(repo_path)
        if "No repository" in target: return target

        add_res = sandbox.run_command("git add .", target)
        if "Error" in add_res:
            return f"Failed to add files: {add_res}"

        commit_res = sandbox.run_command(f"git commit -m '{message}'", target)
        return commit_res

    def push_changes(remote: str = "origin", branch: str = "main", repo_path: Optional[str] = None) -> str:
        """Pushes changes to the remote repository."""
        target = get_repo_path(repo_path)
        if "No repository" in target: return target

        return sandbox.run_command(f"git push {remote} {branch}", target)

    return [
        StructuredTool.from_function(clone_repo, name="clone_repo", description="Clones a git repository into the workspace."),
        StructuredTool.from_function(create_branch, name="create_branch", description="Creates and switches to a new branch."),
        StructuredTool.from_function(checkout_branch, name="checkout_branch", description="Switches to an existing branch."),
        StructuredTool.from_function(commit_changes, name="commit_changes", description="Stages all changes and commits them."),
        StructuredTool.from_function(push_changes, name="push_changes", description="Pushes changes to the remote repository.")
    ]
