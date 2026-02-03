"""
AI Credentials Module

Fetches dynamic AI credentials from the server API based on session context.
The server looks up the session's user and their AI preferences to return appropriate credentials.
"""

import logging
import requests
from dataclasses import dataclass
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class AICredentials:
    """AI credentials for LLM operations."""
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None


def fetch_ai_credentials(session_id: str, worker_token: str) -> Optional[AICredentials]:
    """
    Fetch AI credentials from the server API using session_id and worker_token.

    Args:
        session_id: The session identifier
        worker_token: The worker authentication token

    Returns:
        AICredentials if available, None if retrieval fails

    Raises:
        Exception: If the API call fails
    """
    api_url = settings.API_BASE_URL

    try:
        response = requests.get(
            f"{api_url}/api/v1/internal/sessions/{session_id}/ai-credentials",
            headers={"Authorization": f"Bearer {worker_token}"},
            timeout=30
        )

        if response.status_code == 404:
            logger.warning(f"No AI credentials found for session {session_id}")
            return None

        if response.status_code == 401:
            logger.error(f"Worker token authentication failed for session {session_id} (fetching AI creds)")
            return None

        response.raise_for_status()
        data = response.json()

        return AICredentials(
            provider=data["provider"],
            model=data["model"],
            api_key=data["api_key"],
            base_url=data.get("base_url")
        )

    except requests.Timeout:
        raise Exception(f"Timeout fetching AI credentials for session {session_id}")
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch AI credentials: {e}")
