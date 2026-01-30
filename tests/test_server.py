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
    # args: (session_id, goal, repo_url, base_branch)
    assert args[1] == "Test goal"
    assert args[3] == "develop"

    print("API with branch test passed!")

if __name__ == "__main__":
    try:
        test_create_and_get_session()
        test_create_session_with_branch()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
