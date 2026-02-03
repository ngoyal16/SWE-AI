from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ...common.llm import get_llm
from ...tools.git_tools import create_branch, checkout_branch
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def branch_naming_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] BRANCH_NAMING: Generating branch name...")
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]

    # Check if branch name already exists
    if state.get("branch_name"):
        log_update(state, f"Branch name already exists: {state['branch_name']}. Skipping generation.")
        # Make sure it's checked out
        sandbox = get_active_sandbox(state["session_id"])

        # Try to checkout first
        res = checkout_branch(sandbox, state["branch_name"])
        if "error" in res.lower() or "fatal" in res.lower() or "did not match any file" in res.lower():
             # If checkout fails (e.g. branch deleted or clean sandbox), try creating it
             log_update(state, f"Branch checkout failed ({res}). Creating branch...")
             res = create_branch(sandbox, state["branch_name"])

        log_update(state, f"Branch checkout/creation result: {res}")

        if "error" in res.lower() or "fatal" in res.lower():
             state["status"] = "FAILED"
             return state

        state["status"] = "CODING"
        return state

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Git Branch Name Generator.

### GIT & NAMING CONVENTIONS
You are a strict adherent to Conventional Commits and Git Flow.

Generate a branch name based on the user's goal and plan.
Rules:
1. Format: `type/short-description-kebab-case`
2. Allowed Types: `feature`, `bugfix`, `hotfix`, `chore`, `docs`.
3. NEVER use colons (:) or uppercase.
4. Do NOT include any quotes or backticks.
5. Do NOT include the session ID. It will be added automatically.
"""),
        ("human", "Goal: {goal}\nPlan: {plan}\n\nGenerate the branch name.")
    ])

    chain = prompt | llm | StrOutputParser()
    branch_name = chain.invoke({
        "goal": state["goal"],
        "plan": state["plan"]
    }, config={"callbacks": callbacks})

    # Strict stripping
    branch_name = branch_name.strip().strip("'").strip('"').strip("`").strip()

    # Enforce session_id suffix
    session_suffix = f"-{state['session_id']}"
    if not branch_name.endswith(session_suffix):
        branch_name = f"{branch_name}{session_suffix}"

    state["branch_name"] = branch_name
    log_update(state, f"Generated branch name: {branch_name}")

    sandbox = get_active_sandbox(state["session_id"])
    res = create_branch(sandbox, branch_name)
    log_update(state, f"Branch creation result: {res}")

    if "ERROR" in res: # Validation error
        # Fallback or retry? For now, fail.
        state["status"] = "FAILED"
        log_update(state, f"Branch creation failed: {res}")
        return state

    state["status"] = "CODING"
    return state
