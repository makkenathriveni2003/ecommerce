import time
from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

def test_celery_task_trigger_and_status():
    """Verify that a Celery background task is queued via FastAPI and reaches SUCCESS."""
    # 1. Trigger background job
    response = client.post("/tasks/run", json={"steps": 4, "delay": 0.2, "name": "Pytest Background Test"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert "task_id" in data
    task_id = data["task_id"]
    assert len(task_id) > 10

    # 2. Poll task status until completion
    terminal_reached = False
    observed_states = set()

    for _ in range(30):
        status_res = client.get(f"/tasks/{task_id}/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["task_id"] == task_id
        current_status = status_data["status"]
        observed_states.add(current_status)

        assert 0 <= status_data["percent"] <= 100
        assert "message" in status_data

        if current_status == "SUCCESS":
            assert status_data["percent"] == 100
            assert status_data["result"] is not None
            assert status_data["error"] is None
            terminal_reached = True
            break
        elif current_status == "FAILURE":
            pytest.fail(f"Task failed with error: {status_data.get('error')}")

        time.sleep(0.2)

    assert terminal_reached, f"Task did not reach SUCCESS within timeout. Observed states: {observed_states}"
