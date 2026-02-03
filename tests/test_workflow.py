import asyncio
import unittest
from unittest.mock import MagicMock, patch
from agent.workflow_pkg.manager import WorkflowManager
from agent.workflow_pkg.state import AgentState

class TestWorkflow(unittest.TestCase):

    @patch("agent.workflow_pkg.manager.initializer_node")
    @patch("agent.workflow_pkg.manager.env_setup_node")
    @patch("agent.workflow_pkg.manager.planner_node")
    @patch("agent.workflow_pkg.manager.plan_critic_node")
    @patch("agent.workflow_pkg.manager.branch_naming_node")
    @patch("agent.workflow_pkg.manager.programmer_node")
    @patch("agent.workflow_pkg.manager.tester_node")
    @patch("agent.workflow_pkg.manager.reviewer_node")
    @patch("agent.workflow_pkg.manager.commit_msg_node")
    def test_manager_orchestration_with_init(self, mock_commit_msg, mock_reviewer, mock_tester, mock_programmer, mock_branch_naming, mock_critic, mock_planner, mock_env_setup, mock_init_node):
        # Setup transitions
        def init_side_effect(state):
            state["status"] = "ENV_SETUP" # Changed transition
            state["codebase_tree"] = "tree"
            state["logs"].append("Workspace initialization result:\nInitialized")
            return state
        def env_setup_side_effect(state):
            state["status"] = "PLANNING"
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
            state["status"] = "TESTING"
            return state
        def tester_side_effect(state):
            state["status"] = "REVIEWING"
            return state
        def reviewer_side_effect(state):
            state["status"] = "COMMITTING"
            return state
        def commit_msg_side_effect(state):
            state["status"] = "COMPLETED"
            return state

        mock_init_node.side_effect = init_side_effect
        mock_env_setup.side_effect = env_setup_side_effect
        mock_planner.side_effect = planner_side_effect
        mock_critic.side_effect = critic_side_effect
        mock_branch_naming.side_effect = branch_naming_side_effect
        mock_programmer.side_effect = programmer_side_effect
        mock_tester.side_effect = tester_side_effect
        mock_reviewer.side_effect = reviewer_side_effect
        mock_commit_msg.side_effect = commit_msg_side_effect

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

    @patch("agent.workflow_pkg.manager.initializer_node")
    @patch("agent.workflow_pkg.manager.env_setup_node")
    @patch("agent.workflow_pkg.manager.planner_node")
    @patch("agent.workflow_pkg.manager.plan_critic_node")
    @patch("agent.workflow_pkg.manager.branch_naming_node")
    @patch("agent.workflow_pkg.manager.programmer_node")
    @patch("agent.workflow_pkg.manager.tester_node")
    @patch("agent.workflow_pkg.manager.reviewer_node")
    @patch("agent.workflow_pkg.manager.commit_msg_node")
    def test_manager_review_mode_pause(self, mock_commit_msg, mock_reviewer, mock_tester, mock_programmer, mock_branch_naming, mock_critic, mock_planner, mock_env_setup, mock_init_node):
         # Test that it pauses at WAITING_FOR_USER
        def init_side_effect(state):
            state["status"] = "ENV_SETUP"
            state["codebase_tree"] = "tree"
            return state
        def env_setup_side_effect(state):
            state["status"] = "PLANNING"
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
        mock_env_setup.side_effect = env_setup_side_effect
        mock_planner.side_effect = planner_side_effect
        mock_critic.side_effect = critic_side_effect

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

    @patch("agent.workflow_pkg.manager.initializer_node")
    @patch("agent.workflow_pkg.manager.env_setup_node")
    @patch("agent.workflow_pkg.manager.planner_node")
    @patch("agent.workflow_pkg.manager.plan_critic_node")
    @patch("agent.workflow_pkg.manager.branch_naming_node")
    @patch("agent.workflow_pkg.manager.programmer_node")
    @patch("agent.workflow_pkg.manager.tester_node")
    @patch("agent.workflow_pkg.manager.reviewer_node")
    @patch("agent.workflow_pkg.manager.commit_msg_node")
    def test_manager_orchestration_tester_fail(self, mock_commit_msg, mock_reviewer, mock_tester, mock_programmer, mock_branch_naming, mock_critic, mock_planner, mock_env_setup, mock_init_node):
        # Test the loop Programmer -> Tester -> Programmer

        # We need a counter to break the loop or simulate fix
        self.programmer_calls = 0

        def init_side_effect(state):
            state["status"] = "ENV_SETUP"
            state["codebase_tree"] = "tree"
            return state
        def env_setup_side_effect(state):
            state["status"] = "PLANNING"
            return state
        def planner_side_effect(state):
            state["status"] = "PLAN_CRITIC"
            return state
        def critic_side_effect(state):
            state["status"] = "BRANCH_NAMING"
            return state
        def branch_naming_side_effect(state):
            state["status"] = "CODING"
            return state
        def programmer_side_effect(state):
            self.programmer_calls += 1
            state["status"] = "TESTING"
            return state
        def tester_side_effect(state):
            if self.programmer_calls == 1:
                state["status"] = "CODING"
                state["review_feedback"] = "Tests failed"
            else:
                state["status"] = "REVIEWING"
            return state
        def reviewer_side_effect(state):
            state["status"] = "COMMITTING"
            return state
        def commit_msg_side_effect(state):
            state["status"] = "COMPLETED"
            return state

        mock_init_node.side_effect = init_side_effect
        mock_env_setup.side_effect = env_setup_side_effect
        mock_planner.side_effect = planner_side_effect
        mock_critic.side_effect = critic_side_effect
        mock_branch_naming.side_effect = branch_naming_side_effect
        mock_programmer.side_effect = programmer_side_effect
        mock_tester.side_effect = tester_side_effect
        mock_reviewer.side_effect = reviewer_side_effect
        mock_commit_msg.side_effect = commit_msg_side_effect

        manager = WorkflowManager()
        initial_state: AgentState = {
            "session_id": "test-loop",
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
            "mode": "auto"
        }

        final_state = manager.run_workflow_sync(initial_state)

        self.assertEqual(final_state["status"], "COMPLETED")
        self.assertEqual(self.programmer_calls, 2)

if __name__ == "__main__":
    unittest.main()
