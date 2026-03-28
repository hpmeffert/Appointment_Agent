from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_google_contact_resolution_and_booking() -> None:
    client = TestClient(app)

    upsert = client.post(
        "/api/google/v1.0.0/contacts/upsert",
        json={
            "tenant_id": "demo",
            "customer_id": "C-100",
            "full_name": "Ada Lovelace",
            "phone": "+4912345",
            "email": "ada@example.com",
        },
    )
    assert upsert.status_code == 200

    resolve = client.post(
        "/api/google/v1.0.0/contacts/resolve",
        json={"tenant_id": "demo", "phone": "+4912345"},
    )
    assert resolve.status_code == 200
    assert resolve.json()["customer_id"] == "C-100"

    booking = client.post(
        "/api/google/v1.0.0/bookings",
        json={
            "tenant_id": "demo",
            "journey_id": "journey-1",
            "customer_id": "C-100",
            "slot_id": "gslot-1",
            "calendar_target": "advisor@example.com",
            "title": "Appointment",
            "description": "Prototype booking",
            "timezone": "Europe/Berlin",
        },
    )
    assert booking.status_code == 200
    assert booking.json()["provider"] == "google"
