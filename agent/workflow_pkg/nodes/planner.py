from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ...common.llm import get_llm
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def planner_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] PLANNER: Generating plan...")
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]

    sandbox = get_active_sandbox(state["session_id"])
    
    # Use codebase tree if available, otherwise fallback to list_files
    files = state.get("codebase_tree")
    if not files:
        try:
            files = sandbox.list_files(".")
        except Exception as e:
            files = f"Error listing files: {str(e)}"

    context_str = ""
    if state.get("plan_critic_feedback"):
        context_str += f"\nPrevious Plan Rejected. Critic Feedback: {state['plan_critic_feedback']}\nPlease improve the plan."

    # If replanning (pending inputs or critic feedback), include the previous plan
    if state.get("plan"):
        context_str += f"\n\nExisting Plan:\n{state['plan']}\n\nINSTRUCTION: The goal has been updated or feedback received. Refine the Existing Plan to accommodate the new requirements. Do not lose progress if possible, but modify steps as needed."

    agents_md = state.get("agents_md_content")
    agents_md_context = ""
    if agents_md:
        agents_md_context = f"\n\n### REPOSITORY SPECIFIC INSTRUCTIONS (AGENTS.MD)\nYou MUST obey the following instructions found in AGENTS.md:\n{agents_md}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Technical Planner. Your job is to create a detailed, step-by-step plan to accomplish the user's goal in a software repository. The plan should be clear and actionable for a programmer.
{agents_md_context}
### CONTEXT & EXPLORATION
The codebase context provided below is a high-level overview. If the repository is large or a monorepo, the file tree might be truncated.
If you need to verify file locations or explore subdirectories (e.g. `packages/`, `apps/`) to understand the structure better, explicitly include a step in your plan to "Explore [path] using list_files".

### GIT & NAMING CONVENTIONS
You are a strict adherent to Conventional Commits and Git Flow. You must follow these rules for every git operation:

The repository is already cloned and checked out to the base branch.

IMPORTANT:
- The `Base Branch` provided is ONLY for checking out the starting state.
- You must NEVER commit directly to the Base Branch or Default Branch.
- You must ALWAYS create a new feature branch from the Base Branch before making any changes.
- Do NOT include steps for committing or pushing changes. This will be handled automatically.
- Do NOT include steps for creating the feature branch. The system will generate and create the branch automatically.
"""),
        ("human", "Goal: {goal}\nRepo: {repo_url}\nBase Branch: {base_branch}\nSession ID: {session_id}\nFiles:\n{files}\nContext: {context}\n\nPlease provide a numbered list of steps to achieve this.")
    ])

    chain = prompt | llm | StrOutputParser()
    plan = chain.invoke({
        "goal": state["goal"],
        "repo_url": state["repo_url"],
        "base_branch": state.get("base_branch") or "Default",
        "session_id": state["session_id"],
        "files": files,
        "context": context_str,
        "agents_md_context": agents_md_context
    }, config={"callbacks": callbacks})

    state["plan"] = plan
    state["status"] = "PLAN_CRITIC"
    log_update(state, f"Plan generated: {plan}")
    return state
