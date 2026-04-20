from fastapi.testclient import TestClient

from demo_monitoring_ui.v1_3_0.demo_monitoring_ui.app import app


def test_reminder_scheduler_v130_ui_and_api_routes_load() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/reminder-scheduler/v1.3.0")
    payload_response = client.get("/api/reminder-ui/v1.3.0/payload")
    help_response = client.get("/api/reminder-ui/v1.3.0/help")
    config_response = client.get("/api/reminder-ui/v1.3.0/config")
    preview_response = client.get("/api/reminder-ui/v1.3.0/config/preview")
    jobs_response = client.get("/api/reminder-ui/v1.3.0/jobs")
    health_response = client.get("/api/reminder-ui/v1.3.0/health")

    assert ui_response.status_code == 200
    assert "Appointment Agent Reminder Scheduler v1.3.0" in ui_response.text
    assert "Reminder setup that a new operator can understand in one minute" in ui_response.text
    assert "Reminder Overview" in ui_response.text

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.3.0"
    assert len(payload["demo_stories"]) >= 3

    assert help_response.status_code == 200
    help_payload = help_response.json()
    assert help_payload["version"] == "v1.3.0"
    assert "setup_first" in help_payload["guided_demo_features"]
    assert "manual_mode" in help_payload["setup_features"]

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["mode"] == "manual"
    assert config_payload["reminder_count"] == 1
    assert config_payload["channel_email_enabled"] is True

    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["version"] == "v1.3.0"
    assert len(preview_payload["demo_stories"]) >= 3

    assert jobs_response.status_code == 200
    jobs_payload = jobs_response.json()
    assert jobs_payload["version"] == "v1.3.0"
    assert len(jobs_payload["jobs"]) >= 3

    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload["status"] == "ok"
    assert health_payload["version"] == "v1.3.0"


def test_reminder_scheduler_v130_supports_german_language() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/reminder-scheduler/v1.3.0")
    help_response = client.get("/api/reminder-ui/v1.3.0/help?lang=de")

    assert ui_response.status_code == 200
    assert "Incident-style reminder cockpit" in ui_response.text
    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.3.0"
    assert "help" in help_response.json()["pages"]
