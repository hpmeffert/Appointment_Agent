from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_google_v110_patch2_prepare_preview_returns_preview_only_result() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch2/demo-calendar/prepare-preview",
        json={"mode": "simulation", "timeframe": "week", "count": 3, "vertical": "wallbox"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "prepare"
    assert body["preview_only"] is True
    assert body["generated_count"] == 3
    assert body["deleted_count"] == 0
    assert "No calendar entries were written" in body["message"]


def test_google_v110_patch2_generate_delete_and_reset_routes_exist() -> None:
    client = TestClient(app)

    generate = client.post(
        "/api/google/v1.1.0-patch2/demo-calendar/generate",
        json={"mode": "simulation", "timeframe": "day", "count": 2, "vertical": "dentist"},
    )
    delete = client.post(
        "/api/google/v1.1.0-patch2/demo-calendar/delete",
        json={"mode": "simulation", "timeframe": "day", "count": 2, "vertical": "dentist"},
    )
    reset = client.post(
        "/api/google/v1.1.0-patch2/demo-calendar/reset",
        json={"mode": "simulation", "timeframe": "day", "count": 2, "vertical": "dentist"},
    )

    assert generate.status_code == 200
    assert generate.json()["action"] == "generate"
    assert delete.status_code == 200
    assert delete.json()["action"] == "delete"
    assert reset.status_code == 200
    assert reset.json()["action"] == "reset"
