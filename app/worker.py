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

def log_message(task_id: str, message: str):
    storage.append_log(task_id, message)
    logger.info(f"[Task {task_id}] {message}")

def run_agent_task_sync(task_id: str, goal: str, repo_url: str = ""):
    sandbox = None
    agent_manager = AgentManager()

    try:
        storage.set_task_status(task_id, "RUNNING")
        log_message(task_id, f"Worker picked up task: {goal} on repo {repo_url}")

        # Initialize Sandbox
        if settings.SANDBOX_TYPE == "k8s":
            sandbox = K8sSandbox(task_id)
        else:
            sandbox = LocalSandbox(task_id)

        log_message(task_id, f"Setting up sandbox ({settings.SANDBOX_TYPE})...")
        sandbox.setup()
        agent_manager.register_sandbox(task_id, sandbox)
        log_message(task_id, "Sandbox ready.")

        # Initialize State
        state: AgentState = {
            "task_id": task_id,
            "goal": goal,
            "repo_url": repo_url,
            "workspace_path": sandbox.get_root_path(),
            "plan": None,
            "current_step": 0,
            "review_feedback": None,
            "plan_critic_feedback": None,
            "status": "PLANNING",
            "logs": []
        }

        # Manager runs the loop synchronously
        manager = WorkflowManager()
        final_state = manager.run_workflow_sync(state)

        # Merge logs
        for log in final_state["logs"]:
            log_message(task_id, log)

        if final_state["status"] == "COMPLETED":
            storage.set_task_status(task_id, "COMPLETED")
            storage.set_result(task_id, "Workflow completed successfully.")
        else:
            storage.set_task_status(task_id, "FAILED")
            storage.set_result(task_id, "Workflow failed or timed out.")

    except Exception as e:
        storage.set_task_status(task_id, "FAILED")
        log_message(task_id, f"Task failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if sandbox:
            log_message(task_id, "Tearing down sandbox...")
            sandbox.teardown()
            agent_manager.unregister_sandbox(task_id)

def main():
    logger.info("Worker started. Polling for tasks...")
    while True:
        try:
            task = queue_manager.dequeue()
            if task:
                run_agent_task_sync(task["task_id"], task["goal"], task["repo_url"])
            else:
                # No tasks, wait a bit to avoid tight loop if Redis is fast but empty
                # blpop already waits, but if it returns None (timeout), we loop.
                pass
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
