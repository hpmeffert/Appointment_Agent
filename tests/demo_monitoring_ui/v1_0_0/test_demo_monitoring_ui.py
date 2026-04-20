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
    assert "v1.3.9" in demo_response.text
    assert "Story 1: Create a new address" in demo_response.text
    assert user_response.status_code == 200
    assert "Sprache: DE" in user_response.text
    assert "Benutzerleitfaden v1.3.9" in user_response.text
    assert "v1.3.9" in user_response.text
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


def test_demo_ui_v110_patch7_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch7")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch7/help")
    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch7/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.1.0-patch7" in ui_response.text
    assert "Reply Actions" in ui_response.text
    assert "Available Time Slots" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.1.0-patch6\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch7"
    assert "interactive_reply_buttons" in help_response.json()["communication_features"]
    assert "interactive_slot_buttons" in help_response.json()["communication_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.1.0-patch7"
    first_step = payload["scenarios"][0]["steps"][0]
    assert first_step["communication_message"]["actions"][0]["value"] == "keep"
    assert payload["communication_model"]["provider_neutral"] is True


def test_demo_ui_v110_patch7_payload_is_localized_for_interactive_controls() -> None:
    client = TestClient(app)

    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch7/payload?lang=de")

    assert payload_response.status_code == 200
    payload = payload_response.json()
    first_step = payload["scenarios"][0]["steps"][0]
    action_labels = [action["label"] for action in first_step["communication_message"]["actions"]]
    assert "Termin behalten" in action_labels
    assert "Google Demo Control" == payload["pages"][3]["label"]


def test_demo_ui_v110_patch8_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch8")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch8/help")
    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch8/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.1.0-patch8" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.1.0-patch8\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch8"
    assert "availability_slots" in help_response.json()["google_live_features"]
    assert "real_booking_create_cancel_reschedule" in help_response.json()["google_live_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.1.0-patch8"
    assert payload["communication_model"]["booking_backend"] == "google_adapter_v1.1.0_patch8"


def test_demo_ui_v110_patch8a_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch8a")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch8a/help")
    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch8a/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.1.0-patch8a" in ui_response.text
    assert "Slot Hold Minutes" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.1.0-patch8a\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch8a"
    assert "slot_hold_duration_adjustable" in help_response.json()["slot_hold_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.1.0-patch8a"
    assert payload["hold_settings"]["slot_hold_minutes"] == 2


def test_demo_ui_v110_patch8b_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.1.0-patch8b")
    help_response = client.get("/api/demo-monitoring/v1.1.0-patch8b/help")
    payload_response = client.get("/api/demo-monitoring/v1.1.0-patch8b/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.1.0-patch8b" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.1.0-patch8b\";" in ui_response.text
    assert "Slot Hold Minutes" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.1.0-patch8b"
    assert "end_to_end_booking_flow" in help_response.json()["communication_features"]
    assert "interactive_live_revalidation_before_booking" in help_response.json()["google_live_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.1.0-patch8b"
    assert payload["communication_model"]["booking_backend"] == "google_adapter_v1.1.0_patch8b"
    assert payload["interactive_demo_flow"]["booking_confirmation_actions"][0]["value"] == "confirm"


def test_demo_ui_v120_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.2.0")
    help_response = client.get("/api/demo-monitoring/v1.2.0/help")
    payload_response = client.get("/api/demo-monitoring/v1.2.0/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.2.0" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.2.0\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.2.0"
    assert "end_to_end_booking_flow" in help_response.json()["communication_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.2.0"
    assert payload["communication_model"]["booking_backend"] == "google_adapter_v1_2_0"


def test_demo_ui_v121_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.2.1")
    help_response = client.get("/api/demo-monitoring/v1.2.1/help")
    payload_response = client.get("/api/demo-monitoring/v1.2.1/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.2.1" in ui_response.text
    assert "Message Monitor" in ui_response.text
    assert "Communications Reports" in ui_response.text
    assert "const GOOGLE_API_VERSION = \"v1.2.0\";" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.2.1"
    assert "message_monitor_page" in help_response.json()["communication_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.2.1"
    assert payload["pages"][1]["id"] == "message-monitor"
    assert payload["communication_model"]["messaging_backend"] == "lekab_adapter_v1_2_1"


def test_demo_ui_v121_patch1_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.2.1-patch1")
    help_response = client.get("/api/demo-monitoring/v1.2.1-patch1/help")
    payload_response = client.get("/api/demo-monitoring/v1.2.1-patch1/payload")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.2.1-patch1" in ui_response.text
    assert "RCS Settings" in ui_response.text
    assert "Save RCS Settings" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.2.1-patch1"
    assert "settings_to_rcs_header_navigation" in help_response.json()["settings_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.2.1-patch1"
    assert payload["pages"][4]["id"] == "settings-general"
    assert payload["pages"][5]["id"] == "settings-rcs"


def test_demo_ui_v121_patch2_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.2.1-patch2")
    help_response = client.get("/api/demo-monitoring/v1.2.1-patch2/help")
    payload_response = client.get("/api/demo-monitoring/v1.2.1-patch2/payload")
    docs_asset_response = client.get("/docs/assets/screenshots/v1_2_1_patch2/cockpit-overview.svg")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.2.1-patch2" in ui_response.text
    assert "--action-surface" in ui_response.text
    assert "RCS Settings" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.2.1-patch2"
    assert "day_mode_high_contrast_buttons" in help_response.json()["settings_features"]
    assert "slot_hold_story" in help_response.json()["demo_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.2.1-patch2"
    assert payload["pages"][5]["id"] == "settings-rcs"
    assert payload["documentation_highlights"]

    assert docs_asset_response.status_code == 200
    assert "<svg" in docs_asset_response.text


def test_demo_ui_v121_patch3_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.2.1-patch3")
    help_response = client.get("/api/demo-monitoring/v1.2.1-patch3/help")
    payload_response = client.get("/api/demo-monitoring/v1.2.1-patch3/payload")
    docs_asset_response = client.get("/docs/assets/screenshots/v1_2_1_patch3/platform-flow.svg")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.2.1-patch3" in ui_response.text
    assert "How the Platform Works" in ui_response.text
    assert "Demo Storyboard" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.2.1-patch3"
    assert "platform_story_cards" in help_response.json()["platform_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.2.1-patch3"
    assert payload["platform_overview"]["items"][0]["title"]
    assert payload["demo_storyboard"]["stories"][0]["title"] == "Booking"

    assert docs_asset_response.status_code == 200
    assert "<svg" in docs_asset_response.text


def test_demo_ui_v121_patch4_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.2.1-patch4")
    help_response = client.get("/api/demo-monitoring/v1.2.1-patch4/help")
    payload_response = client.get("/api/demo-monitoring/v1.2.1-patch4/payload")
    docs_asset_response = client.get("/docs/assets/screenshots/v1_2_1_patch4/platform-flow.svg")

    assert ui_response.status_code == 200
    assert "Appointment Agent Cockpit v1.2.1-patch4" in ui_response.text
    assert "Guided Demo Mode" in ui_response.text
    assert "Auto Demo Off" in ui_response.text
    assert "Messages and Customer Journey" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.2.1-patch4"
    assert "story_engine_steps" in help_response.json()["guided_demo_features"]
    assert "message_monitor_visibility" in help_response.json()["message_experience_features"]

    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["version"] == "v1.2.1-patch4"
    assert payload["guided_demo"]["modes"][0]["id"] == "free"
    assert payload["guided_demo"]["steps"][0]["step_id"] == "intro"
    assert payload["platform_visibility"]["channels"][0] == "RCS"

    assert docs_asset_response.status_code == 200
    assert "<svg" in docs_asset_response.text


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
