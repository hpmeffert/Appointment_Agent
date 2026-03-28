from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_root_exposes_version_and_silence_threshold() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v1.0.0"
    assert body["silence_threshold_ms"] == 1300


def test_help_lists_modules() -> None:
    client = TestClient(app)

    response = client.get("/help")

    assert response.status_code == 200
    assert "lekab_adapter/v1_0_0" in response.json()["modules"]
