# SWE Agent

An end-to-end asynchronous coding agent inspired by Open SWE, capable of using Gemini-3.5 or Ops-4.5. It supports deployment on Cloud VMs or Kubernetes with secure sandboxing.

## Documentation

*   [**User Guide**](docs/USER_GUIDE.md): Detailed instructions on installation, configuration, and usage.

## Features

*   **Multi-Model Support**: Gemini-3.5 (via Google GenAI) and Ops-4.5 (via OpenAI).
*   **Git Integration**: Clone, Branch, Commit, Push to any Git provider.
*   **Asynchronous & Multi-Session**: Non-blocking architecture supports concurrent tasks.
*   **Sandboxed Execution**:
    *   **Local**: Isolated directory workspaces.
    *   **Kubernetes**: Ephemeral Pods (can be mapped to MicroVMs like Kata Containers).

## Quick Start (Docker)

1.  **Configure**: Create `.env` (see User Guide).
2.  **Run**:
    ```bash
    docker build -t swe-agent .
    docker run -p 8000:8000 --env-file .env swe-agent
    ```
3.  **Interact**:
    ```bash
    curl -X POST http://localhost:8000/agent/tasks -d '{"goal": "Fix bug", "repo_url": "..."}'
    ```
