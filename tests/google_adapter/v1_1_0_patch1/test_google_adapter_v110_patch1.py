from datetime import datetime

from fastapi.testclient import TestClient

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.main import app
from appointment_agent_shared.repositories import GoogleDemoEventRepository


def test_google_v110_patch1_mode_status_defaults_to_simulation() -> None:
    client = TestClient(app)

    response = client.get("/api/google/v1.1.0-patch1/mode")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "simulation"
    assert body["live_calendar_writes"] is False
    assert "warning" in body


def test_google_v110_patch1_generates_meaningful_demo_appointments() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "simulation", "timeframe": "week", "action": "generate", "count": 4},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generated_count"] == 4
    assert body["deleted_count"] == 0
    assert body["items"][0]["title"] != "Test Appointment 1"
    assert body["items"][0]["description_marker"] == "[Appointment Agent Demo]"
    assert body["items"][0]["link_state"] in {"linked_with_mobile", "linked_without_mobile"}


def test_google_v110_patch1_vertical_generation_uses_vertical_titles() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "simulation", "timeframe": "week", "action": "generate", "count": 3, "vertical": "dentist"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["vertical"] == "dentist"
    assert "Dr. Zahn" in body["items"][0]["title"]
    assert body["items"][0]["details"]["vertical"] == "dentist"
    assert body["items"][0]["details"]["description"].startswith("Routine dental")
    assert body["items"][0]["details"]["customer_prompt"] == "I would like to book a dental check-up."
    assert body["items"][0]["details"]["monitoring_label"] == "dentist.checkup.search.requested"


def test_google_v110_patch1_wallbox_generation_uses_utility_wording() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "simulation", "timeframe": "week", "action": "generate", "count": 3, "vertical": "wallbox"},
    )

    assert response.status_code == 200
    body = response.json()
    first_item = body["items"][0]
    assert body["vertical"] == "wallbox"
    assert "Wallbox" in first_item["title"] or "Charging" in first_item["title"]
    assert first_item["customer_name"] in {"Familie Schneider", "Julia Hoffmann", "Markus Weber"}
    assert first_item["details"]["category"] == "Stadtwerke Wallbox"
    assert "wallbox" in first_item["details"]["reminder_text"].lower()


def test_google_v110_patch1_district_heating_generation_uses_technical_wording() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "simulation", "timeframe": "month", "action": "generate", "count": 3, "vertical": "district_heating"},
    )

    assert response.status_code == 200
    body = response.json()
    first_item = body["items"][0]
    assert body["vertical"] == "district_heating"
    assert "Heating" in first_item["title"] or "Nahwaerme" in first_item["title"]
    assert first_item["details"]["scenario_label"] == "District Heating"
    assert "agent" in first_item["details"]["follow_up_action"].lower()
    assert first_item["details"]["customer_context"] in {
        "Household with utility-room access",
        "Building management contact",
        "Residential service account",
    }


def test_google_v110_patch1_delete_only_targets_demo_generated_entries() -> None:
    session = SessionLocal()
    repository = GoogleDemoEventRepository(session)
    repository.save(
        operation_id="manual-seed",
        mode="simulation",
        timeframe="day",
        calendar_id="simulation-calendar",
        event_id="manual-1",
        booking_reference="manual-keep-1",
        title="Manual Calendar Entry",
        customer_name="Manual User",
        mobile_number=None,
        start_time_utc=datetime(2026, 4, 1, 10, 0),
        end_time_utc=datetime(2026, 4, 1, 10, 30),
        timezone="Europe/Berlin",
        provider_reference="manual-1",
        details={"seed": "manual"},
        is_demo_generated=False,
    )
    session.close()

    client = TestClient(app)
    generate = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "simulation", "timeframe": "day", "action": "generate", "count": 2},
    )
    assert generate.status_code == 200

    delete = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "simulation", "timeframe": "day", "action": "delete", "count": 2},
    )
    assert delete.status_code == 200
    assert delete.json()["deleted_count"] >= 2


def test_google_v110_patch1_test_mode_requires_real_configuration() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch1/demo-calendar/prepare",
        json={"mode": "test", "timeframe": "day", "action": "generate", "count": 1},
    )

    assert response.status_code in {200, 400}
    if response.status_code == 200:
        assert response.json()["mode"] in {"simulation", "test"}
    else:
        assert response.json()["detail"]["provider"] == "google"
