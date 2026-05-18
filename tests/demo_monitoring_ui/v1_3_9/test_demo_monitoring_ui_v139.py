from fastapi.testclient import TestClient

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.main import app
from demo_monitoring_ui.v1_3_9.demo_monitoring_ui.scenario_context import DemoScenarioContextService, DemoScenarioContextUpdate


def test_demo_monitoring_v139_routes_load() -> None:
    client = TestClient(app)

    combined = client.get("/ui/demo-monitoring/v1.3.9")
    assert combined.status_code == 200
    assert "v1.3.10" in combined.text
    assert 'const ADDRESS_API_VERSION = "v1.3.9"' in combined.text
    assert 'const DEMO_API_VERSION = "v1.3.9"' in combined.text
    assert 'const GOOGLE_API_VERSION = "v1.3.6"' in combined.text
    assert 'const LEKAB_API_VERSION = "v1.3.8"' in combined.text
    assert "page-addresses" in combined.text
    assert "page-dashboard-plus" in combined.text
    assert "dashboardPlusPhoneInput" in combined.text
    assert "dashboardPlusStartBtn" in combined.text
    assert "Dashboard+" in combined.text
    assert 'const INITIAL_PAGE = "dashboard-plus"' in combined.text
    assert "reminderAssignBtn" in combined.text
    assert "googleAddressSelect" in combined.text
    assert "runScenarioSimulationBtn" in combined.text
    assert "scenarioArtifactsDetail" in combined.text
    assert "scenarioModeButtons" in combined.text
    assert "scenarioAppointmentTypeSelect" in combined.text
    assert "function appointmentTypeConfirmationText({" in combined.text
    assert "Wir bestaetigen Ihren Zahnarzt Termin am" in combined.text
    assert "Wir bestaetigen Ihren Termin (Arzt) am" in combined.text
    assert "Wir bestaetigen Ihren Termin (Techniker) am" in combined.text
    assert "Wir bestaetigen Ihren Termin (T-Time) am" in combined.text
    assert 'input.type = "radio";' in combined.text
    assert 'input.name = "scenarioExecutionMode";' in combined.text
    assert 'input.name = "dashboardMode";' in combined.text
    assert 'input.name = "guidedMode";' in combined.text
    assert ".radio-chip label {" in combined.text
    assert ".radio-chip label," in combined.text
    assert ".radio-chip label span {" in combined.text
    assert "color: #fff !important;" in combined.text
    assert "opacity: 1;" in combined.text
    assert ".radio-chip label span:last-child {" in combined.text
    assert "padding-left: 4px;" in combined.text
    assert "text-shadow: 0 1px 0 rgba(15, 32, 51, 0.24);" in combined.text
    assert "max-height: 720px;" in combined.text
    assert "scrollbar-width: thin;" in combined.text
    assert ".chat::-webkit-scrollbar" in combined.text
    assert '.radio-chip input[type="radio"]:checked + label {' in combined.text
    assert "color: #fff;" in combined.text
    assert "font-weight: 700;" in combined.text
    assert "const parseMessageTimestamp = (message) => {" in combined.text
    assert "const timestampDiff = parseMessageTimestamp(right) - parseMessageTimestamp(left);" in combined.text
    assert 'return String(right.message_id || "").localeCompare(String(left.message_id || ""));' in combined.text
    assert "refs.chatStream.scrollTop = 0;" in combined.text
    assert '["Target Calendar", latestGoogleWriteback?.target_calendar_summary || "-"],' in combined.text
    assert '["Calendar ID", latestGoogleWriteback?.target_calendar_id || "-"],' in combined.text
    assert '["Provider Ref", latestGoogleWriteback?.provider_reference || "-"],' in combined.text
    assert 'Open Calendar Event' in combined.text
    assert "scenarioAddressSelect" in combined.text
    assert "hydrationDiagnostic" in combined.text
    assert "browserDiagnosticsBody" in combined.text
    assert "scenarioSelectorState" in combined.text
    assert "addressSelectorState" in combined.text
    assert "__APPOINTMENT_AGENT_BROWSER_DIAGNOSTICS__" in combined.text
    assert 'button.disabled = true;' in combined.text
    assert "Real mode waits for provider callback" in combined.text

    standalone = client.get("/ui/address-database/v1.3.9")
    assert standalone.status_code == 200
    assert "Address Database v1.3.10" in standalone.text
    assert 'const INITIAL_PAGE = "addresses"' in standalone.text

    combined_patch = client.get("/ui/demo-monitoring/v1.3.9-patch1")
    assert combined_patch.status_code == 200
    assert "v1.3.10" in combined_patch.text

    standalone_patch = client.get("/ui/address-database/v1.3.9-patch1")
    assert standalone_patch.status_code == 200
    assert "Address Database v1.3.10" in standalone_patch.text

    combined_patch2 = client.get("/ui/demo-monitoring/v1.3.9-patch2")
    assert combined_patch2.status_code == 200
    assert "v1.3.10" in combined_patch2.text

    combined_patch3 = client.get("/ui/demo-monitoring/v1.3.9-patch3")
    assert combined_patch3.status_code == 200
    assert "v1.3.10" in combined_patch3.text

    combined_patch4 = client.get("/ui/demo-monitoring/v1.3.9-patch4")
    assert combined_patch4.status_code == 200
    assert "v1.3.10" in combined_patch4.text

    combined_patch5 = client.get("/ui/demo-monitoring/v1.3.9-patch5")
    assert combined_patch5.status_code == 200
    assert "v1.3.10" in combined_patch5.text

    combined_patch6 = client.get("/ui/demo-monitoring/v1.3.9-patch6")
    assert combined_patch6.status_code == 200
    assert "v1.3.10" in combined_patch6.text

    combined_patch7 = client.get("/ui/demo-monitoring/v1.3.9-patch7")
    assert combined_patch7.status_code == 200
    assert "v1.3.10" in combined_patch7.text

    combined_patch8 = client.get("/ui/demo-monitoring/v1.3.9-patch8")
    assert combined_patch8.status_code == 200
    assert "v1.3.10" in combined_patch8.text


def test_demo_monitoring_v139_payload_exposes_addresses_page() -> None:
    session = SessionLocal()
    try:
        DemoScenarioContextService(session).save_context(
            DemoScenarioContextUpdate(
                scenario_id="confirm-appointment",
                mode="simulation",
                address_id="addr-demo-001",
                status="idle",
                metadata={
                    "ui_modes": {"dashboard_mode": "combined", "guided_mode": "guided"},
                    "dashboard_plus": {"contact_target_mode": "address", "manual_phone_number": ""},
                },
            )
        )
    finally:
        session.close()

    client = TestClient(app)

    payload = client.get("/api/demo-monitoring/v1.3.9/payload?lang=en").json()
    assert payload["version"] == "v1.3.10"
    assert payload["ui_contract"]["demo_api_version"] == "v1.3.9"
    assert payload["ui_contract"]["patch_alias_version"] == "v1.3.10"
    assert payload["ui_contract"]["legacy_patch_aliases"] == ["v1.3.9-patch1", "v1.3.9-patch2", "v1.3.9-patch3", "v1.3.9-patch4", "v1.3.9-patch5", "v1.3.9-patch6", "v1.3.9-patch7", "v1.3.9-patch8"]
    assert payload["ui_version"] == "v1.3.10"
    assert payload["api_version"] == "v1.3.9"
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["menus"][0]["id"] == "dashboard-plus"
    assert payload["menus"][1]["id"] == "dashboard"
    assert payload["operator_panel"]["scenario_options"]
    assert payload["operator_panel"]["address_options"]
    assert payload["operator_panel"]["dashboard_plus"]["scenario_mode"] == "real"
    assert payload["operator_panel"]["dashboard_plus"]["contact_target_mode"] == "address"
    assert payload["operator_panel"]["dashboard_plus"]["selected_contact_phone"]
    assert [item["id"] for item in payload["operator_panel"]["appointment_type_options"]] == ["dentist", "doctor", "technician", "tee_time"]
    assert payload["current_story"]["id"]
    assert payload["current_mode"]["scenario_mode"]
    assert payload["current_mode"]["dashboard_mode"] == "combined"
    assert payload["current_mode"]["guided_mode"] == "guided"
    assert payload["current_mode"]["appointment_type"] == "dentist"
    assert payload["google_workspace"]["calendar_ref"]
    assert payload["messages_customer_journey"]["correlation_ref"]
    assert payload["messages_customer_journey"]["suggestion_buttons"]
    assert payload["messages_customer_journey"]["real_channel_payload"]["message_type"] == "suggestion_buttons"
    assert payload["diagnostics"]["scenario_source_status"] == "loaded"
    assert payload["diagnostics"]["address_source_status"] == "loaded"
    assert payload["diagnostics"]["payload_loaded_at"] == payload["generated_at_utc"]
    assert any(page["id"] == "addresses" for page in payload["pages"])
    assert payload["address_database"]["quick_links"][0]["href"] == "/ui/address-database/v1.3.9"
    assert any(metric["label"] == "Address record" for metric in payload["reminder_scheduler_bridge"]["source_metrics"])
    assert payload["reminder_scheduler_bridge"]["jobs"][0]["address_id"] == "addr-demo-001"
    assert payload["reminder_scheduler_bridge"]["assignment_context"]["appointment_external_id"] == "gcal-87421"
    assert payload["scenario_testing"]["artifact_directory"] == "runtime-artifacts/demo-scenarios/v1_3_9"
    assert any(item["id"] == "confirm-appointment" for item in payload["scenario_testing"]["scenario_matrix"])
    assert any(item["id"] == "this-week" for item in payload["scenario_testing"]["scenario_matrix"])
    assert payload["interactive_demo_flow"]["phase6_enabled"] is True
    assert any(page["id"] == "dashboard-plus" for page in payload["pages"])
    assert [item["label"] for item in payload["interactive_demo_flow"]["initial_actions"]] == ["Confirm", "Reschedule", "Cancel"]
    confirm_scenario = next(item for item in payload["scenarios"] if item["id"] == "confirm-appointment")
    assert [item["label"] for item in confirm_scenario["steps"][0]["communication_message"]["actions"]] == ["Confirm", "Reschedule", "Cancel"]

    payload_patch = client.get("/api/demo-monitoring/v1.3.9-patch1/payload?lang=en")
    assert payload_patch.status_code == 200
    assert payload_patch.json()["version"] == "v1.3.10"
    assert payload_patch.json()["ui_contract"] == payload["ui_contract"]

    payload_patch2 = client.get("/api/demo-monitoring/v1.3.9-patch2/payload?lang=en")
    assert payload_patch2.status_code == 200
    assert payload_patch2.json()["ui_contract"] == payload["ui_contract"]

    payload_patch3 = client.get("/api/demo-monitoring/v1.3.9-patch3/payload?lang=en")
    assert payload_patch3.status_code == 200
    assert payload_patch3.json()["ui_contract"] == payload["ui_contract"]

    payload_patch4 = client.get("/api/demo-monitoring/v1.3.9-patch4/payload?lang=en")
    assert payload_patch4.status_code == 200
    assert payload_patch4.json()["ui_contract"] == payload["ui_contract"]

    payload_patch5 = client.get("/api/demo-monitoring/v1.3.9-patch5/payload?lang=en")
    assert payload_patch5.status_code == 200
    assert payload_patch5.json()["ui_contract"] == payload["ui_contract"]

    payload_patch6 = client.get("/api/demo-monitoring/v1.3.9-patch6/payload?lang=en")
    assert payload_patch6.status_code == 200
    assert payload_patch6.json()["ui_contract"] == payload["ui_contract"]

    payload_patch7 = client.get("/api/demo-monitoring/v1.3.9-patch7/payload?lang=en")
    assert payload_patch7.status_code == 200
    assert payload_patch7.json()["ui_contract"] == payload["ui_contract"]

    payload_patch8 = client.get("/api/demo-monitoring/v1.3.9-patch8/payload?lang=en")
    assert payload_patch8.status_code == 200
    assert payload_patch8.json()["ui_contract"] == payload["ui_contract"]


def test_demo_monitoring_v139_payload_marks_real_callback_selection() -> None:
    session = SessionLocal()
    try:
        DemoScenarioContextService(session).save_context(
            DemoScenarioContextUpdate(
                scenario_id="confirm-appointment",
                mode="real",
                address_id="addr-demo-001",
                appointment_id="appt-real-ui-001",
                booking_reference="book-real-ui-001",
                correlation_ref="corr-real-ui-001",
                current_step="confirmation_complete",
                status="confirmed",
                metadata={
                    "real_callback": {
                        "incoming_data": "confirm_appointment",
                        "selected_action": "keep",
                        "button_state": "selected",
                    }
                },
            )
        )
    finally:
        session.close()

    client = TestClient(app)
    payload = client.get("/api/demo-monitoring/v1.3.9/payload?lang=en").json()
    assert payload["messages_customer_journey"]["mode"] == "real"
    assert payload["messages_customer_journey"]["selected_action"] == "keep"
    assert any(item.get("selected") for item in payload["messages_customer_journey"]["suggestion_buttons"])
    assert any(item.get("selected") for item in payload["messages_customer_journey"]["real_channel_payload"]["suggestions"])


def test_demo_monitoring_v139_context_persists_radio_modes_and_exposes_them_in_payload() -> None:
    client = TestClient(app)

    updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "doctor",
            "dashboard_mode": "demo",
            "guided_mode": "free",
            "status": "configured",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["appointment_type"] == "doctor"
    assert body["metadata"]["ui_modes"]["dashboard_mode"] == "demo"
    assert body["metadata"]["ui_modes"]["guided_mode"] == "free"

    payload = client.get("/api/demo-monitoring/v1.3.9/payload?lang=en").json()
    assert payload["operator_panel"]["dashboard_mode"] == "demo"
    assert payload["operator_panel"]["guided_mode"] == "free"
    assert payload["operator_panel"]["selected_appointment_type"] == "doctor"
    assert payload["current_mode"]["dashboard_mode"] == "demo"
    assert payload["current_mode"]["guided_mode"] == "free"
    assert payload["current_mode"]["appointment_type"] == "doctor"


def test_demo_monitoring_v139_dashboard_plus_persists_manual_phone_target() -> None:
    client = TestClient(app)

    updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "contact_target_mode": "phone",
            "manual_phone_number": "+491701112233",
            "status": "configured",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["metadata"]["dashboard_plus"]["contact_target_mode"] == "phone"
    assert body["metadata"]["dashboard_plus"]["manual_phone_number"] == "+491701112233"

    payload = client.get("/api/demo-monitoring/v1.3.9/payload?lang=en").json()
    dashboard_plus = payload["operator_panel"]["dashboard_plus"]
    assert dashboard_plus["scenario_mode"] == "real"
    assert dashboard_plus["contact_target_mode"] == "phone"
    assert dashboard_plus["manual_phone_number"] == "+491701112233"
    assert dashboard_plus["selected_contact_phone"] == "+491701112233"
    assert dashboard_plus["validation"]["manual_phone_required"] is False


def test_demo_monitoring_v139_payload_keeps_real_digital_twin_message_contract() -> None:
    session = SessionLocal()
    try:
        DemoScenarioContextService(session).save_context(
            DemoScenarioContextUpdate(
                scenario_id="confirm-appointment",
                mode="real",
                address_id="addr-demo-001",
                appointment_id="appt-real-twin-001",
                booking_reference="book-real-twin-001",
                correlation_ref="corr-real-twin-001",
                current_step="reschedule_requested",
                status="action_requested",
                metadata={
                    "real_callback": {
                        "incoming_data": "reschedule_appointment",
                        "selected_action": "reschedule",
                        "button_state": "selected",
                    },
                    "customer_journey_message": {
                        "text": "Choose the preferred scheduling window.",
                        "actions": [
                            {"action_id": "reschedule", "label": "Reschedule", "value": "reschedule", "canonical_action": "appointment.reschedule_requested"},
                            {"action_id": "cancel", "label": "Cancel", "value": "cancel", "canonical_action": "appointment.cancel_requested"},
                        ],
                        "suggestion_buttons": [
                            {"action_id": "reschedule", "label": "Reschedule", "value": "reschedule", "canonical_action": "appointment.reschedule_requested"},
                            {"action_id": "cancel", "label": "Cancel", "value": "cancel", "canonical_action": "appointment.cancel_requested"},
                        ],
                        "real_channel_payload": {
                            "message_type": "suggestion_buttons",
                            "suggestions": [
                                {"label": "Reschedule", "value": "reschedule", "canonical_action": "appointment.reschedule_requested"},
                                {"label": "Cancel", "value": "cancel", "canonical_action": "appointment.cancel_requested"},
                            ],
                        },
                    },
                },
            )
        )
    finally:
        session.close()

    client = TestClient(app)
    payload = client.get("/api/demo-monitoring/v1.3.9/payload?lang=en").json()
    assert payload["messages_customer_journey"]["mode"] == "real"
    assert payload["messages_customer_journey"]["current_message"]["text"] == "Choose the preferred scheduling window."
    assert payload["messages_customer_journey"]["current_message"]["actions"]
    assert payload["messages_customer_journey"]["current_message"]["real_channel_payload"]["suggestions"]
    assert any(item.get("selected") for item in payload["messages_customer_journey"]["current_message"]["actions"])


def test_demo_monitoring_v139_help_route_lists_address_features() -> None:
    client = TestClient(app)

    payload = client.get("/api/demo-monitoring/v1.3.9/help").json()
    assert payload["version"] == "v1.3.10"
    assert payload["route_contract"]["demo_api_version"] == "v1.3.9"
    assert payload["route_contract"]["display_version"] == "v1.3.10"
    assert "address_database_menu_entry" in payload["integrated_features"]
    assert "cross_module_address_anchor" in payload["integrated_features"]
    assert "appointment_address_assignment_controls" in payload["integrated_features"]
    assert "scenario_runner_buttons" in payload["integrated_features"]
    assert "file_based_protocol_artifacts" in payload["integrated_features"]
    assert "unified_demo_scenario_context" in payload["integrated_features"]
    assert "address_aware_google_generation" in payload["integrated_features"]

    payload_patch = client.get("/api/demo-monitoring/v1.3.9-patch1/help")
    assert payload_patch.status_code == 200
    assert payload_patch.json()["version"] == "v1.3.10"
    assert payload_patch.json()["route_contract"] == payload["route_contract"]

    payload_patch2 = client.get("/api/demo-monitoring/v1.3.9-patch2/help")
    assert payload_patch2.status_code == 200
    assert payload_patch2.json()["route_contract"] == payload["route_contract"]

    payload_patch3 = client.get("/api/demo-monitoring/v1.3.9-patch3/help")
    assert payload_patch3.status_code == 200
    assert payload_patch3.json()["route_contract"] == payload["route_contract"]

    payload_patch4 = client.get("/api/demo-monitoring/v1.3.9-patch4/help")
    assert payload_patch4.status_code == 200
    assert payload_patch4.json()["route_contract"] == payload["route_contract"]

    payload_patch5 = client.get("/api/demo-monitoring/v1.3.9-patch5/help")
    assert payload_patch5.status_code == 200
    assert payload_patch5.json()["route_contract"] == payload["route_contract"]

    payload_patch6 = client.get("/api/demo-monitoring/v1.3.9-patch6/help")
    assert payload_patch6.status_code == 200
    assert payload_patch6.json()["route_contract"] == payload["route_contract"]

    payload_patch7 = client.get("/api/demo-monitoring/v1.3.9-patch7/help")
    assert payload_patch7.status_code == 200
    assert payload_patch7.json()["route_contract"] == payload["route_contract"]

    payload_patch8 = client.get("/api/demo-monitoring/v1.3.9-patch8/help")
    assert payload_patch8.status_code == 200
    assert payload_patch8.json()["route_contract"] == payload["route_contract"]


def test_demo_monitoring_v139_exposes_and_updates_unified_scenario_context() -> None:
    client = TestClient(app)

    current = client.get("/api/demo-monitoring/v1.3.9/scenario-context")
    assert current.status_code == 200
    body = current.json()
    assert body["version"] == "v1.3.10"
    assert body["address_id"]
    assert body["selected_address"]["address_id"] == body["address_id"]

    updated = client.put(
        "/api/demo-monitoring/v1.3.9/scenario-context",
        json={
            "scenario_id": "this-week",
            "mode": "real",
            "address_id": "addr-demo-001",
            "appointment_type": "wallbox",
            "from_date": "2026-05-10",
            "to_date": "2026-05-18",
            "status": "configured",
        },
    )
    assert updated.status_code == 200
    updated_body = updated.json()
    assert updated_body["scenario_id"] == "this-week"
    assert updated_body["mode"] == "real"
    assert updated_body["appointment_type"] == "wallbox"


def test_demo_monitoring_v139_can_run_simulation_scenario_and_expose_artifacts() -> None:
    client = TestClient(app)

    run_response = client.post(
        "/api/demo-monitoring/v1.3.9/scenario-testing/run",
        json={"scenario_id": "confirm-appointment", "mode": "simulation", "lang": "en", "address_id": "addr-demo-001"},
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["scenario_id"] == "confirm-appointment"
    assert payload["mode"] == "simulation"
    assert payload["actual"]["action"] == "appointment.confirm_requested"
    assert payload["status"] == "passed"
    assert payload["address_id"] == "addr-demo-001"
    assert payload["selected_address"]["display_name"] == "Anna Berger"

    latest = client.get("/api/demo-monitoring/v1.3.9/scenario-testing/latest")
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["available"] is True
    assert latest_payload["scenario_id"] == "confirm-appointment"

    protocol = client.get("/api/demo-monitoring/v1.3.9/scenario-testing/artifacts/latest/protocol")
    assert protocol.status_code == 200
    assert "Scenario Test Protocol" in protocol.text


def test_demo_monitoring_v139_can_run_real_scenario_without_external_failure() -> None:
    client = TestClient(app)

    class DummyResponse:
        def __init__(self, status_code: int, text: str = "{}") -> None:
            self.status_code = status_code
            self.text = text

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url, headers=None, json=None):
            if url.endswith("/seturl"):
                return DummyResponse(200, '{"configured": true}')
            return DummyResponse(202, '{"accepted": true}')

    import lekab_adapter.v1_2_1_patch4.lekab_adapter.service as lekab_patch4_service

    original_client = lekab_patch4_service.httpx.Client
    lekab_patch4_service.httpx.Client = DummyClient
    try:
        run_response = client.post(
            "/api/demo-monitoring/v1.3.9/scenario-testing/run",
            json={
                "scenario_id": "next-month",
                "mode": "real",
                "lang": "en",
                "address_id": "addr-demo-001",
                "appointment_type": "dentist",
                "contact_target_mode": "phone",
                "manual_phone_number": "+491709998877",
            },
        )
    finally:
        lekab_patch4_service.httpx.Client = original_client

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["mode"] == "real"
    assert payload["selected_address"]["phone"] == "+491709998877"
    assert payload["actual"]["action"] is None
    assert payload["actual"]["state"] == "waiting_for_real_callback"
    assert payload["status"] == "waiting_for_callback"
    assert payload["steps"][0]["payload"]["suggestion_buttons"]
    assert payload["steps"][0]["payload"]["real_channel_payload"]["provider_request_preview"]["json"]["richMessage"]["suggestions"]
    first_suggestion = payload["steps"][0]["payload"]["real_channel_payload"]["provider_request_preview"]["json"]["richMessage"]["suggestions"][0]
    assert "reply" in first_suggestion
    assert first_suggestion["reply"]["text"]
    assert first_suggestion["reply"]["postbackData"]


def test_demo_monitoring_v139_dashboard_plus_real_run_requires_manual_phone() -> None:
    client = TestClient(app)

    run_response = client.post(
        "/api/demo-monitoring/v1.3.9/scenario-testing/run",
        json={
            "scenario_id": "confirm-appointment",
            "mode": "real",
            "lang": "en",
            "address_id": "addr-demo-001",
            "appointment_type": "dentist",
            "contact_target_mode": "phone",
            "manual_phone_number": "",
        },
    )
    assert run_response.status_code == 400
    assert run_response.json()["detail"]["message"] == "No mobile number entered for Dashboard+ phone mode."
