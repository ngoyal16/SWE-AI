# SWE Agent

An end-to-end asynchronous coding agent inspired by Open SWE, capable of using Gemini-3.5 or Ops-4.5. It supports deployment on Cloud VMs or Kubernetes.

## Architecture

The agent follows a multi-stage "Open SWE" workflow:
1.  **Manager**: Routes the request.
2.  **Planner**: Generates a step-by-step plan based on the goal and repository.
3.  **Programmer**: Executes the plan using file system and git tools.
4.  **Reviewer**: Reviews the changes. If approved, the workflow completes (and theoretically pushes). If rejected, it loops back to the Programmer.

## Features

*   **Multi-Model Support**: Gemini-3.5 (via Google GenAI) and Ops-4.5 (via OpenAI).
*   **Git Integration**: Clone, Branch, Commit, Push to any Git provider.
*   **Asynchronous**: Tasks run in the background with status polling.
*   **Containerized**: Ready for Docker and Kubernetes.

## Setup

### 1. Environment Variables

Create a `.env` file or set environment variables:

```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
MODEL_NAME=gemini-3.5 # or ops-4.5
GIT_USERNAME=your-username
GIT_EMAIL=your-email@example.com
GIT_TOKEN=your-git-token # For HTTPS push
```

### 2. Local Run

```bash
pip install -r requirements.txt
uvicorn app.server:app --reload
```

### 3. Usage

Start a task:

```bash
curl -X POST http://localhost:8000/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{"goal": "Fix bug in login page", "repo_url": "https://github.com/user/repo.git"}'
```

Check status:

```bash
curl http://localhost:8000/agent/tasks/{task_id}
```

## Deployment

### Docker

```bash
docker build -t swe-agent .
docker run -p 8000:8000 --env-file .env swe-agent
```

### Kubernetes

1.  Update `k8s/deployment.yaml` with your image name.
2.  Create secrets for API keys.
3.  Apply:
    ```bash
    kubectl apply -f k8s/deployment.yaml
    ```
