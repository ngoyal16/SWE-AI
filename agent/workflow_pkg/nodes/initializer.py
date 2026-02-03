from ..state import AgentState, log_update
from ..utils import get_active_sandbox

def initializer_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] INITIALIZER: Setting up workspace...")
    sandbox = get_active_sandbox(state["session_id"])

    try:
        # Generate Codebase Tree for context
        if hasattr(sandbox, "generate_codebase_tree"):
            # Check for monorepo or large structure
            root_list = sandbox.run_command("ls -F")

            is_monorepo = False
            monorepo_indicators = ["apps/", "packages/", "services/", "modules/"]
            if any(indicator in root_list for indicator in monorepo_indicators):
                is_monorepo = True

            # Adaptive depth
            if is_monorepo:
                # Shallower depth for monorepos to avoid context explosion
                tree = sandbox.generate_codebase_tree(depth=2)
                tree += "\n\n[Note]: This appears to be a Monorepo. The tree is truncated to depth 2. Use `list_files` to explore subdirectories."
                log_update(state, "Detected Monorepo structure. Generated truncated codebase tree.")
            else:
                tree = sandbox.generate_codebase_tree(depth=3)
                log_update(state, "Generated codebase tree for context.")

            state["codebase_tree"] = tree
        else:
            # Fallback to simple ls -F for non-Daytona sandboxes to avoid massive output
            state["codebase_tree"] = sandbox.run_command("ls -F")

        state["status"] = "PLANNING"
    except Exception as e:
        log_update(state, f"Initialization failed: {str(e)}")
        state["status"] = "FAILED"

    return state
