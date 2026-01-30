import redis
import json
from typing import Optional
from app.config import settings

class QueueManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.queue_name = "swe_agent_tasks"

    def enqueue(self, session_id: str, goal: str, repo_url: str, base_branch: Optional[str] = None):
        payload = {
            "session_id": session_id,
            "goal": goal,
            "repo_url": repo_url,
            "base_branch": base_branch
        }
        self.redis.rpush(self.queue_name, json.dumps(payload))

    def dequeue(self):
        # Blocking pop
        item = self.redis.blpop(self.queue_name, timeout=5)
        if item:
            return json.loads(item[1])
        return None

queue_manager = QueueManager()
