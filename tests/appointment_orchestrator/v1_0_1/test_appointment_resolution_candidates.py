from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from appointment_agent_shared.db import SessionLocal
from appointment_agent_shared.repositories import (
    AddressAppointmentLinkRepository,
    AddressRepository,
    BookingRepository,
    GoogleDemoEventRepository,
    JourneyRepository,
)
from appointment_orchestrator.v1_0_1.appointment_orchestrator.appointment_resolution import (
    AppointmentResolutionContext,
    ExistingBookingResolver,
)


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
        customer_number=f"cust-{address_id}",
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


def _seed_journey(
    session,
    *,
    journey_id: str,
    correlation_id: str,
    booking_reference: str,
    appointment_type: str = "dentist",
    customer_id: str = "Hans-Peter",
    address_id: str | None = None,
    provider_reference: str | None = None,
    start_time: datetime | None = None,
    state: str = "BOOKED",
) -> None:
    start_time = start_time or _future_start()
    JourneyRepository(session).upsert(
        journey_id=journey_id,
        correlation_id=correlation_id,
        tenant_id="default",
        customer_id=customer_id,
        channel="RCS",
        current_state=state,
        service_type=appointment_type,
        locale="de",
        timezone="Europe/Berlin",
        booking_reference=booking_reference,
        preference_payload={
            "appointment_type": appointment_type,
            "provider_reference": provider_reference,
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(minutes=30)).isoformat(),
            "address_id": address_id,
            "customer_name": customer_id,
        },
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


def _seed_google_event(
    session,
    *,
    booking_reference: str,
    provider_reference: str,
    customer_name: str,
    start_time: datetime,
    appointment_type: str = "dentist",
    address_id: str | None = None,
    deleted: bool = False,
) -> None:
    GoogleDemoEventRepository(session).save(
        operation_id=f"op-{uuid4().hex[:8]}",
        mode="real",
        timeframe="patch8_booking",
        calendar_id="Appointment Agent Test",
        event_id=provider_reference,
        booking_reference=booking_reference,
        title=f"{appointment_type.title()} Appointment",
        customer_name=customer_name,
        mobile_number=None,
        start_time_utc=start_time.astimezone(timezone.utc).replace(tzinfo=None),
        end_time_utc=(start_time + timedelta(minutes=30)).astimezone(timezone.utc).replace(tzinfo=None),
        timezone="Europe/Berlin",
        provider_reference=provider_reference,
        details={
            "appointment_type": appointment_type,
            "address_id": address_id,
            "correlation_id": f"corr-{booking_reference}",
        },
        is_demo_generated=True,
    )
    if deleted:
        GoogleDemoEventRepository(session).mark_deleted([booking_reference])


def test_candidates_can_be_retrieved_from_current_context_journey() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        journey_id = f"journey-{uuid4().hex[:8]}"
        booking_reference = f"book-{uuid4().hex[:8]}"
        provider_reference = f"prov-{uuid4().hex[:8]}"
        correlation_id = f"corr-{uuid4().hex[:8]}"
        address_id = f"addr-{uuid4().hex[:8]}"
        _seed_address(session, address_id=address_id, display_name="Hans-Peter", phone="+491701234567")
        _seed_journey(
            session,
            journey_id=journey_id,
            correlation_id=correlation_id,
            booking_reference=booking_reference,
            provider_reference=provider_reference,
            address_id=address_id,
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                metadata={"journey_id": journey_id},
                locale="de",
            )
        )

        assert result.resolution_status == "single_match"
        assert result.selected is not None
        assert result.selected.source == "journey_store"
        assert result.selected.booking_reference == booking_reference
    finally:
        session.close()


def test_candidates_can_be_retrieved_from_booking_and_provider_sources_and_deduped() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        booking_reference = f"book-{uuid4().hex[:8]}"
        provider_reference = f"prov-{uuid4().hex[:8]}"
        journey_id = f"journey-{uuid4().hex[:8]}"
        start_time = _future_start(48)
        _seed_booking(
            session,
            booking_reference=booking_reference,
            journey_id=journey_id,
            customer_id="Hans-Peter",
            provider_reference=provider_reference,
            start_time=start_time,
            correlation_id=f"corr-{booking_reference}",
        )
        _seed_google_event(
            session,
            booking_reference=booking_reference,
            provider_reference=provider_reference,
            customer_name="Hans-Peter",
            start_time=start_time,
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                booking_reference=booking_reference,
                provider_event_ref=provider_reference,
                locale="en",
            )
        )

        assert result.resolution_status == "single_match"
        assert len(result.candidates) == 1
        assert result.selected is not None
        assert result.selected.provider_event_ref == provider_reference
        assert result.selected.source_trust_level == "HIGH"
        assert "booking_reference" in result.match_basis or "provider_or_calendar_record" in result.match_basis
    finally:
        session.close()


def test_resolver_supports_reservation_ref_alias_for_booking_reference() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        booking_reference = f"book-{uuid4().hex[:8]}"
        provider_reference = f"prov-{uuid4().hex[:8]}"
        start_time = _future_start(54)
        _seed_booking(
            session,
            booking_reference=booking_reference,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Hans-Peter",
            provider_reference=provider_reference,
            start_time=start_time,
            correlation_id=f"corr-{booking_reference}",
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                reservation_ref=booking_reference,
                locale="de",
            )
        )

        assert result.resolution_status == "single_match"
        assert result.selected is not None
        assert result.selected.booking_reference == booking_reference
        assert "reservation_ref" in result.selected.match_basis
    finally:
        session.close()


def test_resolver_supports_customer_number_lookup() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        address_id = f"addr-{uuid4().hex[:8]}"
        booking_reference = f"book-{uuid4().hex[:8]}"
        appointment_id = f"appt-{uuid4().hex[:8]}"
        correlation_ref = f"corr-{uuid4().hex[:8]}"
        provider_reference = f"prov-{uuid4().hex[:8]}"
        _seed_address(session, address_id=address_id, display_name="Hans-Peter", phone="+491701234567")
        _seed_link(
            session,
            address_id=address_id,
            appointment_id=appointment_id,
            booking_reference=booking_reference,
            correlation_ref=correlation_ref,
        )
        _seed_booking(
            session,
            booking_reference=booking_reference,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Hans-Peter",
            provider_reference=provider_reference,
            start_time=_future_start(72),
            address_id=address_id,
            correlation_id=correlation_ref,
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                customer_number=f"cust-{address_id}",
                locale="de",
            )
        )

        assert result.resolution_status == "single_match"
        assert result.selected is not None
        assert result.selected.address_id == address_id
        assert "customer_number" in result.selected.match_basis
    finally:
        session.close()


def test_filtering_removes_cancelled_and_past_candidates() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        past_booking = f"book-{uuid4().hex[:8]}"
        cancelled_booking = f"book-{uuid4().hex[:8]}"
        _seed_booking(
            session,
            booking_reference=past_booking,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Demo Customer",
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=_future_start(-48),
            status="confirmed",
        )
        _seed_booking(
            session,
            booking_reference=cancelled_booking,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Demo Customer",
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=_future_start(72),
            status="cancelled",
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                customer_name="Demo Customer",
                locale="en",
            )
        )

        assert result.resolution_status == "no_match"
        assert any("filtered out" in note.lower() or "filtered candidate" in note.lower() for note in result.notes)
    finally:
        session.close()


def test_source_trust_survives_merge_in_favor_of_stronger_source() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        booking_reference = f"book-{uuid4().hex[:8]}"
        provider_reference = f"prov-{uuid4().hex[:8]}"
        journey_id = f"journey-{uuid4().hex[:8]}"
        correlation_id = f"corr-{uuid4().hex[:8]}"
        _seed_journey(
            session,
            journey_id=journey_id,
            correlation_id=correlation_id,
            booking_reference=booking_reference,
            provider_reference=provider_reference,
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                booking_reference=booking_reference,
                metadata={
                    "journey_id": journey_id,
                    "scenario_context": {
                        "booking_reference": booking_reference,
                        "correlation_ref": correlation_id,
                        "status": "ready",
                    },
                },
            )
        )

        assert result.resolution_status == "single_match"
        assert result.selected is not None
        assert result.selected.source == "journey_store"
        assert result.selected.source_trust_level == "HIGH"
    finally:
        session.close()


def test_multiple_candidates_build_german_disambiguation_payload() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        address_id = f"addr-{uuid4().hex[:8]}"
        _seed_address(session, address_id=address_id, display_name="Hans-Peter")

        first_booking = f"book-{uuid4().hex[:8]}"
        second_booking = f"book-{uuid4().hex[:8]}"
        first_start = _future_start(24)
        second_start = _future_start(72)

        _seed_link(session, address_id=address_id, appointment_id=f"apt-{uuid4().hex[:8]}", booking_reference=first_booking, correlation_ref=f"corr-{first_booking}")
        _seed_link(session, address_id=address_id, appointment_id=f"apt-{uuid4().hex[:8]}", booking_reference=second_booking, correlation_ref=f"corr-{second_booking}")
        _seed_booking(
            session,
            booking_reference=first_booking,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Hans-Peter",
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=first_start,
            appointment_type="dentist",
            address_id=address_id,
        )
        _seed_booking(
            session,
            booking_reference=second_booking,
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id="Hans-Peter",
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=second_start,
            appointment_type="doctor",
            address_id=address_id,
        )

        result = resolver.resolve(
            AppointmentResolutionContext(
                customer_phone=None,
                address_id=address_id,
                locale="de",
            )
        )

        assert result.resolution_status == "multiple_matches"
        assert result.disambiguation_payload is not None
        assert result.disambiguation_payload.prompt == "Ich habe 2 Termine gefunden. Welchen möchten Sie bearbeiten?"
        assert len(result.disambiguation_payload.options) == 2
        assert all(option.option_id for option in result.disambiguation_payload.options)
        assert any("Dentist" in (option.subtitle or "") for option in result.disambiguation_payload.options)
    finally:
        session.close()


def test_multiple_candidates_build_english_disambiguation_payload() -> None:
    session = SessionLocal()
    try:
        resolver = ExistingBookingResolver(session)
        customer_name = f"Alice-{uuid4().hex[:8]}"
        _seed_booking(
            session,
            booking_reference=f"book-{uuid4().hex[:8]}",
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id=customer_name,
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=_future_start(30),
            appointment_type="doctor",
        )
        _seed_booking(
            session,
            booking_reference=f"book-{uuid4().hex[:8]}",
            journey_id=f"journey-{uuid4().hex[:8]}",
            customer_id=customer_name,
            provider_reference=f"prov-{uuid4().hex[:8]}",
            start_time=_future_start(54),
            appointment_type="technician",
        )

        result = resolver.resolve(AppointmentResolutionContext(customer_name=customer_name, locale="en"))

        assert result.resolution_status == "multiple_matches"
        assert result.disambiguation_payload is not None
        assert result.disambiguation_payload.prompt == "I found 2 appointments. Which one would you like to edit?"
        assert len(result.disambiguation_payload.options) == 2
        assert all("," in (option.title or "") for option in result.disambiguation_payload.options)
    finally:
        session.close()
