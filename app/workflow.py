from typing import Dict, Any, List, TypedDict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import Tool

from app.llm import get_llm
from app.tools import create_filesystem_tools
from app.git_tools import create_git_tools

# Define the state of the workflow
class AgentState(TypedDict):
    task_id: str
    goal: str
    repo_url: Optional[str]
    workspace_path: str
    plan: Optional[str]
    current_step: int
    review_feedback: Optional[str]
    plan_critic_feedback: Optional[str]
    status: str # "PLANNING", "PLAN_CRITIC", "CODING", "REVIEWING", "COMPLETED", "FAILED"
    logs: List[str]

def get_active_sandbox(task_id: str):
    # Retrieve the sandbox from the AgentManager (circular import workaround or registry pattern)
    from app.agent import AgentManager
    manager = AgentManager()
    sandbox = manager.get_sandbox(task_id)
    if not sandbox:
        raise ValueError(f"No active sandbox found for task {task_id}")
    return sandbox

# --- PLANNER AGENT ---
def planner_node(state: AgentState) -> AgentState:
    print(f"[{state['task_id']}] PLANNER: Generating plan...")
    llm = get_llm()

    context_str = ""
    if state.get("plan_critic_feedback"):
        context_str += f"\nPrevious Plan Rejected. Critic Feedback: {state['plan_critic_feedback']}\nPlease improve the plan."

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Senior Technical Planner. Your job is to create a detailed, step-by-step plan to accomplish the user's goal in a software repository. The plan should be clear and actionable for a programmer."),
        ("human", f"Goal: {{goal}}\nRepo: {{repo_url}}{context_str}\n\nPlease provide a numbered list of steps to achieve this.")
    ])

    chain = prompt | llm | StrOutputParser()
    plan = chain.invoke({"goal": state["goal"], "repo_url": state["repo_url"]})

    state["plan"] = plan
    state["status"] = "PLAN_CRITIC"
    state["logs"].append(f"Plan generated: {plan}")
    return state

# --- PLAN CRITIC AGENT ---
def plan_critic_node(state: AgentState) -> AgentState:
    print(f"[{state['task_id']}] PLAN CRITIC: Reviewing plan...")
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Technical Plan Critic. Review the proposed plan for safety, completeness, and feasibility. If the plan is good, respond with 'APPROVED'. If not, provide specific, constructive feedback on what steps are missing or dangerous."),
        ("human", f"Goal: {{goal}}\nProposed Plan:\n{{plan}}\n\nReview the plan.")
    ])

    chain = prompt | llm | StrOutputParser()
    feedback = chain.invoke({"goal": state["goal"], "plan": state["plan"]})

    if "APPROVED" in feedback:
        state["status"] = "CODING"
        state["plan_critic_feedback"] = None
        state["logs"].append("Plan Critic Approved.")
    else:
        state["status"] = "PLANNING"
        state["plan_critic_feedback"] = feedback
        state["logs"].append(f"Plan Critic Feedback: {feedback}")

    return state

# --- PROGRAMMER AGENT ---
def programmer_node(state: AgentState) -> AgentState:
    print(f"[{state['task_id']}] PROGRAMMER: Executing plan...")
    llm = get_llm()

    try:
        sandbox = get_active_sandbox(state["task_id"])
        # Initialize tools with specific sandbox
        tools = create_filesystem_tools(sandbox) + create_git_tools(sandbox)

        # Context includes the plan and previous feedback
        context_str = f"Plan:\n{state['plan']}\n"
        if state["review_feedback"]:
            context_str += f"\nReview Feedback (Fix these issues):\n{state['review_feedback']}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Skilled Software Engineer. You have access to tools to modify the file system and run git commands. Follow the plan to implement the requested changes. If there is review feedback, address it."),
            ("human", f"Goal: {{goal}}\nContext:\n{context_str}\n\nExecute the necessary changes. When finished with the current iteration of changes, simply respond with 'CHANGES_COMPLETE'."),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=15)

        result = agent_executor.invoke({"goal": state["goal"]})
        output = result.get("output", "")
        state["logs"].append(f"Programmer output: {output}")
        state["status"] = "REVIEWING"
    except Exception as e:
        state["logs"].append(f"Programmer error: {str(e)}")
        state["status"] = "FAILED"

    return state

# --- REVIEWER AGENT ---
def reviewer_node(state: AgentState) -> AgentState:
    print(f"[{state['task_id']}] REVIEWER: Reviewing changes...")
    llm = get_llm()

    try:
        sandbox = get_active_sandbox(state["task_id"])
        fs_tools = create_filesystem_tools(sandbox)
        tools = [t for t in fs_tools if t.name in ["read_file", "list_files", "run_command"]]

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Code Reviewer. Check the workspace to verify if the goal has been met and the code is correct. Use 'read_file' or 'run_command' (e.g. tests) to verify. If everything looks good, respond with 'APPROVED'. If changes are needed, provide detailed feedback."),
            ("human", "Goal: {goal}\nPlan: {plan}\n\nVerify the changes."),
             ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

        result = agent_executor.invoke({"goal": state["goal"], "plan": state["plan"]})
        output = result.get("output", "")

        if "APPROVED" in output:
            state["status"] = "COMPLETED"
            state["review_feedback"] = None
            state["logs"].append("Reviewer Approved.")
            pass
        else:
            state["status"] = "CODING"
            state["review_feedback"] = output
            state["logs"].append(f"Reviewer requested changes: {output}")

    except Exception as e:
        state["logs"].append(f"Reviewer error: {str(e)}")
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
        state["status"] = "PLANNING"

        # Max steps to prevent infinite loops
        max_steps = 15 # Increased due to extra step
        steps = 0

        while state["status"] not in ["COMPLETED", "FAILED"] and steps < max_steps:
            steps += 1
            current_status = state["status"]

            if current_status == "PLANNING":
                state = planner_node(state)
            elif current_status == "PLAN_CRITIC":
                state = plan_critic_node(state)
            elif current_status == "CODING":
                state = programmer_node(state)
            elif current_status == "REVIEWING":
                state = reviewer_node(state)

        if steps >= max_steps:
            state["status"] = "FAILED"
            state["logs"].append("Max workflow steps reached.")

        return state
