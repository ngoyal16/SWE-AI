# SWE Agent

An end-to-end asynchronous coding agent inspired by Open SWE, capable of using any LLM (Gemini, OpenAI, Azure, Ollama). It features a scalable microservices architecture and supports secure deployment on Cloud VMs or Kubernetes.

## Documentation

*   [**User Guide**](docs/USER_GUIDE.md): Detailed instructions on installation, configuration, and usage.

## Features

*   **Multi-Model Support**: Dynamic configuration for OpenAI, Google Gemini, Azure, and local Ollama models.
*   **Scalable Architecture**: Decoupled API and Worker services backed by Redis, allowing independent scaling for high throughput.
*   **Advanced Workflow**: Includes a **Plan Critic** step to verify and improve implementation plans before execution.
*   **Git Integration**: Provider-agnostic tools to Clone, Branch, Commit, and Push.
*   **Sandboxed Execution**:
    *   **Local**: Isolated directory workspaces.
    *   **Kubernetes**: Ephemeral Pods with support for **MicroVMs** (Kata Containers, gVisor) for hardware-level isolation.
*   **Persistent Storage**: Task state and logs are persisted (Redis or File-based) to survive restarts.

## Quick Start (Docker Compose)

1.  **Configure**: Create a `.env` file with your keys (see User Guide for details).
    ```bash
    OPENAI_API_KEY=sk-...
    LLM_PROVIDER=openai
    ```

2.  **Run**:
    Start the API, Worker, and Redis services.
    ```bash
    docker-compose up --build
    ```

3.  **Interact**:
    Submit a task to the API (exposed on port 8000).
    ```bash
    curl -X POST http://localhost:8000/agent/tasks \
      -H "Content-Type: application/json" \
      -d '{"goal": "Fix bug in login logic", "repo_url": "https://github.com/example/repo.git"}'
    ```
