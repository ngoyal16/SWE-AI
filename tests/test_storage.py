import os
import shutil
import unittest
from unittest.mock import MagicMock, patch
from app.storage import FileStorage, RedisStorage
from app.config import settings

class TestStorage(unittest.TestCase):

    def setUp(self):
        # Clean up storage
        self.data_dir = os.path.join(settings.WORKSPACE_DIR, "test_data")
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        self.file_storage = FileStorage(data_dir=self.data_dir)

    def test_file_storage(self):
        session_id = "session-1"
        self.file_storage.set_session_status(session_id, "RUNNING")
        self.assertEqual(self.file_storage.get_session_status(session_id), "RUNNING")

        self.file_storage.append_log(session_id, "Log 1")
        logs = self.file_storage.get_logs(session_id)
        self.assertIn("Log 1", logs)

        # Test State Persistence
        state = {"status": "WAITING", "plan": "Do something"}
        self.file_storage.save_state(session_id, state)
        loaded_state = self.file_storage.get_state(session_id)
        self.assertEqual(loaded_state, state)

    @patch("app.storage.redis.from_url")
    def test_redis_storage(self, mock_from_url):
        mock_redis = MagicMock()
        mock_from_url.return_value = mock_redis

        # Mock get/set behavior slightly or just verify calls
        mock_redis.get.side_effect = [b"RUNNING", b'{"status": "WAITING"}']
        mock_redis.lrange.return_value = [b"Log 1"]

        redis_storage = RedisStorage()
        redis_storage.set_session_status("session-1", "RUNNING")

        mock_redis.set.assert_called()

        status = redis_storage.get_session_status("session-1")
        self.assertEqual(status, "RUNNING")

        logs = redis_storage.get_logs("session-1")
        self.assertEqual(logs, ["Log 1"])

        # Test State Persistence
        state = {"status": "WAITING"}
        redis_storage.save_state("session-1", state)
        # Verify set called with json string
        # We need to check the call args but since we have multiple calls, let's just check retrieval
        loaded_state = redis_storage.get_state("session-1")
        self.assertEqual(loaded_state, state)

    def tearDown(self):
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

if __name__ == "__main__":
    unittest.main()
