from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_google_v136_demo_calendar_routes_support_patch7_actions() -> None:
    client = TestClient(app)

    payload = {
        "mode": "simulation",
        "from_date": "2026-03-29",
        "to_date": "2026-04-03",
        "appointment_type": "wallbox",
        "count": 2,
        "linked_address_id": "addr-demo-001",
        "linked_address_name": "Anna Berger",
        "linked_contact_phone": "491705707716",
        "linked_contact_email": "anna.berger@example.com",
        "linked_correlation_ref": "corr-addr-demo-001",
        "linked_contact_reference_id": "addr-demo-001",
        "linked_address_full_details": "Anna Berger | Musterstrasse 5 | 10115 Berlin | Phone: 491705707716 | Email: anna.berger@example.com",
    }

    prepare = client.post("/api/google/v1.3.6/demo-calendar/prepare-preview", json=payload)
    assert prepare.status_code == 200
    assert prepare.json()["action"] == "prepare"
    assert prepare.json()["preview_only"] is True

    generate = client.post("/api/google/v1.3.6/demo-calendar/generate", json=payload)
    assert generate.status_code == 200
    body = generate.json()
    assert body["action"] == "generate"
    assert body["generated_count"] == 2
    assert body["items"][0]["title"] == "Wallbox Check – Anna Berger"
    assert body["items"][0]["details"]["linked_contact_reference_id"] == "addr-demo-001"
    assert "Musterstrasse 5" in body["items"][0]["details"]["linked_address_full_details"]
    assert body["items"][0]["details"]["title_strategy"] == "appointment_type_plus_selected_address"
    assert "Address:" in body["items"][0]["details"]["description"]
    assert "Context:" in body["items"][0]["details"]["description"]

    delete = client.post("/api/google/v1.3.6/demo-calendar/delete", json=payload)
    assert delete.status_code == 200
    assert delete.json()["action"] == "delete"

    reset = client.post("/api/google/v1.3.6/demo-calendar/reset", json=payload)
    assert reset.status_code == 200
    assert reset.json()["action"] == "reset"


def test_google_v136_demo_calendar_route_rejects_invalid_date_range() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.3.6/demo-calendar/generate",
        json={
            "mode": "simulation",
            "from_date": "2026-04-05",
            "to_date": "2026-04-01",
            "appointment_type": "dentist",
            "count": 1,
        },
    )

    assert response.status_code == 422
