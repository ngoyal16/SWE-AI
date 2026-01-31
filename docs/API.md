# SWE Agent API Reference

The SWE Agent API allows you to submit coding sessions, check their status, and manage their workflow.

## Base URL
`http://localhost:8000` (Default)

---

## Endpoints

### 1. Create Session
Starts a new coding session.

*   **URL**: `/agent/sessions`
*   **Method**: `POST`
*   **Content-Type**: `application/json`

#### Request Body
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `goal` | string | Yes | The natural language description of the coding task. |
| `repo_url` | string | No | URL of the git repository to work on (if not using a pre-configured workspace). |
| `base_branch` | string | No | The branch to checkout before starting work. Defaults to the repo's default branch. |
| `mode` | string | No | The execution mode. Options: `"auto"` (default), `"review"`. |

#### Example Request
```json
{
  "goal": "Fix the memory leak in the parser",
  "repo_url": "https://github.com/org/repo.git",
  "base_branch": "main",
  "mode": "review"
}
```

#### Response (200 OK)
```json
{
  "session_id": "123456789012345678"
}
```

---

### 2. Get Session Status
Retrieves the current status, logs, and result of a session.

*   **URL**: `/agent/sessions/{session_id}`
*   **Method**: `GET`

#### Path Parameters
| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | string | The ID of the session returned by the create endpoint. |

#### Response (200 OK)
```json
{
  "id": "123456789012345678",
  "status": "WAITING_FOR_USER",
  "logs": [
    "Worker picked up session...",
    "PLANNER: Generating plan...",
    "Plan Critic Approved. Waiting for user approval."
  ],
  "result": null
}
```

#### Possible Statuses
*   `QUEUED`: Session is waiting for a worker.
*   `RUNNING`: Session is currently executing.
*   `WAITING_FOR_USER`: Session is paused (Review Mode) awaiting approval.
*   `COMPLETED`: Session finished successfully.
*   `FAILED`: Session failed or timed out.

---

### 3. Approve Session
Resumes a paused session that is in `WAITING_FOR_USER` status.

*   **URL**: `/agent/sessions/{session_id}/approve`
*   **Method**: `POST`

#### Path Parameters
| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | string | The ID of the paused session. |

#### Response (200 OK)
```json
{
  "status": "resumed"
}
```

#### Errors
*   **400 Bad Request**: If the session is not in `WAITING_FOR_USER` status or does not exist.

---

### 4. Add Session Input
Provide additional instructions or feedback to a session.

*   **URL**: `/agent/sessions/{session_id}/input`
*   **Method**: `POST`
*   **Content-Type**: `application/json`

#### Request Body
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `message` | string | Yes | The input message or feedback for the agent. |

#### Response (200 OK)
```json
{
  "status": "input_added"
}
```

#### Behavior
*   **Waiting/Completed Sessions**: Immediately updates the goal and triggers replanning.
*   **Running Sessions (Coding)**: Queues the input. It will be processed after the current coding phase completes.

---

### 5. Health Check
Checks if the API service is running.

*   **URL**: `/health`
*   **Method**: `GET`

#### Response (200 OK)
```json
{
  "status": "ok"
}
```
