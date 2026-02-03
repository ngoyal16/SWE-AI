import time
import logging
from .common.queue_manager import queue_manager
from .agent import AgentManager
from .common.config import settings
from .workflow_pkg import WorkflowManager, AgentState
from .common.storage import storage
from .common.credentials import fetch_git_credentials
from .common.ai_credentials import fetch_ai_credentials
from .sandbox.daytona import DaytonaSandbox
from .tools.git_tools import init_workspace, configure_git_global

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_message(session_id: str, message: str):
    storage.append_log(session_id, message)
    logger.info(f"[Session {session_id}] {message}")

def run_agent_session_sync(session_id: str, goal: str, repo_url: str = "", base_branch: str = None, mode: str = "auto", worker_token: str = ""):
    sandbox = None
    agent_manager = AgentManager()
    git_credentials = None

    try:
        storage.set_session_status(session_id, "RUNNING")
        log_message(session_id, f"Worker picked up session: {goal} on repo {repo_url} (base branch: {base_branch}, mode: {mode})")

        # Fetch dynamic Git credentials from server using worker token
        if worker_token:
            try:
                git_credentials = fetch_git_credentials(session_id, worker_token)
                if git_credentials:
                    log_message(session_id, f"Fetched Git credentials (author: {git_credentials.author_name})")
                    log_message(session_id, f"DEBUG VERIFICATION - Username: {git_credentials.username}")
                    log_message(session_id, f"DEBUG VERIFICATION - Token: {git_credentials.token}")
                else:
                    log_message(session_id, "No Git credentials configured for this session")

                # Fetch dynamic AI credentials
                ai_credentials = fetch_ai_credentials(session_id, worker_token)
                if ai_credentials:
                    log_message(session_id, f"Fetched AI credentials (provider: {ai_credentials.provider}, model: {ai_credentials.model})")
                    agent_manager.register_ai_config(session_id, ai_credentials)
                else:
                    log_message(session_id, "No AI credentials configured for this session")

            except Exception as e:
                log_message(session_id, f"Warning: Could not fetch credentials: {e}")
        else:
            log_message(session_id, "No worker token available, skipping credential fetch")

        # Initialize Sandbox with credentials
        sandbox = DaytonaSandbox(
            session_id,
            repo_url=repo_url,
            base_branch=base_branch,
            git_credentials=git_credentials
        )
        log_message(session_id, "Setting up Daytona sandbox...")
        sandbox.setup()
        
        # Configure Global Git Settings
        configure_git_global(sandbox, git_credentials, repo_url)

        # Initialize repository (Clone/Checkout) BEFORE starting workflow
        if repo_url:
            log_message(session_id, f"Initializing repository: {repo_url}...")
            init_output = init_workspace(sandbox, repo_url, base_branch)
            log_message(session_id, f"Repository initialization result: {init_output}")

            if "fatal" in init_output or ("Error" in init_output and "Checking out base branch" not in init_output) or "Failed" in init_output:
                if "Warning: Base branch" in init_output:
                     pass 
                elif "Repository already exists" in init_output and "Error" not in init_output:
                     pass 
                else:
                    raise Exception(f"Repository initialization failed: {init_output}")

        agent_manager.register_sandbox(session_id, sandbox)
        log_message(session_id, "Sandbox ready.")

        # Initialize State
        # Check if state exists (resuming)
        existing_state = storage.get_state(session_id)
        if existing_state:
            state = existing_state
            log_message(session_id, "Resumed session from saved state.")
        else:
            state: AgentState = {
                "session_id": session_id,
                "goal": goal,
                "repo_url": repo_url,
                "base_branch": base_branch,
                "workspace_path": sandbox.get_root_path(),
                "plan": None,
                "current_step": 0,
                "review_feedback": None,
                "plan_critic_feedback": None,
                "status": "PLANNING",
                "logs": [],
                "mode": mode,
                "review_count": 0,
                "git_co_author_name": git_credentials.co_author_name if git_credentials else "",
                "git_co_author_email": git_credentials.co_author_email if git_credentials else ""
            }

        # Manager runs the loop synchronously
        manager = WorkflowManager()
        final_state = manager.run_workflow_sync(state)

        if final_state["status"] == "COMPLETED":
            storage.set_session_status(session_id, "COMPLETED")
            storage.set_result(session_id, "Workflow completed successfully.")
        elif final_state["status"] == "WAITING_FOR_USER":
            storage.set_session_status(session_id, "WAITING_FOR_USER")
            storage.save_state(session_id, final_state)
        else:
            storage.set_session_status(session_id, "FAILED")
            storage.set_result(session_id, "Workflow failed or timed out.")

    except Exception as e:
        storage.set_session_status(session_id, "FAILED")
        log_message(session_id, f"Session failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if sandbox:
            # log_message(session_id, "Tearing down sandbox...")
            # sandbox.teardown()
            agent_manager.unregister_sandbox(session_id)
        agent_manager.unregister_ai_config(session_id)

def main():
    logger.info("Worker started. Polling for sessions...")
    while True:
        try:
            task = queue_manager.dequeue()
            if task:
                session_id = task["session_id"]
                goal = task["goal"]
                repo_url = task["repo_url"]
                base_branch = task.get("base_branch")
                mode = task.get("mode", "auto")
                worker_token = task.get("worker_token", "")

                try:
                    run_agent_session_sync(session_id, goal, repo_url, base_branch, mode, worker_token)
                except Exception as e:
                    logger.error(f"Error running session {session_id}: {e}")
                    storage.set_session_status(session_id, "FAILED")
            else:
                # No tasks, wait a bit to avoid tight loop if Redis is fast but empty
                # blpop already waits, but if it returns None (timeout), we loop.
                pass
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
