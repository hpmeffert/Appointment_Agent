from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .contracts import ContactUpsertCommand, ConversationTurnPayload, ResolveCustomerCommand
from .models import AppointmentJourneyRecord, AuditRecord, BookingRecord, CallbackReceipt, ContactRecord, ConversationTurnRecord


class ContactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, command: ContactUpsertCommand) -> ContactRecord:
        record = self.session.scalar(
            select(ContactRecord).where(ContactRecord.customer_id == command.customer_id)
        )
        if record is None:
            record = ContactRecord(
                tenant_id=command.tenant_id,
                customer_id=command.customer_id,
                full_name=command.full_name,
            )
            self.session.add(record)
        record.full_name = command.full_name
        record.phone = command.phone
        record.email = command.email
        record.consent_sms = command.consent_sms
        record.consent_rcs = command.consent_rcs
        record.details = command.metadata
        self.session.commit()
        self.session.refresh(record)
        return record

    def resolve(self, command: ResolveCustomerCommand) -> Optional[ContactRecord]:
        filters = []
        if command.phone:
            filters.append(ContactRecord.phone == command.phone)
        if command.email:
            filters.append(ContactRecord.email == command.email)
        if not filters:
            return None
        return self.session.scalar(
            select(ContactRecord).where(ContactRecord.tenant_id == command.tenant_id, or_(*filters))
        )


class BookingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        booking_reference: str,
        journey_id: str,
        customer_id: str,
        provider: str,
        external_id: str,
        status: str,
        payload: dict,
    ) -> BookingRecord:
        record = self.session.scalar(
            select(BookingRecord).where(BookingRecord.booking_reference == booking_reference)
        )
        if record is None:
            record = BookingRecord(
                booking_reference=booking_reference,
                journey_id=journey_id,
                customer_id=customer_id,
                provider=provider,
            )
            self.session.add(record)
        record.external_id = external_id
        record.status = status
        record.payload = payload
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, booking_reference: str) -> Optional[BookingRecord]:
        return self.session.scalar(
            select(BookingRecord).where(BookingRecord.booking_reference == booking_reference)
        )


class CallbackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, event_id: str, event_type: str, correlation_id: str, payload: dict, is_duplicate: bool) -> CallbackReceipt:
        receipt = CallbackReceipt(
            event_id=event_id,
            event_type=event_type,
            correlation_id=correlation_id,
            payload=payload,
            is_duplicate=is_duplicate,
        )
        self.session.add(receipt)
        self.session.commit()
        self.session.refresh(receipt)
        return receipt

    def exists(self, event_id: str) -> bool:
        return self.session.scalar(select(CallbackReceipt).where(CallbackReceipt.event_id == event_id)) is not None


class JourneyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, record: AppointmentJourneyRecord) -> AppointmentJourneyRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def upsert(self, **values: object) -> AppointmentJourneyRecord:
        record = self.get(values["journey_id"])
        if record is None:
            record = AppointmentJourneyRecord(**values)
            self.session.add(record)
        else:
            for key, value in values.items():
                setattr(record, key, value)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, journey_id: str) -> Optional[AppointmentJourneyRecord]:
        return self.session.scalar(
            select(AppointmentJourneyRecord).where(AppointmentJourneyRecord.journey_id == journey_id)
        )

    def mark_state(self, journey_id: str, state: str) -> AppointmentJourneyRecord:
        record = self.get(journey_id)
        if record is None:
            raise ValueError("Journey not found")
        record.current_state = state
        self.session.commit()
        self.session.refresh(record)
        return record

    def store_candidate_slots(self, journey_id: str, slots: list[dict]) -> AppointmentJourneyRecord:
        record = self.get(journey_id)
        if record is None:
            raise ValueError("Journey not found")
        record.candidate_slots = slots
        self.session.commit()
        self.session.refresh(record)
        return record

    def store_selected_slot(self, journey_id: str, slot: dict) -> AppointmentJourneyRecord:
        record = self.get(journey_id)
        if record is None:
            raise ValueError("Journey not found")
        record.selected_slot = slot
        self.session.commit()
        self.session.refresh(record)
        return record


class ConversationTurnRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(self, payload: ConversationTurnPayload) -> ConversationTurnRecord:
        record = ConversationTurnRecord(**payload.model_dump())
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        audit_id: str,
        tenant_id: str,
        journey_id: str,
        correlation_id: str,
        trace_id: str,
        decision_type: str,
        human_readable_message: str,
        payload: dict,
        reason_code: Optional[str] = None,
    ) -> AuditRecord:
        record = AuditRecord(
            audit_id=audit_id,
            tenant_id=tenant_id,
            journey_id=journey_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            decision_type=decision_type,
            reason_code=reason_code,
            human_readable_message=human_readable_message,
            payload=payload,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_for_journey(self, journey_id: str) -> list[AuditRecord]:
        return list(
            self.session.scalars(
                select(AuditRecord).where(AuditRecord.journey_id == journey_id).order_by(AuditRecord.created_at_utc.asc())
            )
        )
