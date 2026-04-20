from fastapi.testclient import TestClient

from demo_monitoring_ui.v1_3_6_patch1.demo_monitoring_ui.app import router
from fastapi import FastAPI


app = FastAPI()
app.include_router(router)


def test_combined_demo_ui_v136_patch1_routes_load() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.3.6-patch1")
    reminder_response = client.get("/ui/reminder-cockpit/v1.3.7")
    help_response = client.get("/api/demo-monitoring/v1.3.6-patch1/help")
    payload_response = client.get("/api/demo-monitoring/v1.3.6-patch1/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.3.6-patch1" in ui_response.text
    assert "Appointment Source to Reminder Jobs" in ui_response.text
    assert "Embedded Reminder Cockpit" in ui_response.text
    assert "Last Connection Test" in ui_response.text
    assert "Connection Mode" in ui_response.text
    assert "Fetch Latest Callback" in ui_response.text
    assert "Last Callback Fetch" in ui_response.text
    assert 'const LEKAB_API_VERSION = "v1.2.1-patch4"' in ui_response.text
    assert reminder_response.status_code == 200
    assert "Reminder Cockpit v1.3.6-patch1" in reminder_response.text
    assert 'const INITIAL_PAGE = "appointment-reminders"' in reminder_response.text

    assert help_response.status_code == 200
    help_payload = help_response.json()
    assert help_payload["version"] == "v1.3.6-patch1"
    assert "appointment-reminders" in help_payload["pages"]
    assert "combined_google_to_reminder_demo" in help_payload["demo_features"]
    assert "standalone_reminder_cockpit_route" in help_payload["integrated_demo_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.3.6-patch1"
    assert payload["pages"][7]["id"] == "appointment-reminders"
    assert payload["pages"][7]["label"] == "Reminder"
    assert payload["reminder_scheduler_bridge"]["embedded_ui_url"] == "/ui/reminder-scheduler/v1.3.6"
    assert payload["reminder_scheduler_bridge"]["quick_links"][0]["href"] == "/ui/reminder-cockpit/v1.3.7"
    assert payload["reminder_scheduler_bridge"]["quick_links"][1]["href"] == "/ui/reminder-scheduler/v1.3.6"
    assert payload["reminder_scheduler_bridge"]["quick_links"][2]["href"] == "/docs/demo?lang=en"
    assert payload["reminder_scheduler_bridge"]["quick_links"][3]["href"] == "/docs/user?lang=en"
    assert payload["reminder_scheduler_bridge"]["quick_links"][4]["href"] == "/docs/admin?lang=en"
    assert len(payload["reminder_scheduler_bridge"]["quick_links"]) >= 5


def test_combined_demo_ui_v136_patch1_supports_german_payload() -> None:
    client = TestClient(app)

    response = client.get("/api/demo-monitoring/v1.3.6-patch1/payload?lang=de")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1.3.6-patch1"
    assert payload["pages"][7]["label"] == "Reminder"
    assert payload["reminder_scheduler_bridge"]["title"] == "Terminquelle bis Reminder Jobs"
    assert payload["reminder_scheduler_bridge"]["quick_links"][2]["href"] == "/docs/demo?lang=de"


def test_combined_demo_ui_v136_patch1_uses_patch4_lekab_settings_backend() -> None:
    client = TestClient(app)

    response = client.get("/ui/demo-monitoring/v1.3.6-patch1")

    assert response.status_code == 200
    assert 'const LEKAB_API_VERSION = "v1.2.1-patch4"' in response.text
