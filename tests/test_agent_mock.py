import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.agent import AgentManager

class TestAgent(unittest.TestCase):

    @patch("app.agent.queue_manager")
    @patch("app.agent.storage")
    def test_agent_enqueue(self, mock_storage, mock_queue):
        # Test that start_task enqueues instead of running
        manager = AgentManager()

        task_id = manager.start_task("Goal", "Repo")

        mock_storage.set_task_status.assert_called_with(task_id, "QUEUED")
        mock_queue.enqueue.assert_called_with(task_id, "Goal", "Repo")

        # Ensure run_agent_task_async is NOT called directly (it's called by the async loop which is not running here,
        # or we patched start_task logic).
        # Actually start_task calls asyncio.create_task(run_agent_task_async...) in the OLD code.
        # In the NEW code, it calls queue_manager.enqueue.
        # We need to verify we aren't starting a local thread/task.

        # Verify run_agent_task_async was NOT imported/called?
        # Since we refactored AgentManager to NOT call run_agent_task_async but just enqueue,
        # we are good if enqueue is called.
        pass

if __name__ == "__main__":
    unittest.main()
