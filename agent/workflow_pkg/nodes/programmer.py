from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent

from ...common.llm import get_llm
from ...tools import create_filesystem_tools, create_git_tools, create_editor_tools, create_grep_tool
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

        # Enhanced toolset
        filesystem_tools = create_filesystem_tools(sandbox)
        editor_tools = create_editor_tools(sandbox)
        grep_tools = [create_grep_tool(sandbox)]

        tools = filesystem_tools + editor_tools + grep_tools + allowed_git_tools

        # Context includes the plan and previous feedback
        context_str = f"Plan:\n{state['plan']}\n"
        if state["review_feedback"]:
            context_str += f"\nReview Feedback (Fix these issues):\n{state['review_feedback']}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Skilled Software Engineer. You have access to tools to modify the file system and run git commands. "
                "Follow the plan to implement the requested changes. Do not commit changes. Just modify the files. "
                "If there is review feedback, address it.\n\n"
                "### EXPLORATION & MODIFICATION STRATEGY (The Funnel)\n"
                "When locating code in a large repository (10k+ files), use this structured approach:\n"
                "1. **Search (Compass):** Use `grep_search` to find unique keywords, error messages, or function names. Narrow down the results.\n"
                "2. **Trace (Path):** Follow imports and usages to understand the flow and dependencies. Don't just guess; verify.\n"
                "3. **Read (Magnifying Glass):** Use `view_file` to read the specific files identified in steps 1 & 2. ALWAYS read a file before modifying it.\n"
                "4. **Edit:** Use `replace_in_file` to update the code using the EXACT content found in step 3.\n\n"
                "### SCOPE CONTROL & LOOP PREVENTION\n"
                "- Only implement what is requested in the current plan step. Do NOT autonomously expand the scope (e.g. solving the *next* problem).\n"
                "- If the Tester says the file already exists, VERIFY it. If it is correct, respond 'CHANGES_COMPLETE'. Do NOT modify it just to do something.\n"
                "- Stop and report completion if the goal is met."
            )),
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
