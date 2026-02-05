from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent

from ...common.llm import get_llm
from ...tools import create_filesystem_tools, create_navigation_tools
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def tester_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] TESTER: Running tests...")
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]

    try:
        sandbox = get_active_sandbox(state["session_id"])
        # Tester needs filesystem tools to read config and run commands
        fs_tools = create_filesystem_tools(sandbox)
        nav_tools = create_navigation_tools(sandbox)

        # We explicitly need run_command and navigation tools
        tools = [t for t in fs_tools if t.name in ["read_file", "list_files", "run_command"]] + nav_tools

        system_prompt = (
            "You are a QA Automation Engineer. Your goal is to ensure the codebase passes all tests and meets the plan requirements. "
            "1. Identify the project type (e.g. Python, Node, Go) by looking at files (package.json, pyproject.toml, etc). "
            "2. Determine the command to run tests (e.g. 'npm test', 'pytest', 'go test ./...'). "
            "3. Run the tests using 'run_command'. "
            "4. Analyze the output. "
            "   - If tests PASS: Respond with 'TESTS_PASSED'. "
            "   - If tests FAIL: Read any error logs mentioned in the output. Respond with 'TESTS_FAILED' followed by a detailed summary of the errors.\n\n"
            "### GOAL ADHERENCE & EXIT CRITERIA\n"
            "Sometimes there are no formal tests, or the goal is just to create a file.\n"
            "- **No Tests Found:** If no test suite exists, create a temporary script (e.g., `verify_change.py`) to verify the specific changes work as expected. Run it, then delete it.\n"
            "- **Verification:** If the goal was to create a file/feature, and you verify it exists and functions correctly, treat that as a PASS.\n"
            "- **Existing Files:** If the file already exists, this is usually a SUCCESS, not a failure. Do NOT ask the programmer to 'create it' again.\n"
            "- If the plan is complete, respond 'TESTS_PASSED'."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Goal: {goal}\nPlan: {plan}\n\nRun the tests and report the result."),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

        result = agent_executor.invoke({"goal": state["goal"], "plan": state["plan"]}, config={"callbacks": callbacks})
        output = result.get("output", "")

        if "TESTS_PASSED" in output:
            log_update(state, "Tester: Tests passed. Proceeding to review.")
            state["status"] = "REVIEWING"
            # Clear feedback if we had any
            # state["review_feedback"] = None # Optional: keep history? Better to clear for reviewer.
        else:
            log_update(state, f"Tester: Tests failed. Sending back to programmer. Output: {output}")
            state["status"] = "CODING"
            state["review_feedback"] = f"Test Failure: {output}"

    except Exception as e:
        log_update(state, f"Tester error: {str(e)}")
        state["status"] = "FAILED"

    return state
