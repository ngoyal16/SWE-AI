import time
import logging
from app.queue_manager import queue_manager
from app.agent import AgentManager
from app.workflow import WorkflowManager, AgentState
from app.storage import storage
from app.config import settings
from app.sandbox.k8s import K8sSandbox
from app.sandbox.local import LocalSandbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_message(session_id: str, message: str):
    storage.append_log(session_id, message)
    logger.info(f"[Session {session_id}] {message}")

def run_agent_session_sync(session_id: str, goal: str, repo_url: str = "", base_branch: str = None, mode: str = "auto"):
    sandbox = None
    agent_manager = AgentManager()

    try:
        storage.set_session_status(session_id, "RUNNING")
        log_message(session_id, f"Worker picked up session: {goal} on repo {repo_url} (base branch: {base_branch}, mode: {mode})")

        # Initialize Sandbox
        if settings.SANDBOX_TYPE == "k8s":
            sandbox = K8sSandbox(session_id)
        else:
            sandbox = LocalSandbox(session_id)

        log_message(session_id, f"Setting up sandbox ({settings.SANDBOX_TYPE})...")
        sandbox.setup()
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
                "mode": mode
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

def main():
    logger.info("Worker started. Polling for sessions...")
    while True:
        try:
            task = queue_manager.dequeue()
            if task:
                run_agent_session_sync(
                    task["session_id"],
                    task["goal"],
                    task["repo_url"],
                    task.get("base_branch"),
                    task.get("mode", "auto")
                )
            else:
                # No tasks, wait a bit to avoid tight loop if Redis is fast but empty
                # blpop already waits, but if it returns None (timeout), we loop.
                pass
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
