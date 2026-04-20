from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as dt_timezone
from hashlib import sha256
import json
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .contracts import ContactUpsertCommand, ConversationTurnPayload, ResolveCustomerCommand
from .models import (
    AddressAppointmentLinkRecord,
    AddressRecord,
    AppointmentJourneyRecord,
    AppointmentCacheRecord,
    AuditRecord,
    BookingRecord,
    CallbackReceipt,
    ContactRecord,
    ConversationTurnRecord,
    DemoScenarioContextRecord,
    GoogleDemoEventRecord,
    LekabConfigRecord,
    MessageRecord,
    ReminderAuditRecord,
    ReminderJobRecord,
    ReminderPolicyRecord,
    ReminderRuntimeHealthSnapshot,
    SlotHoldRecord,
)


@dataclass
class AppointmentCacheSyncResult:
    """Describe how one sync snapshot affected the appointment cache."""

    record: AppointmentCacheRecord
    action: str
    hash_changed: bool
    status_changed: bool
    created: bool = False
    updated: bool = False
    cancelled: bool = False


@dataclass
class AddressLinkageResolution:
    """Describe the best-known cross-module linkage for one business entity."""

    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None
    correlation_ref: Optional[str] = None


def _stable_sync_metadata(metadata: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Strip volatile sync keys before hashing appointment metadata.

    The Reminder Scheduler sync hash must not include values that are expected
    to change on every polling run, otherwise we would get a never-ending
    "hash chasing" loop. The helper removes the sync marker fields before we
    serialize the payload for hashing.
    """

    metadata = dict(metadata or {})
    for key in ("sync_hash", "created_at_utc", "updated_at_utc", "last_seen_at_utc"):
        metadata.pop(key, None)
    return metadata


def _normalize_phone_lookup(value: Optional[str]) -> Optional[str]:
    """Reduce phone values to digits so loose cross-module matching stays stable."""

    if not value:
        return None
    digits = "".join(character for character in str(value) if character.isdigit())
    return digits or None


def build_appointment_source_hash(
    *,
    external_appointment_id: str,
    start_at_utc: datetime,
    end_at_utc: datetime,
    timezone: str,
    status: str,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    contact_id: Optional[str] = None,
    source_system: str = "reminder_scheduler",
    source_reference: str = "global",
    source_metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Build a deterministic hash for one normalized appointment snapshot."""

    payload = {
        "external_appointment_id": external_appointment_id,
        "start_at_utc": start_at_utc.astimezone(dt_timezone.utc).isoformat(),
        "end_at_utc": end_at_utc.astimezone(dt_timezone.utc).isoformat(),
        "timezone": timezone,
        "status": status,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        "contact_id": contact_id,
        "source_system": source_system,
        "source_reference": source_reference,
        "source_metadata": _stable_sync_metadata(source_metadata),
    }
    digest = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(digest).hexdigest()


def build_reminder_dispatch_key(
    external_appointment_id: str,
    reminder_sequence: int,
    channel: str,
    *,
    calendar_source: Optional[str] = None,
) -> str:
    """Build the stable key that prevents duplicate reminder jobs.

    The Reminder Scheduler uses this key for deduplication, job lookup and
    operational tracing. The order is intentionally fixed so a job can be
    reconstructed from the same business inputs in every release.
    """

    appointment_id = external_appointment_id.strip()
    channel_name = channel.strip()
    if not appointment_id:
        raise ValueError("external_appointment_id must not be empty")
    if reminder_sequence < 1:
        raise ValueError("reminder_sequence must be at least 1")
    if not channel_name:
        raise ValueError("channel must not be empty")
    parts = [appointment_id, str(reminder_sequence), channel_name]
    if calendar_source:
        source = calendar_source.strip()
        if source:
            parts.insert(0, source)
    return ":".join(parts)


def _count_grouped_values(
    session: Session,
    model: Any,
    column: Any,
    *,
    filters: tuple[Any, ...] = (),
) -> dict[str, int]:
    """Return a stable ``value -> count`` mapping for one table column."""

    query = select(column, func.count()).select_from(model)
    for condition in filters:
        query = query.where(condition)
    query = query.group_by(column)
    return {str(value): int(count or 0) for value, count in session.execute(query).all()}


def build_reminder_runtime_health_snapshot(
    session: Session,
    *,
    tenant_id: str = "default",
    policy_name: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> ReminderRuntimeHealthSnapshot:
    """Collect a compact, release-friendly runtime picture for the scheduler.

    The Reminder Scheduler does not need a heavyweight health system here.
    It only needs a consistent summary of what is planned, what is stuck, and
    what the last activity looked like. Keeping this as a shared helper lets
    the delivery layer, worker, and tests reason about the same snapshot.
    """

    now_utc = now_utc or datetime.now(dt_timezone.utc)
    policy_record = (
        ReminderPolicyRepository(session).get(tenant_id, policy_name or "default")
        if policy_name is not None
        else None
    )
    policy_id = policy_record.id if policy_record is not None else None

    job_filters: tuple[Any, ...] = (ReminderJobRecord.tenant_id == tenant_id,)
    if policy_name is not None:
        job_filters = job_filters + (ReminderJobRecord.policy_name == policy_name,)
    job_counts = _count_grouped_values(session, ReminderJobRecord, ReminderJobRecord.status, filters=job_filters)
    hold_counts = _count_grouped_values(session, SlotHoldRecord, SlotHoldRecord.status)
    message_counts = _count_grouped_values(session, MessageRecord, MessageRecord.status)
    audit_filters: tuple[Any, ...] = (ReminderAuditRecord.tenant_id == tenant_id,)
    audit_counts = _count_grouped_values(session, ReminderAuditRecord, ReminderAuditRecord.event_type, filters=audit_filters)

    if policy_id is not None:
        appointment_count = int(
            session.scalar(
                select(func.count())
                .select_from(AppointmentCacheRecord)
                .where(AppointmentCacheRecord.tenant_id == tenant_id)
                .where(AppointmentCacheRecord.reminder_policy_id == policy_id)
            )
            or 0
        )
    else:
        appointment_count = int(
            session.scalar(
                select(func.count())
                .select_from(AppointmentCacheRecord)
                .where(AppointmentCacheRecord.tenant_id == tenant_id)
            )
            or 0
        )

    next_due_query = select(func.min(ReminderJobRecord.scheduled_for_utc)).where(ReminderJobRecord.tenant_id == tenant_id)
    last_job_query = select(func.max(ReminderJobRecord.updated_at_utc)).where(ReminderJobRecord.tenant_id == tenant_id)
    reclaimable_query = (
        select(func.count())
        .select_from(ReminderJobRecord)
        .where(ReminderJobRecord.tenant_id == tenant_id)
        .where(ReminderJobRecord.status == "dispatching")
        .where(ReminderJobRecord.locked_until_utc.is_not(None))
        .where(ReminderJobRecord.locked_until_utc <= now_utc)
    )
    if policy_name is not None:
        next_due_query = next_due_query.where(ReminderJobRecord.policy_name == policy_name)
        last_job_query = last_job_query.where(ReminderJobRecord.policy_name == policy_name)
        reclaimable_query = reclaimable_query.where(ReminderJobRecord.policy_name == policy_name)
    next_due_query = next_due_query.where(ReminderJobRecord.status.in_(ReminderJobRecord.ACTIVE_STATUSES))
    next_due_at_utc = session.scalar(next_due_query)
    last_job_activity_at_utc = session.scalar(last_job_query)
    last_hold_activity_at_utc = session.scalar(select(func.max(SlotHoldRecord.updated_at)))
    last_message_activity_at_utc = session.scalar(select(func.max(MessageRecord.updated_at)))
    last_audit_activity_at_utc = session.scalar(
        select(func.max(ReminderAuditRecord.created_at_utc))
        .where(ReminderAuditRecord.tenant_id == tenant_id)
    )
    reclaimable_lock_count = int(session.scalar(reclaimable_query) or 0)

    active_job_count = sum(job_counts.get(status, 0) for status in ReminderJobRecord.ACTIVE_STATUSES)
    active_hold_count = hold_counts.get("ACTIVE", 0)
    health_notes: list[str] = []
    if job_counts.get("failed", 0):
        health_notes.append(f"{job_counts['failed']} reminder jobs are failed and need attention")
    if reclaimable_lock_count:
        health_notes.append(f"{reclaimable_lock_count} reminder jobs have expired dispatch locks")
    if active_hold_count:
        health_notes.append(f"{active_hold_count} slot holds are still active")
    if policy_record is None and policy_name is not None:
        health_notes.append(f"Policy '{policy_name}' was not found for tenant '{tenant_id}'")

    return ReminderRuntimeHealthSnapshot(
        tenant_id=tenant_id,
        policy_name=policy_name,
        as_of_utc=now_utc,
        appointment_count=appointment_count,
        job_counts=job_counts,
        hold_counts=hold_counts,
        message_counts=message_counts,
        audit_counts=audit_counts,
        next_due_at_utc=next_due_at_utc,
        last_job_activity_at_utc=last_job_activity_at_utc,
        last_hold_activity_at_utc=last_hold_activity_at_utc,
        last_message_activity_at_utc=last_message_activity_at_utc,
        last_audit_activity_at_utc=last_audit_activity_at_utc,
        active_job_count=active_job_count,
        active_hold_count=active_hold_count,
        reclaimable_lock_count=reclaimable_lock_count,
        health_notes=health_notes,
    )


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


class AddressRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_or_update(
        self,
        *,
        address_id: str,
        display_name: str,
        tenant_id: str = "default",
        external_ref: Optional[str] = None,
        customer_number: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None,
        street: Optional[str] = None,
        house_number: Optional[str] = None,
        postal_code: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        timezone: Optional[str] = None,
        preferred_channel: Optional[str] = None,
        notes: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        application_id: Optional[str] = None,
        is_active: bool = True,
    ) -> AddressRecord:
        record = self.get(address_id)
        if record is None:
            record = AddressRecord(address_id=address_id, display_name=display_name, tenant_id=tenant_id)
            self.session.add(record)
        record.external_ref = external_ref
        record.customer_number = customer_number
        record.display_name = display_name
        record.first_name = first_name
        record.last_name = last_name
        record.company_name = company_name
        record.street = street
        record.house_number = house_number
        record.postal_code = postal_code
        record.city = city
        record.country = country
        record.email = email
        record.phone = phone
        record.timezone = timezone
        record.preferred_channel = preferred_channel
        record.notes = notes
        record.correlation_ref = correlation_ref
        record.tenant_id = tenant_id
        record.application_id = application_id
        record.is_active = is_active
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, address_id: str) -> Optional[AddressRecord]:
        return self.session.scalar(select(AddressRecord).where(AddressRecord.address_id == address_id))

    def list_addresses(
        self,
        *,
        tenant_id: Optional[str] = None,
        query_text: Optional[str] = None,
        city: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 200,
    ) -> list[AddressRecord]:
        query = select(AddressRecord)
        if tenant_id:
            query = query.where(AddressRecord.tenant_id == tenant_id)
        if is_active is not None:
            query = query.where(AddressRecord.is_active == is_active)
        if city:
            query = query.where(AddressRecord.city.ilike(f"%{city}%"))
        if query_text:
            like_value = f"%{query_text}%"
            query = query.where(
                or_(
                    AddressRecord.display_name.ilike(like_value),
                    AddressRecord.email.ilike(like_value),
                    AddressRecord.phone.ilike(like_value),
                    AddressRecord.city.ilike(like_value),
                )
            )
        query = query.order_by(AddressRecord.updated_at.desc()).limit(limit)
        return list(self.session.scalars(query))

    def deactivate(self, address_id: str) -> Optional[AddressRecord]:
        record = self.get(address_id)
        if record is None:
            return None
        record.is_active = False
        self.session.commit()
        self.session.refresh(record)
        return record

    def find_active_by_contact(
        self,
        *,
        tenant_id: str = "default",
        phone: Optional[str] = None,
        email: Optional[str] = None,
        correlation_ref: Optional[str] = None,
    ) -> Optional[AddressRecord]:
        query = select(AddressRecord).where(AddressRecord.tenant_id == tenant_id, AddressRecord.is_active.is_(True))
        if correlation_ref:
            record = self.session.scalar(query.where(AddressRecord.correlation_ref == correlation_ref))
            if record is not None:
                return record
        if email:
            record = self.session.scalar(query.where(AddressRecord.email == email))
            if record is not None:
                return record
        normalized_phone = _normalize_phone_lookup(phone)
        if normalized_phone:
            candidates = list(self.session.scalars(query.where(AddressRecord.phone.is_not(None))))
            for candidate in candidates:
                candidate_phone = _normalize_phone_lookup(candidate.phone)
                if candidate_phone == normalized_phone:
                    return candidate
                if candidate_phone and normalized_phone.endswith(candidate_phone):
                    return candidate
                if candidate_phone and candidate_phone.endswith(normalized_phone):
                    return candidate
        return None


class AddressAppointmentLinkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def link(
        self,
        *,
        link_id: str,
        address_id: str,
        appointment_external_id: str,
        tenant_id: str = "default",
        booking_reference: Optional[str] = None,
        calendar_ref: Optional[str] = None,
        correlation_ref: Optional[str] = None,
    ) -> AddressAppointmentLinkRecord:
        record = self.session.scalar(
            select(AddressAppointmentLinkRecord).where(
                AddressAppointmentLinkRecord.address_id == address_id,
                AddressAppointmentLinkRecord.appointment_external_id == appointment_external_id,
            )
        )
        if record is None:
            record = AddressAppointmentLinkRecord(
                link_id=link_id,
                address_id=address_id,
                appointment_external_id=appointment_external_id,
                tenant_id=tenant_id,
            )
            self.session.add(record)
        record.booking_reference = booking_reference
        record.calendar_ref = calendar_ref
        record.correlation_ref = correlation_ref
        record.tenant_id = tenant_id
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_for_address(self, address_id: str) -> list[AddressAppointmentLinkRecord]:
        return list(
            self.session.scalars(
                select(AddressAppointmentLinkRecord)
                .where(AddressAppointmentLinkRecord.address_id == address_id)
                .order_by(AddressAppointmentLinkRecord.updated_at.desc())
            )
        )

    def list_for_appointment(self, appointment_external_id: str) -> list[AddressAppointmentLinkRecord]:
        return list(
            self.session.scalars(
                select(AddressAppointmentLinkRecord)
                .where(AddressAppointmentLinkRecord.appointment_external_id == appointment_external_id)
                .order_by(AddressAppointmentLinkRecord.updated_at.desc())
            )
        )

    def get_by_appointment_external_id(
        self,
        appointment_external_id: str,
        *,
        tenant_id: str = "default",
    ) -> Optional[AddressAppointmentLinkRecord]:
        return self.session.scalar(
            select(AddressAppointmentLinkRecord).where(
                AddressAppointmentLinkRecord.tenant_id == tenant_id,
                AddressAppointmentLinkRecord.appointment_external_id == appointment_external_id,
            )
        )

    def get_by_booking_reference(
        self,
        booking_reference: str,
        *,
        tenant_id: str = "default",
    ) -> Optional[AddressAppointmentLinkRecord]:
        return self.session.scalar(
            select(AddressAppointmentLinkRecord).where(
                AddressAppointmentLinkRecord.tenant_id == tenant_id,
                AddressAppointmentLinkRecord.booking_reference == booking_reference,
            )
        )

    def get_by_correlation_ref(
        self,
        correlation_ref: str,
        *,
        tenant_id: str = "default",
    ) -> Optional[AddressAppointmentLinkRecord]:
        return self.session.scalar(
            select(AddressAppointmentLinkRecord).where(
                AddressAppointmentLinkRecord.tenant_id == tenant_id,
                AddressAppointmentLinkRecord.correlation_ref == correlation_ref,
            )
        )


class AddressLinkageResolver:
    """Resolve one Address anchor from booking, appointment, correlation, or contact data.

    The same business actor can surface through multiple modules at different
    stages. Keeping the fallback order in one helper avoids each module
    inventing slightly different correlation rules.
    """

    def __init__(self, session: Session) -> None:
        self.addresses = AddressRepository(session)
        self.links = AddressAppointmentLinkRepository(session)

    def resolve(
        self,
        *,
        tenant_id: str = "default",
        address_id: Optional[str] = None,
        appointment_id: Optional[str] = None,
        booking_reference: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> AddressLinkageResolution:
        if address_id:
            address_record = self.addresses.get(address_id)
            if address_record is not None:
                return AddressLinkageResolution(
                    address_id=address_record.address_id,
                    appointment_id=appointment_id,
                    booking_reference=booking_reference,
                    correlation_ref=correlation_ref or address_record.correlation_ref,
                )

        link_record = None
        if booking_reference:
            link_record = self.links.get_by_booking_reference(booking_reference, tenant_id=tenant_id)
        if link_record is None and appointment_id:
            link_record = self.links.get_by_appointment_external_id(appointment_id, tenant_id=tenant_id)
        if link_record is None and correlation_ref:
            link_record = self.links.get_by_correlation_ref(correlation_ref, tenant_id=tenant_id)
        if link_record is not None:
            return AddressLinkageResolution(
                address_id=link_record.address_id,
                appointment_id=appointment_id or link_record.appointment_external_id,
                booking_reference=booking_reference or link_record.booking_reference,
                correlation_ref=correlation_ref or link_record.correlation_ref,
            )

        address_record = self.addresses.find_active_by_contact(
            tenant_id=tenant_id,
            phone=phone_number,
            email=email,
            correlation_ref=correlation_ref,
        )
        if address_record is not None:
            linked_records = self.links.list_for_address(address_record.address_id)
            primary_link = linked_records[0] if linked_records else None
            return AddressLinkageResolution(
                address_id=address_record.address_id,
                appointment_id=appointment_id or getattr(primary_link, "appointment_external_id", None),
                booking_reference=booking_reference or getattr(primary_link, "booking_reference", None),
                correlation_ref=correlation_ref or getattr(primary_link, "correlation_ref", None) or address_record.correlation_ref,
            )

        return AddressLinkageResolution(
            address_id=address_id,
            appointment_id=appointment_id,
            booking_reference=booking_reference,
            correlation_ref=correlation_ref,
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

    def get_by_correlation_id(self, correlation_id: str) -> Optional[AppointmentJourneyRecord]:
        return self.session.scalar(
            select(AppointmentJourneyRecord)
            .where(AppointmentJourneyRecord.correlation_id == correlation_id)
            .order_by(AppointmentJourneyRecord.updated_at.desc())
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


class ReminderPolicyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, tenant_id: str = "default", policy_name: str = "default") -> Optional[ReminderPolicyRecord]:
        return self.session.scalar(
            select(ReminderPolicyRecord).where(
                ReminderPolicyRecord.tenant_id == tenant_id,
                ReminderPolicyRecord.policy_name == policy_name,
            )
        )

    def list_for_tenant(self, tenant_id: str = "default") -> list[ReminderPolicyRecord]:
        return list(
            self.session.scalars(
                select(ReminderPolicyRecord)
                .where(ReminderPolicyRecord.tenant_id == tenant_id)
                .order_by(ReminderPolicyRecord.policy_name.asc(), ReminderPolicyRecord.updated_at_utc.desc())
            )
        )

    def upsert(
        self,
        *,
        tenant_id: str = "default",
        policy_name: str = "default",
        **values: object,
    ) -> ReminderPolicyRecord:
        record = self.get(tenant_id, policy_name)
        if record is None:
            record = ReminderPolicyRecord(tenant_id=tenant_id, policy_name=policy_name)
            self.session.add(record)
        for key, value in values.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self.session.commit()
        self.session.refresh(record)
        return record


class AppointmentCacheRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_source_identity(
        self,
        *,
        tenant_id: str = "default",
        external_appointment_id: str,
        calendar_source_type: str,
        calendar_source_ref: str,
    ) -> Optional[AppointmentCacheRecord]:
        """Return the cached appointment row for one stable source identity."""

        return self.session.scalar(
            select(AppointmentCacheRecord).where(
                AppointmentCacheRecord.tenant_id == tenant_id,
                AppointmentCacheRecord.external_appointment_id == external_appointment_id,
                AppointmentCacheRecord.calendar_source_type == calendar_source_type,
                AppointmentCacheRecord.calendar_source_ref == calendar_source_ref,
            )
        )

    def list_for_source(
        self,
        *,
        tenant_id: str = "default",
        calendar_source_type: str,
        calendar_source_ref: str,
        statuses: Optional[tuple[str, ...]] = None,
        limit: int = 500,
    ) -> list[AppointmentCacheRecord]:
        """List cached appointments for one external source.

        This is the query shape the reminder sync loop needs when it wants to
        compare a calendar provider snapshot against the current local cache.
        """

        query = (
            select(AppointmentCacheRecord)
            .where(AppointmentCacheRecord.tenant_id == tenant_id)
            .where(AppointmentCacheRecord.calendar_source_type == calendar_source_type)
            .where(AppointmentCacheRecord.calendar_source_ref == calendar_source_ref)
        )
        if statuses:
            query = query.where(AppointmentCacheRecord.status.in_(statuses))
        query = query.order_by(AppointmentCacheRecord.start_at_utc.asc()).limit(limit)
        return list(self.session.scalars(query))

    def upsert(
        self,
        *,
        tenant_id: str = "default",
        external_appointment_id: str,
        calendar_source_type: str,
        calendar_source_ref: str,
        **values: object,
    ) -> AppointmentCacheRecord:
        record = self.session.scalar(
            select(AppointmentCacheRecord).where(
                AppointmentCacheRecord.tenant_id == tenant_id,
                AppointmentCacheRecord.external_appointment_id == external_appointment_id,
                AppointmentCacheRecord.calendar_source_type == calendar_source_type,
                AppointmentCacheRecord.calendar_source_ref == calendar_source_ref,
            )
        )
        if record is None:
            record = AppointmentCacheRecord(
                tenant_id=tenant_id,
                external_appointment_id=external_appointment_id,
                calendar_source_type=calendar_source_type,
                calendar_source_ref=calendar_source_ref,
            )
            self.session.add(record)
        for key, value in values.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self.session.commit()
        self.session.refresh(record)
        return record

    def upsert_synced_appointment(
        self,
        *,
        tenant_id: str = "default",
        external_appointment_id: str,
        calendar_source_type: str,
        calendar_source_ref: str,
        title: str,
        start_at_utc: datetime,
        end_at_utc: Optional[datetime],
        timezone: str,
        status: str,
        participant_ref: Optional[str] = None,
        contact_ref: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address_id: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        reminder_policy_id: Optional[int] = None,
        raw_payload_json: Optional[dict[str, Any]] = None,
        source_hash: Optional[str] = None,
        last_seen_at_utc: Optional[datetime] = None,
    ) -> AppointmentCacheSyncResult:
        """Create or refresh one cached appointment row from sync input.

        The method is intentionally idempotent. Repeating the same sync payload
        will reuse the existing row and only update freshness metadata. If the
        caller passes a new ``source_hash`` or a changed status, the helper
        updates the row in place and reports that the cache changed.
        """

        record = self.get_by_source_identity(
            tenant_id=tenant_id,
            external_appointment_id=external_appointment_id,
            calendar_source_type=calendar_source_type,
            calendar_source_ref=calendar_source_ref,
        )
        created = record is None
        now = last_seen_at_utc or datetime.now(dt_timezone.utc)
        if source_hash is None:
            source_hash = build_appointment_source_hash(
                external_appointment_id=external_appointment_id,
                start_at_utc=start_at_utc,
                end_at_utc=end_at_utc or start_at_utc,
                timezone=timezone,
                status=status,
                contact_email=email,
                contact_phone=phone,
                contact_id=contact_ref or participant_ref,
                source_system=calendar_source_type,
                source_reference=calendar_source_ref,
                source_metadata=raw_payload_json,
            )
        if record is None:
            record = AppointmentCacheRecord(
                tenant_id=tenant_id,
                external_appointment_id=external_appointment_id,
                calendar_source_type=calendar_source_type,
                calendar_source_ref=calendar_source_ref,
                title=title,
                description=(raw_payload_json or {}).get("description"),
                location=(raw_payload_json or {}).get("location"),
                start_at_utc=start_at_utc,
                end_at_utc=end_at_utc,
                timezone=timezone,
                status=status,
                participant_ref=participant_ref,
                contact_ref=contact_ref,
                email=email,
                phone=phone,
                address_id=address_id,
                correlation_ref=correlation_ref,
                reminder_policy_id=reminder_policy_id,
                raw_payload_json=raw_payload_json or {},
                source_hash=source_hash,
                last_seen_at_utc=now,
            )
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return AppointmentCacheSyncResult(
                record=record,
                action="created",
                hash_changed=True,
                status_changed=False,
                created=True,
            )

        hash_changed = not record.matches_source_hash(source_hash)
        status_changed = record.status != status
        refresh_needed = record.needs_sync_refresh(source_hash=source_hash, status=status)
        if refresh_needed:
            record.title = title
            record.description = (raw_payload_json or {}).get("description")
            record.location = (raw_payload_json or {}).get("location")
            record.start_at_utc = start_at_utc
            record.end_at_utc = end_at_utc
            record.timezone = timezone
            record.status = status
            record.participant_ref = participant_ref
            record.contact_ref = contact_ref
            record.email = email
            record.phone = phone
            record.address_id = address_id
            record.correlation_ref = correlation_ref
            record.reminder_policy_id = reminder_policy_id
            record.raw_payload_json = raw_payload_json or {}
            record.source_hash = source_hash
        record.last_seen_at_utc = now
        self.session.commit()
        self.session.refresh(record)
        return AppointmentCacheSyncResult(
            record=record,
            action="updated" if (hash_changed or status_changed) else "unchanged",
            hash_changed=hash_changed,
            status_changed=status_changed,
            updated=hash_changed or status_changed,
        )

    def reconcile_synced_appointment(
        self,
        *,
        tenant_id: str = "default",
        external_appointment_id: str,
        calendar_source_type: str,
        calendar_source_ref: str,
        title: str,
        start_at_utc: datetime,
        end_at_utc: Optional[datetime],
        timezone: str,
        status: str,
        participant_ref: Optional[str] = None,
        contact_ref: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address_id: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        reminder_policy_id: Optional[int] = None,
        raw_payload_json: Optional[dict[str, Any]] = None,
        source_hash: Optional[str] = None,
        last_seen_at_utc: Optional[datetime] = None,
    ) -> AppointmentCacheSyncResult:
        """Apply one normalized appointment snapshot and keep cancellations explicit."""

        normalized_status = status.lower().strip()
        result = self.upsert_synced_appointment(
            tenant_id=tenant_id,
            external_appointment_id=external_appointment_id,
            calendar_source_type=calendar_source_type,
            calendar_source_ref=calendar_source_ref,
            title=title,
            start_at_utc=start_at_utc,
            end_at_utc=end_at_utc,
            timezone=timezone,
            status=normalized_status,
            participant_ref=participant_ref,
            contact_ref=contact_ref,
            email=email,
            phone=phone,
            address_id=address_id,
            correlation_ref=correlation_ref,
            reminder_policy_id=reminder_policy_id,
            raw_payload_json=raw_payload_json,
            source_hash=source_hash,
            last_seen_at_utc=last_seen_at_utc,
        )
        if normalized_status == "cancelled":
            result.record.status = "cancelled"
            result.record.locked_until_utc = None
            self.session.commit()
            self.session.refresh(result.record)
            return AppointmentCacheSyncResult(
                record=result.record,
                action="cancelled",
                hash_changed=result.hash_changed,
                status_changed=True if result.record.status == "cancelled" else result.status_changed,
                created=result.created,
                updated=result.updated,
                cancelled=True,
            )
        return result

    def list_due_for_window(
        self,
        *,
        tenant_id: str = "default",
        window_start,
        window_end,
    ) -> list[AppointmentCacheRecord]:
        query = (
            select(AppointmentCacheRecord)
            .where(AppointmentCacheRecord.tenant_id == tenant_id)
            .where(AppointmentCacheRecord.start_at_utc >= window_start)
            .where(AppointmentCacheRecord.start_at_utc <= window_end)
            .order_by(AppointmentCacheRecord.start_at_utc.asc())
        )
        return list(self.session.scalars(query))


class ReminderJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_identity(
        self,
        *,
        tenant_id: str = "default",
        appointment_id: str,
        reminder_sequence: int,
        channel: str,
        policy_name: Optional[str] = None,
    ) -> Optional[ReminderJobRecord]:
        query = select(ReminderJobRecord).where(
            ReminderJobRecord.tenant_id == tenant_id,
            ReminderJobRecord.appointment_id == appointment_id,
            ReminderJobRecord.reminder_sequence == reminder_sequence,
            ReminderJobRecord.channel == channel,
        )
        if policy_name is not None:
            query = query.where(ReminderJobRecord.policy_name == policy_name)
        return self.session.scalar(query)

    def upsert(self, *, job_id: str, **values: object) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            record = ReminderJobRecord(job_id=job_id, **values)
            self.session.add(record)
        else:
            for key, value in values.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, job_id: str) -> Optional[ReminderJobRecord]:
        return self.session.scalar(select(ReminderJobRecord).where(ReminderJobRecord.job_id == job_id))

    def list_for_identity(
        self,
        *,
        tenant_id: str = "default",
        appointment_id: str,
        reminder_sequence: Optional[int] = None,
        channel: Optional[str] = None,
        policy_name: Optional[str] = None,
    ) -> list[ReminderJobRecord]:
        query = select(ReminderJobRecord).where(
            ReminderJobRecord.tenant_id == tenant_id,
            ReminderJobRecord.appointment_id == appointment_id,
        )
        if reminder_sequence is not None:
            query = query.where(ReminderJobRecord.reminder_sequence == reminder_sequence)
        if channel is not None:
            query = query.where(ReminderJobRecord.channel == channel)
        if policy_name is not None:
            query = query.where(ReminderJobRecord.policy_name == policy_name)
        query = query.order_by(
            ReminderJobRecord.reminder_sequence.asc(),
            ReminderJobRecord.channel.asc(),
            ReminderJobRecord.created_at_utc.asc(),
        )
        return list(self.session.scalars(query))

    def list_active_for_identity(
        self,
        *,
        tenant_id: str = "default",
        appointment_id: str,
        reminder_sequence: Optional[int] = None,
        channel: Optional[str] = None,
        policy_name: Optional[str] = None,
    ) -> list[ReminderJobRecord]:
        query = select(ReminderJobRecord).where(
            ReminderJobRecord.tenant_id == tenant_id,
            ReminderJobRecord.appointment_id == appointment_id,
            ReminderJobRecord.status.in_(("planned", "due", "dispatching")),
        )
        if reminder_sequence is not None:
            query = query.where(ReminderJobRecord.reminder_sequence == reminder_sequence)
        if channel is not None:
            query = query.where(ReminderJobRecord.channel == channel)
        if policy_name is not None:
            query = query.where(ReminderJobRecord.policy_name == policy_name)
        query = query.order_by(
            ReminderJobRecord.reminder_sequence.asc(),
            ReminderJobRecord.channel.asc(),
            ReminderJobRecord.created_at_utc.asc(),
        )
        return list(self.session.scalars(query))

    def list_due(
        self,
        *,
        tenant_id: str = "default",
        now,
        limit: int = 100,
    ) -> list[ReminderJobRecord]:
        query = (
            select(ReminderJobRecord)
            .where(ReminderJobRecord.tenant_id == tenant_id)
            .where(ReminderJobRecord.status.in_(("planned", "due")))
            .where(ReminderJobRecord.scheduled_for_utc <= now)
            .order_by(ReminderJobRecord.scheduled_for_utc.asc())
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def list_reclaimable_locks(
        self,
        *,
        tenant_id: str = "default",
        now: datetime,
        limit: int = 100,
    ) -> list[ReminderJobRecord]:
        query = (
            select(ReminderJobRecord)
            .where(ReminderJobRecord.tenant_id == tenant_id)
            .where(ReminderJobRecord.status == "dispatching")
            .where(ReminderJobRecord.locked_until_utc.is_not(None))
            .where(ReminderJobRecord.locked_until_utc <= now)
            .order_by(ReminderJobRecord.locked_until_utc.asc())
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def lock_due_jobs(
        self,
        *,
        tenant_id: str = "default",
        now: datetime,
        lock_seconds: int = 300,
        limit: int = 100,
    ) -> list[ReminderJobRecord]:
        jobs = self.list_due(tenant_id=tenant_id, now=now, limit=limit)
        locked_until = now + timedelta(seconds=lock_seconds)
        for job in jobs:
            job.status = "dispatching"
            job.locked_until_utc = locked_until
        self.session.commit()
        for job in jobs:
            self.session.refresh(job)
        return jobs

    def mark_dispatching(
        self,
        job_id: str,
        *,
        locked_until_utc: Optional[datetime] = None,
        increment_attempt: bool = False,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.status = "dispatching"
        if increment_attempt:
            record.attempt_count += 1
        record.locked_until_utc = locked_until_utc
        self.session.commit()
        self.session.refresh(record)
        return record

    def mark_planned(
        self,
        job_id: str,
        *,
        locked_until_utc: Optional[datetime] = None,
        skip_reason_code: Optional[str] = None,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.status = "planned"
        record.locked_until_utc = locked_until_utc
        record.skip_reason_code = skip_reason_code
        self.session.commit()
        self.session.refresh(record)
        return record

    def mark_sent(
        self,
        job_id: str,
        *,
        provider_message_id: Optional[str] = None,
        dispatched_at_utc: Optional[datetime] = None,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.status = "sent"
        record.provider_message_id = provider_message_id
        record.dispatched_at_utc = dispatched_at_utc or datetime.now(dt_timezone.utc)
        record.locked_until_utc = None
        self.session.commit()
        self.session.refresh(record)
        return record

    def mark_failed(
        self,
        job_id: str,
        *,
        failure_reason_code: Optional[str] = None,
        failure_reason_text: Optional[str] = None,
        retryable: bool = False,
        locked_until_utc: Optional[datetime] = None,
        max_attempts: Optional[int] = None,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.attempt_count += 1
        record.failure_reason_code = failure_reason_code
        record.failure_reason_text = failure_reason_text
        record.locked_until_utc = None
        limit = max_attempts if max_attempts is not None else record.max_attempts
        if retryable and record.attempt_count < limit:
            record.status = "planned"
            record.skip_reason_code = None
        else:
            record.status = "failed"
        if locked_until_utc is not None:
            record.locked_until_utc = locked_until_utc
        self.session.commit()
        self.session.refresh(record)
        return record

    def mark_skipped(
        self,
        job_id: str,
        *,
        skip_reason_code: Optional[str] = None,
        failure_reason_text: Optional[str] = None,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.status = "skipped"
        record.skip_reason_code = skip_reason_code
        record.failure_reason_text = failure_reason_text
        record.locked_until_utc = None
        self.session.commit()
        self.session.refresh(record)
        return record

    def mark_cancelled(
        self,
        job_id: str,
        *,
        skip_reason_code: Optional[str] = None,
        failure_reason_text: Optional[str] = None,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.status = "cancelled"
        record.skip_reason_code = skip_reason_code
        record.failure_reason_text = failure_reason_text
        record.locked_until_utc = None
        self.session.commit()
        self.session.refresh(record)
        return record

    def reclaim_expired_locks(
        self,
        *,
        tenant_id: str = "default",
        now: datetime,
        limit: int = 100,
    ) -> list[ReminderJobRecord]:
        jobs = self.list_reclaimable_locks(tenant_id=tenant_id, now=now, limit=limit)
        for job in jobs:
            job.status = "planned"
            job.locked_until_utc = None
        self.session.commit()
        for job in jobs:
            self.session.refresh(job)
        return jobs

    def cancel_obsolete_future_jobs(
        self,
        *,
        tenant_id: str = "default",
        appointment_id: str,
        scheduled_after: Optional[datetime] = None,
        reason_code: str = "rescheduled",
        reason_text: str = "Reminder job cancelled because the appointment changed.",
    ) -> list[ReminderJobRecord]:
        query = (
            select(ReminderJobRecord)
            .where(ReminderJobRecord.tenant_id == tenant_id)
            .where(ReminderJobRecord.appointment_id == appointment_id)
            .where(ReminderJobRecord.status.in_(("planned", "due", "dispatching")))
        )
        if scheduled_after is not None:
            query = query.where(ReminderJobRecord.scheduled_for_utc >= scheduled_after)
        jobs = list(self.session.scalars(query))
        for job in jobs:
            job.status = "cancelled"
            job.skip_reason_code = reason_code
            job.failure_reason_text = reason_text
            job.locked_until_utc = None
        self.session.commit()
        for job in jobs:
            self.session.refresh(job)
        return jobs

    def list_for_appointment(self, appointment_id: str) -> list[ReminderJobRecord]:
        query = (
            select(ReminderJobRecord)
            .where(ReminderJobRecord.appointment_id == appointment_id)
            .order_by(ReminderJobRecord.reminder_sequence.asc())
        )
        return list(self.session.scalars(query))

    def mark_status(
        self,
        job_id: str,
        *,
        status: str,
        failure_reason_code: Optional[str] = None,
        failure_reason_text: Optional[str] = None,
        skip_reason_code: Optional[str] = None,
        provider_message_id: Optional[str] = None,
        locked_until_utc=None,
        dispatched_at_utc=None,
    ) -> ReminderJobRecord:
        record = self.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        record.status = status
        record.failure_reason_code = failure_reason_code
        record.failure_reason_text = failure_reason_text
        record.skip_reason_code = skip_reason_code
        record.provider_message_id = provider_message_id
        record.locked_until_utc = locked_until_utc
        record.dispatched_at_utc = dispatched_at_utc
        self.session.commit()
        self.session.refresh(record)
        return record


class ReminderAuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append(
        self,
        *,
        audit_id: str,
        tenant_id: str = "default",
        appointment_id: Optional[str] = None,
        reminder_job_id: Optional[str] = None,
        reminder_policy_id: Optional[int] = None,
        event_type: str,
        human_readable_message: str,
        payload: dict,
        reason_code: Optional[str] = None,
    ) -> ReminderAuditRecord:
        record = ReminderAuditRecord(
            audit_id=audit_id,
            tenant_id=tenant_id,
            appointment_id=appointment_id,
            reminder_job_id=reminder_job_id,
            reminder_policy_id=reminder_policy_id,
            event_type=event_type,
            reason_code=reason_code,
            human_readable_message=human_readable_message,
            payload_json=payload,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record


class MessageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        *,
        message_id: str,
        provider_message_id: Optional[str],
        provider_job_id: Optional[str],
        provider: str,
        channel: str,
        direction: str,
        status: str,
        customer_id: Optional[str],
        contact_reference: Optional[str],
        phone_number: Optional[str],
        address_id: Optional[str] = None,
        appointment_id: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        journey_id: Optional[str],
        booking_reference: Optional[str],
        message_type: str,
        body: str,
        preview_text: Optional[str],
        actions: list[dict],
        provider_payload: dict,
        metadata: dict,
    ) -> MessageRecord:
        record = self.get(message_id)
        if record is None:
            record = MessageRecord(message_id=message_id)
            self.session.add(record)
        record.provider_message_id = provider_message_id
        record.provider_job_id = provider_job_id
        record.provider = provider
        record.channel = channel
        record.direction = direction
        record.status = status
        record.customer_id = customer_id
        record.contact_reference = contact_reference
        record.phone_number = phone_number
        record.address_id = address_id
        record.appointment_id = appointment_id
        record.correlation_ref = correlation_ref
        record.journey_id = journey_id
        record.booking_reference = booking_reference
        record.message_type = message_type
        record.body = body
        record.preview_text = preview_text
        record.actions = actions
        record.provider_payload = provider_payload
        record.metadata_payload = metadata
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, message_id: str) -> Optional[MessageRecord]:
        return self.session.scalar(select(MessageRecord).where(MessageRecord.message_id == message_id))

    def list_messages(
        self,
        *,
        channel: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        journey_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[MessageRecord]:
        query = select(MessageRecord)
        if channel:
            query = query.where(MessageRecord.channel == channel)
        if direction:
            query = query.where(MessageRecord.direction == direction)
        if status:
            query = query.where(MessageRecord.status == status)
        if journey_id:
            query = query.where(MessageRecord.journey_id == journey_id)
        query = query.order_by(MessageRecord.created_at.desc()).limit(limit)
        return list(self.session.scalars(query))


class LekabConfigRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, config_key: str = "rcs_settings") -> Optional[LekabConfigRecord]:
        return self.session.scalar(
            select(LekabConfigRecord).where(LekabConfigRecord.config_key == config_key)
        )

    def save(
        self,
        *,
        config_key: str = "rcs_settings",
        config_payload: dict,
        secret_payload: dict,
        status_payload: dict,
    ) -> LekabConfigRecord:
        record = self.get(config_key)
        if record is None:
            record = LekabConfigRecord(config_key=config_key)
            self.session.add(record)
        record.config_payload = config_payload
        record.secret_payload = secret_payload
        record.status_payload = status_payload
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


class GoogleDemoEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        *,
        operation_id: str,
        mode: str,
        timeframe: str,
        calendar_id: str,
        event_id: Optional[str],
        booking_reference: str,
        title: str,
        customer_name: Optional[str],
        mobile_number: Optional[str],
        start_time_utc,
        end_time_utc,
        timezone: str,
        provider_reference: Optional[str],
        details: dict,
        is_demo_generated: bool = True,
    ) -> GoogleDemoEventRecord:
        record = self.session.scalar(
            select(GoogleDemoEventRecord).where(GoogleDemoEventRecord.booking_reference == booking_reference)
        )
        if record is None:
            record = GoogleDemoEventRecord(
                booking_reference=booking_reference,
                operation_id=operation_id,
                mode=mode,
                timeframe=timeframe,
                calendar_id=calendar_id,
                title=title,
                start_time_utc=start_time_utc,
                end_time_utc=end_time_utc,
                timezone=timezone,
                is_demo_generated=is_demo_generated,
            )
            self.session.add(record)
        record.operation_id = operation_id
        record.mode = mode
        record.timeframe = timeframe
        record.calendar_id = calendar_id
        record.event_id = event_id
        record.title = title
        record.customer_name = customer_name
        record.mobile_number = mobile_number
        record.start_time_utc = start_time_utc
        record.end_time_utc = end_time_utc
        record.timezone = timezone
        record.provider_reference = provider_reference
        record.details = details
        record.is_demo_generated = is_demo_generated
        record.is_deleted = False
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_active(self, calendar_id: str, timeframe: Optional[str] = None) -> list[GoogleDemoEventRecord]:
        query = select(GoogleDemoEventRecord).where(
            GoogleDemoEventRecord.calendar_id == calendar_id,
            GoogleDemoEventRecord.is_demo_generated.is_(True),
            GoogleDemoEventRecord.is_deleted.is_(False),
        )
        if timeframe:
            query = query.where(GoogleDemoEventRecord.timeframe == timeframe)
        return list(self.session.scalars(query.order_by(GoogleDemoEventRecord.start_time_utc.asc())))

    def mark_deleted(self, booking_references: list[str]) -> None:
        if not booking_references:
            return
        records = list(
            self.session.scalars(
                select(GoogleDemoEventRecord).where(GoogleDemoEventRecord.booking_reference.in_(booking_references))
            )
        )
        for record in records:
            record.is_deleted = True
        self.session.commit()


class DemoScenarioContextRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, context_key: str) -> Optional[DemoScenarioContextRecord]:
        return self.session.scalar(
            select(DemoScenarioContextRecord).where(DemoScenarioContextRecord.context_key == context_key)
        )

    def save(
        self,
        *,
        context_key: str,
        version: str,
        scenario_id: Optional[str],
        mode: str,
        address_id: Optional[str],
        appointment_id: Optional[str],
        booking_reference: Optional[str],
        correlation_ref: Optional[str],
        calendar_ref: Optional[str],
        output_channel: Optional[str],
        appointment_type: Optional[str],
        from_date: Optional[str],
        to_date: Optional[str],
        current_step: Optional[str],
        status: str,
        latest_protocol_path: Optional[str],
        latest_demo_log_path: Optional[str],
        latest_summary_path: Optional[str],
        latest_run_id: Optional[str],
        metadata: dict,
        started_at_utc: Optional[datetime],
        finished_at_utc: Optional[datetime],
    ) -> DemoScenarioContextRecord:
        record = self.get(context_key)
        if record is None:
            record = DemoScenarioContextRecord(context_key=context_key)
            self.session.add(record)
        record.version = version
        record.scenario_id = scenario_id
        record.mode = mode
        record.address_id = address_id
        record.appointment_id = appointment_id
        record.booking_reference = booking_reference
        record.correlation_ref = correlation_ref
        record.calendar_ref = calendar_ref
        record.output_channel = output_channel
        record.appointment_type = appointment_type
        record.from_date = from_date
        record.to_date = to_date
        record.current_step = current_step
        record.status = status
        record.latest_protocol_path = latest_protocol_path
        record.latest_demo_log_path = latest_demo_log_path
        record.latest_summary_path = latest_summary_path
        record.latest_run_id = latest_run_id
        record.metadata_payload = metadata
        record.started_at_utc = started_at_utc
        record.finished_at_utc = finished_at_utc
        self.session.commit()
        self.session.refresh(record)
        return record


class SlotHoldRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        hold_id: str,
        journey_id: str,
        customer_id: Optional[str],
        slot_id: str,
        provider: str,
        slot_label: Optional[str],
        start_time_utc,
        end_time_utc,
        expires_at_utc,
        reason: Optional[str],
        details: dict,
    ) -> SlotHoldRecord:
        record = SlotHoldRecord(
            hold_id=hold_id,
            journey_id=journey_id,
            customer_id=customer_id,
            slot_id=slot_id,
            provider=provider,
            slot_label=slot_label,
            start_time_utc=start_time_utc,
            end_time_utc=end_time_utc,
            expires_at_utc=expires_at_utc,
            reason=reason,
            details=details,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_active_by_hold_id(self, hold_id: str):
        return self.session.scalar(
            select(SlotHoldRecord).where(
                SlotHoldRecord.hold_id == hold_id,
                SlotHoldRecord.status == "ACTIVE",
            )
        )

    def list_active(self) -> list[SlotHoldRecord]:
        return list(
            self.session.scalars(
                select(SlotHoldRecord).where(SlotHoldRecord.status == "ACTIVE").order_by(SlotHoldRecord.created_at.asc())
            )
        )

    def find_active_for_slot(self, *, slot_id: str, start_time_utc, end_time_utc):
        records = list(
            self.session.scalars(
                select(SlotHoldRecord).where(
                    SlotHoldRecord.slot_id == slot_id,
                    SlotHoldRecord.status == "ACTIVE",
                )
            )
        )
        return [
            record
            for record in records
            if record.start_time_utc < end_time_utc and record.end_time_utc > start_time_utc
        ]

    def expire_stale(self, now_utc) -> list[SlotHoldRecord]:
        records = list(
            self.session.scalars(
                select(SlotHoldRecord).where(
                    SlotHoldRecord.status == "ACTIVE",
                    SlotHoldRecord.expires_at_utc <= now_utc,
                )
            )
        )
        for record in records:
            record.status = "EXPIRED"
        self.session.commit()
        return records

    def release(self, hold_id: str, status: str = "RELEASED") -> Optional[SlotHoldRecord]:
        record = self.session.scalar(select(SlotHoldRecord).where(SlotHoldRecord.hold_id == hold_id))
        if record is None:
            return None
        record.status = status
        self.session.commit()
        self.session.refresh(record)
        return record

    def release_for_journey(self, journey_id: str, keep_hold_id: Optional[str] = None) -> list[SlotHoldRecord]:
        records = list(
            self.session.scalars(
                select(SlotHoldRecord).where(
                    SlotHoldRecord.journey_id == journey_id,
                    SlotHoldRecord.status == "ACTIVE",
                )
            )
        )
        changed: list[SlotHoldRecord] = []
        for record in records:
            if keep_hold_id and record.hold_id == keep_hold_id:
                continue
            record.status = "RELEASED"
            changed.append(record)
        self.session.commit()
        return changed
