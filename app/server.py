from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agent import AgentManager

app = FastAPI(title="SWE Agent API")
agent_manager = AgentManager()

class TaskRequest(BaseModel):
    goal: str
    repo_url: Optional[str] = ""
    base_branch: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str

@app.post("/agent/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    task_id = agent_manager.start_task(request.goal, request.repo_url, request.base_branch)
    return TaskResponse(task_id=task_id)

@app.get("/agent/tasks/{task_id}")
async def get_task_status(task_id: str):
    status = agent_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@app.get("/health")
async def health_check():
    return {"status": "ok"}
