from uuid import uuid4

from fastapi.testclient import TestClient

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.repositories import JourneyRepository
from appointment_agent_shared.main import app


def _new_journey() -> tuple[str, str]:
    return "journey-{}".format(uuid4().hex[:8]), "corr-{}".format(uuid4().hex[:8])


def test_v101_no_slot_retry_with_broader_window() -> None:
    client = TestClient(app)
    journey_id, correlation_id = _new_journey()

    response = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-200",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
            "resource_candidates": ["no-slots"],
            "no_slot_strategy": "RETRY_WITH_BROADER_WINDOW",
        },
    )

    assert response.status_code == 200
    assert response.json()["journey_state"] == "WAITING_FOR_SELECTION"
    assert response.json()["no_slot_action"] == "RETRY_WITH_BROADER_WINDOW"


def test_v101_no_slot_escalation_and_audit() -> None:
    client = TestClient(app)
    journey_id, correlation_id = _new_journey()

    response = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-201",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
            "resource_candidates": ["no-slots"],
            "no_slot_strategy": "ESCALATE_TO_HUMAN",
        },
    )

    assert response.status_code == 200
    assert response.json()["journey_state"] == "ESCALATED"

    audit = client.get("/api/orchestrator/v1.0.1/journeys/{}/audit".format(journey_id))
    assert audit.status_code == 200
    assert any(item["decision_type"] == "escalation" for item in audit.json())


def test_v101_reschedule_happy_path() -> None:
    client = TestClient(app)
    journey_id, correlation_id = _new_journey()

    start = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-202",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
        },
    )
    slot_id = start.json()["slot_options"][0]["slot_id"]
    client.post("/api/orchestrator/v1.0.1/journeys/select", json={"journey_id": journey_id, "tenant_id": "demo", "correlation_id": correlation_id, "slot_id": slot_id})
    client.post(
        "/api/orchestrator/v1.0.1/journeys/confirm",
        json={
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "booking": {
                "tenant_id": "demo",
                "journey_id": journey_id,
                "customer_id": "C-202",
                "slot_id": slot_id,
                "calendar_target": "advisor@example.com",
                "title": "Consultation",
                "description": "Initial booking",
                "timezone": "Europe/Berlin",
            },
            "dispatch": {
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "job_name": "Appointment Confirmation",
                "message": "Confirmed",
                "to_numbers": ["+49123"],
            },
        },
    )

    reschedule = client.post(
        "/api/orchestrator/v1.0.1/journeys/reschedule",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "resource_candidates": ["advisor@example.com"],
        },
    )

    assert reschedule.status_code == 200
    assert reschedule.json()["journey_state"] == "WAITING_FOR_SELECTION"

    replacement_slot = reschedule.json()["slot_options"][0]
    client.post(
        "/api/orchestrator/v1.0.1/journeys/select",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "slot_id": replacement_slot["slot_id"],
        },
    )
    rebook = client.post(
        "/api/orchestrator/v1.0.1/journeys/confirm",
        json={
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "booking": {
                "tenant_id": "demo",
                "journey_id": journey_id,
                "customer_id": "C-202",
                "slot_id": replacement_slot["slot_id"],
                "calendar_target": "advisor@example.com",
                "title": "Consultation Rescheduled",
                "description": "Rescheduled booking",
                "timezone": "Europe/Berlin",
                "metadata": {
                    "new_start": replacement_slot["start_time"],
                    "new_end": replacement_slot["end_time"],
                },
            },
            "dispatch": {
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "job_name": "Appointment Rescheduled",
                "message": "Rescheduled",
                "to_numbers": ["+49123"],
            },
        },
    )

    assert rebook.status_code == 200
    assert rebook.json()["booking"]["status"] == "RESCHEDULED"


def test_v101_reschedule_rejected_by_policy() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    journey_id, correlation_id = _new_journey()

    start = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-203",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
            "resource_candidates": ["no-slots"],
            "no_slot_strategy": "ASK_FOR_MONTH",
        },
    )
    assert start.status_code == 200

    rejected = client.post(
        "/api/orchestrator/v1.0.1/journeys/reschedule",
        json={"journey_id": journey_id, "tenant_id": "demo", "correlation_id": correlation_id},
    )

    assert rejected.status_code >= 400


def test_v101_explicit_help_escalation() -> None:
    client = TestClient(app)
    journey_id, correlation_id = _new_journey()

    client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-204",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
        },
    )

    escalation = client.post(
        "/api/orchestrator/v1.0.1/journeys/escalate",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "reason": "help_requested",
            "message": "Customer asked for a human agent",
        },
    )

    assert escalation.status_code == 200
    assert escalation.json()["journey_state"] == "ESCALATED"


def test_v101_cancellation_missing_provider_reference_escalates() -> None:
    client = TestClient(app)
    journey_id, correlation_id = _new_journey()

    start = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-205",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
        },
    )
    slot_id = start.json()["slot_options"][0]["slot_id"]
    client.post("/api/orchestrator/v1.0.1/journeys/select", json={"journey_id": journey_id, "tenant_id": "demo", "correlation_id": correlation_id, "slot_id": slot_id})
    client.post(
        "/api/orchestrator/v1.0.1/journeys/confirm",
        json={
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "booking": {
                "tenant_id": "demo",
                "journey_id": journey_id,
                "customer_id": "C-205",
                "slot_id": slot_id,
                "calendar_target": "advisor@example.com",
                "title": "Consultation",
                "description": "Initial booking",
                "timezone": "Europe/Berlin",
            },
            "dispatch": {
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "job_name": "Appointment Confirmation",
                "message": "Confirmed",
                "to_numbers": ["+49123"],
            },
        },
    )

    session = SessionLocal()
    try:
        repo = JourneyRepository(session)
        journey = repo.get(journey_id)
        payload = dict(journey.preference_payload or {})
        payload.pop("provider_reference", None)
        journey.preference_payload = payload
        session.commit()
    finally:
        session.close()

    cancelled = client.post(
        "/api/orchestrator/v1.0.1/journeys/cancel",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "reason": "customer_request",
            "requested_by": "customer",
        },
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["journey_state"] == "ESCALATED"


def _create_booked_journey(client: TestClient) -> tuple[str, str, str]:
    journey_id, correlation_id = _new_journey()
    start = client.post(
        "/api/orchestrator/v1.0.1/journeys/start",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "customer_id": "C-300",
            "service_type": "consultation",
            "timezone": "Europe/Berlin",
        },
    )
    slot_id = start.json()["slot_options"][0]["slot_id"]
    client.post(
        "/api/orchestrator/v1.0.1/journeys/select",
        json={"journey_id": journey_id, "tenant_id": "demo", "correlation_id": correlation_id, "slot_id": slot_id},
    )
    client.post(
        "/api/orchestrator/v1.0.1/journeys/confirm",
        json={
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "booking": {
                "tenant_id": "demo",
                "journey_id": journey_id,
                "customer_id": "C-300",
                "slot_id": slot_id,
                "calendar_target": "advisor@example.com",
                "title": "Consultation",
                "description": "Initial booking",
                "timezone": "Europe/Berlin",
            },
            "dispatch": {
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "job_name": "Appointment Confirmation",
                "message": "Confirmed",
                "to_numbers": ["+49123"],
            },
        },
    )
    return journey_id, correlation_id, slot_id


def test_v101_reminder_send_and_keep_action() -> None:
    client = TestClient(app)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    reminder = client.post(
        "/api/orchestrator/v1.0.1/journeys/remind",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "to_numbers": ["+49123"],
        },
    )

    assert reminder.status_code == 200
    assert reminder.json()["journey_state"] == "REMINDER_PENDING"
    assert "Reminder:" in reminder.json()["message"]
    assert "keep" in reminder.json()["available_actions"]

    keep = client.post(
        "/api/orchestrator/v1.0.1/journeys/reminder-action",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "action": "keep",
        },
    )

    assert keep.status_code == 200
    assert keep.json()["journey_state"] == "BOOKED"
    assert keep.json()["selected_action"] == "keep"


def test_v101_reminder_action_reschedule() -> None:
    client = TestClient(app)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    client.post(
        "/api/orchestrator/v1.0.1/journeys/remind",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "to_numbers": ["+49123"],
        },
    )

    reschedule = client.post(
        "/api/orchestrator/v1.0.1/journeys/reminder-action",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "action": "reschedule",
        },
    )

    assert reschedule.status_code == 200
    assert reschedule.json()["journey_state"] == "WAITING_FOR_SELECTION"
    assert len(reschedule.json()["slot_options"]) > 0


def test_v101_reminder_action_cancel() -> None:
    client = TestClient(app)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    client.post(
        "/api/orchestrator/v1.0.1/journeys/remind",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "to_numbers": ["+49123"],
        },
    )

    cancelled = client.post(
        "/api/orchestrator/v1.0.1/journeys/reminder-action",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "action": "cancel",
        },
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["journey_state"] == "CLOSED"
    assert cancelled.json()["selected_action"] == "cancel"


def test_v101_reminder_action_call_me() -> None:
    client = TestClient(app)
    journey_id, correlation_id, _slot_id = _create_booked_journey(client)

    client.post(
        "/api/orchestrator/v1.0.1/journeys/remind",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "to_numbers": ["+49123"],
        },
    )

    escalated = client.post(
        "/api/orchestrator/v1.0.1/journeys/reminder-action",
        json={
            "journey_id": journey_id,
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "action": "call_me",
        },
    )

    assert escalated.status_code == 200
    assert escalated.json()["journey_state"] == "ESCALATED"
    assert escalated.json()["selected_action"] == "call_me"
