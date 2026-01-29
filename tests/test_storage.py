import os
import shutil
import unittest
from app.storage import Storage
from app.config import settings

class TestStorage(unittest.TestCase):

    def setUp(self):
        # Clean up storage
        self.data_dir = os.path.join(settings.WORKSPACE_DIR, "test_data")
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        self.storage = Storage(data_dir=self.data_dir)

    def test_task_status_persistence(self):
        task_id = "task-1"
        self.storage.set_task_status(task_id, "RUNNING")

        # Reload storage
        new_storage = Storage(data_dir=self.data_dir)
        status = new_storage.get_task_status(task_id)
        self.assertEqual(status, "RUNNING")

    def test_logs_persistence(self):
        task_id = "task-2"
        self.storage.append_log(task_id, "Log 1")
        self.storage.append_log(task_id, "Log 2")

        # Reload storage
        new_storage = Storage(data_dir=self.data_dir)
        logs = new_storage.get_logs(task_id)
        self.assertEqual(len(logs), 2)
        self.assertIn("Log 1", logs)
        self.assertIn("Log 2", logs)

    def tearDown(self):
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

if __name__ == "__main__":
    unittest.main()
