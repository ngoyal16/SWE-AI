import random
from typing import Dict, Any, Optional
from app.storage import storage
from app.queue_manager import queue_manager
from app.sandbox.base import Sandbox

# Registry for active sandboxes (Used by Worker process only)
ACTIVE_SANDBOXES: Dict[str, Sandbox] = {}

class AgentManager:
    """Singleton to manage task submission (API side) and execution (Worker side)"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentManager, cls).__new__(cls)
        return cls._instance

    def start_task(self, goal: str, repo_url: str = "", base_branch: Optional[str] = None) -> str:
        """API Side: Enqueue the task"""
        # Generate 64-bit random integer (18-19 digits)
        task_id = str(random.randint(10**17, 9223372036854775807))
        storage.set_task_status(task_id, "QUEUED")
        queue_manager.enqueue(task_id, goal, repo_url, base_branch)
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """API Side: Read status"""
        return {
            "id": task_id,
            "status": storage.get_task_status(task_id),
            "logs": storage.get_logs(task_id),
            "result": storage.get_result(task_id)
        }

    def get_sandbox(self, task_id: str) -> Optional[Sandbox]:
        """Worker Side: Retrieve active sandbox"""
        return ACTIVE_SANDBOXES.get(task_id)

    def register_sandbox(self, task_id: str, sandbox: Sandbox):
        """Worker Side: Register sandbox"""
        ACTIVE_SANDBOXES[task_id] = sandbox

    def unregister_sandbox(self, task_id: str):
        """Worker Side: Cleanup"""
        if task_id in ACTIVE_SANDBOXES:
            del ACTIVE_SANDBOXES[task_id]
