from typing import Dict, Any, List, TypedDict, Optional, TYPE_CHECKING
from ..common.storage import storage

if TYPE_CHECKING:
    pass

# Define the state of the workflow
class AgentState(TypedDict):
    session_id: str
    goal: str
    repo_url: Optional[str]
    base_branch: Optional[str]
    workspace_path: str
    plan: Optional[str]
    current_step: int
    review_feedback: Optional[str]
    plan_critic_feedback: Optional[str]
    status: str # "PLANNING", "ENV_SETUP", "PLAN_CRITIC", "CODING", "TESTING", "REVIEWING", "COMMITTING", "COMPLETED", "FAILED", "WAITING_FOR_USER"
    logs: List[str]
    mode: str # "auto", "review"
    commit_message: Optional[str]
    branch_name: Optional[str]
    next_status: Optional[str]
    pending_inputs: List[str]
    codebase_tree: Optional[str]
    git_co_author_name: str
    git_co_author_email: str
    review_count: int
    pr_url: Optional[str]
    agents_md_content: Optional[str]

def log_update(state: AgentState, message: str):
    state["logs"].append(message)
    storage.append_log(state["session_id"], message)
    # Proactively save state to ensure UI is in sync
    storage.save_state(state["session_id"], state)
