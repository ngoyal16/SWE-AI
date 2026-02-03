from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ...common.llm import get_llm
from ...tools.git_tools import commit_changes, push_changes
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def commit_msg_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] COMMIT_MSG: Generating commit message...")
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]

    sandbox = get_active_sandbox(state["session_id"])

    # Stage all changes to ensure untracked files are included in the diff
    sandbox.run_command("git add .")

    # Get diff of staged changes
    # We use --cached because we just staged everything
    diff = sandbox.run_command("git diff --cached")

    # Truncate diff if too long to avoid context window issues
    if len(diff) > 10000:
        diff = diff[:10000] + "\n... (diff truncated)"

    if not diff.strip():
        log_update(state, "No changes detected to commit.")
        state["status"] = "COMPLETED"
        return state

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

    # Clean up message (remove quotes/backticks if any)
    message = message.strip().strip('"').strip("'").strip("`").strip()

    # Note: Co-authored-by trailer is added by commit_changes() function in git_tools.py
    # using the git_credentials from the sandbox

    log_update(state, f"Generated commit message: {message}")
    state["commit_message"] = message

    # Commit changes
    result = commit_changes(sandbox, message)
    log_update(state, f"Commit result: {result}")

    if "Error" in result:
        state["status"] = "FAILED"
    else:
        # Push changes
        # We need to know the branch name. It should be in state.
        branch_name = state.get("branch_name")
        if branch_name:
            push_res = push_changes(sandbox, state.get("base_branch"), branch=branch_name)
            log_update(state, f"Push result: {push_res}")
            if "Error" in push_res:
                 state["status"] = "FAILED" # Or maybe partially completed?
            else:
                 state["status"] = "PR_CREATION"
        else:
             log_update(state, "Warning: Branch name missing in state. Cannot push.")
             state["status"] = "COMPLETED"

    return state
