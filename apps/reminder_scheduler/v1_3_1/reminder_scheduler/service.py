from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from appointment_agent_shared.models import (
    AppointmentCacheRecord,
    ReminderJobRecord,
    ReminderPolicyRecord,
)
from appointment_agent_shared.repositories import (
    AppointmentCacheRepository,
    ReminderAuditRepository,
    ReminderJobRepository,
    ReminderPolicyRepository,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReminderMode(str, Enum):
    MANUAL = "manual"
    AUTO_DISTRIBUTED = "auto_distributed"


class ReminderStatus(str, Enum):
    PLANNED = "planned"
    DUE = "due"
    DISPATCHING = "dispatching"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ReminderChannel(str, Enum):
    EMAIL = "email"
    VOICE = "voice"
    RCS_SMS = "rcs_sms"


class ReminderLifecycleError(ValueError):
    """Raised when a reminder job tries to move into a forbidden state."""


class ReminderPolicyInput(BaseModel):
    tenant_id: str = "default"
    policy_key: str = "global"
    enabled: bool = True
    mode: ReminderMode = ReminderMode.MANUAL
    reminder_count: int = Field(default=1, ge=0, le=3)
    first_reminder_hours_before: Optional[int] = Field(default=24, ge=0)
    second_reminder_hours_before: Optional[int] = Field(default=None, ge=0)
    third_reminder_hours_before: Optional[int] = Field(default=None, ge=0)
    max_span_between_first_and_last_reminder_hours: int = Field(default=24, ge=0)
    last_reminder_gap_before_appointment_hours: int = Field(default=24, ge=0)
    enforce_max_span: bool = True
    preload_window_hours: int = Field(default=168, ge=1)
    channel_email_enabled: bool = True
    channel_voice_enabled: bool = False
    channel_rcs_sms_enabled: bool = False

    @model_validator(mode="after")
    def ensure_required_values(self) -> "ReminderPolicyInput":
        if self.mode == ReminderMode.MANUAL and self.reminder_count > 0:
            required_values = [self.first_reminder_hours_before]
            if self.reminder_count >= 2:
                required_values.append(self.second_reminder_hours_before)
            if self.reminder_count >= 3:
                required_values.append(self.third_reminder_hours_before)
            if any(value is None for value in required_values):
                raise ValueError(
                    "Manual reminder mode requires explicit reminder hour values for each configured reminder."
                )
        return self


class ReminderAppointmentInput(BaseModel):
    appointment_external_id: str
    title: str
    start_time: datetime
    end_time: datetime
    timezone: str = "Europe/Berlin"
    tenant_id: str = "default"
    customer_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "scheduled"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReminderPreviewRequest(BaseModel):
    policy: ReminderPolicyInput
    appointments: list[ReminderAppointmentInput] = Field(default_factory=list)


class ReminderRebuildRequest(BaseModel):
    policy: Optional[ReminderPolicyInput] = None
    appointments: list[ReminderAppointmentInput] = Field(default_factory=list)
    replace_existing: bool = True


class ReminderJobView(BaseModel):
    job_id: str
    policy_key: str
    appointment_external_id: str
    reminder_sequence: int
    scheduled_for: datetime
    appointment_start_at: datetime
    channel: str
    status: str
    dispatch_key: str
    attempt_count: int
    max_attempts: int
    payload: dict[str, Any]
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None


class ReminderPreviewItem(BaseModel):
    appointment_external_id: str
    reminder_sequence: int
    channel: str
    reminder_hours_before: int
    scheduled_for: datetime
    status: str = ReminderStatus.PLANNED.value


class ReminderConfigView(BaseModel):
    policy: ReminderPolicyInput
    validation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    preview: list[ReminderPreviewItem] = Field(default_factory=list)
    job_count: int = 0
    appointment_count: int = 0


class ReminderHealthView(BaseModel):
    version: str = "v1.3.1"
    scheduler_enabled: bool
    policy_key: str
    policy_ready: bool
    policy_mode: str
    reminder_count: int
    appointment_count: int
    job_counts: dict[str, int]
    next_due_at: Optional[datetime] = None
    reclaimed_locks: int = 0


class ReminderPlanningResult(BaseModel):
    created_jobs: int = 0
    updated_jobs: int = 0
    skipped_jobs: int = 0
    appointment_count: int = 0
    planned_preview: list[ReminderPreviewItem] = Field(default_factory=list)


class ReminderDispatchResult(BaseModel):
    due_jobs: int = 0
    dispatched_jobs: int = 0
    failed_jobs: int = 0
    skipped_jobs: int = 0
    reclaimed_jobs: int = 0


def _default_policy() -> ReminderPolicyInput:
    return ReminderPolicyInput()


def _default_appointments(policy_key: str) -> list[ReminderAppointmentInput]:
    now = utcnow()
    return [
        ReminderAppointmentInput(
            tenant_id="default",
            appointment_external_id="demo-appointment-1",
            title="Dentist reminder demo",
            start_time=now + timedelta(days=2, hours=2),
            end_time=now + timedelta(days=2, hours=2, minutes=30),
            timezone="Europe/Berlin",
            customer_id="customer-1001",
            email="demo@example.test",
            metadata={"policy_key": policy_key},
        ),
        ReminderAppointmentInput(
            tenant_id="default",
            appointment_external_id="demo-appointment-2",
            title="Wallbox reminder demo",
            start_time=now + timedelta(days=4, hours=1),
            end_time=now + timedelta(days=4, hours=1, minutes=45),
            timezone="Europe/Berlin",
            customer_id="customer-1002",
            email="demo2@example.test",
            metadata={"policy_key": policy_key},
        ),
    ]


def _enabled_channels(policy: ReminderPolicyInput) -> list[str]:
    channels: list[str] = []
    if policy.channel_email_enabled:
        channels.append(ReminderChannel.EMAIL.value)
    if policy.channel_rcs_sms_enabled:
        channels.append(ReminderChannel.RCS_SMS.value)
    if policy.channel_voice_enabled:
        channels.append(ReminderChannel.VOICE.value)
    if not channels:
        # Keep previews useful even if the operator has not enabled a channel
        # yet. The runtime fallback stays deterministic for demos and tests.
        channels.append(ReminderChannel.EMAIL.value)
    return channels


def _reminder_hours(policy: ReminderPolicyInput) -> list[int]:
    if policy.reminder_count == 0:
        return []
    if policy.mode == ReminderMode.AUTO_DISTRIBUTED:
        if policy.reminder_count == 1:
            return [policy.last_reminder_gap_before_appointment_hours]
        span = policy.max_span_between_first_and_last_reminder_hours
        step = span / max(policy.reminder_count - 1, 1)
        values = [
            int(round(policy.last_reminder_gap_before_appointment_hours + (step * (policy.reminder_count - 1 - index))))
            for index in range(policy.reminder_count)
        ]
    else:
        values = [policy.first_reminder_hours_before or 0]
        if policy.reminder_count >= 2:
            values.append(policy.second_reminder_hours_before or 0)
        if policy.reminder_count >= 3:
            values.append(policy.third_reminder_hours_before or 0)
    if len(values) != len(set(values)):
        raise ValueError("Reminder hour values must be unique.")
    if values != sorted(values, reverse=True):
        raise ValueError("Reminder hour values must be sorted from earliest to latest notification.")
    if policy.enforce_max_span and values:
        span = values[0] - values[-1]
        if span > policy.max_span_between_first_and_last_reminder_hours:
            raise ValueError("Reminder span exceeds the configured maximum span.")
    return values


def validate_policy(policy: ReminderPolicyInput) -> list[str]:
    warnings: list[str] = []
    hours = _reminder_hours(policy)
    if policy.reminder_count > 3:
        raise ValueError("Reminder count cannot be larger than 3.")
    if policy.reminder_count != len(hours):
        raise ValueError("Reminder count does not match the configured reminder hours.")
    if policy.channel_email_enabled and policy.channel_voice_enabled and policy.channel_rcs_sms_enabled:
        warnings.append("All reminder channels are enabled. Channel assignment will follow priority order.")
    if policy.preload_window_hours < 1:
        raise ValueError("Preload window must be at least 1 hour.")
    if not any([policy.channel_email_enabled, policy.channel_voice_enabled, policy.channel_rcs_sms_enabled]):
        warnings.append("No reminder channel is enabled. Email will be used as a safe fallback for previews.")
    return warnings


def compute_preview(policy: ReminderPolicyInput, appointments: list[ReminderAppointmentInput]) -> list[ReminderPreviewItem]:
    hours = _reminder_hours(policy)
    channels = _enabled_channels(policy)
    preview: list[ReminderPreviewItem] = []
    for appointment in appointments:
        for index, reminder_hours in enumerate(hours, start=1):
            channel = channels[min(index - 1, len(channels) - 1)]
            preview.append(
                ReminderPreviewItem(
                    appointment_external_id=appointment.appointment_external_id,
                    reminder_sequence=index,
                    channel=channel,
                    reminder_hours_before=reminder_hours,
                    scheduled_for=appointment.start_time - timedelta(hours=reminder_hours),
                )
            )
    return preview


class ReminderSchedulerService:
    """Domain service for the reminder scheduler release line.

    The service keeps the reminder logic local to this module, while shared
    SQLAlchemy tables and repositories remain the source of truth for state.
    v1.3.1 tightens lifecycle rules around dedupe, retries, and lock reclaim.
    """

    TERMINAL_STATUSES = {ReminderStatus.SENT.value, ReminderStatus.FAILED.value, ReminderStatus.SKIPPED.value, ReminderStatus.CANCELLED.value}
    ACTIVE_STATUSES = {ReminderStatus.PLANNED.value, ReminderStatus.DUE.value, ReminderStatus.DISPATCHING.value}
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_LOCK_MINUTES = 5

    def __init__(self, session: Session) -> None:
        self.session = session
        self.policy_repo = ReminderPolicyRepository(session)
        self.appointment_repo = AppointmentCacheRepository(session)
        self.job_repo = ReminderJobRepository(session)
        self.audit_repo = ReminderAuditRepository(session)

    def _policy_record_to_input(self, record: ReminderPolicyRecord) -> ReminderPolicyInput:
        return ReminderPolicyInput(
            tenant_id=record.tenant_id,
            policy_key=record.policy_name,
            enabled=record.enabled,
            mode=ReminderMode(record.mode),
            reminder_count=record.reminder_count,
            first_reminder_hours_before=record.first_reminder_hours_before,
            second_reminder_hours_before=record.second_reminder_hours_before,
            third_reminder_hours_before=record.third_reminder_hours_before,
            max_span_between_first_and_last_reminder_hours=record.max_span_between_first_and_last_reminder_hours,
            last_reminder_gap_before_appointment_hours=record.last_reminder_gap_before_appointment_hours,
            enforce_max_span=record.enforce_max_span,
            preload_window_hours=record.preload_window_hours,
            channel_email_enabled=record.channel_email_enabled,
            channel_voice_enabled=record.channel_voice_enabled,
            channel_rcs_sms_enabled=record.channel_rcs_sms_enabled,
        )

    def _get_policy_record(self, policy_key: str = "global") -> ReminderPolicyRecord:
        record = self.policy_repo.get(tenant_id="default", policy_name=policy_key)
        if record is None:
            policy = _default_policy()
            record = self.policy_repo.upsert(
                tenant_id=policy.tenant_id,
                policy_name=policy.policy_key,
                enabled=policy.enabled,
                mode=policy.mode.value,
                reminder_count=policy.reminder_count,
                first_reminder_hours_before=policy.first_reminder_hours_before,
                second_reminder_hours_before=policy.second_reminder_hours_before,
                third_reminder_hours_before=policy.third_reminder_hours_before,
                max_span_between_first_and_last_reminder_hours=policy.max_span_between_first_and_last_reminder_hours,
                last_reminder_gap_before_appointment_hours=policy.last_reminder_gap_before_appointment_hours,
                enforce_max_span=policy.enforce_max_span,
                preload_window_hours=policy.preload_window_hours,
                channel_email_enabled=policy.channel_email_enabled,
                channel_voice_enabled=policy.channel_voice_enabled,
                channel_rcs_sms_enabled=policy.channel_rcs_sms_enabled,
            )
        return record

    def _save_policy(self, policy: ReminderPolicyInput) -> ReminderPolicyRecord:
        return self.policy_repo.upsert(
            tenant_id=policy.tenant_id,
            policy_name=policy.policy_key,
            enabled=policy.enabled,
            mode=policy.mode.value,
            reminder_count=policy.reminder_count,
            first_reminder_hours_before=policy.first_reminder_hours_before,
            second_reminder_hours_before=policy.second_reminder_hours_before,
            third_reminder_hours_before=policy.third_reminder_hours_before,
            max_span_between_first_and_last_reminder_hours=policy.max_span_between_first_and_last_reminder_hours,
            last_reminder_gap_before_appointment_hours=policy.last_reminder_gap_before_appointment_hours,
            enforce_max_span=policy.enforce_max_span,
            preload_window_hours=policy.preload_window_hours,
            channel_email_enabled=policy.channel_email_enabled,
            channel_voice_enabled=policy.channel_voice_enabled,
            channel_rcs_sms_enabled=policy.channel_rcs_sms_enabled,
        )

    def _list_appointments(
        self,
        tenant_id: str,
        policy_key: str,
        policy_record_id: Optional[int] = None,
    ) -> list[ReminderAppointmentInput]:
        rows = list(
            self.session.scalars(
                select(AppointmentCacheRecord)
                .where(AppointmentCacheRecord.tenant_id == tenant_id)
                .where(
                    (AppointmentCacheRecord.reminder_policy_id == policy_record_id)
                    | (AppointmentCacheRecord.calendar_source_ref == policy_key)
                )
                .order_by(AppointmentCacheRecord.start_at_utc.asc())
            )
        )
        if not rows:
            return [
                appointment.model_copy(update={"metadata": {**appointment.metadata, "policy_key": policy_key}})
                for appointment in _default_appointments(policy_key)
            ]
        return [
            ReminderAppointmentInput(
                tenant_id=row.tenant_id,
                appointment_external_id=row.external_appointment_id,
                title=row.title or row.external_appointment_id,
                start_time=row.start_at_utc,
                end_time=row.end_at_utc or row.start_at_utc,
                timezone=row.timezone or "Europe/Berlin",
                customer_id=row.contact_ref or row.participant_ref,
                email=row.email,
                phone=row.phone,
                status=row.status,
                metadata=row.raw_payload_json or {},
            )
            for row in rows
        ]

    def save_appointment_cache(
        self,
        appointments: list[ReminderAppointmentInput],
        *,
        policy_key: str,
        policy_record_id: Optional[int] = None,
    ) -> int:
        saved = 0
        for appointment in appointments:
            existing = self.session.scalar(
                select(AppointmentCacheRecord).where(
                    AppointmentCacheRecord.tenant_id == appointment.tenant_id,
                    AppointmentCacheRecord.external_appointment_id == appointment.appointment_external_id,
                    AppointmentCacheRecord.calendar_source_type == "reminder_scheduler",
                    AppointmentCacheRecord.calendar_source_ref == policy_key,
                )
            )
            changed = existing is not None and (
                existing.start_at_utc != appointment.start_time
                or existing.end_at_utc != appointment.end_time
                or existing.status != appointment.status
                or existing.email != appointment.email
                or existing.phone != appointment.phone
            )
            # The appointment cache keeps the scheduler input stable and lets
            # rebuild/reschedule detect time changes without separate tracking
            # tables.
            self.appointment_repo.upsert(
                tenant_id=appointment.tenant_id,
                external_appointment_id=appointment.appointment_external_id,
                calendar_source_type="reminder_scheduler",
                calendar_source_ref=policy_key,
                title=appointment.title,
                start_at_utc=appointment.start_time,
                end_at_utc=appointment.end_time,
                timezone=appointment.timezone,
                status=appointment.status,
                participant_ref=appointment.customer_id,
                contact_ref=appointment.customer_id,
                email=appointment.email,
                phone=appointment.phone,
                reminder_policy_id=policy_record_id,
                raw_payload_json=appointment.metadata,
                last_seen_at_utc=utcnow(),
            )
            if changed:
                self._append_audit(
                    tenant_id=appointment.tenant_id,
                    policy_key=policy_key,
                    policy_record_id=policy_record_id,
                    event_type="appointment.cache.changed",
                    message="Appointment cache entry updated",
                    payload={
                        "appointment_external_id": appointment.appointment_external_id,
                        "start_time": appointment.start_time.isoformat(),
                        "end_time": appointment.end_time.isoformat(),
                    },
                )
            saved += 1
        return saved

    def _job_identity_key(self, appointment_external_id: str, reminder_sequence: int, channel: str) -> str:
        return f"{appointment_external_id}:{reminder_sequence}:{channel}"

    def _job_to_view(self, record: ReminderJobRecord) -> ReminderJobView:
        return ReminderJobView(
            job_id=record.job_id,
            policy_key=record.policy_name,
            appointment_external_id=record.external_appointment_id,
            reminder_sequence=record.reminder_sequence,
            scheduled_for=record.scheduled_for_utc,
            appointment_start_at=record.appointment_start_at_utc,
            channel=record.channel,
            status=record.status,
            dispatch_key=record.dispatch_key,
            attempt_count=record.attempt_count,
            max_attempts=record.max_attempts,
            payload=record.payload_json,
            last_error=record.failure_reason_text,
            sent_at=record.dispatched_at_utc,
        )

    def _job_to_preview(self, record: ReminderJobRecord) -> ReminderPreviewItem:
        return ReminderPreviewItem(
            appointment_external_id=record.external_appointment_id,
            reminder_sequence=record.reminder_sequence,
            channel=record.channel,
            reminder_hours_before=int(record.payload_json.get("reminder_hours_before", 0)),
            scheduled_for=record.scheduled_for_utc,
            status=record.status,
        )

    def _append_audit(
        self,
        *,
        tenant_id: str = "default",
        policy_key: str,
        event_type: str,
        message: str,
        payload: dict[str, Any],
        policy_record_id: Optional[int] = None,
        job_id: Optional[str] = None,
        appointment_external_id: Optional[str] = None,
        reason_code: Optional[str] = None,
    ) -> None:
        # Audit records stay in the shared repository so the scheduler uses the
        # same visibility pattern as the rest of the demonstrator.
        self.audit_repo.append(
            audit_id=str(uuid4()),
            tenant_id=tenant_id,
            appointment_id=appointment_external_id,
            reminder_job_id=job_id,
            reminder_policy_id=policy_record_id,
            event_type=event_type,
            human_readable_message=message,
            payload=payload,
            reason_code=reason_code,
        )

    def _job_signature(self, appointment: ReminderAppointmentInput, item: ReminderPreviewItem) -> dict[str, Any]:
        return {
            "appointment_external_id": appointment.appointment_external_id,
            "reminder_sequence": item.reminder_sequence,
            "channel": item.channel,
            "scheduled_for": item.scheduled_for.isoformat(),
            "appointment_start_at": appointment.start_time.isoformat(),
            "appointment_timezone": appointment.timezone,
            "target_ref": appointment.email or appointment.phone,
            "reminder_hours_before": item.reminder_hours_before,
        }

    def _transition_job_state(
        self,
        record: ReminderJobRecord,
        new_status: str,
        *,
        reason_code: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        clear_lock: bool = False,
        dispatched_at_utc: Optional[datetime] = None,
        provider_message_id: Optional[str] = None,
    ) -> ReminderJobRecord:
        allowed = {
            ReminderStatus.PLANNED.value: {ReminderStatus.DISPATCHING.value, ReminderStatus.SKIPPED.value, ReminderStatus.CANCELLED.value, ReminderStatus.PLANNED.value},
            ReminderStatus.DUE.value: {ReminderStatus.DISPATCHING.value, ReminderStatus.PLANNED.value, ReminderStatus.CANCELLED.value, ReminderStatus.SKIPPED.value},
            ReminderStatus.DISPATCHING.value: {ReminderStatus.SENT.value, ReminderStatus.FAILED.value, ReminderStatus.PLANNED.value},
            ReminderStatus.FAILED.value: {ReminderStatus.PLANNED.value},
            ReminderStatus.SKIPPED.value: set(),
            ReminderStatus.CANCELLED.value: set(),
            ReminderStatus.SENT.value: set(),
        }
        current = record.status
        if new_status != current and new_status not in allowed.get(current, set()):
            raise ReminderLifecycleError(f"Illegal reminder job transition: {current} -> {new_status}")

        record.status = new_status
        if payload is not None:
            record.payload_json = payload
        if reason_code is not None:
            record.failure_reason_code = reason_code if new_status == ReminderStatus.FAILED.value else record.failure_reason_code
            record.skip_reason_code = reason_code if new_status in {ReminderStatus.SKIPPED.value, ReminderStatus.CANCELLED.value} else record.skip_reason_code
        if clear_lock:
            record.locked_until_utc = None
        if dispatched_at_utc is not None:
            record.dispatched_at_utc = dispatched_at_utc
        if provider_message_id is not None:
            record.provider_message_id = provider_message_id
        self.session.commit()
        self.session.refresh(record)
        return record

    def _deliver_job(self, record: ReminderJobRecord) -> str:
        # Delivery is intentionally simulated in v1.3.1. Later releases can
        # replace this hook with a real provider adapter without changing the
        # lifecycle contract around locking and retries.
        if record.payload_json.get("simulate_failure"):
            raise RuntimeError("Simulated dispatch failure")
        return f"provider-{record.job_id}"

    def _active_jobs_for_appointment(self, appointment_external_id: str) -> list[ReminderJobRecord]:
        query = select(ReminderJobRecord).where(
            ReminderJobRecord.appointment_id == appointment_external_id,
            ReminderJobRecord.status.in_(sorted(self.ACTIVE_STATUSES)),
        )
        return list(self.session.scalars(query))

    def _reclaim_expired_locks(self, *, policy_key: str, tenant_id: str, now: datetime) -> int:
        expired = list(
            self.session.scalars(
                select(ReminderJobRecord)
                .where(ReminderJobRecord.tenant_id == tenant_id)
                .where(ReminderJobRecord.policy_name == policy_key)
                .where(ReminderJobRecord.status == ReminderStatus.DISPATCHING.value)
                .where(ReminderJobRecord.locked_until_utc.is_not(None))
                .where(ReminderJobRecord.locked_until_utc <= now)
            )
        )
        reclaimed = 0
        for record in expired:
            if record.attempt_count >= record.max_attempts:
                self._transition_job_state(
                    record,
                    ReminderStatus.FAILED.value,
                    reason_code="lock_expired",
                    clear_lock=True,
                )
                self._append_audit(
                    tenant_id=record.tenant_id,
                    policy_key=record.policy_name,
                    policy_record_id=record.reminder_policy_id,
                    job_id=record.job_id,
                    appointment_external_id=record.appointment_id,
                    event_type="job.lock_expired_failed",
                    message="Expired lock moved job to failed",
                    reason_code="lock_expired",
                    payload={"job_id": record.job_id, "attempt_count": record.attempt_count},
                )
            else:
                self._transition_job_state(
                    record,
                    ReminderStatus.PLANNED.value,
                    reason_code="lock_expired",
                    clear_lock=True,
                )
                self._append_audit(
                    tenant_id=record.tenant_id,
                    policy_key=record.policy_name,
                    policy_record_id=record.reminder_policy_id,
                    job_id=record.job_id,
                    appointment_external_id=record.appointment_id,
                    event_type="job.lock_reclaimed",
                    message="Expired lock reclaimed for retry",
                    reason_code="lock_expired",
                    payload={"job_id": record.job_id, "attempt_count": record.attempt_count},
                )
            reclaimed += 1
        return reclaimed

    def _plan_jobs(
        self,
        policy: ReminderPolicyInput,
        appointments: list[ReminderAppointmentInput],
        *,
        policy_record_id: Optional[int],
        persist: bool,
    ) -> tuple[list[ReminderJobRecord], int, int, int]:
        if not policy.enabled:
            return [], 0, 0, 0
        preview = compute_preview(policy, appointments)
        jobs: list[ReminderJobRecord] = []
        created = 0
        updated = 0
        skipped = 0
        for item in preview:
            appointment = next(
                appointment for appointment in appointments if appointment.appointment_external_id == item.appointment_external_id
            )
            dispatch_key = self._job_identity_key(item.appointment_external_id, item.reminder_sequence, item.channel)
            existing = self.session.scalar(
                select(ReminderJobRecord).where(ReminderJobRecord.dispatch_key == dispatch_key)
            )
            payload = self._job_signature(appointment, item)
            if existing is not None:
                if existing.status in self.TERMINAL_STATUSES:
                    skipped += 1
                    jobs.append(existing)
                    self._append_audit(
                        tenant_id=appointment.tenant_id,
                        policy_key=policy.policy_key,
                        policy_record_id=policy_record_id,
                        job_id=existing.job_id,
                        appointment_external_id=appointment.appointment_external_id,
                        event_type="job.skipped_terminal",
                        message="Terminal reminder job kept as-is",
                        reason_code=existing.status,
                        payload={"dispatch_key": dispatch_key, "status": existing.status},
                    )
                    continue
                if (
                    existing.scheduled_for_utc == item.scheduled_for
                    and existing.appointment_start_at_utc == appointment.start_time
                    and existing.channel == item.channel
                    and existing.payload_json.get("reminder_hours_before") == item.reminder_hours_before
                ):
                    skipped += 1
                    jobs.append(existing)
                    continue
                existing.scheduled_for_utc = item.scheduled_for
                existing.appointment_start_at_utc = appointment.start_time
                existing.appointment_timezone = appointment.timezone
                existing.channel = item.channel
                existing.target_ref = appointment.email or appointment.phone
                existing.status = ReminderStatus.PLANNED.value
                existing.failure_reason_code = None
                existing.failure_reason_text = None
                existing.skip_reason_code = None
                existing.attempt_count = 0
                existing.max_attempts = self.DEFAULT_MAX_ATTEMPTS
                existing.locked_until_utc = None
                existing.dispatched_at_utc = None
                existing.provider_message_id = None
                existing.payload_json = payload
                self.session.commit()
                self.session.refresh(existing)
                updated += 1
                jobs.append(existing)
                self._append_audit(
                    tenant_id=appointment.tenant_id,
                    policy_key=policy.policy_key,
                    policy_record_id=policy_record_id,
                    job_id=existing.job_id,
                    appointment_external_id=appointment.appointment_external_id,
                    event_type="job.updated",
                    message="Reminder job updated to the current schedule",
                    payload={"dispatch_key": dispatch_key, "scheduled_for": item.scheduled_for.isoformat()},
                )
                continue
            record = self.job_repo.upsert(
                job_id=str(uuid4()),
                tenant_id=appointment.tenant_id,
                policy_name=policy.policy_key,
                appointment_id=appointment.appointment_external_id,
                external_appointment_id=appointment.appointment_external_id,
                reminder_policy_id=policy_record_id,
                reminder_sequence=item.reminder_sequence,
                scheduled_for_utc=item.scheduled_for,
                appointment_start_at_utc=appointment.start_time,
                appointment_timezone=appointment.timezone,
                channel=item.channel,
                target_ref=appointment.email or appointment.phone,
                status=item.status,
                failure_reason_code=None,
                failure_reason_text=None,
                skip_reason_code=None,
                attempt_count=0,
                max_attempts=self.DEFAULT_MAX_ATTEMPTS,
                dispatch_key=dispatch_key,
                locked_until_utc=None,
                dispatched_at_utc=None,
                provider_message_id=None,
                payload_json=payload,
            )
            created += 1
            jobs.append(record)
        if persist and (created or updated or skipped):
            self._append_audit(
                policy_key=policy.policy_key,
                policy_record_id=policy_record_id,
                event_type="jobs.planned",
                message="Reminder jobs planned",
                payload={"created": created, "updated": updated, "skipped": skipped, "appointments": len(appointments)},
            )
        return jobs, created, updated, skipped

    def get_config(self, policy_key: str = "global") -> ReminderConfigView:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        validation = validate_policy(policy)
        appointments = self._list_appointments(policy.tenant_id, policy.policy_key, policy_record.id)
        preview = compute_preview(policy, appointments)
        job_count = int(
            self.session.scalar(
                select(func.count())
                .select_from(ReminderJobRecord)
                .where(ReminderJobRecord.tenant_id == policy.tenant_id)
                .where(ReminderJobRecord.policy_name == policy.policy_key)
            )
            or 0
        )
        return ReminderConfigView(
            policy=policy,
            validation=validation,
            warnings=validation,
            preview=preview[:10],
            job_count=job_count,
            appointment_count=len(appointments),
        )

    def save_config(self, policy: ReminderPolicyInput) -> ReminderConfigView:
        validation = validate_policy(policy)
        policy_record = self._save_policy(policy)
        self._append_audit(
            tenant_id=policy.tenant_id,
            policy_key=policy.policy_key,
            policy_record_id=policy_record.id,
            event_type="config.saved",
            message="Reminder policy saved",
            payload={"validation": validation, "policy": policy.model_dump(mode="json")},
        )
        return self.get_config(policy.policy_key)

    def preview(self, request: ReminderPreviewRequest) -> ReminderConfigView:
        validation = validate_policy(request.policy)
        appointments = request.appointments or self._list_appointments(request.policy.tenant_id, request.policy.policy_key)
        preview = compute_preview(request.policy, appointments)
        return ReminderConfigView(
            policy=request.policy,
            validation=validation,
            warnings=validation,
            preview=preview,
            job_count=0,
            appointment_count=len(appointments),
        )

    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> list[ReminderJobView]:
        query = select(ReminderJobRecord).order_by(ReminderJobRecord.scheduled_for_utc.asc()).limit(limit)
        if status:
            query = query.where(ReminderJobRecord.status == status)
        rows = list(self.session.scalars(query))
        return [self._job_to_view(row) for row in rows]

    def get_job(self, job_id: str) -> ReminderJobView:
        record = self.job_repo.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        return self._job_to_view(record)

    def cancel_job(self, job_id: str, *, reason_code: str = "manual_cancel") -> ReminderJobView:
        record = self.job_repo.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        if record.status not in {ReminderStatus.PLANNED.value, ReminderStatus.DUE.value}:
            raise ReminderLifecycleError(f"Cannot cancel reminder job in state {record.status}")
        self._transition_job_state(
            record,
            ReminderStatus.CANCELLED.value,
            reason_code=reason_code,
            clear_lock=True,
        )
        self._append_audit(
            tenant_id=record.tenant_id,
            policy_key=record.policy_name,
            policy_record_id=record.reminder_policy_id,
            job_id=record.job_id,
            appointment_external_id=record.appointment_id,
            event_type="job.cancelled",
            message="Reminder job cancelled",
            reason_code=reason_code,
            payload={"job_id": record.job_id, "status": record.status},
        )
        return self._job_to_view(record)

    def retry_job(self, job_id: str) -> ReminderJobView:
        record = self.job_repo.get(job_id)
        if record is None:
            raise ValueError("Reminder job not found")
        if record.status != ReminderStatus.FAILED.value:
            raise ReminderLifecycleError("Only failed reminder jobs can be retried explicitly")
        if record.attempt_count >= record.max_attempts:
            raise ReminderLifecycleError("Retry limit reached for this reminder job")
        self._transition_job_state(
            record,
            ReminderStatus.PLANNED.value,
            reason_code="manual_retry",
            clear_lock=True,
        )
        self._append_audit(
            tenant_id=record.tenant_id,
            policy_key=record.policy_name,
            policy_record_id=record.reminder_policy_id,
            job_id=record.job_id,
            appointment_external_id=record.appointment_id,
            event_type="job.retry_requested",
            message="Reminder job moved back to planned for retry",
            reason_code="manual_retry",
            payload={"job_id": record.job_id, "attempt_count": record.attempt_count},
        )
        return self._job_to_view(record)

    def rebuild(self, request: ReminderRebuildRequest) -> dict[str, Any]:
        policy_record = self._get_policy_record(request.policy.policy_key if request.policy else "global")
        policy = request.policy or self._policy_record_to_input(policy_record)
        if request.policy is not None:
            policy_record = self._save_policy(policy)
        validation = validate_policy(policy)
        appointments = request.appointments or self._list_appointments(policy.tenant_id, policy.policy_key, policy_record.id)
        self.save_appointment_cache(appointments, policy_key=policy.policy_key, policy_record_id=policy_record.id)
        if request.replace_existing:
            # The rebuild pass keeps the latest future schedule in place. When
            # a reminder job changes its timing, we replace the old active row
            # before planning the fresh one so the dispatch key stays stable
            # and no duplicate active rows remain behind.
            desired_preview = compute_preview(policy, appointments)
            for item in desired_preview:
                appointment = next(
                    appointment for appointment in appointments if appointment.appointment_external_id == item.appointment_external_id
                )
                dispatch_key = self._job_identity_key(item.appointment_external_id, item.reminder_sequence, item.channel)
                existing = self.session.scalar(
                    select(ReminderJobRecord).where(ReminderJobRecord.dispatch_key == dispatch_key)
                )
                if existing is None:
                    continue
                if existing.status == ReminderStatus.DISPATCHING.value and existing.locked_until_utc and existing.locked_until_utc > utcnow():
                    self._append_audit(
                        tenant_id=existing.tenant_id,
                        policy_key=existing.policy_name,
                        policy_record_id=policy_record.id,
                        job_id=existing.job_id,
                        appointment_external_id=existing.appointment_id,
                        event_type="job.rebuild_skipped_locked",
                        message="Active dispatching job was left untouched during rebuild",
                        reason_code="locked_job",
                        payload={"dispatch_key": dispatch_key},
                    )
                    continue
                if (
                    existing.scheduled_for_utc == item.scheduled_for
                    and existing.appointment_start_at_utc == appointment.start_time
                    and existing.channel == item.channel
                ):
                    continue
                if existing.status in self.TERMINAL_STATUSES:
                    self._append_audit(
                        tenant_id=existing.tenant_id,
                        policy_key=existing.policy_name,
                        policy_record_id=policy_record.id,
                        job_id=existing.job_id,
                        appointment_external_id=existing.appointment_id,
                        event_type="job.rebuild_skipped_terminal",
                        message="Terminal reminder job was not recreated during rebuild",
                        reason_code=existing.status,
                        payload={"dispatch_key": dispatch_key},
                    )
                    continue
                self._append_audit(
                    tenant_id=existing.tenant_id,
                    policy_key=existing.policy_name,
                    policy_record_id=policy_record.id,
                    job_id=existing.job_id,
                    appointment_external_id=existing.appointment_id,
                    event_type="job.replaced",
                    message="Reminder job replaced during rebuild",
                    reason_code="rebuild_replace_existing",
                    payload={"dispatch_key": dispatch_key},
                )
                self.session.delete(existing)
                self.session.commit()
        planned, created, updated, skipped = self._plan_jobs(policy, appointments, policy_record_id=policy_record.id, persist=True)
        self._append_audit(
            tenant_id=policy.tenant_id,
            policy_key=policy.policy_key,
            policy_record_id=policy_record.id,
            event_type="jobs.rebuilt",
            message="Reminder jobs rebuilt",
            payload={"planned_jobs": len(planned), "created": created, "updated": updated, "skipped": skipped, "appointments": len(appointments), "validation": validation},
        )
        return {
            "success": True,
            "version": "v1.3.1",
            "policy_key": policy.policy_key,
            "appointment_count": len(appointments),
            "planned_jobs": len(planned),
            "jobs": [self._job_to_view(item).model_dump(mode="json") for item in planned],
            "validation": validation,
        }

    def plan_jobs(self, policy_key: str = "global") -> ReminderPlanningResult:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        appointments = self._list_appointments(policy.tenant_id, policy.policy_key, policy_record.id)
        planned, created, updated, skipped = self._plan_jobs(policy, appointments, policy_record_id=policy_record.id, persist=True)
        return ReminderPlanningResult(
            created_jobs=created,
            updated_jobs=updated,
            skipped_jobs=skipped,
            appointment_count=len(appointments),
            planned_preview=[self._job_to_preview(item) for item in planned],
        )

    def dispatch_due_jobs(self, policy_key: str = "global") -> ReminderDispatchResult:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        now = utcnow()
        reclaimed = self._reclaim_expired_locks(policy_key=policy.policy_key, tenant_id=policy.tenant_id, now=now)
        due_jobs = list(
            self.session.scalars(
                select(ReminderJobRecord)
                .where(ReminderJobRecord.tenant_id == policy.tenant_id)
                .where(ReminderJobRecord.policy_name == policy.policy_key)
                .where(ReminderJobRecord.status.in_([ReminderStatus.PLANNED.value, ReminderStatus.DUE.value]))
                .where(ReminderJobRecord.scheduled_for_utc <= now)
                .order_by(ReminderJobRecord.scheduled_for_utc.asc())
            )
        )
        dispatched = 0
        failed = 0
        skipped = 0
        for job in due_jobs:
            try:
                # A job may re-enter dispatching only after we explicitly claim
                # it. That keeps the worker deterministic and prevents stale
                # rows from being left in a pseudo-active state.
                self._transition_job_state(
                    job,
                    ReminderStatus.DISPATCHING.value,
                    reason_code="dispatch_claimed",
                )
                job.locked_until_utc = now + timedelta(minutes=self.DEFAULT_LOCK_MINUTES)
                job.attempt_count += 1
                self.session.commit()
                self.session.refresh(job)

                provider_message_id = self._deliver_job(job)
                self._transition_job_state(
                    job,
                    ReminderStatus.SENT.value,
                    clear_lock=True,
                    dispatched_at_utc=now,
                    provider_message_id=provider_message_id,
                )
                dispatched += 1
                self._append_audit(
                    tenant_id=job.tenant_id,
                    policy_key=job.policy_name,
                    policy_record_id=policy_record.id,
                    job_id=job.job_id,
                    appointment_external_id=job.appointment_id,
                    event_type="job.sent",
                    message="Reminder dispatched",
                    payload={
                        "channel": job.channel,
                        "scheduled_for_utc": job.scheduled_for_utc.isoformat(),
                        "provider_message_id": provider_message_id,
                    },
                )
            except Exception as exc:  # pragma: no cover - defensive worker guard
                failed += 1
                job.failure_reason_code = "dispatch_error"
                job.failure_reason_text = str(exc)
                if job.attempt_count < job.max_attempts:
                    self._transition_job_state(
                        job,
                        ReminderStatus.PLANNED.value,
                        reason_code="dispatch_retryable",
                        clear_lock=True,
                    )
                else:
                    self._transition_job_state(
                        job,
                        ReminderStatus.FAILED.value,
                        reason_code="dispatch_failed",
                        clear_lock=True,
                    )
                self._append_audit(
                    tenant_id=job.tenant_id,
                    policy_key=job.policy_name,
                    policy_record_id=policy_record.id,
                    job_id=job.job_id,
                    appointment_external_id=job.appointment_id,
                    event_type="job.failed",
                    message="Reminder dispatch failed",
                    reason_code="dispatch_error",
                    payload={
                        "attempt_count": job.attempt_count,
                        "max_attempts": job.max_attempts,
                        "error": str(exc),
                    },
                )
        return ReminderDispatchResult(
            due_jobs=len(due_jobs),
            dispatched_jobs=dispatched,
            failed_jobs=failed,
            skipped_jobs=skipped,
            reclaimed_jobs=reclaimed,
        )

    def health(self, policy_key: str = "global") -> ReminderHealthView:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        job_counts = {
            status.value: int(
                self.session.scalar(
                    select(func.count())
                    .select_from(ReminderJobRecord)
                    .where(ReminderJobRecord.tenant_id == policy.tenant_id)
                    .where(ReminderJobRecord.policy_name == policy.policy_key)
                    .where(ReminderJobRecord.status == status.value)
                )
                or 0
            )
            for status in ReminderStatus
        }
        next_due_at = self.session.scalar(
            select(func.min(ReminderJobRecord.scheduled_for_utc))
            .where(ReminderJobRecord.tenant_id == policy.tenant_id)
            .where(ReminderJobRecord.policy_name == policy.policy_key)
            .where(ReminderJobRecord.status.in_([ReminderStatus.PLANNED.value, ReminderStatus.DUE.value]))
        )
        appointment_count = int(
            self.session.scalar(
                select(func.count())
                .select_from(AppointmentCacheRecord)
                .where(AppointmentCacheRecord.tenant_id == policy.tenant_id)
                .where(AppointmentCacheRecord.reminder_policy_id == policy_record.id)
            )
            or 0
        )
        return ReminderHealthView(
            scheduler_enabled=policy.enabled,
            policy_key=policy.policy_key,
            policy_ready=policy.enabled,
            policy_mode=policy.mode.value,
            reminder_count=policy.reminder_count,
            appointment_count=appointment_count,
            job_counts=job_counts,
            next_due_at=next_due_at,
            reclaimed_locks=0,
        )


def get_default_service(session: Session) -> ReminderSchedulerService:
    return ReminderSchedulerService(session)
