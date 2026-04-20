from fastapi.testclient import TestClient

from demo_monitoring_ui.v1_3_6.demo_monitoring_ui.app import app


def test_reminder_scheduler_v136_ui_and_api_routes_load() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/reminder-scheduler/v1.3.6")
    payload_response = client.get("/api/reminder-ui/v1.3.6/payload")
    help_response = client.get("/api/reminder-ui/v1.3.6/help")
    config_response = client.get("/api/reminder-ui/v1.3.6/config")
    preview_response = client.get("/api/reminder-ui/v1.3.6/config/preview")
    results_response = client.get("/api/reminder-ui/v1.3.6/results")
    jobs_response = client.get("/api/reminder-ui/v1.3.6/jobs")
    health_response = client.get("/api/reminder-ui/v1.3.6/health")

    assert ui_response.status_code == 200
    assert "Appointment Agent Reminder Scheduler v1.3.6" in ui_response.text
    assert "A simple cockpit for appointment source, Google linkage, and reminder jobs" in ui_response.text
    assert "Appointment Source" in ui_response.text
    assert "Google Linkage" in ui_response.text
    assert "Appointment Details" in ui_response.text
    assert "Reminder Policy" in ui_response.text
    assert "Reminder Preview" in ui_response.text
    assert "Reminder Jobs" in ui_response.text
    assert "Health" in ui_response.text

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.3.6"
    assert len(payload["pages"]) >= 8
    assert len(payload["demo_stories"]) == 3
    assert payload["reminder_policy"]["metrics"][1]["value"] == "1300 ms"
    assert payload["dashboard_summary"]["metrics"][0]["value"] == "Google Calendar"
    assert len(payload["reminder_jobs"]["jobs"]) >= 4
    assert "appointment_source" in payload
    assert "google_linkage" in payload
    assert "appointment_details" in payload
    assert "reminder_policy" in payload
    assert "reminder_preview" in payload
    assert "reminder_jobs" in payload
    assert "runtime_health" in payload

    assert help_response.status_code == 200
    help_payload = help_response.json()
    assert help_payload["version"] == "v1.3.6"
    assert "appointment_source" in help_payload["guided_demo_features"]
    assert "google_linkage" in help_payload["guided_demo_features"]
    assert "appointment_details" in help_payload["guided_demo_features"]
    assert "reminder_policy" in help_payload["guided_demo_features"]
    assert "reminder_preview" in help_payload["guided_demo_features"]
    assert "reminder_jobs" in help_payload["guided_demo_features"]
    assert "runtime_health_visibility" in help_payload["guided_demo_features"]
    assert "silence_threshold_ms" in help_payload["setup_features"]
    assert "reminder_offsets_minutes" in help_payload["setup_features"]
    assert "google_calendar_id" in help_payload["setup_features"]
    assert "appointment_type" in help_payload["setup_features"]

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["enabled"] is True
    assert config_payload["silence_threshold_ms"] == 1300
    assert config_payload["reminder_offsets_minutes"] == [1440, 120, 30]
    assert config_payload["primary_channel"] == "rcs_sms"
    assert config_payload["result_retention_days"] == 30

    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["version"] == "v1.3.6"
    assert "appointment_source" in preview_payload
    assert "google_linkage" in preview_payload
    assert "appointment_details" in preview_payload
    assert "reminder_policy" in preview_payload
    assert "reminder_preview" in preview_payload
    assert "reminder_jobs" in preview_payload
    assert "runtime_health" in preview_payload
    assert preview_payload["operator_summary"]["flow_steps"][0]

    assert results_response.status_code == 200
    results_payload = results_response.json()
    assert results_payload["version"] == "v1.3.6"
    assert len(results_payload["results"]) >= 4
    assert results_payload["status_overview"]["planned"] >= 1
    assert results_payload["status_overview"]["updated"] >= 1
    assert results_payload["status_overview"]["cancelled"] >= 1
    assert results_payload["status_overview"]["sent"] >= 1

    assert jobs_response.status_code == 200
    assert jobs_response.json()["version"] == "v1.3.6"

    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload["status"] == "ok"
    assert health_payload["version"] == "v1.3.6"
    assert health_payload["scheduler_enabled"] is True
    assert health_payload["reminder_ready"] is True
    assert health_payload["db_status"] == "ok"
    assert "runtime_health" in health_payload
    assert health_payload["runtime_health"]["metrics"][1]["value"] == "ready"


def test_reminder_scheduler_v136_supports_german_language() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/reminder-scheduler/v1.3.6")
    help_response = client.get("/api/reminder-ui/v1.3.6/help?lang=de")
    payload_response = client.get("/api/reminder-ui/v1.3.6/payload?lang=de")

    assert ui_response.status_code == 200
    assert "Combined reminder cockpit" in ui_response.text
    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.3.6"
    assert "appointment_source" in help_response.json()["pages"]
    assert "reminder_policy" in help_response.json()["pages"]
    assert "reminder_jobs" in help_response.json()["pages"]
    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.3.6"
    assert payload["dashboard_summary"]["metrics"][3]["value"] == "1300 ms"
    assert payload["appointment_details"]["metrics"][1]["value"] == "Zahnarztkontrolle"
