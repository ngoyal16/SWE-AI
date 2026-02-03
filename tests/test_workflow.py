import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.workflow import WorkflowManager, AgentState

class TestWorkflow(unittest.TestCase):

    @patch("app.workflow.initializer_node")
    @patch("app.workflow.get_active_sandbox")
    @patch("app.workflow.planner_node")
    @patch("app.workflow.plan_critic_node")
    @patch("app.workflow.branch_naming_node")
    @patch("app.workflow.programmer_node")
    @patch("app.workflow.reviewer_node")
    @patch("app.workflow.commit_msg_node")
    def test_manager_orchestration_with_init(self, mock_commit_msg, mock_reviewer, mock_programmer, mock_branch_naming, mock_critic, mock_planner, mock_get_sandbox, mock_init_node):
        # Setup transitions
        def init_side_effect(state):
            state["status"] = "PLANNING"
            state["codebase_tree"] = "tree"
            state["logs"].append("Workspace initialization result:\nInitialized")
            return state
        def planner_side_effect(state):
            state["status"] = "PLAN_CRITIC"
            return state
        def critic_side_effect(state):
            # Check mode to determine transition
            if state.get("mode") == "review":
                 state["status"] = "WAITING_FOR_USER"
                 state["next_status"] = "BRANCH_NAMING"
            else:
                 state["status"] = "BRANCH_NAMING"
            return state
        def branch_naming_side_effect(state):
            # Should go directly to CODING regardless of mode
            state["status"] = "CODING"
            return state
        def programmer_side_effect(state):
            state["status"] = "REVIEWING"
            return state
        def reviewer_side_effect(state):
            state["status"] = "COMMITTING"
            return state
        def commit_msg_side_effect(state):
            state["status"] = "COMPLETED"
            return state

        mock_init_node.side_effect = init_side_effect
        mock_planner.side_effect = planner_side_effect
        mock_critic.side_effect = critic_side_effect
        mock_branch_naming.side_effect = branch_naming_side_effect
        mock_programmer.side_effect = programmer_side_effect
        mock_reviewer.side_effect = reviewer_side_effect
        mock_commit_msg.side_effect = commit_msg_side_effect

        mock_sandbox = MagicMock()
        mock_get_sandbox.return_value = mock_sandbox

        manager = WorkflowManager()
        initial_state: AgentState = {
            "session_id": "test",
            "goal": "test",
            "repo_url": "http://repo",
            "base_branch": "develop",
            "plan": None,
            "current_step": 0,
            "review_feedback": None,
            "plan_critic_feedback": None,
            "status": "PLANNING",
            "logs": [],
            "workspace_path": "/tmp/test",
            "mode": "auto" # Default mode test
        }

        final_state = manager.run_workflow_sync(initial_state)

        self.assertEqual(final_state["status"], "COMPLETED")

        # Verify initializer_node was called
        mock_init_node.assert_called_once()
        self.assertIn("Workspace initialization result:\nInitialized", final_state["logs"])

    @patch("app.workflow.initializer_node")
    @patch("app.workflow.get_active_sandbox")
    @patch("app.workflow.planner_node")
    @patch("app.workflow.plan_critic_node")
    @patch("app.workflow.branch_naming_node")
    @patch("app.workflow.programmer_node")
    @patch("app.workflow.reviewer_node")
    @patch("app.workflow.commit_msg_node")
    def test_manager_review_mode_pause(self, mock_commit_msg, mock_reviewer, mock_programmer, mock_branch_naming, mock_critic, mock_planner, mock_get_sandbox, mock_init_node):
         # Test that it pauses at WAITING_FOR_USER
        def init_side_effect(state):
            state["status"] = "PLANNING"
            state["codebase_tree"] = "tree"
            return state
        def planner_side_effect(state):
            state["status"] = "PLAN_CRITIC"
            return state
        def critic_side_effect(state):
            if state.get("mode") == "review":
                 state["status"] = "WAITING_FOR_USER"
                 state["next_status"] = "BRANCH_NAMING"
            return state

        mock_init_node.side_effect = init_side_effect
        mock_planner.side_effect = planner_side_effect
        mock_critic.side_effect = critic_side_effect

        mock_sandbox = MagicMock()
        mock_get_sandbox.return_value = mock_sandbox

        manager = WorkflowManager()
        initial_state: AgentState = {
            "session_id": "test-review",
            "goal": "test",
            "repo_url": "",
            "base_branch": None,
            "plan": None,
            "current_step": 0,
            "review_feedback": None,
            "plan_critic_feedback": None,
            "status": "PLANNING",
            "logs": [],
            "workspace_path": "/tmp/test",
            "mode": "review"
        }

        final_state = manager.run_workflow_sync(initial_state)

        self.assertEqual(final_state["status"], "WAITING_FOR_USER")
        self.assertEqual(final_state["next_status"], "BRANCH_NAMING")

    @patch("app.workflow.init_workspace")
    @patch("app.workflow.get_active_sandbox")
    def test_initializer_node_logic(self, mock_get_sandbox, mock_init_workspace):
        from app.workflow import initializer_node
        mock_sandbox = MagicMock()
        mock_sandbox.generate_codebase_tree.return_value = "tree-output"
        mock_get_sandbox.return_value = mock_sandbox
        mock_init_workspace.return_value = "Cloned"

        state: AgentState = {
            "session_id": "test-init",
            "goal": "test",
            "repo_url": "http://repo",
            "logs": [],
            "status": "PLANNING",
            "workspace_path": "/tmp/test"
        }

        new_state = initializer_node(state)

        self.assertEqual(new_state["status"], "PLANNING")
        self.assertEqual(new_state["codebase_tree"], "tree-output")
        mock_init_workspace.assert_called_once()

    @patch("app.workflow.init_workspace")
    @patch("app.workflow.get_active_sandbox")
    def test_initializer_node_failure(self, mock_get_sandbox, mock_init_workspace):
        from app.workflow import initializer_node
        mock_sandbox = MagicMock()
        mock_get_sandbox.return_value = mock_sandbox
        mock_init_workspace.side_effect = Exception("Git error")

        state: AgentState = {
            "session_id": "test-fail",
            "goal": "test",
            "repo_url": "http://repo",
            "logs": [],
            "status": "PLANNING",
            "workspace_path": "/tmp/test"
        }

        new_state = initializer_node(state)

        self.assertEqual(new_state["status"], "FAILED")
        self.assertIn("Initialization failed: Git error", new_state["logs"])

if __name__ == "__main__":
    unittest.main()
