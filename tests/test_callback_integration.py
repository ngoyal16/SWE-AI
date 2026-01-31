import unittest
from unittest.mock import MagicMock, patch
from app.callbacks import SessionCallbackHandler

class TestCallbackIntegration(unittest.TestCase):
    @patch('app.callbacks.storage')
    def test_callback_handler_tool_events(self, mock_storage):
        handler = SessionCallbackHandler("session-123")

        # Test start
        handler.on_tool_start({"name": "ls"}, ".")
        mock_storage.append_log.assert_called_with("session-123", "Executing tool 'ls' with input: .")

        # Test end
        handler.on_tool_end("file_list.txt")
        mock_storage.append_log.assert_called_with("session-123", "Tool output: file_list.txt")

        # Test end truncated
        long_output = "a" * 1005
        handler.on_tool_end(long_output)
        args, _ = mock_storage.append_log.call_args
        self.assertTrue("truncated" in args[1])
        self.assertTrue(len(args[1]) < 1050)

    @patch('app.workflow.storage')
    def test_workflow_log_update(self, mock_storage):
        from app.workflow import log_update
        state = {"session_id": "session-456", "logs": []}
        log_update(state, "New message")

        # Verify state update
        self.assertIn("New message", state["logs"])

        # Verify storage update
        mock_storage.append_log.assert_called_with("session-456", "New message")

if __name__ == '__main__':
    unittest.main()
