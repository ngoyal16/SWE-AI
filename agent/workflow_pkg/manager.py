from langgraph.graph import StateGraph, END, START
from langgraph.errors import GraphRecursionError
from ..common.storage import storage
from .state import AgentState, log_update

# Import nodes
from .nodes.initializer import initializer_node
from .nodes.planner import planner_node
from .nodes.critic import plan_critic_node
from .nodes.branch import branch_naming_node
from .nodes.programmer import programmer_node
from .nodes.reviewer import reviewer_node
from .nodes.commit_msg import commit_msg_node

def router_node(state: AgentState) -> AgentState:
    # Acts as an entry point to route based on existing status
    return state

class WorkflowManager:
    def __init__(self):
        pass

    def build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router", router_node)
        workflow.add_node("initializer", initializer_node)
        workflow.add_node("planner", planner_node)
        workflow.add_node("plan_critic", plan_critic_node)
        workflow.add_node("branch_naming", branch_naming_node)
        workflow.add_node("programmer", programmer_node)
        workflow.add_node("reviewer", reviewer_node)
        workflow.add_node("commit_msg", commit_msg_node)

        workflow.add_edge(START, "router")

        workflow.add_conditional_edges(
            "router",
            lambda state: "INITIALIZING" if state.get("status") == "PLANNING" and not state.get("codebase_tree") else state.get("status", "PLANNING"),
            {
                "INITIALIZING": "initializer",
                "PLANNING": "planner",
                "PLAN_CRITIC": "plan_critic",
                "BRANCH_NAMING": "branch_naming",
                "CODING": "programmer",
                "REVIEWING": "reviewer",
                "COMMITTING": "commit_msg",
                "WAITING_FOR_USER": END,
                "COMPLETED": END,
                "FAILED": END
            }
        )

        workflow.add_edge("initializer", "planner")
        workflow.add_edge("planner", "plan_critic")

        workflow.add_conditional_edges(
            "plan_critic",
            lambda state: "WAITING_FOR_USER" if state.get("status") == "WAITING_FOR_USER" else state.get("status", "PLANNING"),
            {
                "WAITING_FOR_USER": END,
                "BRANCH_NAMING": "branch_naming",
                "PLANNING": "planner",
                "FAILED": END,
                "PLAN_CRITIC": "plan_critic" # Fallback if status doesn't change?
            }
        )

        workflow.add_conditional_edges(
            "branch_naming",
            lambda state: state["status"],
            {
                "CODING": "programmer",
                "FAILED": END
            }
        )

        workflow.add_conditional_edges(
            "programmer",
            lambda state: state["status"],
            {
                "REVIEWING": "reviewer",
                "FAILED": END
            }
        )

        workflow.add_conditional_edges(
            "reviewer",
            lambda state: state["status"],
            {
                "COMMITTING": "commit_msg",
                "CODING": "programmer",
                "FAILED": END
            }
        )

        workflow.add_edge("commit_msg", END)

        return workflow.compile()

    def run_workflow_sync(self, state: AgentState):
        """
        Runs the workflow synchronously. This should be called from a separate thread
        to avoid blocking the main asyncio loop.
        """
        # Initialization is now handled by the 'initializer' node in the graph
        
        # Ensure status is set to PLANNING if not already set (e.g. fresh state)
        if "status" not in state:
            state["status"] = "PLANNING"

        max_steps = 50
        steps = 0

        # Construct graph
        app = self.build_graph()

        while state["status"] not in ["COMPLETED", "FAILED", "WAITING_FOR_USER"] and steps < max_steps:
            # We use a loop here primarily to handle interruptions (pending inputs) which might trigger replanning
            # and to check step limits globally.

            try:
                # app.stream yields state updates. We consume them.
                # We set recursion_limit to (max_steps - steps) + safety to avoid premature error
                # inside a single run if we want global limit.
                # But LangGraph counts nodes.
                # Let's just set a high recursion limit for the graph run, and check global steps manually if possible,
                # or just rely on global steps counter.

                # IMPORTANT: app.stream(state) starts execution from the entry point.
                # The router node will send it to the correct node based on 'state'.

                # Check for pending inputs BEFORE running the graph chunk
                stored_state = storage.get_state(state["session_id"])
                if stored_state and stored_state.get("pending_inputs"):
                    inputs = stored_state["pending_inputs"]
                    if state["status"] != "CODING":
                        log_update(state, f"Received user inputs: {inputs}")
                        new_input_str = "\n\n[User Input]: " + "\n".join(inputs)
                        state["goal"] += new_input_str
                        state["status"] = "PLANNING"

                        # Clear inputs
                        latest_stored_state = storage.get_state(state["session_id"])
                        if latest_stored_state and "pending_inputs" in latest_stored_state:
                             processed_count = len(inputs)
                             current_pending = latest_stored_state["pending_inputs"]
                             if len(current_pending) >= processed_count:
                                 latest_stored_state["pending_inputs"] = current_pending[processed_count:]
                                 storage.save_state(state["session_id"], latest_stored_state)

                        # Continue loop to restart graph with PLANNING
                        continue

                # Run the graph. We iterate over the stream.
                # If we want to check for inputs *during* execution (between nodes), we can do it inside the loop.
                for output in app.stream(state, config={"recursion_limit": max_steps - steps + 2}):
                    # Update local state with result from node
                    for key, value in output.items():
                        # value is the state returned by the node
                        state = value
                        steps += 1
                        # Save state after each node execution to keep UI in sync
                        storage.save_state(state["session_id"], state)

                    # Check for pending inputs between steps
                    stored_state = storage.get_state(state["session_id"])
                    if stored_state and stored_state.get("pending_inputs"):
                         if state["status"] != "CODING":
                             # Interrupt!
                             log_update(state, "Interruption: New user input received.")
                             # Break out of stream loop. The outer while loop will handle input processing at top.
                             break

                    if steps >= max_steps:
                        break

                # After stream ends (either by END or break), check status.
                if state["status"] in ["COMPLETED", "FAILED", "WAITING_FOR_USER"]:
                    break

            except GraphRecursionError:
                state["status"] = "FAILED"
                log_update(state, "Max workflow steps reached (GraphRecursionError).")
                break
            except Exception as e:
                 state["status"] = "FAILED"
                 log_update(state, f"Workflow error: {str(e)}")
                 break

        if steps >= max_steps:
            state["status"] = "FAILED"
            log_update(state, "Max workflow steps reached.")

        return state
