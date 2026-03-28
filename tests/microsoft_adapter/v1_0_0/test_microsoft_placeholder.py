from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_microsoft_module_is_prepared() -> None:
    client = TestClient(app)

    response = client.get("/api/microsoft/v1.0.0/help")

    assert response.status_code == 200
    assert response.json()["status"] == "prepared"
