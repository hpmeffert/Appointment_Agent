from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_demo_ui_page_loads() -> None:
    client = TestClient(app)

    response = client.get("/ui/demo-monitoring/v1.0.0")

    assert response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.0.0" in response.text
    assert "Release shown: v1.0.4 Patch 2" in response.text
    assert "Technical Mode Off" in response.text
    assert "Timeline" in response.text
    assert "Performance" in response.text
    assert "Combined" in response.text
    assert "Monitoring Mode" in response.text
    assert "Google Demo Control" in response.text
    assert "Simulation does not write to Google Calendar" in response.text
    assert "Current mode: Simulation. No real Google calendar entries will be created." in response.text
    assert "?" in response.text


def test_demo_ui_scenario_payload_contains_required_scenarios() -> None:
    client = TestClient(app)

    response = client.get("/api/demo-monitoring/v1.0.0/scenarios")

    assert response.status_code == 200
    payload = response.json()
    scenario_ids = [scenario["id"] for scenario in payload["scenarios"]]
    assert "standard-booking" in scenario_ids
    assert "appointment-reminder-keep" in scenario_ids
    assert "appointment-reminder-reschedule" in scenario_ids
    assert "appointment-reminder-cancel" in scenario_ids
    assert "appointment-reminder-call-me" in scenario_ids
    assert "reschedule" in scenario_ids
    assert "cancellation" in scenario_ids
    assert "no-slot-escalation" in scenario_ids
    assert "provider-failure" in scenario_ids
    first_message_step = payload["scenarios"][0]["steps"][0]
    assert "message_id" in first_message_step
    assert "lekab_job_id" in first_message_step
    assert first_message_step["message_channel"] in {"RCS", "SMS"}
    assert "events" in first_message_step
    assert "correlation_id" in first_message_step
    assert "trace_id" in first_message_step
    assert payload["load_profiles"][0]["id"] == "20"


def test_demo_ui_scenario_payload_is_localized_in_german() -> None:
    client = TestClient(app)

    response = client.get("/api/demo-monitoring/v1.0.0/scenarios?lang=de")

    assert response.status_code == 200
    payload = response.json()
    assert payload["modes"][2]["label"] == "Kombiniert"
    assert payload["scenarios"][0]["title"] == "Termin-Erinnerung Behalten"


def test_demo_ui_help_lists_modes() -> None:
    client = TestClient(app)

    response = client.get("/api/demo-monitoring/v1.0.0/help")

    assert response.status_code == 200
    assert "combined" in response.json()["modes"]


def test_docs_routes_render_markdown_in_new_pages() -> None:
    client = TestClient(app)

    demo_response = client.get("/docs/demo?lang=en")
    user_response = client.get("/docs/user?lang=de")
    admin_response = client.get("/docs/admin?lang=en")

    assert demo_response.status_code == 200
    assert "Demo Guide" in demo_response.text
    assert "Version: v1.1.0-patch6" in demo_response.text
    assert user_response.status_code == 200
    assert "Sprache: DE" in user_response.text
    assert "User Guide Demo Monitoring UI v1.1.0 Patch 6" in user_response.text
    assert "Version: v1.1.0-patch6" in user_response.text
    assert admin_response.status_code == 200
    assert "Admin Guide" in admin_response.text


def test_demo_ui_v102_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.0.2")
    help_response = client.get("/api/demo-monitoring/v1.0.2/help")
    scenarios_response = client.get("/api/demo-monitoring/v1.0.2/scenarios")

    assert ui_response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.0.2" in ui_response.text
    assert "demoApiBase()" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.0.2"

    assert scenarios_response.status_code == 200
    assert "scenarios" in scenarios_response.json()


def test_demo_ui_v104_patch1_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.0.4-patch2")
    help_response = client.get("/api/demo-monitoring/v1.0.4-patch2/help")
    scenarios_response = client.get("/api/demo-monitoring/v1.0.4-patch2/scenarios")

    assert ui_response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.0.4-patch2" in ui_response.text
    assert "Release shown: v1.0.4 Patch 2" in ui_response.text
    assert "demoApiBase()" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.0.4-patch2"

    assert scenarios_response.status_code == 200
    assert "scenarios" in scenarios_response.json()


def test_demo_ui_v110_patch1_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch1")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch1/help")
    scenarios_response = client.get("/api/demo-monitoring/v1.1.0-patch1/scenarios")

    assert ui_response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.1.0-patch1" in ui_response.text
    assert "Release shown: v1.1.0 Patch 1" in ui_response.text
    assert "Google Demo Control" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch1"
    assert "simulation_test_switch" in help_response.json()["google_operator_features"]

    assert scenarios_response.status_code == 200
    assert "scenarios" in scenarios_response.json()


def test_demo_ui_v110_patch2_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch2")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch2/help")
    scenarios_response = client.get("/api/demo-monitoring/v1.1.0-patch2/scenarios")

    assert ui_response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.1.0-patch2" in ui_response.text
    assert "Release shown: v1.1.0 Patch 2" in ui_response.text
    assert "Prepare Demo Calendar" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch2"
    assert "prepare_preview" in help_response.json()["google_operator_features"]

    assert scenarios_response.status_code == 200
    assert "scenarios" in scenarios_response.json()


def test_demo_ui_v110_patch4_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch4")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch4/help")
    scenarios_response = client.get("/api/demo-monitoring/v1.1.0-patch4/scenarios")

    assert ui_response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.1.0-patch4" in ui_response.text
    assert "Release shown: v1.1.0 Patch 4" in ui_response.text
    assert "Google Source" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch4"
    assert help_response.json()["design_baseline"] == "Incident Demo UI"

    assert scenarios_response.status_code == 200
    assert "scenarios" in scenarios_response.json()


def test_demo_ui_v110_patch5_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch5")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch5/help")
    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch5/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.1.0-patch5" in ui_response.text
    assert "Google Demo Control" in ui_response.text
    assert "Simulation does not write to Google Calendar" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.1.0-patch3\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch5"
    assert "google-demo-control" in help_response.json()["pages"]
    assert "dedicated_google_demo_control_page" in help_response.json()["google_demo_control_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.1.0-patch5"
    assert payload["pages"][3]["id"] == "google-demo-control"
    assert payload["google_demo_control"]["title"] == "Google Demo Control"


def test_demo_ui_v110_patch6_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch6")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch6/help")
    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch6/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.1.0-patch6" in ui_response.text
    assert "From Date" in ui_response.text
    assert "Appointment Type" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.1.0-patch6\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch6"
    assert "date_range_selection" in help_response.json()["google_demo_control_features"]
    assert "appointment_type_dropdown" in help_response.json()["google_demo_control_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.1.0-patch6"
    assert payload["google_demo_control"]["default_from_date"]
    assert payload["google_demo_control"]["appointment_types"][0]["id"] == "dentist"


def test_demo_ui_v105_cockpit_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.0.5")
    help_response = client.get("/api/demo-monitoring/v1.0.5/help")
    payload_response = client.get("/api/demo-monitoring/v1.0.5/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.0.5" in ui_response.text
    assert "Dashboard" in ui_response.text
    assert "Settings" in ui_response.text
    assert "Night" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.0.5"
    assert "dashboard" in help_response.json()["pages"]

    assert payload_response.status_code == 200
    assert payload_response.json()["version"] == "v1.0.5"
    assert payload_response.json()["pages"][0]["id"] == "dashboard"


def test_demo_ui_v106_vertical_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.0.6")
    help_response = client.get("/api/demo-monitoring/v1.0.6/help")
    payload_response = client.get("/api/demo-monitoring/v1.0.6/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.0.6" in ui_response.text
    assert "Vertical Quick Start" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.0.6"
    assert "dentist" in help_response.json()["verticals"]

    assert payload_response.status_code == 200
    assert payload_response.json()["version"] == "v1.0.6"
    assert payload_response.json()["verticals"][0]["id"] == "dentist"


def test_demo_ui_v106_patch1_vertical_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.0.6-patch1")
    help_response = client.get("/api/demo-monitoring/v1.0.6-patch1/help")
    payload_response = client.get("/api/demo-monitoring/v1.0.6-patch1/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.0.6-patch1" in ui_response.text
    assert "Vertical Quick Start" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.0.6-patch1"
    assert "dentist" in help_response.json()["verticals"]
    assert "vertical_descriptions" in help_response.json()

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.0.6-patch1"
    assert payload["verticals"][0]["id"] == "dentist"
    assert payload["verticals"][0]["audience_fit"]
    assert payload["verticals"][1]["reminder_example"]
    assert payload["verticals"][2]["sample_description"]
