import asyncio
import os
import shutil
import unittest
from unittest.mock import MagicMock, patch
from app.agent import run_agent_task, TASK_STATUS
from app.config import settings

class TestMultiSession(unittest.TestCase):

    def setUp(self):
        # Clean up workspace
        if os.path.exists(settings.WORKSPACE_DIR):
            shutil.rmtree(settings.WORKSPACE_DIR)
        os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)

    @patch("app.workflow.get_llm")
    @patch("app.workflow.create_tool_calling_agent")
    @patch("app.workflow.AgentExecutor")
    def test_isolation(self, mock_executor_cls, mock_create_agent, mock_get_llm):
        # Mock LLM and Agent Executor
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # We need to simulate the agent actually writing files to test isolation
        # But since we mock the executor, the tools won't run via the LLM.
        # We can simulate the side effects in the agent executor invoke return or by manually verifying the path setup.

        # Let's verify that run_agent_task creates the directories correctly.

        # Mocking the workflow manager to avoid running the full loop,
        # but we want to check if the state received has the correct workspace path.

        task1_id = "task-1"
        task2_id = "task-2"

        # We'll use a side effect on WorkflowManager.run_workflow to verify state
        with patch("app.agent.WorkflowManager") as MockManager:
            mock_instance = MockManager.return_value

            async def run_workflow_side_effect(state):
                # Simulate doing work in the workspace
                path = state["workspace_path"]
                os.makedirs(path, exist_ok=True)
                with open(os.path.join(path, f"{state['task_id']}.txt"), "w") as f:
                    f.write(f"I am {state['task_id']}")

                state["status"] = "COMPLETED"
                state["logs"] = ["Done"]
                return state

            mock_instance.run_workflow.side_effect = run_workflow_side_effect

            # Run tasks
            asyncio.run(run_agent_task(task1_id, "Goal 1"))
            asyncio.run(run_agent_task(task2_id, "Goal 2"))

            # Verify isolation
            path1 = os.path.join(settings.WORKSPACE_DIR, task1_id)
            path2 = os.path.join(settings.WORKSPACE_DIR, task2_id)

            self.assertTrue(os.path.exists(path1))
            self.assertTrue(os.path.exists(path2))

            self.assertTrue(os.path.exists(os.path.join(path1, "task-1.txt")))
            self.assertFalse(os.path.exists(os.path.join(path1, "task-2.txt")))

            self.assertTrue(os.path.exists(os.path.join(path2, "task-2.txt")))
            self.assertFalse(os.path.exists(os.path.join(path2, "task-1.txt")))

            print("Multi-session isolation verified!")

if __name__ == "__main__":
    unittest.main()
