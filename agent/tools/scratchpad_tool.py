"""
Scratchpad Tool - Store technical notes across workflow steps.

Allows the agent to save observations and findings for later use.
"""
from langchain_core.tools import StructuredTool
from typing import List, Dict, Any


def create_scratchpad_tool(state: Dict[str, Any]) -> StructuredTool:
    """
    Creates a scratchpad tool that saves notes to the workflow state.
    
    Args:
        state: The AgentState dictionary (will be mutated to store notes)
    """
    
    def scratchpad(notes: List[str]) -> str:
        """
        Save technical notes to the scratchpad for future reference.
        
        Args:
            notes: List of notes to save. Each note should be concise but useful.
        
        Returns:
            Confirmation message with number of notes saved.
        """
        if "scratchpad_notes" not in state:
            state["scratchpad_notes"] = []
        
        # Add new notes
        state["scratchpad_notes"].extend(notes)
        
        total = len(state["scratchpad_notes"])
        return f"Saved {len(notes)} note(s) to scratchpad. Total notes: {total}"
    
    return StructuredTool.from_function(
        func=scratchpad,
        name="scratchpad",
        description=(
            "Write technical notes to your scratchpad. Use this to record observations, "
            "findings, code patterns, or any information you want to remember for later steps. "
            "Notes are accumulated throughout the session."
        )
    )


def get_scratchpad_notes(state: Dict[str, Any]) -> List[str]:
    """Retrieve all scratchpad notes from state."""
    return state.get("scratchpad_notes", [])


def format_scratchpad_context(state: Dict[str, Any]) -> str:
    """Format scratchpad notes as context for prompts."""
    notes = get_scratchpad_notes(state)
    if not notes:
        return ""
    
    formatted = "\n".join(f"- {note}" for note in notes)
    return f"\n## Technical Notes (from scratchpad):\n{formatted}\n"
