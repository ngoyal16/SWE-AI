import asyncio
import logging
from typing import List, Dict, Any, Optional
import concurrent.futures

from app.workflow import WorkflowManager, AgentState
from app.sandbox.base import Sandbox
from app.sandbox.local import LocalSandbox
from app.sandbox.k8s import K8sSandbox
from app.config import settings
from app.storage import storage

# Registry for active sandboxes
ACTIVE_SANDBOXES: Dict[str, Sandbox] = {}

def log_message(task_id: str, message: str):
    storage.append_log(task_id, message)
    print(f"[Task {task_id}] {message}")

async def run_agent_task_async(task_id: str, goal: str, repo_url: str):
    """
    Wrapper to run the blocking workflow in a thread pool executor
    to prevent blocking the asyncio event loop.
    """
    loop = asyncio.get_running_loop()
    # Use a ThreadPoolExecutor to run the synchronous workflow logic
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, run_agent_task_sync, task_id, goal, repo_url)

def run_agent_task_sync(task_id: str, goal: str, repo_url: str = ""):
    # This function contains blocking calls (subprocess, k8s client, synchronous LLM invokes)
    # It must be run in a separate thread.
    sandbox = None
    try:
        storage.set_task_status(task_id, "RUNNING")
        log_message(task_id, f"Starting task: {goal} on repo {repo_url}")

        # Initialize Sandbox
        if settings.SANDBOX_TYPE == "k8s":
            sandbox = K8sSandbox(task_id)
        else:
            sandbox = LocalSandbox(task_id)

        log_message(task_id, f"Setting up sandbox ({settings.SANDBOX_TYPE})...")
        sandbox.setup()
        ACTIVE_SANDBOXES[task_id] = sandbox
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

        # Manager runs the loop synchronously now
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
            if task_id in ACTIVE_SANDBOXES:
                del ACTIVE_SANDBOXES[task_id]

class AgentManager:
    """Singleton to manage background tasks"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
        return cls._instance

    def start_task(self, goal: str, repo_url: str = "") -> str:
        import uuid
        task_id = str(uuid.uuid4())
        storage.set_task_status(task_id, "QUEUED")
        # Fire and forget async task which wraps the sync execution
        asyncio.create_task(run_agent_task_async(task_id, goal, repo_url))
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return {
            "id": task_id,
            "status": storage.get_task_status(task_id),
            "logs": storage.get_logs(task_id),
            "result": storage.get_result(task_id)
        }

    def get_sandbox(self, task_id: str) -> Optional[Sandbox]:
        return ACTIVE_SANDBOXES.get(task_id)
