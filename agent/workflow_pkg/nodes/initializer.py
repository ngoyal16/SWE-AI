from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def initializer_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] INITIALIZER: Setting up workspace...")
    sandbox = get_active_sandbox(state["session_id"])

    try:
        # Generate Codebase Tree for context
        if hasattr(sandbox, "generate_codebase_tree"):
            tree = sandbox.generate_codebase_tree(depth=3)
            state["codebase_tree"] = tree
            log_update(state, "Generated codebase tree for context.")
        else:
            # Fallback to simple ls -R if not using DaytonaSandbox with tree support
            state["codebase_tree"] = sandbox.run_command("ls -R")

        state["status"] = "PLANNING"
    except Exception as e:
        log_update(state, f"Initialization failed: {str(e)}")
        state["status"] = "FAILED"

    return state
