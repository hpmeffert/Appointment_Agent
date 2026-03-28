from fastapi.testclient import TestClient
from uuid import uuid4

from appointment_agent_shared.main import app


def test_orchestrator_plans_and_confirms_journey() -> None:
    client = TestClient(app)
    journey_id = f"journey-{uuid4().hex[:8]}"
    correlation_id = f"corr-{uuid4().hex[:8]}"

    start = client.post(
        "/api/orchestrator/v1.0.0/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-100",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
            "resource_candidates": ["advisor@example.com"],
            "preferences": {
                "earliest_date": "2026-03-28T00:00:00+01:00",
                "latest_date": "2026-03-30T23:59:59+01:00",
            },
        },
    )
    assert start.status_code == 200
    assert start.json()["journey_state"] == "WAITING_FOR_SELECTION"
    assert start.json()["journey_id"] == journey_id

    select = client.post(
        "/api/orchestrator/v1.0.0/journeys/select",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "slot_id": start.json()["slot_options"][0]["slot_id"],
        },
    )
    assert select.status_code == 200
    assert select.json()["journey_state"] == "WAITING_FOR_CONFIRMATION"

    confirm = client.post(
        "/api/orchestrator/v1.0.0/journeys/confirm",
        json={
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "booking": {
                "tenant_id": "demo",
                "journey_id": journey_id,
                "customer_id": "C-100",
                "slot_id": "gslot-1",
                "calendar_target": "advisor@example.com",
                "title": "Consultation",
                "description": "Initial appointment",
                "timezone": "Europe/Berlin",
            },
                "dispatch": {
                    "tenant_id": "demo",
                    "correlation_id": correlation_id,
                    "job_id": "job-template-1",
                    "job_name": "Appointment Confirmation",
                    "message": "Your appointment is confirmed",
                "to_numbers": ["+4912345"],
            },
        },
    )
    assert confirm.status_code == 200
    assert confirm.json()["journey_state"] == "booking_confirmed"
    assert confirm.json()["dispatch"]["status"] == "accepted"

    remind = client.post(
        "/api/orchestrator/v1.0.0/journeys/remind",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "message": "Reminder: your appointment is tomorrow",
            "to_numbers": ["+4912345"],
        },
    )
    assert remind.status_code == 200
    assert remind.json()["journey_state"] == "REMINDER_PENDING"

    cancel = client.post(
        "/api/orchestrator/v1.0.0/journeys/cancel",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "reason": "customer_request",
            "requested_by": "customer",
        },
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
