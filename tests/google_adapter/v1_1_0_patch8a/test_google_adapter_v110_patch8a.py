from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.main import app
from appointment_agent_shared.models import SlotHoldRecord


def _future_date_range(day_offset: int = 90) -> tuple[str, str]:
    start_day = (datetime.now(timezone.utc) + timedelta(days=day_offset)).date()
    end_day = start_day + timedelta(days=1)
    return start_day.isoformat(), end_day.isoformat()


def _first_available_slot(client: TestClient, base_path: str, *, day_offset: int) -> dict:
    """Find a slot in a future window even if earlier tests already reserved one."""

    for offset in range(day_offset, day_offset + 15):
        from_date, to_date = _future_date_range(day_offset=offset)
        response = client.post(
            f"{base_path}/availability/slots",
            json={"mode": "simulation", "from_date": from_date, "to_date": to_date, "max_slots": 3},
        )
        assert response.status_code == 200
        slots = response.json()["slots"]
        if slots:
            return slots[0]
    raise AssertionError("No simulation slot was available in the checked date windows.")


def test_google_v110_patch8a_hold_hides_slot_and_blocks_parallel_hold() -> None:
    client = TestClient(app)
    from_date, to_date = _future_date_range()

    slots_response = client.post(
        "/api/google/v1.1.0-patch8a/availability/slots",
        json={"mode": "simulation", "from_date": from_date, "to_date": to_date, "max_slots": 3},
    )
    assert slots_response.status_code == 200
    original_slot = slots_response.json()["slots"][0]

    hold_response = client.post(
        "/api/google/v1.1.0-patch8a/slot-hold/create",
        json={
            "mode": "simulation",
            "journey_id": "journey-p8a-a",
            "customer_id": "customer-a",
            "slot_id": original_slot["slot_id"],
            "start_time": original_slot["start"],
            "end_time": original_slot["end"],
            "slot_label": original_slot["label"],
        },
    )
    assert hold_response.status_code == 200
    created_hold = hold_response.json()
    assert created_hold["success"] is True
    assert created_hold["hold_duration_minutes"] == 2
    assert "slot.hold.created" in created_hold["monitoring_labels"]

    blocked_response = client.post(
        "/api/google/v1.1.0-patch8a/slot-hold/create",
        json={
            "mode": "simulation",
            "journey_id": "journey-p8a-b",
            "customer_id": "customer-b",
            "slot_id": original_slot["slot_id"],
            "start_time": original_slot["start"],
            "end_time": original_slot["end"],
            "slot_label": original_slot["label"],
        },
    )
    assert blocked_response.status_code == 200
    blocked = blocked_response.json()
    assert blocked["success"] is False
    assert blocked["technical_reason"] == "slot.temporarily_reserved"

    filtered_response = client.post(
        "/api/google/v1.1.0-patch8a/availability/slots",
        json={"mode": "simulation", "from_date": from_date, "to_date": to_date, "max_slots": 3},
    )
    assert filtered_response.status_code == 200
    filtered = filtered_response.json()
    assert all(slot["slot_id"] != original_slot["slot_id"] for slot in filtered["slots"])
    assert "slot.hold.filtered" in filtered["monitoring_labels"]


def test_google_v110_patch8a_booking_requires_active_matching_hold() -> None:
    client = TestClient(app)
    slot = _first_available_slot(client, "/api/google/v1.1.0-patch8a", day_offset=95)

    hold_response = client.post(
        "/api/google/v1.1.0-patch8a/slot-hold/create",
        json={
            "mode": "simulation",
            "journey_id": "journey-p8a-book",
            "customer_id": "customer-book",
            "slot_id": slot["slot_id"],
            "start_time": slot["start"],
            "end_time": slot["end"],
            "slot_label": slot["label"],
        },
    )
    hold = hold_response.json()

    booking_response = client.post(
        "/api/google/v1.1.0-patch8a/booking/create",
        json={
            "journey_id": "journey-p8a-book",
            "hold_id": hold["hold_id"],
            "booking": {
                "mode": "simulation",
                "slot_id": slot["slot_id"],
                "start_time": slot["start"],
                "end_time": slot["end"],
                "label": slot["label"],
                "appointment_type": "dentist",
                "customer_name": "Anna Becker",
            },
        },
    )
    assert booking_response.status_code == 200
    booking = booking_response.json()
    assert booking["success"] is True
    assert booking["status"] == "confirmed"
    assert "slot.hold.consumed" in booking["monitoring_labels"]


def test_google_v110_patch8a_expired_hold_blocks_booking() -> None:
    client = TestClient(app)
    slot = _first_available_slot(client, "/api/google/v1.1.0-patch8a", day_offset=100)

    hold_response = client.post(
        "/api/google/v1.1.0-patch8a/slot-hold/create",
        json={
            "mode": "simulation",
            "journey_id": "journey-p8a-expired",
            "customer_id": "customer-expired",
            "slot_id": slot["slot_id"],
            "start_time": slot["start"],
            "end_time": slot["end"],
            "slot_label": slot["label"],
            "hold_duration_minutes": 2,
        },
    )
    hold_id = hold_response.json()["hold_id"]

    with SessionLocal() as session:
        record = session.scalar(select(SlotHoldRecord).where(SlotHoldRecord.hold_id == hold_id))
        assert record is not None
        record.expires_at_utc = datetime.utcnow() - timedelta(minutes=1)
        session.commit()

    booking_response = client.post(
        "/api/google/v1.1.0-patch8a/booking/create",
        json={
            "journey_id": "journey-p8a-expired",
            "hold_id": hold_id,
            "booking": {
                "mode": "simulation",
                "slot_id": slot["slot_id"],
                "start_time": slot["start"],
                "end_time": slot["end"],
                "label": slot["label"],
                "appointment_type": "wallbox",
                "customer_name": "Julia Hoffmann",
            },
        },
    )
    assert booking_response.status_code == 200
    booking = booking_response.json()
    assert booking["success"] is False
    assert booking["status"] == "hold_expired"
    assert booking["technical_reason"] == "slot.hold.expired"
