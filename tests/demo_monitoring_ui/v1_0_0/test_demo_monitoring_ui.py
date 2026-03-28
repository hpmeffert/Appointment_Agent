from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_demo_ui_page_loads() -> None:
    client = TestClient(app)

    response = client.get("/ui/demo-monitoring/v1.0.0")

    assert response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.0.0" in response.text
    assert "Combined" in response.text
    assert "Monitoring Mode" in response.text
    assert "?" in response.text


def test_demo_ui_scenario_payload_contains_required_scenarios() -> None:
    client = TestClient(app)

    response = client.get("/api/demo-monitoring/v1.0.0/scenarios")

    assert response.status_code == 200
    payload = response.json()
    scenario_ids = [scenario["id"] for scenario in payload["scenarios"]]
    assert "standard-booking" in scenario_ids
    assert "reschedule" in scenario_ids
    assert "cancellation" in scenario_ids
    assert "no-slot-escalation" in scenario_ids
    assert "provider-failure" in scenario_ids


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
    assert user_response.status_code == 200
    assert "Language: DE" in user_response.text
    assert admin_response.status_code == 200
    assert "Admin Guide" in admin_response.text


def test_demo_ui_v102_release_routes_are_available() -> None:
    client = TestClient(app)

    ui_response = client.get("/ui/demo-monitoring/v1.0.2")
    help_response = client.get("/api/demo-monitoring/v1.0.2/help")
    scenarios_response = client.get("/api/demo-monitoring/v1.0.2/scenarios")

    assert ui_response.status_code == 200
    assert "Appointment Agent Demo + Monitoring v1.0.2" in ui_response.text
    assert "/api/demo-monitoring/v1.0.2/scenarios" in ui_response.text

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.0.2"

    assert scenarios_response.status_code == 200
    assert "scenarios" in scenarios_response.json()
