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
        task_id = "task-1"
        self.file_storage.set_task_status(task_id, "RUNNING")
        self.assertEqual(self.file_storage.get_task_status(task_id), "RUNNING")

        self.file_storage.append_log(task_id, "Log 1")
        logs = self.file_storage.get_logs(task_id)
        self.assertIn("Log 1", logs)

    @patch("app.storage.redis.from_url")
    def test_redis_storage(self, mock_from_url):
        mock_redis = MagicMock()
        mock_from_url.return_value = mock_redis

        # Mock get/set behavior slightly or just verify calls
        mock_redis.get.return_value = b"RUNNING"
        mock_redis.lrange.return_value = [b"Log 1"]

        redis_storage = RedisStorage()
        redis_storage.set_task_status("task-1", "RUNNING")

        mock_redis.set.assert_called()

        status = redis_storage.get_task_status("task-1")
        self.assertEqual(status, "RUNNING")

        logs = redis_storage.get_logs("task-1")
        self.assertEqual(logs, ["Log 1"])

    def tearDown(self):
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

if __name__ == "__main__":
    unittest.main()
