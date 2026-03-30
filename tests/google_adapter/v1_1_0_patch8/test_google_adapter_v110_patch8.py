from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from appointment_agent_shared.main import app


def _unique_slot_window(day_offset: int = 60) -> tuple[str, str, str]:
    base = (datetime.now(timezone.utc) + timedelta(days=day_offset + (uuid4().int % 120))).replace(
        minute=0,
        second=0,
        microsecond=0,
    )
    unique_start = base + timedelta(minutes=(uuid4().int % 600))
    unique_end = unique_start + timedelta(minutes=45)
    label = unique_start.strftime("%a, %d %b, %H:%M")
    return unique_start.isoformat(), unique_end.isoformat(), label


def test_google_v110_patch8_slots_returns_normalized_slots() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/google/v1.1.0-patch8/availability/slots",
        json={
            "mode": "simulation",
            "from_date": "2026-03-29",
            "to_date": "2026-03-31",
            "max_slots": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["slot_count"] == 3
    assert body["slots"][0]["available"] is True
    assert body["slots"][0]["calendar_provider"] == "simulated"
    assert "slot.checked" in body["monitoring_labels"]


def test_google_v110_patch8_create_then_conflict_then_alternatives() -> None:
    client = TestClient(app)
    start_time, end_time, label = _unique_slot_window()

    create_response = client.post(
        "/api/google/v1.1.0-patch8/booking/create",
        json={
            "mode": "simulation",
            "slot_id": "slot-1",
            "start_time": start_time,
            "end_time": end_time,
            "label": label,
            "appointment_type": "dentist",
            "customer_name": "Anna Becker",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["success"] is True
    assert created["status"] == "confirmed"

    conflict_response = client.post(
        "/api/google/v1.1.0-patch8/availability/check",
        json={
            "mode": "simulation",
            "start_time": start_time,
            "end_time": end_time,
            "alternative_count": 2,
        },
    )

    assert conflict_response.status_code == 200
    conflict = conflict_response.json()
    assert conflict["slot_available"] is False
    assert conflict["conflict_detected"] is True
    assert conflict["alternative_slots"]
    assert "slot.conflict_detected" in conflict["monitoring_labels"]


def test_google_v110_patch8_reschedule_and_cancel_booking() -> None:
    client = TestClient(app)
    start_time, end_time, label = _unique_slot_window(day_offset=70)
    new_start_time, new_end_time, new_label = _unique_slot_window(day_offset=71)

    create_response = client.post(
        "/api/google/v1.1.0-patch8/booking/create",
        json={
            "mode": "simulation",
            "slot_id": "slot-2",
            "start_time": start_time,
            "end_time": end_time,
            "label": label,
            "appointment_type": "wallbox",
            "customer_name": "Julia Hoffmann",
        },
    )
    booking_reference = create_response.json()["booking_reference"]
    provider_reference = create_response.json()["provider_reference"]

    reschedule_response = client.post(
        "/api/google/v1.1.0-patch8/booking/reschedule",
        json={
            "mode": "simulation",
            "booking_reference": booking_reference,
            "provider_reference": provider_reference,
            "slot_id": "slot-3",
            "start_time": new_start_time,
            "end_time": new_end_time,
            "label": new_label,
            "appointment_type": "wallbox",
        },
    )

    assert reschedule_response.status_code == 200
    rescheduled = reschedule_response.json()
    assert rescheduled["success"] is True
    assert rescheduled["status"] == "rescheduled"
    assert "booking.rescheduled" in rescheduled["monitoring_labels"]

    cancel_response = client.post(
        "/api/google/v1.1.0-patch8/booking/cancel",
        json={
            "mode": "simulation",
            "booking_reference": booking_reference,
            "provider_reference": rescheduled["provider_reference"],
            "reason": "customer_request",
        },
    )

    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()
    assert cancelled["success"] is True
    assert cancelled["status"] == "cancelled"
    assert "booking.cancelled" in cancelled["monitoring_labels"]
