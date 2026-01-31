from typing import Dict, Any, List, TypedDict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import Tool

from app.llm import get_llm
from app.tools import create_filesystem_tools
from app.git_tools import create_git_tools, init_workspace, commit_changes, create_branch, push_changes, checkout_branch
from app.storage import storage
from app.callbacks import SessionCallbackHandler

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
    status: str # "PLANNING", "PLAN_CRITIC", "CODING", "REVIEWING", "COMMITTING", "COMPLETED", "FAILED", "WAITING_FOR_USER"
    logs: List[str]
    mode: str # "auto", "review"
    commit_message: Optional[str]
    branch_name: Optional[str]
    next_status: Optional[str]
    pending_inputs: List[str]

def log_update(state: AgentState, message: str):
    state["logs"].append(message)
    storage.append_log(state["session_id"], message)

def get_active_sandbox(session_id: str):
    # Retrieve the sandbox from the AgentManager (circular import workaround or registry pattern)
    from app.agent import AgentManager
    manager = AgentManager()
    sandbox = manager.get_sandbox(session_id)
    if not sandbox:
        raise ValueError(f"No active sandbox found for session {session_id}")
    return sandbox

# --- PLANNER AGENT ---
def planner_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] PLANNER: Generating plan...")
    llm = get_llm()
    callbacks = [SessionCallbackHandler(state["session_id"])]

    sandbox = get_active_sandbox(state["session_id"])
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Technical Planner. Your job is to create a detailed, step-by-step plan to accomplish the user's goal in a software repository. The plan should be clear and actionable for a programmer.

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
        "context": context_str
    }, config={"callbacks": callbacks})

    state["plan"] = plan
    state["status"] = "PLAN_CRITIC"
    log_update(state, f"Plan generated: {plan}")
    return state

# --- PLAN CRITIC AGENT ---
def plan_critic_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] PLAN CRITIC: Reviewing plan...")
    llm = get_llm()
    callbacks = [SessionCallbackHandler(state["session_id"])]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Technical Plan Critic. Review the proposed plan for safety, completeness, and feasibility. If the plan is good, respond with 'APPROVED'. If not, provide specific, constructive feedback on what steps are missing or dangerous."),
        ("human", "Goal: {goal}\nProposed Plan:\n{plan}\n\nReview the plan.")
    ])

    chain = prompt | llm | StrOutputParser()
    feedback = chain.invoke({"goal": state["goal"], "plan": state["plan"]}, config={"callbacks": callbacks})

    if "APPROVED" in feedback:
        if state.get("mode") == "review":
            state["status"] = "WAITING_FOR_USER"
            state["next_status"] = "BRANCH_NAMING"
            log_update(state, "Plan Critic Approved. Waiting for user approval before generating branch.")
        else:
            state["status"] = "BRANCH_NAMING"
        state["plan_critic_feedback"] = None
        log_update(state, "Plan Critic Approved.")
    else:
        state["status"] = "PLANNING"
        state["plan_critic_feedback"] = feedback
        log_update(state, f"Plan Critic Feedback: {feedback}")

    return state

# --- BRANCH NAMING AGENT ---
def branch_naming_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] BRANCH_NAMING: Generating branch name...")
    llm = get_llm()
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
You are a strict adherent to Conventional Commits and Git Flow. You must follow these rules for every git operation:

Generate a branch name based on the user's goal and plan.
Rules:
1. Format: `type/short-description-kebab-case-{session_id}`
2. Allowed Types: `feature`, `bugfix`, `hotfix`, `chore`, `docs`.
3. NEVER use colons (:) or uppercase.
4. Append `-{session_id}` to the end.
"""),
        ("human", "Goal: {goal}\nPlan: {plan}\nSession ID: {session_id}\n\nGenerate the branch name.")
    ])

    chain = prompt | llm | StrOutputParser()
    branch_name = chain.invoke({
        "goal": state["goal"],
        "plan": state["plan"],
        "session_id": state["session_id"]
    }, config={"callbacks": callbacks})

    branch_name = branch_name.strip().strip("'").strip('"')

    # Enforce session_id suffix
    if not branch_name.endswith(f"-{state['session_id']}"):
        branch_name = f"{branch_name}-{state['session_id']}"

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

# --- PROGRAMMER AGENT ---
def programmer_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] PROGRAMMER: Executing plan...")
    llm = get_llm()
    callbacks = [SessionCallbackHandler(state["session_id"])]

    try:
        sandbox = get_active_sandbox(state["session_id"])
        # Initialize tools with specific sandbox
        base_branch = state.get("base_branch")
        all_git_tools = create_git_tools(sandbox, base_branch)
        # Filter out commit and push tools to prevent premature commits
        allowed_git_tools = [t for t in all_git_tools if t.name not in ["commit_changes", "push_changes"]]
        tools = create_filesystem_tools(sandbox) + allowed_git_tools

        # Context includes the plan and previous feedback
        context_str = f"Plan:\n{state['plan']}\n"
        if state["review_feedback"]:
            context_str += f"\nReview Feedback (Fix these issues):\n{state['review_feedback']}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Skilled Software Engineer. You have access to tools to modify the file system and run git commands. Follow the plan to implement the requested changes. Do not commit changes. Just modify the files. If there is review feedback, address it."),
            ("human", "Goal: {goal}\nContext:\n{context}\n\nExecute the necessary changes. When finished with the current iteration of changes, simply respond with 'CHANGES_COMPLETE'."),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=15)

        result = agent_executor.invoke({"goal": state["goal"], "context": context_str}, config={"callbacks": callbacks})
        output = result.get("output", "")
        log_update(state, f"Programmer output: {output}")
        state["status"] = "REVIEWING"
    except Exception as e:
        log_update(state, f"Programmer error: {str(e)}")
        state["status"] = "FAILED"

    return state

# --- COMMIT MSG AGENT ---
def commit_msg_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] COMMIT_MSG: Generating commit message...")
    llm = get_llm()
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
3. The description must be lowercase and present tense ("add" not "added").
4. Keep it concise.
"""),
        ("human", "Goal: {goal}\nDiff:\n{diff}\n\nGenerate the commit message.")
    ])

    chain = prompt | llm | StrOutputParser()
    message = chain.invoke({"goal": state["goal"], "diff": diff}, config={"callbacks": callbacks})

    # Clean up message (remove quotes if any)
    message = message.strip().strip('"').strip("'")

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
                 state["status"] = "COMPLETED"
        else:
             log_update(state, "Warning: Branch name missing in state. Cannot push.")
             state["status"] = "COMPLETED"

    return state

# --- REVIEWER AGENT ---
def reviewer_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] REVIEWER: Reviewing changes...")
    llm = get_llm()
    callbacks = [SessionCallbackHandler(state["session_id"])]

    try:
        sandbox = get_active_sandbox(state["session_id"])
        fs_tools = create_filesystem_tools(sandbox)
        tools = [t for t in fs_tools if t.name in ["read_file", "list_files", "run_command"]]

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Code Reviewer. Check the workspace to verify if the goal has been met and the code is correct. Use 'read_file' or 'run_command' (e.g. tests) to verify. If everything looks good, respond with 'APPROVED'. If changes are needed, provide detailed feedback."),
            ("human", "Goal: {goal}\nPlan: {plan}\n\nVerify the changes."),
             ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

        result = agent_executor.invoke({"goal": state["goal"], "plan": state["plan"]}, config={"callbacks": callbacks})
        output = result.get("output", "")

        if "APPROVED" in output:
            state["status"] = "COMMITTING"
            state["review_feedback"] = None
            log_update(state, "Reviewer Approved. Proceeding to commit generation.")
            pass
        else:
            state["status"] = "CODING"
            state["review_feedback"] = output
            log_update(state, f"Reviewer requested changes: {output}")

    except Exception as e:
        log_update(state, f"Reviewer error: {str(e)}")
        state["status"] = "FAILED"

    return state

# --- MANAGER / ORCHESTRATOR ---
class WorkflowManager:
    def __init__(self):
        pass

    def run_workflow_sync(self, state: AgentState):
        """
        Runs the workflow synchronously. This should be called from a separate thread
        to avoid blocking the main asyncio loop.
        """
        # Initialize workspace before starting the agent loop
        if state.get("status", "PLANNING") == "PLANNING":
             # Only initialize if just starting
             try:
                sandbox = get_active_sandbox(state["session_id"])
                if state["repo_url"]:
                    log_update(state, f"Initializing workspace for repo: {state['repo_url']}...")
                    init_output = init_workspace(sandbox, state["repo_url"], state["base_branch"])
                    log_update(state, f"Workspace initialization result:\n{init_output}")
             except Exception as e:
                log_update(state, f"Failed to initialize workspace: {str(e)}")
                state["status"] = "FAILED"
                return state

        # Ensure status is set to PLANNING if not already set (e.g. fresh state)
        if "status" not in state:
            state["status"] = "PLANNING"

        # Max steps to prevent infinite loops
        max_steps = 50 # Increased to handle complex tasks
        steps = 0

        while state["status"] not in ["COMPLETED", "FAILED"] and steps < max_steps:
            steps += 1

            # Check for pending inputs from storage
            # We must reload state from storage to check for updates from API
            stored_state = storage.get_state(state["session_id"])
            if stored_state and stored_state.get("pending_inputs"):
                inputs = stored_state["pending_inputs"]
                # Only interrupt if NOT in CODING phase (as per user request)
                # If we are in CODING phase, we wait until it completes (transitions to REVIEWING)
                if state["status"] != "CODING":
                    log_update(state, f"Received user inputs: {inputs}")
                    new_input_str = "\n\n[User Input]: " + "\n".join(inputs)
                    state["goal"] += new_input_str
                    state["status"] = "PLANNING"

                    # Clear pending inputs safely (re-read to minimize race condition)
                    # We remove the inputs we just processed
                    latest_stored_state = storage.get_state(state["session_id"])
                    if latest_stored_state and "pending_inputs" in latest_stored_state:
                         # Remove the exact number of items we processed from the front
                         processed_count = len(inputs)
                         current_pending = latest_stored_state["pending_inputs"]
                         if len(current_pending) >= processed_count:
                             latest_stored_state["pending_inputs"] = current_pending[processed_count:]
                             storage.save_state(state["session_id"], latest_stored_state)

            current_status = state["status"]

            if current_status == "PLANNING":
                state = planner_node(state)
            elif current_status == "PLAN_CRITIC":
                state = plan_critic_node(state)
            elif current_status == "BRANCH_NAMING":
                state = branch_naming_node(state)
            elif current_status == "CODING":
                state = programmer_node(state)
            elif current_status == "REVIEWING":
                state = reviewer_node(state)
            elif current_status == "COMMITTING":
                state = commit_msg_node(state)
            elif current_status == "WAITING_FOR_USER":
                log_update(state, "Pausing workflow for user approval.")
                # State persistence is handled by the worker upon return
                return state

        if steps >= max_steps:
            state["status"] = "FAILED"
            log_update(state, "Max workflow steps reached.")

        return state
