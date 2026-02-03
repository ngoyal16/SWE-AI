from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent

from ...common.llm import get_llm
from ...tools import create_filesystem_tools
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def env_setup_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] ENV_SETUP: Setting up environment...")
    llm = get_llm(state["session_id"])
    callbacks = [SessionCallbackHandler(state["session_id"])]

    try:
        sandbox = get_active_sandbox(state["session_id"])
        fs_tools = create_filesystem_tools(sandbox)
        # We need read_file to check for config files, and run_command to install
        tools = [t for t in fs_tools if t.name in ["read_file", "list_files", "run_command"]]

        system_prompt = (
            "You are a DevOps Engineer. Your goal is to prepare the development environment by installing dependencies. "
            "1. Scan the repository for configuration files (e.g. package.json, requirements.txt, pyproject.toml, go.mod, Cargo.toml). "
            "2. Based on the files found, run the appropriate installation command (e.g. 'npm install', 'pip install -r requirements.txt', 'go mod download'). "
            "3. If multiple types are found, handle them. "
            "4. If no dependencies are found or installation fails, just report it. "
            "5. Respond with 'SETUP_COMPLETE' when done."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Repo Context: {codebase_tree}\n\nPlease install dependencies."),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

        # We pass codebase_tree to give it a hint of the file structure immediately
        context = state.get("codebase_tree", "")
        result = agent_executor.invoke({"codebase_tree": context}, config={"callbacks": callbacks})
        output = result.get("output", "")

        log_update(state, f"Env Setup Output: {output}")
        state["status"] = "PLANNING"

    except Exception as e:
        log_update(state, f"Env Setup error: {str(e)}")
        # Proceed to planning anyway, don't block
        state["status"] = "PLANNING"

    return state
