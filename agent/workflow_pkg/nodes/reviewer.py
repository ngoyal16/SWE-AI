from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent

from ...common.llm import get_llm
from ...tools import create_filesystem_tools
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def reviewer_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] REVIEWER: Reviewing changes...")
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]

    try:
        sandbox = get_active_sandbox(state["session_id"])
        fs_tools = create_filesystem_tools(sandbox)
        tools = [t for t in fs_tools if t.name in ["read_file", "list_files", "run_command"]]

        review_count = state.get("review_count", 0)
        
        system_prompt = (
            "You are a pragmatic Code Reviewer. Check the workspace to verify if the core goal has been met and the code is functionally correct. "
            "Use 'read_file' or 'run_command' (e.g. tests) to verify.\n"
            "- **Focus:** Core logic, correctness, security, and potential regressions.\n"
            "- **Ignore:** Formatting, style preferences, or comments, unless they cause build failures.\n"
            "If the core requirements are satisfied, respond with 'APPROVED'."
        )
        
        if review_count >= 2:
            system_prompt += " This is a subsequent review. Be even more lenient. Prioritize functional correctness over everything else. Do NOT request changes unless the code is broken."

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Goal: {goal}\nPlan: {plan}\n\nVerify the changes. If good, say APPROVED. Otherwise, list critical changes needed."),
             ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

        result = agent_executor.invoke({"goal": state["goal"], "plan": state["plan"]}, config={"callbacks": callbacks})
        output = result.get("output", "")

        if "APPROVED" in output:
            state["status"] = "SUBMITTING"
            state["review_feedback"] = None
            log_update(state, "Reviewer Approved. Proceeding to submission.")
        else:
            state["review_count"] = review_count + 1
            if state["review_count"] >= 4:
                log_update(state, f"Max review attempts reached. Forced approval of functional changes: {output}")
                state["status"] = "SUBMITTING"
                state["review_feedback"] = None
            else:
                state["status"] = "CODING"
                state["review_feedback"] = output
                log_update(state, f"Reviewer requested changes (Attempt {state['review_count']}): {output}")

    except Exception as e:
        log_update(state, f"Reviewer error: {str(e)}")
        state["status"] = "FAILED"

    return state
