from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_address_database_v139_create_list_update_delete_flow() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/addresses/v1.3.9",
        json={
            "display_name": "Anna Berger",
            "city": "Berlin",
            "email": "anna@example.com",
            "phone": "+491701234567",
            "preferred_channel": "rcs_sms",
        },
    )
    assert created.status_code == 200
    address = created.json()
    assert address["display_name"] == "Anna Berger"
    assert address["is_active"] is True
    assert address["timezone"] == "Europe/Berlin"

    listed = client.get("/api/addresses/v1.3.9?q=Anna")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    updated = client.put(
        f"/api/addresses/v1.3.9/{address['address_id']}",
        json={
            "display_name": "Anna Berger Updated",
            "city": "Hamburg",
            "email": "anna.updated@example.com",
            "phone": "+491701234567",
            "timezone": "Europe/Berlin",
            "preferred_channel": "email",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Anna Berger Updated"
    assert updated.json()["city"] == "Hamburg"
    assert updated.json()["timezone"] == "Europe/Berlin"

    deactivated = client.delete(f"/api/addresses/v1.3.9/{address['address_id']}")
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False


def test_address_database_v139_linkage_visible() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/addresses/v1.3.9",
        json={"display_name": "Linked Address", "city": "Munich", "phone": "+491700000001"},
    )
    address_id = created.json()["address_id"]

    linked = client.post(
        "/api/addresses/v1.3.9/link-to-appointment",
        json={
            "address_id": address_id,
            "appointment_external_id": "appt-123",
            "booking_reference": "book-123",
            "calendar_ref": "gcal-123",
        },
    )
    assert linked.status_code == 200
    assert linked.json()["appointment_external_id"] == "appt-123"

    links = client.get(f"/api/addresses/v1.3.9/{address_id}/links")
    assert links.status_code == 200
    payload = links.json()
    assert payload["version"] == "v1.3.9"
    assert len(payload["links"]) == 1
    assert payload["links"][0]["calendar_ref"] == "gcal-123"

    appointment_links = client.get("/api/addresses/v1.3.9/appointment-links/appt-123")
    assert appointment_links.status_code == 200
    appointment_payload = appointment_links.json()
    assert appointment_payload["version"] == "v1.3.9"
    assert appointment_payload["links"][0]["address_id"] == address_id
    assert appointment_payload["links"][0]["address_summary"]["display_name"] == "Linked Address"
