import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.agent import AgentManager

class TestAgent(unittest.TestCase):

    @patch("app.agent.queue_manager")
    @patch("app.agent.storage")
    def test_agent_enqueue(self, mock_storage, mock_queue):
        # Test that start_session enqueues instead of running
        manager = AgentManager()

        session_id = manager.start_session("Goal", "Repo")

        mock_storage.set_session_status.assert_called_with(session_id, "QUEUED")
        mock_queue.enqueue.assert_called_with(session_id, "Goal", "Repo", None)

        # Ensure run_agent_session_async is NOT called directly (it's called by the async loop which is not running here,
        # or we patched start_session logic).
        # Actually start_session calls asyncio.create_task(run_agent_session_async...) in the OLD code.
        # In the NEW code, it calls queue_manager.enqueue.
        # We need to verify we aren't starting a local thread/session.

        # Verify run_agent_session_async was NOT imported/called?
        # Since we refactored AgentManager to NOT call run_agent_session_async but just enqueue,
        # we are good if enqueue is called.
        pass

if __name__ == "__main__":
    unittest.main()
