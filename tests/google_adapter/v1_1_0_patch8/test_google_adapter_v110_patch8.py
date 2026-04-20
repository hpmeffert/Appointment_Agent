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
    created = None
    conflict = None
    for slot_id, day_offset in (
        ("slot-1", 60),
        ("slot-1b", 61),
        ("slot-1c", 62),
        ("slot-1d", 63),
        ("slot-1e", 64),
    ):
        start_time, end_time, label = _unique_slot_window(day_offset=day_offset)
        create_response = client.post(
            "/api/google/v1.1.0-patch8/booking/create",
            json={
                "mode": "simulation",
                "slot_id": slot_id,
                "start_time": start_time,
                "end_time": end_time,
                "label": label,
                "appointment_type": "dentist",
                "customer_name": "Anna Becker",
            },
        )
        if create_response.status_code != 200:
            continue

        created = create_response.json()
        if created.get("success") is not True:
            continue

        conflict_response = client.post(
            "/api/google/v1.1.0-patch8/availability/check",
            json={
                "mode": "simulation",
                "start_time": start_time,
                "end_time": end_time,
                "alternative_count": 2,
            },
        )
        if conflict_response.status_code != 200:
            continue

        conflict = conflict_response.json()
        if conflict.get("conflict_detected") and conflict.get("alternative_slots"):
            break

    assert created is not None
    assert created["success"] is True
    assert created["status"] == "confirmed"
    assert conflict is not None
    assert conflict["slot_available"] is False
    assert conflict["conflict_detected"] is True
    assert conflict["alternative_slots"]
    assert "slot.conflict_detected" in conflict["monitoring_labels"]


def test_google_v110_patch8_reschedule_and_cancel_booking() -> None:
    client = TestClient(app)
    new_start_time, new_end_time, new_label = _unique_slot_window(day_offset=71)

    create_response = None
    for slot_id, day_offset in (
        ("slot-2", 70),
        ("slot-2b", 71),
        ("slot-2c", 72),
        ("slot-2d", 73),
    ):
        start_time, end_time, label = _unique_slot_window(day_offset=day_offset)
        create_response = client.post(
            "/api/google/v1.1.0-patch8/booking/create",
            json={
                "mode": "simulation",
                "slot_id": slot_id,
                "start_time": start_time,
                "end_time": end_time,
                "label": label,
                "appointment_type": "wallbox",
                "customer_name": "Julia Hoffmann",
            },
        )
        if create_response.status_code == 200 and create_response.json().get("success") is True:
            break

    assert create_response is not None
    assert create_response.status_code == 200
    assert create_response.json()["success"] is True
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

    if reschedule_response.status_code == 200 and reschedule_response.json().get("success") is not True:
        retry_start_time, retry_end_time, retry_label = _unique_slot_window(day_offset=72)
        reschedule_response = client.post(
            "/api/google/v1.1.0-patch8/booking/reschedule",
            json={
                "mode": "simulation",
                "booking_reference": booking_reference,
                "provider_reference": provider_reference,
                "slot_id": "slot-4",
                "start_time": retry_start_time,
                "end_time": retry_end_time,
                "label": retry_label,
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
