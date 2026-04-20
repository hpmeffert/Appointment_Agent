from fastapi.testclient import TestClient

from demo_monitoring_ui.v1_3_4.demo_monitoring_ui.app import app


def test_reminder_scheduler_v134_ui_and_api_routes_load() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/reminder-scheduler/v1.3.4")
    payload_response = client.get("/api/reminder-ui/v1.3.4/payload")
    help_response = client.get("/api/reminder-ui/v1.3.4/help")
    config_response = client.get("/api/reminder-ui/v1.3.4/config")
    preview_response = client.get("/api/reminder-ui/v1.3.4/config/preview")
    results_response = client.get("/api/reminder-ui/v1.3.4/results")
    health_response = client.get("/api/reminder-ui/v1.3.4/health")

    assert ui_response.status_code == 200
    assert "Appointment Agent Reminder Scheduler v1.3.4" in ui_response.text
    assert "Reminder delivery that a new operator can understand in one minute" in ui_response.text
    assert "Delivery Overview" in ui_response.text
    assert "Delivery Controls" in ui_response.text
    assert "Validation Outcomes" in ui_response.text
    assert "Delivery Results" in ui_response.text
    assert "Delivery Channels" in ui_response.text
    assert "Operator Summary" in ui_response.text

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.3.4"
    assert len(payload["demo_stories"]) >= 3
    assert len(payload["delivery_channels"]) >= 3
    assert len(payload["delivery_results"]) >= 6
    assert "delivery_overview" in payload
    assert "validation_outcomes" in payload
    assert payload["delivery_setup"]["primary_channel"] == "rcs_sms"

    assert help_response.status_code == 200
    help_payload = help_response.json()
    assert help_payload["version"] == "v1.3.4"
    assert "delivery_channels" in help_payload["guided_demo_features"]
    assert "validation_outcomes" in help_payload["guided_demo_features"]
    assert "delivery_results" in help_payload["guided_demo_features"]
    assert "three_demo_stories" in help_payload["guided_demo_features"]
    assert "fallback_handling" in help_payload["guided_demo_features"]
    assert "result_visibility" in help_payload["guided_demo_features"]
    assert "primary_channel" in help_payload["setup_features"]
    assert "fallback_channels" in help_payload["setup_features"]
    assert "message_length_limit" in help_payload["setup_features"]

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["enabled"] is True
    assert config_payload["delivery_mode"] == "priority_order"
    assert config_payload["primary_channel"] == "rcs_sms"
    assert config_payload["allow_fallback_channels"] is True
    assert config_payload["channel_rcs_sms_enabled"] is True

    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["version"] == "v1.3.4"
    assert len(preview_payload["validation_outcomes"]) >= 3
    assert len(preview_payload["delivery_results"]) >= 6
    assert len(preview_payload["demo_stories"]) >= 3
    assert preview_payload["operator_summary"]["flow_steps"][0]

    assert results_response.status_code == 200
    results_payload = results_response.json()
    assert results_payload["version"] == "v1.3.4"
    assert len(results_payload["results"]) >= 6
    assert results_payload["status_overview"]["sent"] >= 1
    assert results_payload["status_overview"]["fallback_sent"] >= 1
    assert results_payload["status_overview"]["blocked"] >= 1
    assert results_payload["status_overview"]["retrying"] >= 1
    assert results_payload["status_overview"]["failed"] >= 1
    assert results_payload["status_overview"]["skipped"] >= 1

    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload["status"] == "ok"
    assert health_payload["version"] == "v1.3.4"
    assert health_payload["delivery_ready"] is True
    assert "delivery_states" in health_payload
    assert health_payload["channels"]["rcs_sms"] is True


def test_reminder_scheduler_v134_supports_german_language() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/reminder-scheduler/v1.3.4")
    help_response = client.get("/api/reminder-ui/v1.3.4/help?lang=de")
    payload_response = client.get("/api/reminder-ui/v1.3.4/payload?lang=de")

    assert ui_response.status_code == 200
    assert "Delivery-style reminder cockpit" in ui_response.text
    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.3.4"
    assert "setup" in help_response.json()["pages"]
    assert "preview" in help_response.json()["pages"]
    assert "jobs" in help_response.json()["pages"]
    assert payload_response.status_code == 200
    assert payload_response.json()["version"] == "v1.3.4"
