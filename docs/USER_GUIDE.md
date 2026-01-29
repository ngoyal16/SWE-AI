# SWE Agent User Guide

This guide provides detailed instructions on how to install, configure, and use the SWE Agent. The agent is designed to run autonomously to solve coding tasks using advanced LLMs (Gemini-3.5 or Ops-4.5) in a secure, sandboxed environment.

## Table of Contents
1.  [Prerequisites](#prerequisites)
2.  [Installation](#installation)
3.  [Configuration](#configuration)
4.  [Deployment](#deployment)
    *   [Local Docker Mode](#local-docker-mode)
    *   [Kubernetes Mode](#kubernetes-mode)
5.  [Usage](#usage)
6.  [Architecture & Sandbox Details](#architecture--sandbox-details)

---

## Prerequisites

*   **Docker**: Required for containerization.
*   **Kubernetes Cluster** (Optional): For `k8s` sandbox mode. You can use Minikube, Kind, or a managed cloud provider (GKE, EKS, AKS).
*   **Python 3.12+**: If running from source.
*   **API Keys**:
    *   OpenAI API Key (if using `ops-4.5` / GPT-4).
    *   Google Gemini API Key (if using `gemini-3.5`).

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

The agent is configured via environment variables. Create a `.env` file in the root directory:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_API_KEY=AIza-your-google-key
MODEL_NAME=ops-4.5 # Options: ops-4.5 (GPT-4), gemini-3.5 (Gemini Pro 1.5)

# Git Configuration (for the agent to commit/push)
GIT_USERNAME=swe-agent-bot
GIT_EMAIL=bot@example.com
GIT_TOKEN=github_pat_... # Personal Access Token for HTTPS auth

# Sandbox Configuration
# 'local': Runs in ./workspace/{task_id}
# 'k8s': Spawns a dedicated Pod for each task
SANDBOX_TYPE=local
# K8s Settings (Only if SANDBOX_TYPE=k8s)
K8S_NAMESPACE=default
WORKER_IMAGE=python:3.12-slim # The image used for the worker pods
```

---

## Deployment

### Local Docker Mode

This runs the agent in a single container. If `SANDBOX_TYPE=local`, tasks run in isolated directories inside this container.

1.  **Build the Image**
    ```bash
    docker build -t swe-agent .
    ```

2.  **Run the Container**
    ```bash
    docker run -p 8000:8000 --env-file .env swe-agent
    ```

### Kubernetes Mode

This mode provides strong isolation. The Agent itself runs as a Service, and it spawns *new* Pods for every task.

1.  **Build Images**
    You need two images: the Agent image and the Worker image.
    ```bash
    # Build Agent
    docker build -t your-registry/swe-agent:latest .

    # Push to your registry (so K8s can pull it)
    docker push your-registry/swe-agent:latest
    ```
    *Note: For the worker, you can use a standard python image (e.g., `python:3.12-slim`) or build a custom one with pre-installed build tools.*

2.  **Create Secrets**
    ```bash
    kubectl create secret generic swe-agent-secrets \
      --from-literal=openai-api-key=$OPENAI_API_KEY \
      --from-literal=google-api-key=$GOOGLE_API_KEY \
      --from-literal=git-token=$GIT_TOKEN
    ```

3.  **Deploy the Agent**
    Edit `k8s/deployment.yaml` to set your image and sandbox config:
    ```yaml
        env:
        - name: SANDBOX_TYPE
          value: "k8s"
        - name: WORKER_IMAGE
          value: "python:3.12-slim" # Or your custom worker image
    ```

    Apply the deployment:
    ```bash
    kubectl apply -f k8s/deployment.yaml
    ```

4.  **RBAC Permissions**
    The Agent needs permission to create/delete Pods. Create a `Role` and `RoleBinding` if not already present (default ServiceAccount might need upgrades depending on cluster setup).

    *Example RBAC (rbac.yaml):*
    ```yaml
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: swe-agent-manager
      namespace: default
    rules:
    - apiGroups: [""]
      resources: ["pods", "pods/exec", "pods/log"]
      verbs: ["create", "get", "list", "watch", "delete"]
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: swe-agent-manager-binding
      namespace: default
    subjects:
    - kind: ServiceAccount
      name: default # Or specific SA
      namespace: default
    roleRef:
      kind: Role
      name: swe-agent-manager
      apiGroup: rbac.authorization.k8s.io
    ```
    `kubectl apply -f rbac.yaml`

---

## Usage

Once running (port 8000), you can interact via the HTTP API.

### 1. Start a New Task

**Endpoint**: `POST /agent/tasks`

```bash
curl -X POST http://localhost:8000/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Refactor the login function in auth.py to use async/await",
    "repo_url": "https://github.com/example/my-repo.git"
  }'
```

**Response**:
```json
{"task_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### 2. Check Task Status

**Endpoint**: `GET /agent/tasks/{task_id}`

```bash
curl http://localhost:8000/agent/tasks/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING", # QUEUED, RUNNING, COMPLETED, FAILED
  "logs": [
    "Starting task...",
    "Cloning repo...",
    "PLANNER: Generating plan...",
    "PROGRAMMER: Executing plan..."
  ],
  "result": null
}
```

---

## Architecture & Sandbox Details

The agent uses a **Workflow Manager** pattern:
1.  **Manager**: Receives the request.
2.  **Planner**: Analyzes the repo and creates a plan.
3.  **Programmer**: Writes code and runs tests.
4.  **Reviewer**: Validates changes.

### Multi-Session Support
The agent is fully asynchronous. API requests return immediately, and the workflow runs in a background thread. You can submit multiple tasks simultaneously.

### K8s Sandbox (MicroVMs)
When `SANDBOX_TYPE=k8s`, the agent creates a dedicated Pod for the task. All file operations and git commands are executed inside this Pod via `kubectl exec` equivalents.
*   **Isolation**: File system is ephemeral (`emptyDir`).
*   **Security**: The Agent only has access to the Pod it created.
*   **MicroVMs**: To use MicroVMs (like Firecracker/Kata), configure your Kubernetes cluster with a RuntimeClass (e.g., `kata`) and update the `K8sSandbox` code or Pod spec to request that runtime.
