import re
from urllib.parse import urlparse, urlunparse
from langchain_core.tools import StructuredTool
from ..sandbox.base import Sandbox
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..common.credentials import GitCredentials

def configure_git_global(sandbox: Sandbox, credentials: Optional["GitCredentials"] = None, repo_url: Optional[str] = None):
    """
    Sets global git/user config and credential helper.
    """
    # 1. Global User Config
    if credentials:
        sandbox.run_command(f"git config --global user.name '{credentials.author_name}'")
        sandbox.run_command(f"git config --global user.email '{credentials.author_email}'")
    else:
        sandbox.run_command("git config --global user.name 'swe-agent'")
        sandbox.run_command("git config --global user.email 'swe-agent@example.com'")

    # 2. Credential Helper
    sandbox.run_command("git config --global credential.helper store")
    
    # 3. Disable SSL Verify (Fix for internal/self-hosted git servers)
    sandbox.run_command("git config --global http.sslVerify false")

    if credentials and credentials.token and repo_url:
        # 3. Write credentials to store using the known repo_url
        setup_git_auth(sandbox, repo_url, credentials)

def setup_git_auth(sandbox: Sandbox, repo_url: str, credentials: Optional["GitCredentials"] = None):
    """
    Configures git auth for a specific repository host by writing to ~/.git-credentials.
    """
    if not credentials or not credentials.token:
        return

    parsed = urlparse(repo_url)
    username = credentials.username or "oauth2"
    
    # Construct auth URL: https://user:token@host
    # Note: we strip path and query
    auth_url_str = f"{parsed.scheme}://{username}:{credentials.token}@{parsed.netloc}"
    
    # Append to ~/.git-credentials
    # echo "url" >> ~/.git-credentials
    sandbox.run_command(f"echo '{auth_url_str}' >> ~/.git-credentials")

def _add_auth_to_url(repo_url: str, credentials: "GitCredentials" = None) -> str:
    """
    [DEPRECATED] Adds authentication credentials to the repository URL.
    We now prefer using credential helper, so this returns the original URL.
    """
    return repo_url

def validate_branch_name(branch_name: str) -> tuple[bool, str]:
    # Regex: strict "type/kebab-case"
    pattern = r"^(feature|bugfix|hotfix|chore|docs)\/[a-z0-9-]+$"

    if not re.match(pattern, branch_name):
        return False, f"ERROR: Branch '{branch_name}' violates convention. Format must be 'type/kebab-case'. Allowed types: feature, bugfix, hotfix, chore, docs."
    return True, "OK"

def clone_repo(sandbox: Sandbox, repo_url: str) -> str:
    """Clones a git repository into the workspace. Returns the directory path."""
    workspace_root = sandbox.get_root_path()
    
    # Get credentials from sandbox if available
    credentials = getattr(sandbox, 'git_credentials', None)
    
    # Extract repo name from URL to create a subfolder
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    target_dir = f"{workspace_root}/{repo_name}"

    # Check for .git directory in the subfolder
    check = sandbox.run_command(f"test -d {repo_name}/.git && echo EXISTS", workspace_root)
    if "EXISTS" in check:
         sandbox.set_cwd(target_dir)
         return f"Repository already exists at {target_dir}"

    # Setup auth credentials
    if credentials:
        setup_git_auth(sandbox, repo_url, credentials)
        
        # DEBUG: Verify credentials file
        try:
            creds_content = sandbox.run_command("cat ~/.git-credentials")
            # Redact token for logs
            if cr := credentials.token:
                 safe_content = creds_content.replace(cr, "***")
            else:
                 safe_content = creds_content
        except:
             safe_content = "Could not read ~/.git-credentials"

    # Clone into the specific subfolder
    # We use repo_url directly as credentials are in the store
    
    # Attempt 1: Standard Clone
    cmd = f"git clone {repo_url} {repo_name}"
    res = sandbox.run_command(cmd, workspace_root)

    if "already exists" in res and "not an empty directory" in res:
         # Fallback: if somehow the subfolder exists but is not a git repo
         return f"Failed to clone: {res}"

    # Attempt 2: Retry with TLS 1.2 & other compat fixes if failed
    if "Error" in res or "fatal" in res or "Failed" in res:
         # Try enforcing TLS 1.2 via multiple mechanisms (env vars + config)
         # Also try to fallback to HTTP/1.1 if possible via config (though git doesn't expose it easily)
         cmd_retry = f"GIT_SSL_VERSION=tlsv1.2 CURL_SSLVERSION=TLSv1_2 git -c http.sslVersion=tlsv1.2 clone {repo_url} {repo_name}"
         res = sandbox.run_command(cmd_retry, workspace_root)
    
    # If still failed, run verbose debug
    if "Error" in res or "fatal" in res or "Failed" in res:
         # RETRY with VERBOSE LOGGING using the aggressive fix
         verbose_res = sandbox.run_command(f"GIT_CURL_VERBOSE=1 GIT_TRACE=1 GIT_SSL_VERSION=tlsv1.2 CURL_SSLVERSION=TLSv1_2 git -c http.sslVersion=tlsv1.2 clone {repo_url} {repo_name}", workspace_root)
         
         # Capture config and version state
         config_dump = sandbox.run_command("git config --global --list")
         version_info = sandbox.run_command("git --version && curl --version")
         
         debug_info = f"\n\n--- DEBUG INFO ---\nCredentials File (~/.git-credentials):\n{safe_content}\n\nGlobal Config:\n{config_dump}\n\nVersions:\n{version_info}\n\nVerbose Log:\n{verbose_res}"
         return f"Failed to clone: {res}{debug_info}"

    if "Error" not in res and "fatal" not in res:
        # Set sandbox CWD to the cloned repo path
        sandbox.set_cwd(target_dir)
        return f"Successfully cloned to {target_dir}"
    return res

def get_repo_path(sandbox: Sandbox, provided_path: Optional[str] = None) -> str:
    """Returns the effective repository path (prioritizes sandbox CWD)."""
    # Use provided path if valid
    if provided_path:
         return provided_path

    # Use the current working directory of the sandbox
    return sandbox.get_cwd()

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
    """Stages all changes and commits them with co-author attribution."""
    target = get_repo_path(sandbox, repo_path)

    add_res = sandbox.run_command("git add .", target)
    if "Error" in add_res:
        return f"Failed to add files: {add_res}"

    # Build commit message with co-author trailer if available
    credentials = getattr(sandbox, 'git_credentials', None)
    if credentials and credentials.co_author_name and credentials.co_author_email:
        # Create full message with co-author trailer
        co_author_line = f"\nCo-authored-by: {credentials.co_author_name} <{credentials.co_author_email}>"
        # Use git commit with -m for title and -m for body to handle newlines properly
        # This avoids shell escaping issues with $'...' syntax
        safe_message = message.replace('"', '\\"')
        commit_res = sandbox.run_command(f'git commit -m "{safe_message}" -m "{co_author_line}"', target)
    else:
        # No co-author info available
        safe_message = message.replace('"', '\\"')
        commit_res = sandbox.run_command(f'git commit -m "{safe_message}"', target)
    
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

def git_status(sandbox: Sandbox, repo_path: Optional[str] = None) -> str:
    """Shows the working tree status."""
    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command("git status", target)

def git_diff(sandbox: Sandbox, filepath: Optional[str] = None, staged: bool = False, repo_path: Optional[str] = None) -> str:
    """Shows changes between commits, commit and working tree, etc."""
    target = get_repo_path(sandbox, repo_path)
    cmd = "git diff"
    if staged:
        cmd += " --staged"
    if filepath:
        cmd += f" {filepath}"
    return sandbox.run_command(cmd, target)

def git_log(sandbox: Sandbox, n: int = 10, repo_path: Optional[str] = None) -> str:
    """Shows the commit logs."""
    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command(f"git log -n {n} --oneline", target)

def git_restore(sandbox: Sandbox, filepath: str, repo_path: Optional[str] = None) -> str:
    """Restore working tree files."""
    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command(f"git restore {filepath}", target)

def git_blame(sandbox: Sandbox, filepath: str, repo_path: Optional[str] = None) -> str:
    """Show what revision and author last modified each line of a file."""
    target = get_repo_path(sandbox, repo_path)
    return sandbox.run_command(f"git blame {filepath}", target)

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

    def tool_git_status(repo_path: Optional[str] = None) -> str:
        return git_status(sandbox, repo_path)

    def tool_git_diff(filepath: Optional[str] = None, staged: bool = False, repo_path: Optional[str] = None) -> str:
        return git_diff(sandbox, filepath, staged, repo_path)

    def tool_git_log(n: int = 10, repo_path: Optional[str] = None) -> str:
        return git_log(sandbox, n, repo_path)

    def tool_git_restore(filepath: str, repo_path: Optional[str] = None) -> str:
        return git_restore(sandbox, filepath, repo_path)

    def tool_git_blame(filepath: str, repo_path: Optional[str] = None) -> str:
        return git_blame(sandbox, filepath, repo_path)

    return [
        StructuredTool.from_function(tool_clone, name="clone_repo", description="Clones a git repository into the workspace."),
        StructuredTool.from_function(tool_create_branch, name="create_branch", description="Creates and switches to a new branch."),
        StructuredTool.from_function(tool_checkout_branch, name="checkout_branch", description="Switches to an existing branch."),
        StructuredTool.from_function(tool_commit_changes, name="commit_changes", description="Stages all changes and commits them."),
        StructuredTool.from_function(tool_push_changes, name="push_changes", description="Pushes changes to the remote repository."),
        StructuredTool.from_function(tool_git_status, name="git_status", description="Shows the working tree status."),
        StructuredTool.from_function(tool_git_diff, name="git_diff", description="Shows changes between commits, commit and working tree, etc."),
        StructuredTool.from_function(tool_git_log, name="git_log", description="Shows the recent commit logs."),
        StructuredTool.from_function(tool_git_restore, name="git_restore", description="Restore working tree files, discarding changes."),
        StructuredTool.from_function(tool_git_blame, name="git_blame", description="Show what revision and author last modified each line of a file.")
    ]
