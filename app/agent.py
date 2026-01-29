import asyncio
import logging
import os
from typing import List, Dict, Any

from app.workflow import WorkflowManager, AgentState
from app.config import settings

# Simple in-memory logger/storage
TASK_LOGS: Dict[str, List[str]] = {}
TASK_STATUS: Dict[str, str] = {}
TASK_RESULTS: Dict[str, str] = {}

def log_message(task_id: str, message: str):
    if task_id not in TASK_LOGS:
        TASK_LOGS[task_id] = []
    TASK_LOGS[task_id].append(message)
    print(f"[Task {task_id}] {message}")

async def run_agent_task(task_id: str, goal: str, repo_url: str = ""):
    try:
        TASK_STATUS[task_id] = "RUNNING"
        log_message(task_id, f"Starting task: {goal} on repo {repo_url}")

        # Define workspace for this task
        workspace_path = os.path.join(settings.WORKSPACE_DIR, task_id)
        os.makedirs(workspace_path, exist_ok=True)
        log_message(task_id, f"Workspace created at: {workspace_path}")

        # Initialize State
        state: AgentState = {
            "task_id": task_id,
            "goal": goal,
            "repo_url": repo_url,
            "workspace_path": workspace_path,
            "plan": None,
            "current_step": 0,
            "review_feedback": None,
            "status": "PLANNING",
            "logs": []
        }

        manager = WorkflowManager()
        final_state = await manager.run_workflow(state)

        # Merge logs
        for log in final_state["logs"]:
            log_message(task_id, log)

        if final_state["status"] == "COMPLETED":
            TASK_STATUS[task_id] = "COMPLETED"
            TASK_RESULTS[task_id] = "Workflow completed successfully."
        else:
            TASK_STATUS[task_id] = "FAILED"
            TASK_RESULTS[task_id] = "Workflow failed or timed out."

    except Exception as e:
        TASK_STATUS[task_id] = "FAILED"
        log_message(task_id, f"Task failed: {str(e)}")
        import traceback
        traceback.print_exc()

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
        TASK_STATUS[task_id] = "QUEUED"
        # Fire and forget async task
        asyncio.create_task(run_agent_task(task_id, goal, repo_url))
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return {
            "id": task_id,
            "status": TASK_STATUS.get(task_id, "UNKNOWN"),
            "logs": TASK_LOGS.get(task_id, []),
            "result": TASK_RESULTS.get(task_id)
        }
