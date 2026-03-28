from __future__ import annotations

from datetime import timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from appointment_agent_shared.contracts import BookingResult, CandidateSlot, ContactUpsertCommand, CreateBookingCommand, ResolveCustomerCommand, SearchSlotsCommand
from appointment_agent_shared.repositories import BookingRepository, ContactRepository


class GoogleAdapterService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.bookings = BookingRepository(session)
        self.contacts = ContactRepository(session)

    def search_slots(self, command: SearchSlotsCommand) -> list[CandidateSlot]:
        base = command.date_window_start.replace(minute=0, second=0, microsecond=0)
        candidates = command.resource_candidates or ["default-calendar@example.com"]
        slots: list[CandidateSlot] = []
        for index in range(min(command.max_slots, len(candidates) * 2)):
            start = base + timedelta(days=index, hours=13 if command.preferred_daypart == "afternoon" else 9)
            slots.append(
                CandidateSlot(
                    slot_id=f"gslot-{index + 1}",
                    start_time=start,
                    end_time=start + timedelta(minutes=command.duration_minutes),
                    resource_id=candidates[index % len(candidates)],
                    timezone=command.timezone,
                    score=max(0.5, 0.95 - (index * 0.03)),
                )
            )
        return slots

    def create_booking(self, command: CreateBookingCommand) -> BookingResult:
        reference = f"gbook-{uuid4().hex[:10]}"
        external_id = f"google-{uuid4().hex[:12]}"
        self.bookings.save(
            booking_reference=reference,
            journey_id=command.journey_id,
            customer_id=command.customer_id,
            provider="google",
            external_id=external_id,
            status="confirmed",
            payload=command.model_dump(mode="json"),
        )
        return BookingResult(
            booking_reference=reference,
            provider="google",
            external_calendar_id=external_id,
            status="confirmed",
            details={"calendar_target": command.calendar_target, "slot_id": command.slot_id},
        )

    def upsert_contact(self, command: ContactUpsertCommand) -> dict[str, str]:
        record = self.contacts.upsert(command)
        return {"customer_id": record.customer_id, "status": "upserted"}

    def resolve_customer(self, command: ResolveCustomerCommand) -> dict[str, Optional[str]]:
        record = self.contacts.resolve(command)
        if record is None:
            return {"customer_id": None, "status": "not_found"}
        return {"customer_id": record.customer_id, "status": "resolved"}
