from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_demo_monitoring_v138_routes_load() -> None:
    client = TestClient(app)

    combined = client.get("/ui/demo-monitoring/v1.3.8")
    assert combined.status_code == 200
    assert "v1.3.8" in combined.text
    assert 'const LEKAB_API_VERSION = "v1.3.8"' in combined.text

    reminder = client.get("/ui/reminder-cockpit/v1.3.8")
    assert reminder.status_code == 200
    assert "Reminder Cockpit" in reminder.text
    assert 'const INITIAL_PAGE = "appointment-reminders"' in reminder.text


def test_demo_monitoring_v138_payload_points_to_v138_routes() -> None:
    client = TestClient(app)

    payload = client.get("/api/demo-monitoring/v1.3.8/payload?lang=en").json()
    assert payload["version"] == "v1.3.8"
    links = payload["reminder_scheduler_bridge"]["quick_links"]
    assert links[0]["href"] == "/ui/reminder-cockpit/v1.3.8"
    assert links[1]["href"] == "/ui/reminder-scheduler/v1.3.6"
    assert links[2]["href"] == "/docs/demo?lang=en"


def test_demo_monitoring_v138_help_route_lists_reply_to_action() -> None:
    client = TestClient(app)

    payload = client.get("/api/demo-monitoring/v1.3.8/help").json()
    assert payload["version"] == "v1.3.8"
    assert "reply_to_action_engine_visibility" in payload["integrated_features"]
