"""
Human Help Tool - Request user clarification or assistance.

Pauses workflow execution until user responds.
"""
from langchain_core.tools import StructuredTool
from typing import Dict, Any


def create_request_human_help_tool(state: Dict[str, Any]) -> StructuredTool:
    """
    Creates a tool that allows the agent to request help from the user.
    
    Args:
        state: The AgentState dictionary (will be mutated to store help request)
    """
    
    def request_human_help(help_request: str) -> str:
        """
        Request help from the user. This will pause execution until the user responds.
        
        Args:
            help_request: A clear description of what help is needed. Include:
                - What you're trying to accomplish
                - What you've already tried
                - Specific questions or information you need
        
        Returns:
            Confirmation that the request was registered.
        """
        # Store the help request in state
        state["pending_help_request"] = help_request
        state["status"] = "WAITING_FOR_USER"
        
        return (
            f"Help request registered. Execution will pause until user responds.\n\n"
            f"Request: {help_request[:200]}{'...' if len(help_request) > 200 else ''}"
        )
    
    return StructuredTool.from_function(
        func=request_human_help,
        name="request_human_help",
        description=(
            "Use this to request help from the user when you're stuck. This pauses execution "
            "until the user responds. Only use when you genuinely need information or clarification "
            "that you cannot find in the codebase. The user does NOT have access to modify files - "
            "they can only provide guidance, context, or answer questions."
        )
    )


def create_session_plan_tool(state: Dict[str, Any]) -> StructuredTool:
    """Creates a tool for generating structured session plans."""
    
    def session_plan(title: str, plan: List[str]) -> str:
        """
        Generate a structured plan for the session.
        
        Args:
            title: Short, one-sentence description of the plan's goal.
            plan: List of steps to accomplish the goal.
        
        Returns:
            Formatted plan confirmation.
        """
        from typing import List
        
        state["session_plan_title"] = title
        state["session_plan_steps"] = plan if isinstance(plan, list) else [plan]
        
        formatted_steps = "\n".join(f"{i+1}. {step}" for i, step in enumerate(state["session_plan_steps"]))
        return f"## Plan: {title}\n\n{formatted_steps}"
    
    return StructuredTool.from_function(
        func=session_plan,
        name="session_plan",
        description=(
            "Create a structured plan for the session. Use this when starting work to "
            "organize your approach into clear, numbered steps."
        )
    )


def create_update_plan_tool(state: Dict[str, Any]) -> StructuredTool:
    """Creates a tool for updating the current plan."""
    
    def update_plan(update_plan_reasoning: str) -> str:
        """
        Update the current plan based on new information or findings.
        
        Args:
            update_plan_reasoning: Explanation of why the plan needs updating and what changes to make.
        
        Returns:
            Confirmation of the update request.
        """
        state["plan_update_reasoning"] = update_plan_reasoning
        state["plan_needs_update"] = True
        
        return f"Plan update queued. Reasoning recorded for next planning phase."
    
    return StructuredTool.from_function(
        func=update_plan,
        name="update_plan",
        description=(
            "Request an update to the current plan. Use this when you discover that the plan "
            "needs changes - such as adding steps, removing unnecessary steps, or reordering. "
            "Do NOT use this to mark steps as complete."
        )
    )


def create_mark_task_completed_tool(state: Dict[str, Any]) -> StructuredTool:
    """Creates a tool for marking tasks as completed."""
    
    def mark_task_completed(completed_task_summary: str) -> str:
        """
        Mark the current task as completed with a summary.
        
        Args:
            completed_task_summary: Detailed summary of actions taken, insights learned,
                and any relevant context for reviewers.
        
        Returns:
            Confirmation of task completion.
        """
        if "completed_tasks" not in state:
            state["completed_tasks"] = []
        
        state["completed_tasks"].append({
            "summary": completed_task_summary,
            "step": state.get("current_step", 0)
        })
        
        return f"Task marked as completed.\n\nSummary: {completed_task_summary[:300]}..."
    
    return StructuredTool.from_function(
        func=mark_task_completed,
        name="mark_task_completed",
        description=(
            "Mark the current task as completed and provide a summary. Include specifics "
            "about actions taken, insights learned, and context useful for reviewers."
        )
    )
