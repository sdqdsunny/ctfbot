import pytest
from src.asas_agent.ui_server import app, manager
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.mark.asyncio
async def test_api_chat():
    response = client.post("/api/chat", json={"message": "Abort current scan"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_api_approve():
    response = client.post("/api/approve", json={
        "action_id": "act_123",
        "approved": False,
        "feedback": "Use safe mode instead"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
