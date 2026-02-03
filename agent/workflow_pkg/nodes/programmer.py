from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent

from ...common.llm import get_llm
from ...tools import create_filesystem_tools, create_git_tools
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def programmer_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] PROGRAMMER: Executing plan...")
    llm = get_llm(state["session_id"])
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
        state["status"] = "TESTING"
    except Exception as e:
        log_update(state, f"Programmer error: {str(e)}")
        state["status"] = "FAILED"

    return state
