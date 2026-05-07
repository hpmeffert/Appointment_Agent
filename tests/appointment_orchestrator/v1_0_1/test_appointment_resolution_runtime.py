from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.repositories import JourneyRepository
from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_resolution import (
    AppointmentCandidate,
    AppointmentChoiceOption,
    AppointmentDisambiguationPayload,
    AppointmentResolutionResult,
)
from appointment_orchestrator.v1_0_1.appointment_orchestrator.service import AppointmentOrchestratorServiceV101


def _future(hours: int = 24) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours)


def _journey_id() -> tuple[str, str]:
    return f"journey-{uuid4().hex[:8]}", f"corr-{uuid4().hex[:8]}"


def _seed_journey(
    service: AppointmentOrchestratorServiceV101,
    *,
    journey_id: str,
    correlation_id: str,
    state: str,
    booking_reference: str = "book-existing",
    provider_reference: str = "provider-existing",
) -> None:
    service.journeys.upsert(
        journey_id=journey_id,
        correlation_id=correlation_id,
        tenant_id="demo",
        customer_id="Hans-Peter",
        channel="RCS",
        current_state=state,
        service_type="dentist",
        locale="de",
        timezone="Europe/Berlin",
        booking_reference=booking_reference,
        preference_payload={
            "provider_reference": provider_reference,
            "appointment_id": "apt-123",
            "address_id": "addr-123",
            "appointment_type": "dentist",
            "customer_name": "Hans-Peter",
            "start_time": _future().isoformat(),
            "end_time": _future(25).isoformat(),
            "journey_mode": "booking",
        },
    )


def _single_result() -> AppointmentResolutionResult:
    candidate = AppointmentCandidate(
        appointment_id="apt-123",
        booking_reference="book-existing",
        provider_event_ref="provider-existing",
        correlation_id="corr-existing",
        customer_name="Hans-Peter",
        appointment_type="dentist",
        starts_at=_future().isoformat(),
        ends_at=_future(25).isoformat(),
        address_id="addr-123",
        status="BOOKED",
        source="journey_store",
        source_trust_level="HIGH",
        match_basis=["booking_reference"],
    )
    return AppointmentResolutionResult(
        resolution_status="single_match",
        candidates=[candidate],
        selected=candidate,
        match_basis=["booking_reference"],
        clarification_required=False,
    )


def _multiple_result() -> AppointmentResolutionResult:
    first = AppointmentCandidate(
        appointment_id="apt-1",
        booking_reference="book-1",
        provider_event_ref="provider-1",
        customer_name="Hans-Peter",
        appointment_type="dentist",
        starts_at=_future().isoformat(),
        address_id="addr-123",
        status="BOOKED",
        source="booking_store",
        source_trust_level="HIGH",
        match_basis=["customer_phone"],
    )
    second = AppointmentCandidate(
        appointment_id="apt-2",
        booking_reference="book-2",
        provider_event_ref="provider-2",
        customer_name="Hans-Peter",
        appointment_type="doctor",
        starts_at=_future(48).isoformat(),
        address_id="addr-123",
        status="BOOKED",
        source="booking_store",
        source_trust_level="HIGH",
        match_basis=["customer_phone"],
    )
    payload = AppointmentDisambiguationPayload(
        prompt="Ich habe 2 Termine gefunden. Welchen möchten Sie bearbeiten?",
        options=[
            AppointmentChoiceOption(option_id="booking:book-1", booking_reference="book-1", title="Dienstag, 21. April, 14:00"),
            AppointmentChoiceOption(option_id="booking:book-2", booking_reference="book-2", title="Freitag, 24. April, 09:30"),
        ],
    )
    return AppointmentResolutionResult(
        resolution_status="multiple_matches",
        candidates=[first, second],
        selected=None,
        match_basis=["customer_phone"],
        clarification_required=True,
        clarification_reason="multiple_candidates",
        disambiguation_payload=payload,
    )


def _no_match_result() -> AppointmentResolutionResult:
    return AppointmentResolutionResult(
        resolution_status="no_match",
        clarification_required=False,
        clarification_reason="no_candidates",
        notes=["No appointment candidates survived staged resolution."],
    )


class _FakeProviderResult:
    def __init__(self, *, booking_reference: str, provider_reference: str, status: str) -> None:
        self.booking_reference = booking_reference
        self.provider_reference = provider_reference
        self.status = status
        self.provider = "google"
        self.calendar_target = "advisor@example.com"
        self.start_time = _future()
        self.end_time = _future(1)

    def model_dump(self, mode: str = "json") -> dict:
        return {
            "booking_reference": self.booking_reference,
            "provider_reference": self.provider_reference,
            "status": self.status,
            "provider": self.provider,
            "calendar_target": self.calendar_target,
        }


def test_runtime_keep_single_match_proceeds(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _single_result())

        result = service.handle_reminder_action(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "action": "keep",
            }
        )

        assert result["status"] == "appointment_kept"
        journey = service.journeys.get(journey_id)
        assert journey.current_state == JourneyState.BOOKED.value
    finally:
        session.close()


def test_runtime_keep_multiple_matches_returns_clarification_and_stores_state(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _multiple_result())

        result = service.handle_reminder_action(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "action": "keep",
            }
        )

        assert result["status"] == "clarification_required"
        journey = service.journeys.get(journey_id)
        assert (journey.preference_payload or {}).get("awaiting_appointment_selection") is True
        assert (journey.preference_payload or {}).get("pending_requested_action") == "keep"
    finally:
        session.close()


def test_runtime_keep_no_match_is_safe_noop(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _no_match_result())

        result = service.handle_reminder_action(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "action": "keep",
            }
        )

        assert result["status"] == "appointment_not_resolved"
        journey = service.journeys.get(journey_id)
        assert journey.current_state == JourneyState.REMINDER_PENDING.value
    finally:
        session.close()


def test_runtime_reschedule_single_match_proceeds(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.BOOKED.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _single_result())
        monkeypatch.setattr(service, "plan_journey", lambda payload: {"status": "planned", "journey_id": payload["journey_id"]})

        result = service.start_reschedule(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
            }
        )

        assert result["status"] == "planned"
    finally:
        session.close()


def test_runtime_reschedule_multiple_matches_returns_clarification_without_planning(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.BOOKED.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _multiple_result())
        monkeypatch.setattr(service, "plan_journey", lambda payload: (_ for _ in ()).throw(AssertionError("plan_journey must not run")))

        result = service.start_reschedule(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
            }
        )

        assert result["status"] == "clarification_required"
    finally:
        session.close()


def test_runtime_reschedule_no_match_does_not_mutate(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.BOOKED.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _no_match_result())
        monkeypatch.setattr(service, "plan_journey", lambda payload: (_ for _ in ()).throw(AssertionError("plan_journey must not run")))

        result = service.start_reschedule(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
            }
        )

        assert result["status"] == "appointment_not_resolved"
    finally:
        session.close()


def test_runtime_cancel_single_match_proceeds(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.BOOKED.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _single_result())
        monkeypatch.setattr(
            service.google,
            "cancel_booking",
            lambda command: _FakeProviderResult(booking_reference=command.booking_reference, provider_reference=command.provider_reference, status="cancelled"),
        )

        result = service.cancel_journey(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "reason": "customer_cancel",
                "requested_by": "customer",
            }
        )

        assert result["status"] == "cancelled"
    finally:
        session.close()


def test_runtime_cancel_multiple_matches_does_not_mutate(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.BOOKED.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _multiple_result())
        monkeypatch.setattr(
            service.google,
            "cancel_booking",
            lambda command: (_ for _ in ()).throw(AssertionError("cancel_booking must not run")),
        )

        result = service.cancel_journey(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "reason": "customer_cancel",
                "requested_by": "customer",
            }
        )

        assert result["status"] == "clarification_required"
    finally:
        session.close()


def test_runtime_cancel_no_match_does_not_mutate(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.BOOKED.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _no_match_result())
        monkeypatch.setattr(
            service.google,
            "cancel_booking",
            lambda command: (_ for _ in ()).throw(AssertionError("cancel_booking must not run")),
        )

        result = service.cancel_journey(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "reason": "customer_cancel",
                "requested_by": "customer",
            }
        )

        assert result["status"] == "appointment_not_resolved"
    finally:
        session.close()


def test_runtime_confirm_reschedule_multiple_matches_returns_clarification(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.WAITING_FOR_CONFIRMATION.value)
        service._set_journey_mode(journey_id, "reschedule")
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _multiple_result())
        monkeypatch.setattr(
            service.google,
            "update_booking",
            lambda command: (_ for _ in ()).throw(AssertionError("update_booking must not run")),
        )

        result = service.confirm_booking(
            {
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "booking": {
                    "tenant_id": "demo",
                    "journey_id": journey_id,
                    "customer_id": "Hans-Peter",
                    "slot_id": "slot-1",
                    "calendar_target": "advisor@example.com",
                    "title": "Consultation Rescheduled",
                    "description": "Rescheduled booking",
                    "timezone": "Europe/Berlin",
                    "metadata": {"new_start": _future().isoformat(), "new_end": _future(1).isoformat()},
                },
                "dispatch": {
                    "tenant_id": "demo",
                    "correlation_id": correlation_id,
                    "job_name": "Appointment Rescheduled",
                    "message": "Rescheduled",
                    "to_numbers": ["+49123"],
                },
            }
        )

        assert result["status"] == "clarification_required"
    finally:
        session.close()


def test_runtime_follow_up_selection_resumes_original_action(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        service._update_preference_payload(
            journey_id,
            {
                "awaiting_appointment_selection": True,
                "pending_requested_action": "cancel",
                "appointment_selection_options": {
                    "booking:book-1": {
                        "appointment_id": "apt-1",
                        "booking_reference": "book-1",
                        "provider_event_ref": "provider-1",
                        "correlation_id": correlation_id,
                        "customer_name": "Hans-Peter",
                        "appointment_type": "dentist",
                        "address_id": "addr-123",
                        "status": "BOOKED",
                        "source": "booking_store",
                        "source_trust_level": "HIGH",
                        "match_basis": ["booking_reference"],
                        "metadata": {},
                    }
                },
            },
        )

        monkeypatch.setattr(service, "cancel_journey", lambda payload: {"status": "cancelled_via_selection", "payload": payload})

        result = service.handle_reminder_action(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "action": "booking:book-1",
            }
        )

        assert result["status"] == "cancelled_via_selection"
        assert result["payload"]["resolution_gate_passed"] is True
    finally:
        session.close()
