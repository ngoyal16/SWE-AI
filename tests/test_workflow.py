import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.workflow import WorkflowManager, AgentState

class TestWorkflow(unittest.TestCase):

    @patch("app.workflow.get_llm")
    @patch("app.workflow.create_tool_calling_agent")
    @patch("app.workflow.AgentExecutor")
    def test_workflow_transitions(self, mock_executor_cls, mock_create_agent, mock_get_llm):
        # Setup mocks
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # Mock Planner output
        mock_planner_chain = MagicMock()
        mock_planner_chain.invoke.return_value = "Step 1: Do something"
        # We need to mock the chain construction pipeline in planner_node
        # prompt | llm | parser -> invoke
        # It's easier to mock planner_node directly or the components inside.

        # Let's mock the nodes directly for unit testing the manager logic
        # But here we want to test the manager orchestrating the nodes.

        pass

    @patch("app.workflow.planner_node")
    @patch("app.workflow.programmer_node")
    @patch("app.workflow.reviewer_node")
    def test_manager_orchestration(self, mock_reviewer, mock_programmer, mock_planner):
        # Setup transitions
        # 1. Start PLANNING -> returns CODING
        # 2. Start CODING -> returns REVIEWING
        # 3. Start REVIEWING -> returns COMPLETED

        def planner_side_effect(state):
            state["status"] = "CODING"
            state["plan"] = "Plan created"
            return state

        def programmer_side_effect(state):
            state["status"] = "REVIEWING"
            return state

        def reviewer_side_effect(state):
            state["status"] = "COMPLETED"
            return state

        mock_planner.side_effect = planner_side_effect
        mock_programmer.side_effect = programmer_side_effect
        mock_reviewer.side_effect = reviewer_side_effect

        manager = WorkflowManager()
        initial_state: AgentState = {
            "task_id": "test",
            "goal": "test",
            "repo_url": "http://repo",
            "plan": None,
            "current_step": 0,
            "review_feedback": None,
            "status": "PLANNING",
            "logs": []
        }

        final_state = asyncio.run(manager.run_workflow(initial_state))

        self.assertEqual(final_state["status"], "COMPLETED")
        self.assertEqual(mock_planner.call_count, 1)
        self.assertEqual(mock_programmer.call_count, 1)
        self.assertEqual(mock_reviewer.call_count, 1)
        print("Workflow Manager test passed!")

if __name__ == "__main__":
    unittest.main()
