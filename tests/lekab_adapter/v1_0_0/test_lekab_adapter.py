from fastapi.testclient import TestClient
from uuid import uuid4

from appointment_agent_shared.main import app


def test_lekab_token_and_callback_duplicate_handling() -> None:
    client = TestClient(app)

    token_response = client.post("/api/lekab/v1.0.0/auth/token")
    assert token_response.status_code == 200
    assert token_response.json()["token_type"] == "Bearer"

    payload = {
        "event_id": f"evt-{uuid4().hex}",
        "event_type": "JOB_START",
        "correlation_id": "corr-1",
        "job_id": "job-123",
        "status": "started",
        "details": {"tenant": "demo"},
    }
    first = client.post("/api/lekab/v1.0.0/callbacks", json=payload)
    second = client.post("/api/lekab/v1.0.0/callbacks", json=payload)

    assert first.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
