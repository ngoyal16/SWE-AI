# SWE Agent

An end-to-end asynchronous coding agent inspired by Open SWE, capable of using any LLM (Gemini, OpenAI, Azure, Ollama). It features a scalable microservices architecture and supports secure deployment on Cloud VMs.

## Documentation

*   [**User Guide**](docs/USER_GUIDE.md): Detailed instructions on installation, configuration, and usage.
*   [**API Reference**](docs/API.md): Full documentation of all API endpoints.

## Tech Stack

*   **Go (v1.25)**: API Service
*   **Python (v3.12+)**: Agent Worker & Workflow Logic (managed by `uv`)
*   **Node (v22+)**: React Frontend (managed by `pnpm`)

## Features

*   **Multi-Model Support**: Dynamic configuration for OpenAI, Google Gemini, Azure, and local Ollama models.
*   **Scalable Architecture**: Decoupled API and Worker services backed by Redis, allowing independent scaling for high throughput.
*   **Advanced Workflow**: Includes a **Plan Critic** step to verify and improve implementation plans before execution.
*   **Git Integration**: Provider-agnostic tools to Clone, Branch, Commit, and Push.
*   **Review Mode**: Optional pause-and-resume workflow to allow humans to review and approve plans before code execution.
*   **Sandboxed Execution**:
    *   **Daytona**: (Default) Remote, secure, and ephemeral development environments.
    *   **Local**: Isolated directory workspaces for simple testing.
*   **Persistent Storage**: Session state and logs are persisted (Redis or File-based) to survive restarts.

## Quick Start (Docker Compose)

1.  **Configure**: Create a `.env` file with your keys (see User Guide for details).
    ```bash
    OPENAI_API_KEY=sk-...
    LLM_PROVIDER=openai
    DAYTONA_API_KEY=...
    ```

2.  **Run**:
    Start the API, Worker, and Redis services.
    ```bash
    docker-compose up --build
    ```

3.  **Interact**:
    Submit a session to the API (exposed on port 8000).
    ```bash
    curl -X POST http://localhost:8000/agent/sessions \
      -H "Content-Type: application/json" \
      -d '{"goal": "Fix bug in login logic", "repo_url": "https://github.com/example/repo.git", "mode": "auto"}'
    ```
