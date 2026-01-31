from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.server import app

# Use FastAPI's TestClient which handles ASGI properly without httpx setup
client = TestClient(app)

@patch("app.agent.queue_manager.enqueue")
def test_create_and_get_session(mock_enqueue):
    response = client.post("/agent/sessions", json={"goal": "Test goal"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]

    mock_enqueue.assert_called()

    response = client.get(f"/agent/sessions/{session_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["id"] == session_id
    assert status_data["status"] == "QUEUED"

    print("API test passed!")

@patch("app.agent.queue_manager.enqueue")
def test_create_session_with_branch(mock_enqueue):
    response = client.post("/agent/sessions", json={"goal": "Test goal", "base_branch": "develop"})
    assert response.status_code == 200

    # Verify enqueue was called with base_branch
    args, kwargs = mock_enqueue.call_args
    # args: (session_id, goal, repo_url, base_branch, mode)
    assert args[1] == "Test goal"
    assert args[3] == "develop"

    print("API with branch test passed!")

@patch("app.agent.queue_manager.enqueue")
@patch("app.storage.storage.get_state")
@patch("app.storage.storage.save_state")
@patch("app.storage.storage.set_session_status")
def test_approve_session(mock_set_status, mock_save_state, mock_get_state, mock_enqueue):
    # Setup state
    session_id = "waiting-session"
    mock_get_state.return_value = {
        "session_id": session_id,
        "status": "WAITING_FOR_USER",
        "mode": "review",
        "goal": "Test",
        "repo_url": "",
        "base_branch": None
    }

    response = client.post(f"/agent/sessions/{session_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "resumed"

    # Verify state update
    mock_save_state.assert_called()
    saved_state = mock_save_state.call_args[0][1]
    assert saved_state["status"] == "CODING"

    # Verify re-enqueue
    mock_enqueue.assert_called()

    print("Approve session test passed!")

if __name__ == "__main__":
    try:
        test_create_and_get_session()
        test_create_session_with_branch()
        test_approve_session()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
