from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Dict, Optional, Union

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .enums import BookingStatus, JourneyState, SlotHoldStatus


class ProviderReference(BaseModel):
    provider: str
    external_id: str
    operation: Optional[str] = None


class AppointmentJourney(BaseModel):
    journey_id: str
    tenant_id: str
    correlation_id: str
    customer_id: Optional[str] = None
    channel: Optional[str] = None
    service_type: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    current_state: JourneyState = JourneyState.NEW
    created_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None
    booking_reference: Optional[str] = None
    active_provider: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerProfile(BaseModel):
    customer_id: str
    external_customer_id: Optional[str] = None
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    consent_messaging: Optional[bool] = None
    consent_reminders: Optional[bool] = None
    crm_reference: Optional[str] = None
    lekab_contact_id: Optional[str] = None
    google_person_resource_name: Optional[str] = None
    status: Optional[str] = None
    created_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None


class AddressProfile(BaseModel):
    address_id: str
    external_ref: Optional[str] = None
    customer_number: Optional[str] = None
    display_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    preferred_channel: Optional[str] = None
    notes: Optional[str] = None
    correlation_ref: Optional[str] = None
    tenant_id: Optional[str] = None
    application_id: Optional[str] = None
    is_active: bool = True
    created_at_utc: Optional[str] = None
    updated_at_utc: Optional[str] = None


class AppointmentPreference(BaseModel):
    earliest_date: Optional[datetime] = None
    latest_date: Optional[datetime] = None
    preferred_month: Optional[str] = None
    preferred_weekdays: list[str] = Field(default_factory=list)
    preferred_daypart: Optional[str] = None
    preferred_location_type: Optional[str] = None
    preferred_language: Optional[str] = None
    urgency: Optional[str] = None
    free_text_preference: Optional[str] = None


class ReminderPolicyRecord(Base):
    __tablename__ = "reminder_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_name", name="uq_reminder_policies_tenant_policy"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True, default="default")
    policy_name: Mapped[str] = mapped_column(String(80), index=True, default="default")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    mode: Mapped[str] = mapped_column(String(32), default="manual", index=True)
    reminder_count: Mapped[int] = mapped_column(Integer, default=1)
    first_reminder_hours_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    second_reminder_hours_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    third_reminder_hours_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_span_between_first_and_last_reminder_hours: Mapped[int] = mapped_column(Integer, default=24)
    last_reminder_gap_before_appointment_hours: Mapped[int] = mapped_column(Integer, default=24)
    enforce_max_span: Mapped[bool] = mapped_column(Boolean, default=True)
    preload_window_hours: Mapped[int] = mapped_column(Integer, default=168)
    channel_email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    channel_voice_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    channel_rcs_sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class AppointmentCacheRecord(Base):
    __tablename__ = "appointment_cache"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "external_appointment_id",
            "calendar_source_type",
            "calendar_source_ref",
            name="uq_appointment_cache_external_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True, default="default")
    external_appointment_id: Mapped[str] = mapped_column(String(255), index=True)
    calendar_source_type: Mapped[str] = mapped_column(String(32), index=True)
    calendar_source_ref: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_at_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_at_utc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", index=True)
    participant_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    contact_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    address_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    correlation_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    reminder_policy_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminder_policies.id"), nullable=True, index=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    last_seen_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    def source_identity(self) -> tuple[str, str, str, str]:
        """Return the stable source identity used for cache lookups.

        The Reminder Scheduler uses the four fields below as the immutable
        identity of an imported appointment. Keeping that identity in one
        helper avoids accidental drift between repository code paths.
        """

        return (
            self.tenant_id,
            self.external_appointment_id,
            self.calendar_source_type,
            self.calendar_source_ref,
        )

    def matches_source_hash(self, source_hash: Optional[str]) -> bool:
        """Return ``True`` when the cached row already carries ``source_hash``."""

        return source_hash is not None and self.source_hash == source_hash

    def needs_sync_refresh(self, *, source_hash: Optional[str], status: Optional[str] = None) -> bool:
        """Return ``True`` when a sync pass should update the row.

        The helper is intentionally conservative: a missing hash, a different
        hash, or a status change all count as reasons to refresh the cache row.
        That keeps repeated polling runs idempotent while still allowing
        updates and cancellations to flow through deterministically.
        """

        if source_hash is None:
            return True
        if self.source_hash != source_hash:
            return True
        if status is not None and self.status != status:
            return True
        return False


class ReminderJobRecord(Base):
    __tablename__ = "reminder_jobs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "appointment_id",
            "reminder_sequence",
            "channel",
            name="uq_reminder_jobs_unique",
        ),
        UniqueConstraint("dispatch_key", name="uq_reminder_jobs_dispatch_key"),
        CheckConstraint("reminder_sequence BETWEEN 1 AND 3", name="ck_reminder_sequence_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True, default="default")
    policy_name: Mapped[str] = mapped_column(String(80), index=True, default="default")
    appointment_id: Mapped[str] = mapped_column(String(255), index=True)
    external_appointment_id: Mapped[str] = mapped_column(String(255), index=True)
    reminder_policy_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminder_policies.id"), nullable=True, index=True)
    reminder_sequence: Mapped[int] = mapped_column(Integer, index=True)
    scheduled_for_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    appointment_start_at_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    appointment_timezone: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    address_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    correlation_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), index=True)
    target_ref: Mapped[Optional[str]] = mapped_column(String(320), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="planned", index=True)
    failure_reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    failure_reason_text: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    skip_reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    dispatch_key: Mapped[str] = mapped_column(String(255), index=True)
    locked_until_utc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    dispatched_at_utc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # The scheduler uses a small, deterministic lifecycle vocabulary so helper
    # methods can make safe decisions without re-encoding the status rules in
    # every call site. The status strings still remain plain text for easy
    # filtering and SQL compatibility.
    ACTIVE_STATUSES: ClassVar[tuple[str, ...]] = ("planned", "due", "dispatching")
    TERMINAL_STATUSES: ClassVar[tuple[str, ...]] = ("sent", "failed", "skipped", "cancelled")

    def is_active(self) -> bool:
        """Return ``True`` while the reminder job can still be worked."""

        return self.status in self.ACTIVE_STATUSES

    def is_terminal(self) -> bool:
        """Return ``True`` once the reminder job reached a final outcome."""

        return self.status in self.TERMINAL_STATUSES

    def is_reclaimable(self, now: datetime) -> bool:
        """Return ``True`` when a lock expired and the job can be retried."""

        return self.status == "dispatching" and self.locked_until_utc is not None and self.locked_until_utc <= now


class ReminderAuditRecord(Base):
    __tablename__ = "reminder_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True, default="default")
    appointment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    reminder_job_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    reminder_policy_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminder_policies.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    human_readable_message: Mapped[str] = mapped_column(String(500))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ReminderRuntimeHealthSnapshot(BaseModel):
    """Summarize the runtime state that the Reminder Scheduler should expose.

    The snapshot keeps the health logic in one place so release lines can show
    the same operational picture in health endpoints, dashboards, and tests.
    It intentionally uses simple counters and timestamps so it stays stable
    across v1.3.x releases.
    """

    tenant_id: str
    policy_name: Optional[str] = None
    as_of_utc: datetime
    appointment_count: int = 0
    job_counts: Dict[str, int] = Field(default_factory=dict)
    hold_counts: Dict[str, int] = Field(default_factory=dict)
    message_counts: Dict[str, int] = Field(default_factory=dict)
    audit_counts: Dict[str, int] = Field(default_factory=dict)
    next_due_at_utc: Optional[datetime] = None
    last_job_activity_at_utc: Optional[datetime] = None
    last_hold_activity_at_utc: Optional[datetime] = None
    last_message_activity_at_utc: Optional[datetime] = None
    last_audit_activity_at_utc: Optional[datetime] = None
    active_job_count: int = 0
    active_hold_count: int = 0
    reclaimable_lock_count: int = 0
    health_notes: list[str] = Field(default_factory=list)

    def has_reclaimable_jobs(self) -> bool:
        """Return ``True`` when a dispatch lock needs operator attention."""

        return self.reclaimable_lock_count > 0


class CandidateSlot(BaseModel):
    slot_id: str
    start_time: datetime
    end_time: datetime
    timezone: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    location: Optional[str] = None
    score: Optional[float] = None
    hold_expires_at: Optional[datetime] = None
    provider: Optional[str] = None
    provider_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SlotHold(BaseModel):
    hold_id: str
    journey_id: str
    slot_id: str
    customer_id: Optional[str] = None
    created_at_utc: datetime
    expires_at_utc: datetime
    status: SlotHoldStatus = SlotHoldStatus.ACTIVE
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AppointmentBooking(BaseModel):
    booking_reference: str
    journey_id: str
    customer_id: Optional[str] = None
    slot_id: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    provider: Optional[str] = None
    provider_reference: Optional[str] = None
    calendar_target: Optional[str] = None
    crm_reference: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    created_at_utc: Optional[datetime] = None
    updated_at_utc: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationTurnPayload(BaseModel):
    turn_id: str
    journey_id: str
    direction: str
    channel: str
    message_type: str
    normalized_payload: dict[str, Any]
    raw_payload_reference: Optional[str] = None
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)


class ConversationTurn(BaseModel):
    turn_id: str
    journey_id: str
    direction: str
    channel: str
    message_type: str
    provider: Optional[str] = None
    provider_reference: Optional[str] = None
    raw_payload_reference: Optional[str] = None
    normalized_payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp_utc: datetime


class MessageAction(BaseModel):
    action_id: str
    label: str
    value: str
    action_type: str = "reply"


class NormalizedMessage(BaseModel):
    message_id: str
    provider_message_id: Optional[str] = None
    provider_job_id: Optional[str] = None
    provider: str = "lekab"
    channel: str
    direction: str
    status: str
    customer_id: Optional[str] = None
    contact_reference: Optional[str] = None
    phone_number: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    journey_id: Optional[str] = None
    booking_reference: Optional[str] = None
    message_type: str = "text"
    body: str
    preview_text: Optional[str] = None
    actions: list[MessageAction] = Field(default_factory=list)
    provider_payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookingResult(BaseModel):
    booking_reference: str
    provider: str
    external_calendar_id: Optional[str] = None
    provider_reference: Optional[str] = None
    status: Union[BookingStatus, str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    calendar_target: Optional[str] = None
    attendees: list[Dict[str, Any]] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContactRecord(Base):
    __tablename__ = "contact_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True)
    customer_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    consent_sms: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_rcs: Mapped[bool] = mapped_column(Boolean, default=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AddressRecord(Base):
    __tablename__ = "address_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    external_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    customer_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    street: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    house_number: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    preferred_channel: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    correlation_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), default="default", index=True)
    application_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class AddressAppointmentLinkRecord(Base):
    __tablename__ = "address_appointment_links"
    __table_args__ = (
        UniqueConstraint("address_id", "appointment_external_id", name="uq_address_appointment_link"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    address_id: Mapped[str] = mapped_column(String(80), index=True)
    appointment_external_id: Mapped[str] = mapped_column(String(255), index=True)
    booking_reference: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    calendar_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    correlation_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), default="default", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class BookingRecord(Base):
    __tablename__ = "booking_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    journey_id: Mapped[str] = mapped_column(String(80), index=True)
    customer_id: Mapped[str] = mapped_column(String(80), index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="created")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CallbackReceipt(Base):
    __tablename__ = "callback_receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    correlation_id: Mapped[str] = mapped_column(String(80), index=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AppointmentJourneyRecord(Base):
    __tablename__ = "appointment_journeys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    journey_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String(80), index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True)
    customer_id: Mapped[str] = mapped_column(String(80), index=True)
    channel: Mapped[str] = mapped_column(String(40), default="RCS")
    current_state: Mapped[str] = mapped_column(String(40), default=JourneyState.NEW.value, index=True)
    service_type: Mapped[str] = mapped_column(String(80))
    locale: Mapped[str] = mapped_column(String(20), default="en")
    timezone: Mapped[str] = mapped_column(String(60))
    preference_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    candidate_slots: Mapped[dict] = mapped_column(JSON, default=list)
    selected_slot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    booking_reference: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    escalation_reason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationTurnRecord(Base):
    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turn_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    journey_id: Mapped[str] = mapped_column(String(80), index=True)
    direction: Mapped[str] = mapped_column(String(20))
    channel: Mapped[str] = mapped_column(String(20))
    message_type: Mapped[str] = mapped_column(String(40))
    normalized_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_payload_reference: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MessageRecord(Base):
    __tablename__ = "message_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    provider_job_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="lekab", index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    contact_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    address_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    appointment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    correlation_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    journey_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    booking_reference: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    message_type: Mapped[str] = mapped_column(String(40), default="text", index=True)
    body: Mapped[str] = mapped_column(String(2000))
    preview_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    provider_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_payload: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class LekabConfigRecord(Base):
    __tablename__ = "lekab_config_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    config_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    secret_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), index=True)
    journey_id: Mapped[str] = mapped_column(String(80), index=True)
    correlation_id: Mapped[str] = mapped_column(String(80), index=True)
    trace_id: Mapped[str] = mapped_column(String(80), index=True)
    decision_type: Mapped[str] = mapped_column(String(80), index=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    human_readable_message: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class GoogleDemoEventRecord(Base):
    __tablename__ = "google_demo_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_id: Mapped[str] = mapped_column(String(80), index=True)
    mode: Mapped[str] = mapped_column(String(20), index=True)
    timeframe: Mapped[str] = mapped_column(String(20), index=True)
    calendar_id: Mapped[str] = mapped_column(String(160), index=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True, index=True)
    booking_reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    customer_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    mobile_number: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    start_time_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    timezone: Mapped[str] = mapped_column(String(60), default="Europe/Berlin")
    provider_reference: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    is_demo_generated: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DemoScenarioContextRecord(Base):
    __tablename__ = "demo_scenario_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    context_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    version: Mapped[str] = mapped_column(String(40), default="v1.3.9-patch1", index=True)
    scenario_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(20), default="simulation", index=True)
    address_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    appointment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    booking_reference: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    correlation_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    calendar_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    output_channel: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    appointment_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    from_date: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    to_date: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    current_step: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="idle", index=True)
    latest_protocol_path: Mapped[Optional[str]] = mapped_column(String(600), nullable=True)
    latest_demo_log_path: Mapped[Optional[str]] = mapped_column(String(600), nullable=True)
    latest_summary_path: Mapped[Optional[str]] = mapped_column(String(600), nullable=True)
    latest_run_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    metadata_payload: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    started_at_utc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    finished_at_utc: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class SlotHoldRecord(Base):
    __tablename__ = "slot_holds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hold_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    journey_id: Mapped[str] = mapped_column(String(80), index=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    slot_id: Mapped[str] = mapped_column(String(120), index=True)
    provider: Mapped[str] = mapped_column(String(40), default="google", index=True)
    slot_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    start_time_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    expires_at_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), default=SlotHoldStatus.ACTIVE.value, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
