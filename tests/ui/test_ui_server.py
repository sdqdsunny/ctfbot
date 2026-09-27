from fastapi.testclient import TestClient
from asas_agent.ui_server import app

client = TestClient(app)

def test_emit_event_endpoint():
    # Attempt to post an event
    response = client.post("/api/events", json={
        "type": "orchestrator_message",
        "data": {"content": "Hello World"}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
