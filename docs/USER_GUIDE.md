# SWE Agent User Guide

This guide provides detailed instructions on how to install, configure, and use the SWE Agent. The agent is designed to run autonomously to solve coding sessions using advanced LLMs (Gemini-3.5 or Ops-4.5) in a secure, sandboxed environment.

## Table of Contents
1.  [Prerequisites](#prerequisites)
2.  [Installation](#installation)
3.  [Configuration](#configuration)
4.  [AI Setup](#ai-setup)
5.  [Deployment](#deployment)
    *   [Local Docker Mode](#local-docker-mode)
    *   [Daytona Mode](#daytona-mode)
6.  [Usage](#usage)
7.  [Architecture & Sandbox Details](#architecture--sandbox-details)

---

## Prerequisites

*   **Docker**: Required for containerization.
*   **Daytona**: Required for `daytona` sandbox mode.
*   **Python 3.12+**: If running from source.
*   **AI API Keys**: You will need keys for your preferred providers (OpenAI, Google, Azure, etc.) to configure them in the UI.

---

## Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-org/swe-agent.git
    cd swe-agent
    ```

2.  **Install Dependencies (Local Run)**
    ```bash
    pip install -r requirements.txt
    ```

---

## Configuration

The agent's infrastructure is configured via environment variables. Create a `.env` file in the root directory:

```bash
# Infrastructure Configuration
REDIS_URL=redis://localhost:6379/0

# Sandbox Configuration
# 'local': Runs in ./workspace/{session_id}
# 'daytona': Runs in a remote Daytona environment
SANDBOX_TYPE=daytona

# Daytona Configuration (Only if SANDBOX_TYPE=daytona)
DAYTONA_API_KEY=your-daytona-api-key
DAYTONA_SERVER_URL=https://api.daytona.io # Optional
DAYTONA_TARGET_IMAGE=ubuntu:22.04 # Image for the sandbox environment
```

---

## AI Setup

The agent uses dynamic, session-based AI credentials. You do **not** configure LLM keys in the `.env` file.

1.  Start the application (see [Deployment](#deployment)).
2.  Navigate to the UI (default: `http://localhost:8000`).
3.  Go to **Settings > AI Profiles**.
4.  Create a new AI Profile:
    *   **Name**: A descriptive name (e.g., "My GPT-4").
    *   **Provider**: Select OpenAI, Gemini, Azure, or Ollama.
    *   **Model**: The model identifier (e.g., `gpt-4-turbo`, `gemini-1.5-pro`).
    *   **API Key**: Enter your secret key.
5.  (Optional) Set a profile as **Default** or assign specific profiles to your user account.

---

## Deployment

### Local Docker Mode

This runs the agent in a single container. If `SANDBOX_TYPE=local`, sessions run in isolated directories inside this container.

1.  **Build the Image**
    ```bash
    docker build -t swe-agent .
    ```

2.  **Run the Container**
    ```bash
    docker run -p 8000:8000 --env-file .env swe-agent
    ```

### Daytona Mode

This mode uses Daytona for strong isolation. The Agent orchestrates sessions, but code execution happens in remote Daytona sandboxes.

1.  **Ensure Daytona is Configured**
    Make sure your `DAYTONA_API_KEY` is set in the environment.

2.  **Run the Agent**
    Start the agent normally (e.g., via Docker or locally). When `SANDBOX_TYPE=daytona`, it will automatically create and manage Daytona environments for each session.

---

## Usage

Once running (port 8000), you can interact via the HTTP API.

### 1. Start a New Session

**Endpoint**: `POST /agent/sessions`

You can start a session in **Auto** (default) or **Review** mode.

#### Auto Mode
The agent plans and executes the entire session autonomously.

```bash
curl -X POST http://localhost:8000/agent/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Refactor the login function in auth.py to use async/await",
    "repo_url": "https://github.com/example/my-repo.git",
    "mode": "auto"
  }'
```

#### Review Mode
The agent creates a plan and then pauses execution (Status: `WAITING_FOR_USER`). You can review the plan in the logs and then approve it to continue.

```bash
curl -X POST http://localhost:8000/agent/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Critical security fix",
    "repo_url": "https://github.com/example/my-repo.git",
    "mode": "review"
  }'
```

**Response**:
```json
{"session_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### 2. Approve a Session (Review Mode)

If a session is in `WAITING_FOR_USER` status, use this endpoint to approve the plan and resume execution.

**Endpoint**: `POST /agent/sessions/{session_id}/approve`

```bash
curl -X POST http://localhost:8000/agent/sessions/550e8400-e29b-41d4-a716-446655440000/approve
```

### 3. Check Session Status

**Endpoint**: `GET /agent/sessions/{session_id}`

```bash
curl http://localhost:8000/agent/sessions/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING", # QUEUED, RUNNING, COMPLETED, FAILED
  "logs": [
    "Starting session...",
    "Cloning repo...",
    "PLANNER: Generating plan...",
    "PROGRAMMER: Executing plan..."
  ],
  "result": null
}
```

### 4. Interact with a Session (Provide Feedback)

You can send additional instructions or feedback to a session at any time.

**Endpoint**: `POST /agent/sessions/{session_id}/input`

```bash
curl -X POST http://localhost:8000/agent/sessions/550e8400-e29b-41d4-a716-446655440000/input \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please also update the README with the new changes."
  }'
```

**Behavior**:
*   **If Waiting/Completed**: The agent updates its goal and immediately starts replanning.
*   **If Coding**: The agent queues your input. Once the current coding iteration is complete, it will pause, incorporate your feedback into the goal, and replan before reviewing.

---

## Architecture & Sandbox Details

The agent uses a **Workflow Manager** pattern:
1.  **Manager**: Receives the request.
2.  **Planner**: Analyzes the repo and creates a plan.
3.  **Programmer**: Writes code and runs tests.
4.  **Reviewer**: Validates changes.

### Multi-Session Support
The agent is fully asynchronous. API requests return immediately, and the workflow runs in a background thread. You can submit multiple sessions simultaneously.

### Daytona Sandbox
When `SANDBOX_TYPE=daytona`, the agent uses the Daytona platform to create secure, ephemeral development environments. All file operations and command executions happen remotely via the Daytona API/SDK.
*   **Isolation**: Runs in isolated Daytona environments.
*   **Security**: Leveraging Daytona's secure infrastructure.
