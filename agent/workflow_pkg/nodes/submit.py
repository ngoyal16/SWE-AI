import requests
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ...common.llm import get_llm
from ...common.config import settings
from ...tools.git_tools import commit_changes, push_changes
from ...callbacks import SessionCallbackHandler
from ...agent import AgentManager
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

logger = logging.getLogger(__name__)

def submit_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] SUBMIT: Generating commit message and submitting...")

    # --- Commit Logic ---
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]
    sandbox = get_active_sandbox(state["session_id"])

    # Stage all changes
    sandbox.run_command("git add .")

    # Get diff of staged changes
    diff = sandbox.run_command("git diff --cached")

    # Truncate diff if too long
    if len(diff) > 10000:
        diff = diff[:10000] + "\n... (diff truncated)"

    if not diff.strip():
        # No changes to commit.
        # However, we might still want to check if we need to push or create PR for existing commits?
        # The previous commit_msg_node logic stopped here.
        # But if we want to ensure PR creation for previously committed code (e.g. if previous run failed at PR step),
        # we might want to continue.
        # But checking if there are unpushed commits is complex without git logic.
        # For now, let's assume if no diff, we might be done or we might just skip to PR.
        # Let's check if there are unpushed commits?
        # "git log @{u}.." checks for commits ahead of upstream.
        # But we might not have upstream set correctly in sandbox or it might be complex.
        # Consolidating strict logic: If no changes staged, log it.
        log_update(state, "No changes detected to commit.")
        # We continue to PR creation anyway, in case there are local commits from previous steps that weren't pushed?
        # Or should we return? commit_msg_node returned COMPLETED.
        # If I return COMPLETED here, I might miss creating a PR if the commit happened but PR failed previously.
        # But the prompt says "it will generate the git commit ... once that is done. it will create a pull request".
        # If I don't commit, I might still want to PR.
        # Let's try to proceed to push/PR logic even if diff is empty.
        pass
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Commit Message Generator.

### GIT & NAMING CONVENTIONS
You are a strict adherent to Conventional Commits and Git Flow. You must follow these rules for every git operation:

Generate a Git commit message based on the provided diff.
Follow these strict rules:
1. Format: `type(scope): description`
2. Allowed Types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `test`.
3. The subject description must be lowercase and present tense ("add" not "added").
4. The subject line must be concise (under 50 chars).
5. You MUST include a detailed body describing the changes, separated from the subject line by a blank line.
6. The body should explain *what* changed and *why*, using bullet points if necessary.
"""),
            ("human", "Goal: {goal}\nDiff:\n{diff}\n\nGenerate the commit message.")
        ])

        chain = prompt | llm | StrOutputParser()
        message = chain.invoke({"goal": state["goal"], "diff": diff}, config={"callbacks": callbacks})

        # Clean up message
        message = message.strip().strip('"').strip("'").strip("`").strip()

        log_update(state, f"Generated commit message: {message}")
        state["commit_message"] = message

        # Commit changes
        result = commit_changes(sandbox, message)
        log_update(state, f"Commit result: {result}")

        if "Error" in result:
            state["status"] = "FAILED"
            return state

    # --- Push Logic ---
    branch_name = state.get("branch_name")
    if branch_name:
        # Push changes (even if we didn't just commit, maybe there were previous commits)
        push_res = push_changes(sandbox, state.get("base_branch"), branch=branch_name)
        log_update(state, f"Push result: {push_res}")
        if "Error" in push_res:
             state["status"] = "FAILED"
             # If push fails, we probably can't create PR effectively (or it won't show changes)
             return state
    else:
         log_update(state, "Warning: Branch name missing in state. Cannot push.")
         state["status"] = "COMPLETED"
         return state

    # --- PR Creation Logic ---
    log_update(state, "Starting PR creation process...")
    session_id = state["session_id"]
    agent_manager = AgentManager()
    worker_token = agent_manager.get_worker_token(session_id)

    if not worker_token:
        log_update(state, "Error: Worker token not found. Cannot create PR.")
        state["status"] = "COMPLETED"
        return state

    # Prepare input
    # Use commit message for title/body if available, else goal
    commit_msg = state.get("commit_message", "")
    if not commit_msg:
        # Check if we can get the last commit message if state doesn't have it?
        # For now, fallback to goal.
        log_update(state, "Warning: No commit message found in state. Using goal as title.")
        title = state["goal"][:50]
        body = state["goal"]
    else:
        parts = commit_msg.split("\n", 1)
        title = parts[0]
        body = parts[1].strip() if len(parts) > 1 else ""

    head = branch_name # We checked this exists above
    base = state.get("base_branch") or "main"

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
             log_update(state, f"PR Creation Failed ({response.status_code}): {response.text}")

    except Exception as e:
        log_update(state, f"PR Creation Error: {str(e)}")

    state["status"] = "COMPLETED"
    return state
