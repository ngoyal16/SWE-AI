import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.agent import AgentManager, run_agent_task_sync
from app.storage import storage

class TestAgent(unittest.TestCase):

    @patch("app.workflow.get_llm")
    @patch("app.workflow.AgentExecutor")
    @patch("app.workflow.create_tool_calling_agent")
    def test_agent_execution_flow(self, mock_create_agent, mock_executor_cls, mock_get_llm):
        # Setup mocks
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # Mock LLM response to be a string-like object that satisfies Pydantic validation for StrOutputParser
        # LangChain's StrOutputParser expects an AIMessage or string.
        # If it gets an AIMessage, it takes .content.

        from langchain_core.messages import AIMessage
        mock_llm.invoke.return_value = AIMessage(content="Mocked Plan")

        # IMPORTANT: The Chain invoke in planner_node calls llm.invoke.
        # We need to make sure the pipeline `prompt | llm | parser` works with our mock.
        # It's safer to patch `planner_node` directly if we don't want to rely on internal chain behavior mocking.
        # But let's try to fix the validation error.
        # The validation error "Generation text str type expected" usually happens when the parser
        # receives something that isn't a string/message.

        # Let's bypass the chain logic by patching planner_node
        # This is an integration test of the agent loop, not the LangChain internals.

        with patch("app.workflow.planner_node") as mock_planner, \
             patch("app.workflow.programmer_node") as mock_programmer, \
             patch("app.workflow.reviewer_node") as mock_reviewer:

            mock_planner.side_effect = lambda state: {**state, "status": "CODING", "plan": "Mock Plan"}
            mock_programmer.side_effect = lambda state: {**state, "status": "REVIEWING"}
            mock_reviewer.side_effect = lambda state: {**state, "status": "COMPLETED"}

            task_id = "test-task-1"
            goal = "Write a file"

            with patch("app.agent.LocalSandbox") as MockSandbox:
                 mock_sb_instance = MockSandbox.return_value
                 mock_sb_instance.get_root_path.return_value = "/tmp/test"

                 run_agent_task_sync(task_id, goal)

            # Verify flow
            mock_planner.assert_called()
            mock_programmer.assert_called()
            mock_reviewer.assert_called()

        print("Agent mock test passed!")

if __name__ == "__main__":
    unittest.main()
