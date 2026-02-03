import logging
import time
from typing import List, Optional, TYPE_CHECKING
from daytona import Daytona, DaytonaConfig, CreateSandboxFromImageParams, CreateSandboxFromSnapshotParams, Resources, DaytonaError, DaytonaNotFoundError

from .base import Sandbox
from ..common.config import settings

if TYPE_CHECKING:
    from ..common.credentials import GitCredentials

class DaytonaSandbox(Sandbox):
    def __init__(self, session_id: str, repo_url: str = None, base_branch: str = None, git_credentials: "GitCredentials" = None):
        self.session_id = session_id
        self.repo_url = repo_url
        self.base_branch = base_branch
        self.git_credentials = git_credentials
        self.daytona = None
        self.sandbox = None

    @property
    def git(self):
        return self.sandbox.git if self.sandbox else None

    @property
    def fs(self):
        return self.sandbox.fs if self.sandbox else None

    @property
    def process(self):
        return self.sandbox.process if self.sandbox else None

    def setup(self):
        if not Daytona:
            raise ImportError("Daytona SDK not installed. Please install 'daytona'.")

        config = DaytonaConfig(
            api_key=settings.DAYTONA_API_KEY
        )
        self.daytona = Daytona(config)

        # Labels for idempotency and metadata
        labels = {"session_id": self.session_id}
        if self.repo_url:
            labels["repo_url"] = self.repo_url
        if self.base_branch:
            labels["base_branch"] = self.base_branch
        if self.git_credentials:
            if self.git_credentials.co_author_name:
                labels["git_co_author_name"] = self.git_credentials.co_author_name
            if self.git_credentials.co_author_email:
                labels["git_co_author_email"] = self.git_credentials.co_author_email
        
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                # 1. Try to find existing sandbox by label for idempotency
                try:
                    self.sandbox = self.daytona.find_one(labels=labels)
                    logging.info(f"Found existing sandbox for session {self.session_id}: {self.sandbox.id}")
                    
                    # Check state and start if needed
                    state = self.sandbox.state
                    if state in ["stopped", "archived"]:
                        logging.info(f"Sandbox {self.sandbox.id} is {state}, starting it...")
                        self.sandbox.start()
                    elif state != "started":
                        logging.warning(f"Sandbox {self.sandbox.id} in unexpected state: {state}")
                        # If in an unrecoverable state, we might want to recreate it
                        # but for now let's just try to proceed or fail.
                    
                    break # Success
                except (DaytonaNotFoundError, DaytonaError) as e:
                    # If not found, create a new one
                    if isinstance(e, DaytonaNotFoundError) or "No sandbox found" in str(e):
                        logging.info(f"Creating new sandbox for session {self.session_id} (attempt {attempt + 1})")
                        
                        resources = Resources(cpu=2, memory=4, disk=10)
                        
                        if settings.DAYTONA_SNAPSHOT_NAME:
                            logging.info(f"Using snapshot: {settings.DAYTONA_SNAPSHOT_NAME}")
                            params = CreateSandboxFromSnapshotParams(
                                snapshot=settings.DAYTONA_SNAPSHOT_NAME,
                                labels=labels,
                                resources=resources,
                                auto_stop_interval=30
                            )
                        else:
                            logging.info(f"Using image: {settings.DAYTONA_TARGET_IMAGE}")
                            params = CreateSandboxFromImageParams(
                                image=settings.DAYTONA_TARGET_IMAGE,
                                labels=labels,
                                resources=resources,
                                auto_stop_interval=30
                            )
                        
                        self.sandbox = self.daytona.create(params, timeout=300)
                        break # Success
                    else:
                        logging.error(f"Error checking for existing sandbox (attempt {attempt + 1}): {e}")
                        if attempt == max_attempts - 1:
                            raise e
            except Exception as e:
                logging.error(f"Failed to setup Daytona sandbox (attempt {attempt + 1}): {e}")
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(2) # Wait before retry
            
            attempt += 1

        if self.sandbox:
            logging.info(f"Daytona Sandbox ready: {self.sandbox.id}")

        return self

    def teardown(self):
        if self.sandbox:
            try:
                self.daytona.delete(self.sandbox)
                logging.info(f"Deleted Daytona sandbox: {self.sandbox.id}")
            except Exception as e:
                logging.warning(f"Error deleting sandbox: {e}")

    def run_command(self, command: str, cwd: str = None, env: dict = None) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        if cwd is None:
            cwd = self.get_cwd()

        # Default environment variables
        default_env = {
            "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"
        }
        if self.git_credentials:
            if self.git_credentials.co_author_name:
                default_env["GIT_CO_AUTHOR_NAME"] = self.git_credentials.co_author_name
            if self.git_credentials.co_author_email:
                default_env["GIT_CO_AUTHOR_EMAIL"] = self.git_credentials.co_author_email
            
        if env:
            default_env.update(env)

        try:
            # Using latest process exec pattern
            resp = self.sandbox.process.exec(command, cwd=cwd, env=default_env)
            return resp.result
        except Exception as e:
            logging.error(f"Command execution error: {e}")
            return f"Error running command: {str(e)}"

    def _resolve_path(self, path: str) -> str:
        """Resolves a path against the current working directory if it's relative."""
        import os
        if not os.path.isabs(path):
            cwd = self.get_cwd()
            return os.path.join(cwd, path)
        return path

    def read_file(self, filepath: str) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        try:
            full_path = self._resolve_path(filepath)
            # Using latest fs download pattern
            content_bytes = self.sandbox.fs.download_file(full_path)
            return content_bytes.decode('utf-8')
        except Exception as e:
            logging.error(f"File read error: {e}")
            return f"Error reading file: {str(e)}"

    def write_file(self, filepath: str, content: str) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        try:
            full_path = self._resolve_path(filepath)
            # Using latest fs upload pattern
            self.sandbox.fs.upload_file(content.encode('utf-8'), full_path)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            logging.error(f"File write error: {e}")
            return f"Error writing file: {str(e)}"

    def list_files(self, path: str) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        target_path = self._resolve_path(path if path and path != "." else self.get_cwd())

        try:
            files = self.sandbox.fs.list_files(target_path)
            # Format: name/ for dirs, name for files
            formatted = []
            for f in files:
                name = f.name
                if f.is_dir:
                    name += "/"
                formatted.append(name)
            return "\n".join(formatted)
        except Exception as e:
            logging.error(f"List files error: {e}")
            return f"Error listing files: {str(e)}"

    def get_root_path(self) -> str:
        if self.sandbox:
            try:
                return self.sandbox.get_work_dir()
            except Exception as e:
                logging.warning(f"Failed to get work dir, falling back to /workspace: {e}")
                return "/workspace"
        return "/workspace"

    def clone_repo(self, url: str, branch: str = None, token: str = None) -> bool:
        """Clones a repository into the sandbox."""
        if not self.sandbox:
            logging.error("Sandbox not initialized for cloning.")
            return False
        
        # Use credentials token if not explicitly provided
        if not token and self.git_credentials:
            token = self.git_credentials.token
        
        try:
            repo_name = url.split("/")[-1].replace(".git", "")
            root_path = self.get_root_path()
            target_dir = f"{root_path}/{repo_name}"
            
            logging.info(f"Cloning {url} into {target_dir}")
            
            # Using sandbox git client if available, otherwise shell
            if hasattr(self.sandbox, 'git') and self.sandbox.git:
                self.sandbox.git.clone(url, target_dir, branch=branch, token=token)
            else:
                cmd = f"git clone {url} {target_dir}"
                if branch:
                    cmd = f"git clone -b {branch} {url} {target_dir}"
                self.run_command(cmd, cwd=root_path)

            self.set_cwd(target_dir)
            return True
        except Exception as e:
            logging.error(f"Clone error: {e}")
            return False

    def pull_latest_changes(self, token: str = None) -> bool:
        """Pulls latest changes in the workspace."""
        if not self.sandbox:
            return False
        
        # Use credentials token if not explicitly provided
        if not token and self.git_credentials:
            token = self.git_credentials.token
        
        try:
            target_dir = self.get_cwd()
            if hasattr(self.sandbox, 'git') and self.sandbox.git:
                self.sandbox.git.pull(target_dir, token=token)
            else:
                self.run_command("git pull", cwd=target_dir)
            return True
        except Exception as e:
            logging.error(f"Pull error: {e}")
            return False

    def generate_codebase_tree(self, depth: int = 3) -> str:
        """Generates a tree representation of the codebase."""
        if not self.sandbox:
            return "Error: Sandbox not initialized."
        
        try:
            # Using git ls-files | tree to respect gitignore
            cmd = f"git ls-files | tree --fromfile -L {depth}"
            return self.run_command(cmd, cwd=self.get_cwd())
        except Exception as e:
            logging.error(f"Tree generation error: {e}")
            return f"Error generating codebase tree: {str(e)}"
