import os
import json
import redis
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from app.config import settings

class BaseStorage(ABC):
    @abstractmethod
    def set_session_status(self, session_id: str, status: str): pass
    @abstractmethod
    def get_session_status(self, session_id: str) -> str: pass
    @abstractmethod
    def append_log(self, session_id: str, message: str): pass
    @abstractmethod
    def get_logs(self, session_id: str) -> List[str]: pass
    @abstractmethod
    def set_result(self, session_id: str, result: str): pass
    @abstractmethod
    def get_result(self, session_id: str) -> Optional[str]: pass
    @abstractmethod
    def save_state(self, session_id: str, state: Dict[str, Any]): pass
    @abstractmethod
    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]: pass

class FileStorage(BaseStorage):
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(settings.WORKSPACE_DIR, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.sessions_file = os.path.join(self.data_dir, "sessions.json")
        self._load()

    def _load(self):
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, "r") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {"sessions": {}, "logs": {}, "results": {}, "states": {}}
        else:
            self.data = {"sessions": {}, "logs": {}, "results": {}, "states": {}}

    def _save(self):
        with open(self.sessions_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def set_session_status(self, session_id: str, status: str):
        self._load() # Reload to reduce race conditions (still poor for concurrency)
        self.data["sessions"][session_id] = status
        self._save()

    def get_session_status(self, session_id: str) -> str:
        self._load()
        return self.data["sessions"].get(session_id, "UNKNOWN")

    def append_log(self, session_id: str, message: str):
        self._load()
        if session_id not in self.data["logs"]:
            self.data["logs"][session_id] = []
        self.data["logs"][session_id].append(message)
        self._save()

    def get_logs(self, session_id: str) -> List[str]:
        self._load()
        return self.data["logs"].get(session_id, [])

    def set_result(self, session_id: str, result: str):
        self._load()
        self.data["results"][session_id] = result
        self._save()

    def get_result(self, session_id: str) -> Optional[str]:
        self._load()
        return self.data["results"].get(session_id)

    def save_state(self, session_id: str, state: Dict[str, Any]):
        self._load()
        self.data["states"][session_id] = state
        self._save()

    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        self._load()
        return self.data["states"].get(session_id)

class RedisStorage(BaseStorage):
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.ttl = 86400 * 7 # 7 days

    def set_session_status(self, session_id: str, status: str):
        self.redis.set(f"session:{session_id}:status", status, ex=self.ttl)

    def get_session_status(self, session_id: str) -> str:
        status = self.redis.get(f"session:{session_id}:status")
        return status.decode('utf-8') if status else "UNKNOWN"

    def append_log(self, session_id: str, message: str):
        self.redis.rpush(f"session:{session_id}:logs", message)
        self.redis.expire(f"session:{session_id}:logs", self.ttl)

    def get_logs(self, session_id: str) -> List[str]:
        logs = self.redis.lrange(f"session:{session_id}:logs", 0, -1)
        return [log.decode('utf-8') for log in logs]

    def set_result(self, session_id: str, result: str):
        self.redis.set(f"session:{session_id}:result", result, ex=self.ttl)

    def get_result(self, session_id: str) -> Optional[str]:
        res = self.redis.get(f"session:{session_id}:result")
        return res.decode('utf-8') if res else None

    def save_state(self, session_id: str, state: Dict[str, Any]):
        self.redis.set(f"session:{session_id}:state", json.dumps(state), ex=self.ttl)

    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        state = self.redis.get(f"session:{session_id}:state")
        return json.loads(state) if state else None

# Factory
def get_storage():
    if hasattr(settings, "STORAGE_TYPE") and settings.STORAGE_TYPE == "redis":
        return RedisStorage()
    return FileStorage()

storage = get_storage()
