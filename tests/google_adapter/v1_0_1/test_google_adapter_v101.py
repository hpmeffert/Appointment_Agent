from uuid import uuid4

from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def test_google_v101_contact_resolution_and_lifecycle() -> None:
    client = TestClient(app)
    booking_reference = "gbook-{}".format(uuid4().hex[:8])

    upsert = client.post(
        "/api/google/v1.0.1/contacts/upsert",
        json={
            "tenant_id": "demo",
            "customer_id": "C-300",
            "full_name": "Grace Hopper",
            "phone": "+498765",
            "email": "grace@example.com",
        },
    )
    assert upsert.status_code == 200

    resolve = client.post(
        "/api/google/v1.0.1/contacts/resolve",
        json={"tenant_id": "demo", "phone": "+498765"},
    )
    assert resolve.status_code == 200
    assert resolve.json()["customer_id"] == "C-300"

    slots = client.post(
        "/api/google/v1.0.1/slots",
        json={
            "tenant_id": "demo",
            "journey_id": "journey-google-1",
            "customer_id": "C-300",
            "service_type": "consultation",
            "duration_minutes": 30,
            "date_window_start": "2026-03-28T00:00:00+01:00",
            "date_window_end": "2026-03-30T23:59:59+01:00",
            "timezone": "Europe/Berlin",
            "resource_candidates": ["advisor@example.com"],
        },
    )
    assert slots.status_code == 200
    assert slots.json()[0]["provider"] == "google"

    created = client.post(
        "/api/google/v1.0.1/bookings",
        json={
            "tenant_id": "demo",
            "journey_id": "journey-google-1",
            "customer_id": "C-300",
            "booking_reference": booking_reference,
            "slot_id": slots.json()[0]["slot_id"],
            "calendar_target": "advisor@example.com",
            "title": "Appointment",
            "description": "Provider lifecycle test",
            "timezone": "Europe/Berlin",
        },
    )
    assert created.status_code == 200
    assert created.json()["provider_reference"].startswith("google-")

    updated = client.patch(
        "/api/google/v1.0.1/bookings",
        json={
            "booking_reference": booking_reference,
            "provider_reference": created.json()["provider_reference"],
            "new_start": "2026-03-29T10:00:00+01:00",
            "new_end": "2026-03-29T10:30:00+01:00",
            "new_title": "Updated Appointment",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "RESCHEDULED"

    fetched = client.get("/api/google/v1.0.1/bookings/{}".format(booking_reference))
    assert fetched.status_code == 200
    assert fetched.json()["provider_reference"] == created.json()["provider_reference"]

    cancelled = client.post(
        "/api/google/v1.0.1/bookings/cancel",
        json={
            "booking_reference": booking_reference,
            "provider_reference": created.json()["provider_reference"],
            "reason": "customer_request",
            "requested_by": "customer",
        },
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"


def test_google_v101_update_missing_provider_reference() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.patch(
        "/api/google/v1.0.1/bookings",
        json={
            "booking_reference": "missing-booking",
            "provider_reference": "",
        },
    )

    assert response.status_code >= 400


def test_google_v101_cancel_missing_booking() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/google/v1.0.1/bookings/cancel",
        json={
            "booking_reference": "missing-booking",
            "provider_reference": "google-missing",
        },
    )

    assert response.status_code == 404
