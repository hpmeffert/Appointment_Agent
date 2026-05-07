from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.repositories import (
    AddressAppointmentLinkRepository,
    AddressRepository,
    BookingRepository,
    JourneyRepository,
)
from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_resolution import (
    AppointmentCandidate,
    AppointmentListPayload,
    AppointmentListOption,
    AppointmentResolutionContext,
    AppointmentResolutionResult,
    ExistingBookingResolver,
)
from appointment_orchestrator.v1_0_1.appointment_orchestrator.service import AppointmentOrchestratorServiceV101


def _future_start(hours: int = 24) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def _seed_address(session, *, address_id: str, display_name: str, phone: str | None = None) -> None:
    AddressRepository(session).create_or_update(
        address_id=address_id,
        display_name=display_name,
        city="Düsseldorf",
        phone=phone,
        tenant_id="default",
        correlation_ref=f"corr-{address_id}",
        preferred_language="de",
        timezone="Europe/Berlin",
    )


def _seed_link(session, *, address_id: str, appointment_id: str, booking_reference: str, correlation_ref: str) -> None:
    AddressAppointmentLinkRepository(session).link(
        link_id=f"link-{uuid4().hex[:8]}",
        address_id=address_id,
        appointment_external_id=appointment_id,
        booking_reference=booking_reference,
        correlation_ref=correlation_ref,
        calendar_ref="Appointment Agent Test",
        tenant_id="default",
    )


def _seed_booking(
    session,
    *,
    booking_reference: str,
    journey_id: str,
    customer_id: str,
    provider_reference: str,
    start_time: datetime,
    appointment_type: str = "dentist",
    address_id: str | None = None,
    correlation_id: str | None = None,
    status: str = "confirmed",
) -> None:
    BookingRepository(session).save(
        booking_reference=booking_reference,
        journey_id=journey_id,
        customer_id=customer_id,
        provider="google",
        external_id=provider_reference,
        status=status,
        payload={
            "appointment_type": appointment_type,
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(minutes=30)).isoformat(),
            "address_id": address_id,
            "correlation_id": correlation_id,
            "customer_name": customer_id,
        },
    )


def _seed_journey(
    service: AppointmentOrchestratorServiceV101,
    *,
    journey_id: str,
    correlation_id: str,
    state: str,
    booking_reference: str = "book-existing",
    provider_reference: str = "provider-existing",
) -> None:
    JourneyRepository(service.session).upsert(
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
            "start_time": _future_start().isoformat(),
            "end_time": _future_start(25).isoformat(),
            "journey_mode": "booking",
        },
    )


def _list_result() -> AppointmentResolutionResult:
    first = AppointmentCandidate(
        appointment_id="apt-1",
        booking_reference="book-1",
        provider_event_ref="provider-1",
        correlation_id="corr-1",
        customer_name="Hans-Peter",
        appointment_type="dentist",
        starts_at=_future_start(24).isoformat(),
        ends_at=_future_start(25).isoformat(),
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
        correlation_id="corr-2",
        customer_name="Hans-Peter",
        appointment_type="doctor",
        starts_at=_future_start(48).isoformat(),
        ends_at=_future_start(49).isoformat(),
        address_id="addr-123",
        status="BOOKED",
        source="booking_store",
        source_trust_level="HIGH",
        match_basis=["customer_phone"],
    )
    payload = AppointmentListPayload(
        prompt="Ich habe diese zukünftigen Termine gefunden.",
        options=[
            AppointmentListOption(
                option_id="booking:book-1",
                booking_reference="book-1",
                appointment_type="dentist",
                starts_at=first.starts_at,
                ends_at=first.ends_at,
                address_label="Hans-Peter | Düsseldorf",
                status="BOOKED",
                summary_line="Dienstag, 21. April, 14:00 — Zahnarzt",
            ),
            AppointmentListOption(
                option_id="booking:book-2",
                booking_reference="book-2",
                appointment_type="doctor",
                starts_at=second.starts_at,
                ends_at=second.ends_at,
                address_label="Hans-Peter | Düsseldorf",
                status="BOOKED",
                summary_line="Freitag, 24. April, 09:30 — Arzt",
            ),
        ],
        metadata={"locale": "de", "requested_action": "show_appointments", "candidate_count": 2},
    )
    return AppointmentResolutionResult(
        resolution_status="multiple_matches",
        candidates=[first, second],
        selected=None,
        match_basis=["customer_phone"],
        clarification_required=True,
        clarification_reason="multiple_candidates",
        notes=[],
        appointment_list_payload=payload,
    )


def test_multi_ux_lists_future_appointments_in_stable_order_and_excludes_cancelled() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        customer_name = f"Hans-Peter-{uuid4().hex[:6]}"
        address_id = f"addr-{uuid4().hex[:8]}"
        _seed_address(session, address_id=address_id, display_name="Hans-Peter", phone="+491701234567")
        first_start = _future_start(24)
        second_start = _future_start(72)
        _seed_booking(
            session,
            booking_reference=f"book-{uuid4().hex[:8]}",
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id=customer_name,
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=first_start,
            appointment_type="dentist",
            address_id=address_id,
            correlation_id=f"corr-{uuid4().hex[:8]}",
        )
        _seed_booking(
            session,
            booking_reference=f"book-{uuid4().hex[:8]}",
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id=customer_name,
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=second_start,
            appointment_type="doctor",
            address_id=address_id,
            correlation_id=f"corr-{uuid4().hex[:8]}",
        )
        _seed_booking(
            session,
            booking_reference=f"book-{uuid4().hex[:8]}",
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id=customer_name,
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=_future_start(96),
            appointment_type="technician",
            address_id=address_id,
            correlation_id=f"corr-{uuid4().hex[:8]}",
            status="cancelled",
        )

        result = resolver.list_appointments(
            AppointmentResolutionContext(
                customer_name=customer_name,
                address_id=address_id,
                requested_action="show_appointments",
                locale="de",
            )
        )

        assert result.appointment_list_payload is not None
        assert result.appointment_list_payload.prompt == "Ich habe diese zukünftigen Termine gefunden."
        assert [option.booking_reference for option in result.appointment_list_payload.options] == [
            result.candidates[0].booking_reference,
            result.candidates[1].booking_reference,
        ]
        assert all(option.status != "cancelled" for option in result.appointment_list_payload.options)
        assert "Zahnarzt" in (result.appointment_list_payload.options[0].summary_line or "")
        assert "Arzt" in (result.appointment_list_payload.options[1].summary_line or "")
    finally:
        session.close()


def test_multi_ux_formats_english_listing_prompt_and_summary() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        address_id = f"addr-{uuid4().hex[:8]}"
        _seed_address(session, address_id=address_id, display_name="Alex Carter", phone="+491701234568")
        booking_reference = f"book-{uuid4().hex[:8]}"
        correlation_id = f"corr-{uuid4().hex[:8]}"
        _seed_link(
            session,
            address_id=address_id,
            appointment_id="apt-english",
            booking_reference=booking_reference,
            correlation_ref=correlation_id,
        )
        _seed_booking(
            session,
            booking_reference=booking_reference,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Alex Carter",
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=_future_start(36),
            appointment_type="doctor",
            address_id=address_id,
            correlation_id=correlation_id,
        )

        result = resolver.list_appointments(
            AppointmentResolutionContext(
                customer_name="Alex Carter",
                address_id=address_id,
                requested_action="show_future_appointments",
                locale="en",
            )
        )

        assert result.appointment_list_payload is not None
        assert result.appointment_list_payload.prompt == "I found these upcoming appointments."
        assert len(result.appointment_list_payload.options) == 1
        assert "Doctor" in (result.appointment_list_payload.options[0].summary_line or "")
    finally:
        session.close()


def test_multi_ux_show_appointments_runtime_is_non_destructive(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id = f"journey-{uuid4().hex[:8]}"
        correlation_id = f"corr-{uuid4().hex[:8]}"
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        monkeypatch.setattr(service.resolver, "list_appointments", lambda context: _list_result())

        result = service.handle_reminder_action(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "action": "show appointments",
                "message": "show my appointments",
            }
        )

        assert result["status"] == "appointments_listed"
        journey = service.journeys.get(journey_id)
        payload = journey.preference_payload or {}
        assert payload.get("requested_action_category") == "show_appointments"
        assert payload.get("future_appointments_requested") is True
        assert payload.get("bulk_action_requested") is False
        assert result["candidate_count"] == 2
    finally:
        session.close()


def test_multi_ux_bulk_action_request_is_blocked(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id = f"journey-{uuid4().hex[:8]}"
        correlation_id = f"corr-{uuid4().hex[:8]}"
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        monkeypatch.setattr(service, "cancel_journey", lambda payload: (_ for _ in ()).throw(AssertionError("cancel_journey must not run")))

        result = service.handle_reminder_action(
            {
                "journey_id": journey_id,
                "tenant_id": "demo",
                "correlation_id": correlation_id,
                "action": "cancel all appointments",
                "message": "delete all my appointments",
            }
        )

        assert result["status"] == "bulk_action_not_supported"
        journey = service.journeys.get(journey_id)
        payload = journey.preference_payload or {}
        assert payload.get("bulk_action_requested") is True
        assert payload.get("blocked_bulk_action") is True
    finally:
        session.close()


def test_multi_ux_selection_persists_user_choice_and_resumed_action(monkeypatch) -> None:
    session = SessionLocal()
    try:
        service = AppointmentOrchestratorServiceV101(session)
        journey_id = f"journey-{uuid4().hex[:8]}"
        correlation_id = f"corr-{uuid4().hex[:8]}"
        _seed_journey(service, journey_id=journey_id, correlation_id=correlation_id, state=JourneyState.REMINDER_PENDING.value)
        candidate = AppointmentCandidate(
            appointment_id="apt-1",
            booking_reference="book-1",
            provider_event_ref="provider-1",
            correlation_id=correlation_id,
            customer_name="Hans-Peter",
            appointment_type="dentist",
            address_id="addr-123",
            status="BOOKED",
            source="booking_store",
            source_trust_level="HIGH",
            match_basis=["booking_reference"],
        )
        service._update_preference_payload(
            journey_id,
            {
                "awaiting_appointment_selection": True,
                "pending_requested_action": "cancel",
                "appointment_selection_options": {"booking:book-1": asdict(candidate)},
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
        payload = service.journeys.get(journey_id).preference_payload or {}
        assert payload.get("user_selected_option_id") == "booking:book-1"
        assert payload.get("resumed_action") == "cancel"
    finally:
        session.close()
