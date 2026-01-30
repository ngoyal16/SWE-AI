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
    @patch("app.workflow.plan_critic_node")
    @patch("app.workflow.programmer_node")
    @patch("app.workflow.reviewer_node")
    def test_manager_orchestration(self, mock_reviewer, mock_programmer, mock_critic, mock_planner):
        # Setup transitions
        # 1. Start PLANNING -> returns PLAN_CRITIC
        # 2. Start PLAN_CRITIC -> returns CODING (Approved)
        # 3. Start CODING -> returns REVIEWING
        # 4. Start REVIEWING -> returns COMPLETED

        def planner_side_effect(state):
            state["status"] = "PLAN_CRITIC"
            state["plan"] = "Plan created"
            return state

        def critic_side_effect(state):
            state["status"] = "CODING"
            return state

        def programmer_side_effect(state):
            state["status"] = "REVIEWING"
            return state

        def reviewer_side_effect(state):
            state["status"] = "COMPLETED"
            return state

        mock_planner.side_effect = planner_side_effect
        mock_critic.side_effect = critic_side_effect
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
            "plan_critic_feedback": None,
            "status": "PLANNING",
            "logs": [],
            "workspace_path": "/tmp/test"
        }

        # Updated to call sync method (simulating what run_in_executor does)
        final_state = manager.run_workflow_sync(initial_state)

        self.assertEqual(final_state["status"], "COMPLETED")
        self.assertEqual(mock_planner.call_count, 1)
        self.assertEqual(mock_critic.call_count, 1)
        self.assertEqual(mock_programmer.call_count, 1)
        self.assertEqual(mock_reviewer.call_count, 1)
        print("Workflow Manager test passed!")

    @patch("app.workflow.planner_node")
    @patch("app.workflow.plan_critic_node")
    def test_critic_rejection_loop(self, mock_critic, mock_planner):
        # Test loop: PLANNING -> PLAN_CRITIC -> PLANNING -> PLAN_CRITIC -> CODING

        def planner_side_effect(state):
            state["status"] = "PLAN_CRITIC"
            return state

        mock_critic.side_effect = [
            lambda s: {**s, "status": "PLANNING", "plan_critic_feedback": "Bad plan"}, # First call rejects
            lambda s: {**s, "status": "CODING"} # Second call accepts
        ]
        mock_planner.side_effect = planner_side_effect

        manager = WorkflowManager()
        initial_state: AgentState = {
            "task_id": "test",
            "goal": "test",
            "repo_url": "http://repo",
            "plan": None,
            "current_step": 0,
            "review_feedback": None,
            "plan_critic_feedback": None,
            "status": "PLANNING",
            "logs": [],
            "workspace_path": "/tmp/test"
        }

        # We need to mock programmer/reviewer too or stop the loop manually for test if status becomes CODING
        # But run_workflow_sync loops until COMPLETED/FAILED.
        # Let's mock programmer to finish it
        with patch("app.workflow.programmer_node") as mock_prog, \
             patch("app.workflow.reviewer_node") as mock_rev:

             mock_prog.side_effect = lambda s: {**s, "status": "REVIEWING"}
             mock_rev.side_effect = lambda s: {**s, "status": "COMPLETED"}

             # The mock_critic needs to be callable with side_effect list
             # The lambda wrapper above doesn't work with side_effect list directly if we want different behaviors
             # Let's use an iterator

             iter_critic = iter([
                 lambda s: {**s, "status": "PLANNING", "plan_critic_feedback": "Bad plan"},
                 lambda s: {**s, "status": "CODING"}
             ])
             mock_critic.side_effect = lambda s: next(iter_critic)(s)

             manager.run_workflow_sync(initial_state)

             # Planner called twice (initial + retry)
             self.assertEqual(mock_planner.call_count, 2)
             # Critic called twice
             self.assertEqual(mock_critic.call_count, 2)

if __name__ == "__main__":
    unittest.main()
