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
            "0. **AGENTS.MD INSTRUCTIONS:** Prioritize any setup instructions found in AGENTS.md below.\n"
            "1. **Analyze Configs:** Scan for config files (package.json, requirements.txt, pyproject.toml, go.mod, Cargo.toml).\n"
            "2. **Lock File Detection:** Check for lock files to determine the package manager:\n"
            "   - `pnpm-lock.yaml` -> use `pnpm install`\n"
            "   - `yarn.lock` -> use `yarn install`\n"
            "   - `package-lock.json` -> use `npm install`\n"
            "   - `bun.lockb` -> use `bun install`\n"
            "3. **Monorepos:** If `apps/` or `packages/` exist, check if the root has a workspace config. If not, install dependencies in subdirectories.\n"
            "4. **Install:** Run the appropriate install commands. If tools are missing (e.g., `go`, `cargo`), try installing them via `sudo apt-get`.\n"
            "5. **Diagnose Failures:** If installation fails, READ the error log. Do not just retry blindly.\n"
            "6. Respond with 'SETUP_COMPLETE' when done."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Repo Context: {codebase_tree}\n\nAGENTS.MD Instructions: {agents_md_content}\n\nPlease install dependencies."),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

        # We pass codebase_tree to give it a hint of the file structure immediately
        context = state.get("codebase_tree", "")
        agents_md = state.get("agents_md_content", "None")
        result = agent_executor.invoke({"codebase_tree": context, "agents_md_content": agents_md}, config={"callbacks": callbacks})
        output = result.get("output", "")

        log_update(state, f"Env Setup Output: {output}")
        state["status"] = "PLANNING"

    except Exception as e:
        log_update(state, f"Env Setup error: {str(e)}")
        # Proceed to planning anyway, don't block
        state["status"] = "PLANNING"

    return state
