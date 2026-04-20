from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def _future_date_range(day_offset: int = 120) -> tuple[str, str]:
    start_day = (datetime.now(timezone.utc) + timedelta(days=day_offset)).date()
    end_day = start_day + timedelta(days=1)
    return start_day.isoformat(), end_day.isoformat()


def _first_available_slot(client: TestClient, *, day_offset: int) -> dict:
    for offset in range(day_offset, day_offset + 15):
        from_date, to_date = _future_date_range(day_offset=offset)
        response = client.post(
            "/api/google/v1.1.0-patch8b/availability/slots",
            json={"mode": "simulation", "from_date": from_date, "to_date": to_date, "max_slots": 3},
        )
        assert response.status_code == 200
        slots = response.json()["slots"]
        if slots:
            return slots[0]
    raise AssertionError("No patch8b simulation slot was available.")


def test_google_v110_patch8b_booking_after_hold_exposes_revalidation_labels() -> None:
    client = TestClient(app)
    slot = _first_available_slot(client, day_offset=120)

    hold_response = client.post(
        "/api/google/v1.1.0-patch8b/slot-hold/create",
        json={
            "mode": "simulation",
            "journey_id": "journey-p8b",
            "customer_id": "customer-p8b",
            "slot_id": slot["slot_id"],
            "start_time": slot["start"],
            "end_time": slot["end"],
            "slot_label": slot["label"],
            "hold_duration_minutes": 2,
        },
    )
    assert hold_response.status_code == 200
    hold = hold_response.json()

    booking_response = client.post(
        "/api/google/v1.1.0-patch8b/booking/create",
        json={
            "journey_id": "journey-p8b",
            "hold_id": hold["hold_id"],
            "booking": {
                "mode": "simulation",
                "slot_id": slot["slot_id"],
                "start_time": slot["start"],
                "end_time": slot["end"],
                "label": slot["label"],
                "appointment_type": "dentist",
                "customer_name": "Patch 8b Tester",
            },
        },
    )

    assert booking_response.status_code == 200
    body = booking_response.json()
    assert body["success"] is True
    assert "booking.revalidation.started" in body["monitoring_labels"]
    assert "booking.revalidation.succeeded" in body["monitoring_labels"]
