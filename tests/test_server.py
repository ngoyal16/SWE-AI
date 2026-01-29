from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.server import app

client = TestClient(app)

@patch("app.agent.run_agent_task")
def test_create_and_get_task(mock_run_task):
    response = client.post("/agent/tasks", json={"goal": "Test goal"})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    response = client.get(f"/agent/tasks/{task_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["id"] == task_id
    assert status_data["status"] == "QUEUED"

    print("API test passed!")

if __name__ == "__main__":
    try:
        test_create_and_get_task()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
