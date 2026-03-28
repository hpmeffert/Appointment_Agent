from __future__ import annotations

from datetime import timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from appointment_agent_shared.commands import (
    CancelBookingCommand,
    CreateBookingCommand,
    ResolveCustomerCommand,
    SearchSlotsCommand,
    UpdateBookingCommand,
    UpsertCustomerCommand,
)
from appointment_agent_shared.enums import BookingStatus, ErrorCategory
from appointment_agent_shared.errors import ProviderError
from appointment_agent_shared.models import BookingResult, CandidateSlot, ProviderReference
from appointment_agent_shared.repositories import BookingRepository, ContactRepository


class GoogleAdapterException(Exception):
    def __init__(self, error: ProviderError) -> None:
        super().__init__(error.message)
        self.error = error


class GoogleAdapterServiceV101:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.bookings = BookingRepository(session)
        self.contacts = ContactRepository(session)

    def _make_provider_reference(self, external_id: str) -> ProviderReference:
        return ProviderReference(provider="google", external_id=external_id, operation="calendar_event")

    def search_slots(self, command: SearchSlotsCommand) -> list[CandidateSlot]:
        base = command.date_window_start.replace(minute=0, second=0, microsecond=0)
        candidates = command.resource_candidates or ["default-calendar@example.com"]
        slots: list[CandidateSlot] = []
        for index in range(min(command.max_slots, max(1, len(candidates) * 2))):
            start = base + timedelta(days=index, hours=13 if command.preferred_daypart == "afternoon" else 9)
            provider_ref = self._make_provider_reference("slot-{}-{}".format(index + 1, candidates[index % len(candidates)]))
            slots.append(
                CandidateSlot(
                    slot_id="gslot-{}".format(index + 1),
                    start_time=start,
                    end_time=start + timedelta(minutes=command.duration_minutes),
                    timezone=command.timezone,
                    resource_id=candidates[index % len(candidates)],
                    score=max(0.5, 0.95 - (index * 0.03)),
                    provider="google",
                    provider_reference=provider_ref.external_id,
                    metadata={"provider_reference": provider_ref.model_dump(mode="json")},
                )
            )
        return slots

    def create_booking(self, command: CreateBookingCommand) -> BookingResult:
        reference = command.booking_reference or "gbook-{}".format(uuid4().hex[:10])
        external_id = "google-{}".format(uuid4().hex[:12])
        provider_ref = self._make_provider_reference(external_id)
        payload = command.model_dump(mode="json")
        payload["provider_reference"] = provider_ref.model_dump(mode="json")
        self.bookings.save(
            booking_reference=reference,
            journey_id=command.journey_id,
            customer_id=command.customer_id or "unknown",
            provider="google",
            external_id=external_id,
            status=BookingStatus.CONFIRMED.value,
            payload=payload,
        )
        return BookingResult(
            booking_reference=reference,
            provider="google",
            external_calendar_id=external_id,
            provider_reference=provider_ref.external_id,
            status=BookingStatus.CONFIRMED,
            timezone=command.timezone,
            calendar_target=command.calendar_target,
            attendees=command.attendees,
            metadata={"provider_reference": provider_ref.model_dump(mode="json"), "journey_id": command.journey_id},
        )

    def update_booking(self, command: UpdateBookingCommand) -> BookingResult:
        record = self.bookings.get(command.booking_reference)
        if record is None:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="update_booking",
                    error_category=ErrorCategory.NOT_FOUND,
                    message="Booking reference was not found",
                )
            )
        if not command.provider_reference:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="update_booking",
                    error_category=ErrorCategory.VALIDATION,
                    message="Provider reference is required",
                )
            )
        payload = dict(record.payload or {})
        payload["updated"] = {
            "new_start": command.new_start.isoformat() if command.new_start else None,
            "new_end": command.new_end.isoformat() if command.new_end else None,
            "new_title": command.new_title,
            "new_description": command.new_description,
            "attendees": command.attendees,
        }
        self.bookings.save(
            booking_reference=record.booking_reference,
            journey_id=record.journey_id,
            customer_id=record.customer_id,
            provider=record.provider,
            external_id=command.provider_reference,
            status=BookingStatus.RESCHEDULED.value,
            payload=payload,
        )
        return BookingResult(
            booking_reference=record.booking_reference,
            provider="google",
            external_calendar_id=command.provider_reference,
            provider_reference=command.provider_reference,
            status=BookingStatus.RESCHEDULED,
            start_time=command.new_start,
            end_time=command.new_end,
            attendees=command.attendees,
            metadata={"updated": True},
        )

    def cancel_booking(self, command: CancelBookingCommand) -> BookingResult:
        record = self.bookings.get(command.booking_reference)
        if record is None:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="cancel_booking",
                    error_category=ErrorCategory.NOT_FOUND,
                    message="Booking reference was not found",
                )
            )
        if not command.provider_reference:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="cancel_booking",
                    error_category=ErrorCategory.VALIDATION,
                    message="Provider reference is required",
                )
            )
        payload = dict(record.payload or {})
        payload["cancelled"] = {"reason": command.reason, "requested_by": command.requested_by}
        self.bookings.save(
            booking_reference=record.booking_reference,
            journey_id=record.journey_id,
            customer_id=record.customer_id,
            provider=record.provider,
            external_id=command.provider_reference,
            status=BookingStatus.CANCELLED.value,
            payload=payload,
        )
        return BookingResult(
            booking_reference=record.booking_reference,
            provider="google",
            external_calendar_id=command.provider_reference,
            provider_reference=command.provider_reference,
            status=BookingStatus.CANCELLED,
            metadata={"cancelled": True, "reason": command.reason},
        )

    def get_booking(self, booking_reference: str) -> BookingResult:
        record = self.bookings.get(booking_reference)
        if record is None:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="get_booking",
                    error_category=ErrorCategory.NOT_FOUND,
                    message="Booking reference was not found",
                )
            )
        provider_reference = None
        if isinstance(record.payload, dict):
            provider_reference = (record.payload.get("provider_reference") or {}).get("external_id")
        return BookingResult(
            booking_reference=record.booking_reference,
            provider=record.provider,
            external_calendar_id=record.external_id,
            provider_reference=provider_reference or record.external_id,
            status=record.status,
            metadata={"stored_payload": bool(record.payload)},
        )

    def upsert_contact(self, command: UpsertCustomerCommand) -> dict[str, str]:
        record = self.contacts.upsert(command)
        return {"customer_id": record.customer_id, "status": "upserted"}

    def resolve_customer(self, command: ResolveCustomerCommand) -> dict[str, Optional[str]]:
        record = self.contacts.resolve(command)
        if record is None:
            return {"customer_id": None, "status": "not_found"}
        return {"customer_id": record.customer_id, "status": "resolved"}
