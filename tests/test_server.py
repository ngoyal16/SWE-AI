from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.server import app

# Use FastAPI's TestClient which handles ASGI properly without httpx setup
client = TestClient(app)

@patch("app.agent.queue_manager.enqueue")
def test_create_and_get_task(mock_enqueue):
    response = client.post("/agent/tasks", json={"goal": "Test goal"})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    mock_enqueue.assert_called()

    response = client.get(f"/agent/tasks/{task_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["id"] == task_id
    assert status_data["status"] == "QUEUED"

    print("API test passed!")

@patch("app.agent.queue_manager.enqueue")
def test_create_task_with_branch(mock_enqueue):
    response = client.post("/agent/tasks", json={"goal": "Test goal", "base_branch": "develop"})
    assert response.status_code == 200

    # Verify enqueue was called with base_branch
    args, kwargs = mock_enqueue.call_args
    # args: (task_id, goal, repo_url, base_branch)
    assert args[1] == "Test goal"
    assert args[3] == "develop"

    print("API with branch test passed!")

if __name__ == "__main__":
    try:
        test_create_and_get_task()
        test_create_task_with_branch()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
