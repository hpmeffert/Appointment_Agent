from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_google_v110_patch3_live_sync_status_returns_source_and_events() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch3/live-sync/status",
        json={"mode": "simulation", "timeframe": "week"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["google_source"] == "simulation"
    assert body["last_sync_status"] == "ok"
    assert "google.sync.read.completed" in body["monitoring_labels"]


def test_google_v110_patch3_conflict_check_detects_free_slot_without_conflict() -> None:
    client = TestClient(app)
    start_time = datetime.utcnow() + timedelta(days=10)
    end_time = start_time + timedelta(minutes=30)

    response = client.post(
        "/api/google/v1.1.0-patch3/live-sync/conflict-check",
        json={
            "mode": "simulation",
            "timeframe": "week",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conflict_detected"] is False
    assert "calendar.slot.revalidated" in body["monitoring_labels"]


def test_google_v110_patch3_action_routes_are_available() -> None:
    client = TestClient(app)

    for route, expected_action in [
        ("/api/google/v1.1.0-patch3/demo-calendar/prepare-preview", "prepare"),
        ("/api/google/v1.1.0-patch3/demo-calendar/generate", "generate"),
        ("/api/google/v1.1.0-patch3/demo-calendar/delete", "delete"),
        ("/api/google/v1.1.0-patch3/demo-calendar/reset", "reset"),
    ]:
        response = client.post(route, json={"mode": "simulation", "timeframe": "day", "count": 1})
        assert response.status_code == 200
        assert response.json()["action"] == expected_action
