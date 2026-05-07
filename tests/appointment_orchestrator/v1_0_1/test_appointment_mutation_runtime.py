from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.enums import ErrorCategory
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.errors import ProviderError
from appointment_agent_shared.models import BookingResult
from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_resolution import (
    AppointmentCandidate,
    AppointmentResolutionResult,
)
from appointment_orchestrator.v1_0_1.appointment_orchestrator.service import AppointmentOrchestratorServiceV101
from google_adapter.v1_0_1.google_adapter.service import GoogleAdapterException


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
            "journey_mode": "reschedule",
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


def _no_match_result() -> AppointmentResolutionResult:
    return AppointmentResolutionResult(
        resolution_status="no_match",
        clarification_required=False,
        clarification_reason="no_candidates",
        notes=["No appointment candidates survived staged resolution."],
    )


def _booking_payload(journey_id: str, correlation_id: str, *, force_replace: bool = False) -> dict:
    return {
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
            "metadata": {
                "new_start": _future().isoformat(),
                "new_end": _future(1).isoformat(),
                "force_replace_existing": force_replace,
            },
        },
        "dispatch": {
            "tenant_id": "demo",
            "correlation_id": correlation_id,
            "job_name": "Appointment Rescheduled",
            "message": "Rescheduled",
            "to_numbers": ["+49123"],
        },
    }


def test_runtime_reschedule_uses_patch_strategy_when_eligible(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.WAITING_FOR_CONFIRMATION.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _single_result())
        monkeypatch.setattr(
            service.google,
            "update_booking",
            lambda command: BookingResult(
                booking_reference=command.booking_reference,
                provider="google",
                provider_reference=command.provider_reference,
                status="RESCHEDULED",
                start_time=command.new_start,
                end_time=command.new_end,
                metadata={},
            ),
        )
        monkeypatch.setattr(service, "_execute_replace_reschedule", lambda **kwargs: (_ for _ in ()).throw(AssertionError("replace path must not run")))
        monkeypatch.setattr(service.lekab, "dispatch_workflow", lambda command: {"runtime_id": "rt-1"})

        result = service.confirm_booking(_booking_payload(journey_id, correlation_id))

        assert result["booking"]["status"] == "RESCHEDULED"
        payload = (service.journeys.get(journey_id).preference_payload or {})
        assert payload.get("mutation_strategy") == "patch_existing"
        assert payload.get("mutation_outcome") == "success"
    finally:
        session.close()


def test_runtime_reschedule_uses_replace_strategy_when_forced(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.WAITING_FOR_CONFIRMATION.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _single_result())
        monkeypatch.setattr(
            service,
            "_execute_replace_reschedule",
            lambda **kwargs: BookingResult(
                booking_reference="book-existing",
                provider="google",
                provider_reference="provider-new",
                status="RESCHEDULED",
                start_time=_future(),
                end_time=_future(1),
                metadata={"mutation_strategy": "replace_existing"},
            ),
        )
        monkeypatch.setattr(service.google, "update_booking", lambda command: (_ for _ in ()).throw(AssertionError("patch path must not run")))
        monkeypatch.setattr(service.lekab, "dispatch_workflow", lambda command: {"runtime_id": "rt-2"})

        result = service.confirm_booking(_booking_payload(journey_id, correlation_id, force_replace=True))

        assert result["booking"]["provider_reference"] == "provider-new"
        payload = (service.journeys.get(journey_id).preference_payload or {})
        assert payload.get("mutation_strategy") == "replace_existing"
        assert payload.get("mutation_outcome") == "success"
    finally:
        session.close()


def test_runtime_replace_failure_preserves_previous_provider_reference(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.WAITING_FOR_CONFIRMATION.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _single_result())
        monkeypatch.setattr(
            service,
            "_execute_replace_reschedule",
            lambda **kwargs: (_ for _ in ()).throw(
                GoogleAdapterException(
                    ProviderError(
                        provider="google",
                        provider_operation="replace_reschedule",
                        error_category=ErrorCategory.UNKNOWN,
                        message="replace failed",
                    )
                )
            ),
        )
        monkeypatch.setattr(service.google, "update_booking", lambda command: (_ for _ in ()).throw(AssertionError("patch path must not run")))
        monkeypatch.setattr(service.lekab, "dispatch_workflow", lambda command: {"runtime_id": "rt-3"})

        result = service.confirm_booking(_booking_payload(journey_id, correlation_id, force_replace=True))

        payload = service.journeys.get(journey_id).preference_payload or {}
        assert result["journey_state"] == "ESCALATED"
        assert payload.get("provider_reference") == "provider-existing"
        assert payload.get("mutation_strategy") == "replace_existing"
    finally:
        session.close()


def test_runtime_no_match_still_does_not_mutate_on_reschedule_confirm(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id, correlation_id = _journey_id()
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.WAITING_FOR_CONFIRMATION.value)
        monkeypatch.setattr(service.resolver, "resolve", lambda context: _no_match_result())
        monkeypatch.setattr(service.google, "update_booking", lambda command: (_ for _ in ()).throw(AssertionError("patch path must not run")))
        monkeypatch.setattr(service, "_execute_replace_reschedule", lambda **kwargs: (_ for _ in ()).throw(AssertionError("replace path must not run")))

        result = service.confirm_booking(_booking_payload(journey_id, correlation_id))

        assert result["status"] == "appointment_not_resolved"
        payload = service.journeys.get(journey_id).preference_payload or {}
        assert payload.get("mutation_strategy") is None
    finally:
        session.close()
