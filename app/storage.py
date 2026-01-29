import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.config import settings

class Storage:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(settings.WORKSPACE_DIR, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.tasks_file = os.path.join(self.data_dir, "tasks.json")
        self._load()

    def _load(self):
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, "r") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {"tasks": {}, "logs": {}, "results": {}}
        else:
            self.data = {"tasks": {}, "logs": {}, "results": {}}

    def _save(self):
        with open(self.tasks_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def set_task_status(self, task_id: str, status: str):
        self.data["tasks"][task_id] = status
        self._save()

    def get_task_status(self, task_id: str) -> str:
        return self.data["tasks"].get(task_id, "UNKNOWN")

    def append_log(self, task_id: str, message: str):
        if task_id not in self.data["logs"]:
            self.data["logs"][task_id] = []
        self.data["logs"][task_id].append(message)
        self._save()

    def get_logs(self, task_id: str) -> List[str]:
        return self.data["logs"].get(task_id, [])

    def set_result(self, task_id: str, result: str):
        self.data["results"][task_id] = result
        self._save()

    def get_result(self, task_id: str) -> Optional[str]:
        return self.data["results"].get(task_id)

# Global storage instance
storage = Storage()
