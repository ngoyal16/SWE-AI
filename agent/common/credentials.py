"""
Git Credentials Module

Fetches dynamic Git credentials from the server API based on session context.
The server looks up the session's repository and provider to generate appropriate credentials.
"""

import logging
import requests
from dataclasses import dataclass
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class GitCredentials:
    """Git credentials for repository operations."""
    token: str
    username: str
    author_name: str
    author_email: str
    co_author_name: Optional[str] = None
    co_author_email: Optional[str] = None


def fetch_git_credentials(session_id: str, worker_token: str) -> Optional[GitCredentials]:
    """
    Fetch Git credentials from the server API using session_id and worker_token.
    
    The server looks up the session's repository and provider to generate credentials:
    - For GitHub App: Generates an installation access token
    - For OAuth: Returns the stored user token
    
    Args:
        session_id: The session identifier
        worker_token: The worker authentication token (generated when session was created)
        
    Returns:
        GitCredentials if available, None if no credentials configured
        
    Raises:
        Exception: If the API call fails
    """
    api_url = settings.API_BASE_URL
    
    try:
        response = requests.get(
            f"{api_url}/api/v1/internal/sessions/{session_id}/git-credentials",
            headers={"Authorization": f"Bearer {worker_token}"},
            timeout=30
        )
        
        if response.status_code == 404:
            logger.warning(f"No Git credentials found for session {session_id}")
            return None
        
        if response.status_code == 401:
            logger.error(f"Worker token authentication failed for session {session_id}")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return GitCredentials(
            token=data["token"],
            username=data["username"],
            author_name=data["author_name"],
            author_email=data["author_email"],
            co_author_name=data.get("co_author_name"),
            co_author_email=data.get("co_author_email")
        )
        
    except requests.Timeout:
        raise Exception(f"Timeout fetching Git credentials for session {session_id}")
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch Git credentials: {e}")

