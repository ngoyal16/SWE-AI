import requests
import logging
from ..state import AgentState, log_update
from ...agent import AgentManager
from ...common.config import settings

logger = logging.getLogger(__name__)

def pr_creation_node(state: AgentState) -> AgentState:
    log_update(state, "Starting PR creation process...")

    session_id = state["session_id"]
    agent_manager = AgentManager()
    worker_token = agent_manager.get_worker_token(session_id)

    if not worker_token:
        log_update(state, "Error: Worker token not found. Cannot create PR.")
        state["status"] = "COMPLETED"
        return state

    # Prepare input
    # Use commit message for title/body
    commit_msg = state.get("commit_message", "")
    if not commit_msg:
        log_update(state, "Warning: No commit message found. Using goal as title.")
        title = state["goal"][:50]
        body = state["goal"]
    else:
        # Split title and body
        parts = commit_msg.split("\n", 1)
        title = parts[0]
        body = parts[1].strip() if len(parts) > 1 else ""

    head = state.get("branch_name")
    if not head:
         log_update(state, "Error: Branch name not found in state.")
         state["status"] = "COMPLETED"
         return state

    base = state.get("base_branch") or "main" # Fallback to main if not specified, though backend might handle defaults too

    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }

    api_url = f"{settings.API_BASE_URL}/api/v1/internal/sessions/{session_id}/pr"

    try:
        log_update(state, f"Sending PR creation request to {api_url}...")
        response = requests.post(
            api_url,
            json=payload,
            headers={"Authorization": f"Bearer {worker_token}"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            pr_url = data.get("url")
            status = data.get("status")
            state["pr_url"] = pr_url

            if status == "existed":
                log_update(state, f"Pull Request already exists: {pr_url}")
            else:
                log_update(state, f"Successfully created Pull Request: {pr_url}")

        else:
             # Soft failure
             log_update(state, f"PR Creation Failed ({response.status_code}): {response.text}")

    except Exception as e:
        log_update(state, f"PR Creation Error: {str(e)}")

    # Always complete successfully even if PR creation failed, as code is already pushed
    state["status"] = "COMPLETED"
    return state
