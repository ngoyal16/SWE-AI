import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.agent import AgentManager, run_agent_task

class TestAgent(unittest.TestCase):

    @patch("app.agent.get_llm")
    @patch("app.agent.AgentExecutor")
    @patch("app.agent.create_tool_calling_agent")
    def test_agent_execution_flow(self, mock_create_agent, mock_executor_cls, mock_get_llm):
        # Setup mocks
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        mock_executor_instance = MagicMock()
        mock_executor_cls.return_value = mock_executor_instance

        # Mock ainvoke to be an async function
        async def async_return(*args, **kwargs):
            return {"output": "Mocked success"}

        mock_executor_instance.ainvoke.side_effect = async_return

        # Initialize manager
        manager = AgentManager()

        # Since start_task calls create_task, we need to run it in an event loop
        # But unit testing async create_task is tricky without proper async test runner.
        # We will test run_agent_task directly.

        task_id = "test-task-1"
        goal = "Write a file"

        asyncio.run(run_agent_task(task_id, goal))

        # Verify interactions
        mock_get_llm.assert_called_once()
        mock_create_agent.assert_called_once()
        mock_executor_cls.assert_called_once()
        mock_executor_instance.ainvoke.assert_called_once_with({"input": goal})

        from app.agent import TASK_STATUS, TASK_RESULTS
        self.assertEqual(TASK_STATUS[task_id], "COMPLETED")
        self.assertEqual(TASK_RESULTS[task_id], "Mocked success")
        print("Agent mock test passed!")

if __name__ == "__main__":
    unittest.main()
