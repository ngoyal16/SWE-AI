from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agent import AgentManager

app = FastAPI(title="SWE Agent API")
agent_manager = AgentManager()

class SessionRequest(BaseModel):
    goal: str
    repo_url: Optional[str] = ""
    base_branch: Optional[str] = None
    mode: Optional[str] = "auto" # "auto" or "review"

class SessionResponse(BaseModel):
    session_id: str

@app.post("/agent/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    session_id = agent_manager.start_session(request.goal, request.repo_url, request.base_branch, request.mode)
    return SessionResponse(session_id=session_id)

@app.post("/agent/sessions/{session_id}/approve")
async def approve_session(session_id: str):
    success = agent_manager.resume_session(session_id)
    if not success:
         raise HTTPException(status_code=400, detail="Session cannot be resumed (it might not be in waiting state or does not exist)")
    return {"status": "resumed"}

@app.get("/agent/sessions/{session_id}")
async def get_session_status(session_id: str):
    status = agent_manager.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status

@app.get("/health")
async def health_check():
    return {"status": "ok"}
