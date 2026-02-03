def get_active_sandbox(session_id: str):
    # Retrieve the sandbox from the AgentManager (circular import workaround or registry pattern)
    from agent.agent import AgentManager
    manager = AgentManager()
    sandbox = manager.get_sandbox(session_id)
    if not sandbox:
        raise ValueError(f"No active sandbox found for session {session_id}")
    return sandbox
