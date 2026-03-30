from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from appointment_agent_shared.main import app


def _future_date_range(day_offset: int = 150) -> tuple[str, str]:
    start_day = (datetime.now(timezone.utc) + timedelta(days=day_offset)).date()
    end_day = start_day + timedelta(days=1)
    return start_day.isoformat(), end_day.isoformat()


def test_google_v120_booking_after_hold_exposes_release_route() -> None:
    client = TestClient(app)
    from_date, to_date = _future_date_range()

    slots_response = client.post(
        "/api/google/v1.2.0/availability/slots",
        json={"mode": "simulation", "from_date": from_date, "to_date": to_date, "max_slots": 1},
    )
    assert slots_response.status_code == 200
    slot = slots_response.json()["slots"][0]

    hold_response = client.post(
        "/api/google/v1.2.0/slot-hold/create",
        json={
            "mode": "simulation",
            "journey_id": "journey-v120",
            "customer_id": "customer-v120",
            "slot_id": slot["slot_id"],
            "start_time": slot["start"],
            "end_time": slot["end"],
            "slot_label": slot["label"],
        },
    )
    assert hold_response.status_code == 200
    hold = hold_response.json()

    booking_response = client.post(
        "/api/google/v1.2.0/booking/create",
        json={
            "journey_id": "journey-v120",
            "hold_id": hold["hold_id"],
            "booking": {
                "mode": "simulation",
                "slot_id": slot["slot_id"],
                "start_time": slot["start"],
                "end_time": slot["end"],
                "label": slot["label"],
                "appointment_type": "dentist",
                "customer_name": "Release Tester",
            },
        },
    )

    assert booking_response.status_code == 200
    body = booking_response.json()
    assert body["success"] is True
    assert "booking.revalidation.started" in body["monitoring_labels"]
