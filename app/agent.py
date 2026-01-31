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

    def start_session(self, goal: str, repo_url: str = "", base_branch: Optional[str] = None, mode: str = "auto") -> str:
        """API Side: Enqueue the session"""
        # Generate 64-bit random integer (18-19 digits)
        session_id = str(random.randint(10**17, 9223372036854775807))
        storage.set_session_status(session_id, "QUEUED")
        queue_manager.enqueue(session_id, goal, repo_url, base_branch, mode)
        return session_id

    def resume_session(self, session_id: str) -> bool:
        """API Side: Resume a session waiting for user approval"""
        state = storage.get_state(session_id)
        if not state:
            return False

        if state.get("status") != "WAITING_FOR_USER":
            return False

        # Update status to CODING
        state["status"] = "CODING"
        storage.save_state(session_id, state)
        storage.set_session_status(session_id, "QUEUED") # Re-queue status

        # Re-enqueue
        # Note: Parameters are redundant if worker loads from state, but queue_manager requires them.
        # We can pass empty strings for goal/repo as they should be in the saved state.
        # However, to be safe and consistent with queue_manager signature:
        queue_manager.enqueue(
            session_id,
            state.get("goal", ""),
            state.get("repo_url", ""),
            state.get("base_branch"),
            state.get("mode", "auto")
        )
        return True

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """API Side: Read status"""
        return {
            "id": session_id,
            "status": storage.get_session_status(session_id),
            "logs": storage.get_logs(session_id),
            "result": storage.get_result(session_id)
        }

    def get_sandbox(self, session_id: str) -> Optional[Sandbox]:
        """Worker Side: Retrieve active sandbox"""
        return ACTIVE_SANDBOXES.get(session_id)

    def register_sandbox(self, session_id: str, sandbox: Sandbox):
        """Worker Side: Register sandbox"""
        ACTIVE_SANDBOXES[session_id] = sandbox

    def unregister_sandbox(self, session_id: str):
        """Worker Side: Cleanup"""
        if session_id in ACTIVE_SANDBOXES:
            del ACTIVE_SANDBOXES[session_id]
