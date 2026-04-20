from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appointment_agent_shared.models import AppointmentCacheRecord, ReminderJobRecord, ReminderPolicyRecord
from appointment_agent_shared.repositories import (
    AppointmentCacheRepository,
    ReminderAuditRepository,
    ReminderJobRepository,
    ReminderPolicyRepository,
    build_reminder_runtime_health_snapshot,
)

from . import adapter, calculator, delivery, sync, time_utils, validation


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

    @model_validator(mode="after")
    def ensure_time_values_are_safe(self) -> "ReminderAppointmentInput":
        self.start_time = time_utils.canonicalize_datetime(
            self.start_time,
            timezone_name=self.timezone,
            field_name=f"{self.appointment_external_id}.start_time",
        )
        self.end_time = time_utils.canonicalize_datetime(
            self.end_time,
            timezone_name=self.timezone,
            field_name=f"{self.appointment_external_id}.end_time",
        )
        if self.end_time < self.start_time:
            raise ValueError("end_time must be later than or equal to start_time.")
        return self


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
    skip_reason_code: Optional[str] = None


class ReminderConfigView(BaseModel):
    policy: ReminderPolicyInput
    validation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    preview: list[ReminderPreviewItem] = Field(default_factory=list)
    skipped_preview_items: int = 0
    cancelled_preview_items: int = 0
    job_count: int = 0
    appointment_count: int = 0


class ReminderHealthView(BaseModel):
    version: str = "v1.3.5"
    scheduler_enabled: bool
    db_status: str = "ok"
    worker_status: str = "ready"
    policy_key: str
    policy_ready: bool
    policy_mode: str
    reminder_count: int
    appointment_count: int
    job_counts: dict[str, int]
    hold_counts: dict[str, int] = Field(default_factory=dict)
    message_counts: dict[str, int] = Field(default_factory=dict)
    audit_counts: dict[str, int] = Field(default_factory=dict)
    next_due_at: Optional[datetime] = None
    reclaimed_locks: int = 0
    active_job_count: int = 0
    last_job_activity_at: Optional[datetime] = None
    last_message_activity_at: Optional[datetime] = None
    last_audit_activity_at: Optional[datetime] = None
    health_notes: list[str] = Field(default_factory=list)


class ReminderPlanningResult(BaseModel):
    created_jobs: int = 0
    updated_jobs: int = 0
    skipped_jobs: int = 0
    skipped_past_jobs: int = 0
    cancelled_jobs: int = 0
    appointment_count: int = 0
    planned_preview: list[ReminderPreviewItem] = Field(default_factory=list)


class ReminderDispatchResult(BaseModel):
    due_jobs: int = 0
    dispatched_jobs: int = 0
    retryable_failures: int = 0
    terminal_failures: int = 0
    failed_jobs: int = 0
    skipped_jobs: int = 0
    reclaimed_jobs: int = 0


def _default_policy() -> ReminderPolicyInput:
    return ReminderPolicyInput()


def _default_appointments(policy_key: str) -> list[ReminderAppointmentInput]:
    now = time_utils.utcnow()
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


class ReminderCalculationAdapter:
    """Small translation layer between pure calculation items and API models."""

    @staticmethod
    def to_preview(item: calculator.CalculatedReminderItem) -> ReminderPreviewItem:
        return ReminderPreviewItem(
            appointment_external_id=item.appointment_external_id,
            reminder_sequence=item.reminder_sequence,
            channel=item.channel,
            reminder_hours_before=item.reminder_hours_before,
            scheduled_for=item.scheduled_for,
            status=item.status,
            skip_reason_code=item.skip_reason_code,
        )



class ReminderSchedulerService:
    """Reminder scheduler domain service with hardened UTC lifecycle rules."""

    TERMINAL_STATUSES = {
        ReminderStatus.SENT.value,
        ReminderStatus.FAILED.value,
        ReminderStatus.SKIPPED.value,
        ReminderStatus.CANCELLED.value,
    }
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

    def _normalized_appointments(
        self,
        appointments: list[ReminderAppointmentInput],
    ) -> list[ReminderAppointmentInput]:
        return validation.normalize_appointments(appointments)

    def _appointment_sync_snapshot(
        self,
        appointment: ReminderAppointmentInput,
        *,
        policy_key: str,
    ) -> adapter.NormalizedAppointmentSnapshot:
        # The sync snapshot is the canonical contract for adapter-style
        # ingestion. It carries UTC timestamps plus a stable hash so repeated
        # sync runs can cheaply detect whether anything changed.
        return adapter.normalize_appointment_snapshot(appointment, policy_key=policy_key)

    def save_appointment_cache(
        self,
        appointments: list[ReminderAppointmentInput],
        *,
        policy_key: str,
        policy_record_id: Optional[int] = None,
    ) -> int:
        saved = 0
        for appointment in appointments:
            snapshot = self._appointment_sync_snapshot(appointment, policy_key=policy_key)
            existing = self.session.scalar(
                select(AppointmentCacheRecord).where(
                    AppointmentCacheRecord.tenant_id == appointment.tenant_id,
                    AppointmentCacheRecord.external_appointment_id == appointment.appointment_external_id,
                    AppointmentCacheRecord.calendar_source_type == "reminder_scheduler",
                    AppointmentCacheRecord.calendar_source_ref == policy_key,
                )
            )
            existing_hash = (existing.raw_payload_json or {}).get("sync_hash") if existing is not None else None
            decision = sync.classify_appointment_sync(
                existing_hash=existing_hash,
                existing_status=existing.status if existing is not None else None,
                snapshot=snapshot,
            )
            # Appointment cache rows intentionally store UTC-normalized times
            # plus a stable sync hash. That makes reconciliation deterministic
            # and allows repeated polling syncs to stay idempotent.
            self.appointment_repo.upsert(
                tenant_id=appointment.tenant_id,
                external_appointment_id=appointment.appointment_external_id,
                calendar_source_type="reminder_scheduler",
                calendar_source_ref=policy_key,
                title=appointment.title,
                start_at_utc=snapshot.start_at_utc,
                end_at_utc=snapshot.end_at_utc,
                timezone=snapshot.timezone,
                status=snapshot.status,
                participant_ref=appointment.customer_id,
                contact_ref=appointment.customer_id,
                email=appointment.email,
                phone=appointment.phone,
                reminder_policy_id=policy_record_id,
                raw_payload_json={
                    **snapshot.raw_payload_json,
                    "sync_hash": snapshot.payload_hash,
                },
                last_seen_at_utc=time_utils.utcnow(),
            )
            if decision.hash_changed or decision.status_changed:
                self._append_audit(
                    tenant_id=appointment.tenant_id,
                    policy_key=policy_key,
                    policy_record_id=policy_record_id,
                    event_type=f"appointment.sync.{decision.action}",
                    message="Appointment cache entry updated from sync snapshot",
                    payload={
                        "appointment_external_id": appointment.appointment_external_id,
                        "sync_hash": snapshot.payload_hash,
                        "status": snapshot.status,
                        "hash_changed": decision.hash_changed,
                        "status_changed": decision.status_changed,
                    },
                )
            saved += 1
        return saved

    def _job_identity_key(self, appointment_external_id: str, reminder_sequence: int, channel: str) -> str:
        return f"{appointment_external_id}:{reminder_sequence}:{channel}"

    def _job_to_view(self, record: ReminderJobRecord) -> ReminderJobView:
        scheduled_for = record.scheduled_for_utc
        appointment_start_at = record.appointment_start_at_utc
        sent_at = record.dispatched_at_utc
        if scheduled_for.tzinfo is None:
            scheduled_for = scheduled_for.replace(tzinfo=time_utils.UTC)
        if appointment_start_at.tzinfo is None:
            appointment_start_at = appointment_start_at.replace(tzinfo=time_utils.UTC)
        if sent_at is not None and sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=time_utils.UTC)
        return ReminderJobView(
            job_id=record.job_id,
            policy_key=record.policy_name,
            appointment_external_id=record.external_appointment_id,
            reminder_sequence=record.reminder_sequence,
            scheduled_for=scheduled_for,
            appointment_start_at=appointment_start_at,
            channel=record.channel,
            status=record.status,
            dispatch_key=record.dispatch_key,
            attempt_count=record.attempt_count,
            max_attempts=record.max_attempts,
            payload=record.payload_json,
            last_error=record.failure_reason_text,
            sent_at=sent_at,
        )

    def _calculated_item_to_preview(self, item: calculator.CalculatedReminderItem) -> ReminderPreviewItem:
        return ReminderPreviewItem(
            appointment_external_id=item.appointment_external_id,
            reminder_sequence=item.reminder_sequence,
            channel=item.channel,
            reminder_hours_before=item.reminder_hours_before,
            scheduled_for=item.scheduled_for,
            status=item.status,
            skip_reason_code=item.skip_reason_code,
        )

    def _preview_item_for_appointment(
        self,
        appointment: ReminderAppointmentInput,
        item: calculator.CalculatedReminderItem,
    ) -> ReminderPreviewItem:
        # Cancelled appointments still participate in the sync graph, but the
        # reminder preview should make it obvious that no delivery will happen.
        if appointment.status.lower() == "cancelled":
            return ReminderPreviewItem(
                appointment_external_id=item.appointment_external_id,
                reminder_sequence=item.reminder_sequence,
                channel=item.channel,
                reminder_hours_before=item.reminder_hours_before,
                scheduled_for=item.scheduled_for,
                status=ReminderStatus.SKIPPED.value,
                skip_reason_code="appointment_cancelled",
            )
        return self._calculated_item_to_preview(item)

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

    def _target_ref_for_channel(self, appointment: ReminderAppointmentInput, channel: str) -> Optional[str]:
        # Channel-specific target selection stays in one helper so planning,
        # update, and dispatch all see the same contact data.
        if channel in {ReminderChannel.VOICE.value, ReminderChannel.RCS_SMS.value}:
            return appointment.phone or appointment.email
        return appointment.email or appointment.phone

    def _job_signature(self, appointment: ReminderAppointmentInput, item: calculator.CalculatedReminderItem) -> dict[str, Any]:
        return {
            "appointment_external_id": appointment.appointment_external_id,
            "reminder_sequence": item.reminder_sequence,
            "channel": item.channel,
            "scheduled_for": item.scheduled_for.isoformat(),
            "appointment_start_at": appointment.start_time.isoformat(),
            "appointment_timezone": appointment.timezone,
            "target_ref": self._target_ref_for_channel(appointment, item.channel),
            "reminder_hours_before": item.reminder_hours_before,
            # The metadata travels with the job so the delivery layer can
            # inspect simulation flags without reaching back into the cache.
            "appointment_metadata": appointment.metadata,
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
            ReminderStatus.PLANNED.value: {
                ReminderStatus.DISPATCHING.value,
                ReminderStatus.SKIPPED.value,
                ReminderStatus.CANCELLED.value,
                ReminderStatus.PLANNED.value,
            },
            ReminderStatus.DUE.value: {
                ReminderStatus.DISPATCHING.value,
                ReminderStatus.PLANNED.value,
                ReminderStatus.CANCELLED.value,
                ReminderStatus.SKIPPED.value,
            },
            ReminderStatus.DISPATCHING.value: {
                ReminderStatus.SENT.value,
                ReminderStatus.FAILED.value,
                ReminderStatus.PLANNED.value,
                ReminderStatus.CANCELLED.value,
            },
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

    def _delivery_registry(self, policy: ReminderPolicyInput) -> delivery.ReminderDispatcherRegistry:
        return delivery.build_dispatcher_registry(
            email_enabled=policy.channel_email_enabled,
            voice_enabled=policy.channel_voice_enabled,
            rcs_sms_enabled=policy.channel_rcs_sms_enabled,
        )

    def _dispatch_result_payload(self, result: delivery.DispatchResult, *, now: datetime) -> dict[str, Any]:
        payload = result.to_payload()
        payload["dispatched_at_utc"] = now.isoformat()
        return payload

    def _finalize_dispatch_result(
        self,
        record: ReminderJobRecord,
        result: delivery.DispatchResult,
        *,
        now: datetime,
        policy_record_id: Optional[int],
        policy_key: str,
    ) -> tuple[bool, bool]:
        """Apply one normalized delivery result to one reminder job.

        Returning a tuple keeps the worker summary logic simple:
        ``(dispatched, retryable_failure)``. Terminal failures are the
        complementary non-success outcome.
        """

        record.payload_json = {
            **record.payload_json,
            "last_dispatch_result": self._dispatch_result_payload(result, now=now),
        }

        if result.success:
            record.failure_reason_code = None
            record.failure_reason_text = None
            record.skip_reason_code = None
            self._transition_job_state(
                record,
                ReminderStatus.SENT.value,
                clear_lock=True,
                dispatched_at_utc=now,
                provider_message_id=result.provider_message_id,
            )
            self._append_audit(
                tenant_id=record.tenant_id,
                policy_key=policy_key,
                policy_record_id=policy_record_id,
                job_id=record.job_id,
                appointment_external_id=record.appointment_id,
                event_type="job.sent",
                message="Reminder dispatched",
                payload={
                    "channel": record.channel,
                    "scheduled_for_utc": record.scheduled_for_utc.isoformat(),
                    "provider_message_id": result.provider_message_id,
                    "dispatch_result": result.to_payload(),
                },
            )
            return True, False

        record.failure_reason_code = result.failure_reason_code
        record.failure_reason_text = result.failure_reason_text
        if result.retryable and record.attempt_count < record.max_attempts:
            self._transition_job_state(
                record,
                ReminderStatus.PLANNED.value,
                reason_code=result.failure_reason_code or "dispatch_retryable",
                clear_lock=True,
            )
            self._append_audit(
                tenant_id=record.tenant_id,
                policy_key=policy_key,
                policy_record_id=policy_record_id,
                job_id=record.job_id,
                appointment_external_id=record.appointment_id,
                event_type="job.failed_retryable",
                message="Reminder dispatch failed but remains retryable",
                reason_code=result.failure_reason_code or "dispatch_retryable",
                payload={
                    "attempt_count": record.attempt_count,
                    "max_attempts": record.max_attempts,
                    "dispatch_result": result.to_payload(),
                },
            )
            return False, True

        self._transition_job_state(
            record,
            ReminderStatus.FAILED.value,
            reason_code=result.failure_reason_code or "dispatch_failed",
            clear_lock=True,
        )
        self._append_audit(
            tenant_id=record.tenant_id,
            policy_key=policy_key,
            policy_record_id=policy_record_id,
            job_id=record.job_id,
            appointment_external_id=record.appointment_id,
            event_type="job.failed",
            message="Reminder dispatch failed",
            reason_code=result.failure_reason_code or "dispatch_failed",
            payload={
                "attempt_count": record.attempt_count,
                "max_attempts": record.max_attempts,
                "dispatch_result": result.to_payload(),
            },
        )
        return False, False

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
        calculation: calculator.ReminderCalculationResult,
        policy_record_id: Optional[int],
    ) -> tuple[list[ReminderJobRecord], int, int, int, int, int]:
        if not policy.enabled:
            return [], 0, 0, 0, 0, 0

        appointment_map = {appointment.appointment_external_id: appointment for appointment in appointments}
        jobs: list[ReminderJobRecord] = []
        created = 0
        updated = 0
        skipped = 0
        skipped_past = 0
        cancelled = 0
        now_utc = time_utils.utcnow()

        for item in calculation.items:
            appointment = appointment_map[item.appointment_external_id]
            dispatch_key = self._job_identity_key(item.appointment_external_id, item.reminder_sequence, item.channel)
            existing = self.session.scalar(select(ReminderJobRecord).where(ReminderJobRecord.dispatch_key == dispatch_key))
            payload = self._job_signature(appointment, item)
            appointment_status = appointment.status.lower()

            if appointment_status == "cancelled":
                cancelled += 1
                if existing is None:
                    self._append_audit(
                        tenant_id=appointment.tenant_id,
                        policy_key=policy.policy_key,
                        policy_record_id=policy_record_id,
                        job_id=None,
                        appointment_external_id=appointment.appointment_external_id,
                        event_type="job.cancelled_missing",
                        message="Cancelled appointment had no reminder job to cancel",
                        reason_code="appointment_cancelled",
                        payload={"dispatch_key": dispatch_key, **payload},
                    )
                    continue
                if existing.status in self.ACTIVE_STATUSES:
                    self._transition_job_state(
                        existing,
                        ReminderStatus.CANCELLED.value,
                        reason_code="appointment_cancelled",
                        clear_lock=True,
                        payload={**existing.payload_json, "skip_reason_code": "appointment_cancelled"},
                    )
                    jobs.append(existing)
                    updated += 1
                    self._append_audit(
                        tenant_id=appointment.tenant_id,
                        policy_key=policy.policy_key,
                        policy_record_id=policy_record_id,
                        job_id=existing.job_id,
                        appointment_external_id=appointment.appointment_external_id,
                        event_type="job.cancelled_by_sync",
                        message="Reminder job cancelled because the source appointment was cancelled",
                        reason_code="appointment_cancelled",
                        payload={"dispatch_key": dispatch_key, "job_id": existing.job_id},
                    )
                    continue
                skipped += 1
                jobs.append(existing)
                continue

            if item.status == ReminderStatus.SKIPPED.value:
                skipped_past += 1
                if existing is None:
                    self._append_audit(
                        tenant_id=appointment.tenant_id,
                        policy_key=policy.policy_key,
                        policy_record_id=policy_record_id,
                        job_id=None,
                        appointment_external_id=appointment.appointment_external_id,
                        event_type="job.skipped_past",
                        message="Past reminder skipped before job creation",
                        reason_code=item.skip_reason_code or "past_reminder",
                        payload={"dispatch_key": dispatch_key, **payload},
                    )
                    continue
                if existing.status in self.ACTIVE_STATUSES:
                    self._transition_job_state(
                        existing,
                        ReminderStatus.SKIPPED.value,
                        reason_code=item.skip_reason_code or "past_reminder",
                        clear_lock=True,
                        payload={**existing.payload_json, "skip_reason_code": item.skip_reason_code or "past_reminder"},
                    )
                    jobs.append(existing)
                    updated += 1
                    self._append_audit(
                        tenant_id=appointment.tenant_id,
                        policy_key=policy.policy_key,
                        policy_record_id=policy_record_id,
                        job_id=existing.job_id,
                        appointment_external_id=appointment.appointment_external_id,
                        event_type="job.skipped_past",
                        message="Active reminder moved to skipped because its fire time is already in the past",
                        reason_code=item.skip_reason_code or "past_reminder",
                        payload={"dispatch_key": dispatch_key, "job_id": existing.job_id},
                    )
                    continue
                skipped += 1
                jobs.append(existing)
                continue

            if existing is not None:
                if existing.status == ReminderStatus.DISPATCHING.value and existing.locked_until_utc and existing.locked_until_utc > now_utc:
                    skipped += 1
                    jobs.append(existing)
                    self._append_audit(
                        tenant_id=appointment.tenant_id,
                        policy_key=policy.policy_key,
                        policy_record_id=policy_record_id,
                        job_id=existing.job_id,
                        appointment_external_id=appointment.appointment_external_id,
                        event_type="job.rebuild_skipped_locked",
                        message="Active dispatching job was left untouched during rebuild",
                        reason_code="locked_job",
                        payload={"dispatch_key": dispatch_key},
                    )
                    continue
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
                existing.target_ref = self._target_ref_for_channel(appointment, item.channel)
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
                target_ref=self._target_ref_for_channel(appointment, item.channel),
                status=item.status,
                failure_reason_code=None,
                failure_reason_text=None,
                skip_reason_code=item.skip_reason_code,
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
            self._append_audit(
                tenant_id=appointment.tenant_id,
                policy_key=policy.policy_key,
                policy_record_id=policy_record_id,
                job_id=record.job_id,
                appointment_external_id=appointment.appointment_external_id,
                event_type="job.created",
                message="Reminder job created",
                payload={"dispatch_key": dispatch_key, "scheduled_for": item.scheduled_for.isoformat()},
            )

        self._append_audit(
            policy_key=policy.policy_key,
            policy_record_id=policy_record_id,
            event_type="jobs.planned",
            message="Reminder jobs planned",
            payload={
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "skipped_past": skipped_past,
                "cancelled": cancelled,
                "appointments": len(appointments),
            },
        )
        return jobs, created, updated, skipped, skipped_past, cancelled

    def _calculate(self, policy: ReminderPolicyInput, appointments: list[ReminderAppointmentInput]) -> calculator.ReminderCalculationResult:
        normalized = self._normalized_appointments(appointments)
        return calculator.calculate_schedule(policy, normalized, now_utc=time_utils.utcnow())

    def get_config(self, policy_key: str = "global") -> ReminderConfigView:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        validation_result = validation.validate_policy(policy)
        appointments = self._normalized_appointments(self._list_appointments(policy.tenant_id, policy.policy_key, policy_record.id))
        calculation = calculator.calculate_schedule(policy, appointments, now_utc=time_utils.utcnow())
        appointment_map = {appointment.appointment_external_id: appointment for appointment in appointments}
        job_count = int(
            self.session.scalar(
                select(func.count())
                .select_from(ReminderJobRecord)
                .where(ReminderJobRecord.tenant_id == policy.tenant_id)
                .where(ReminderJobRecord.policy_name == policy.policy_key)
            )
            or 0
        )
        preview_items = [self._preview_item_for_appointment(appointment_map[item.appointment_external_id], item) for item in calculation.items[:10]]
        return ReminderConfigView(
            policy=policy,
            validation=validation_result,
            warnings=validation_result,
            preview=preview_items,
            skipped_preview_items=calculation.skipped_count,
            cancelled_preview_items=sum(1 for item in preview_items if item.skip_reason_code == "appointment_cancelled"),
            job_count=job_count,
            appointment_count=len(appointments),
        )

    def save_config(self, policy: ReminderPolicyInput) -> ReminderConfigView:
        validation_result = validation.validate_policy(policy)
        policy_record = self._save_policy(policy)
        self._append_audit(
            tenant_id=policy.tenant_id,
            policy_key=policy.policy_key,
            policy_record_id=policy_record.id,
            event_type="config.saved",
            message="Reminder policy saved",
            payload={"validation": validation_result, "policy": policy.model_dump(mode="json")},
        )
        return self.get_config(policy.policy_key)

    def preview(self, request: ReminderPreviewRequest) -> ReminderConfigView:
        validation_result = validation.validate_policy(request.policy)
        appointments = request.appointments or self._list_appointments(request.policy.tenant_id, request.policy.policy_key)
        normalized_appointments = self._normalized_appointments(appointments)
        calculation = calculator.calculate_schedule(request.policy, normalized_appointments, now_utc=time_utils.utcnow())
        appointment_map = {appointment.appointment_external_id: appointment for appointment in normalized_appointments}
        preview_items = [self._preview_item_for_appointment(appointment_map[item.appointment_external_id], item) for item in calculation.items]
        return ReminderConfigView(
            policy=request.policy,
            validation=validation_result,
            warnings=validation_result,
            preview=preview_items,
            skipped_preview_items=calculation.skipped_count,
            cancelled_preview_items=sum(1 for item in preview_items if item.skip_reason_code == "appointment_cancelled"),
            job_count=0,
            appointment_count=len(normalized_appointments),
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
        validation_result = validation.validate_policy(policy)
        appointments = request.appointments or self._list_appointments(policy.tenant_id, policy.policy_key, policy_record.id)
        normalized_appointments = self._normalized_appointments(appointments)
        self.save_appointment_cache(normalized_appointments, policy_key=policy.policy_key, policy_record_id=policy_record.id)
        calculation = calculator.calculate_schedule(policy, normalized_appointments, now_utc=time_utils.utcnow())
        planned, created, updated, skipped, skipped_past, cancelled = self._plan_jobs(
            policy,
            normalized_appointments,
            calculation=calculation,
            policy_record_id=policy_record.id,
        )
        self._append_audit(
            tenant_id=policy.tenant_id,
            policy_key=policy.policy_key,
            policy_record_id=policy_record.id,
            event_type="jobs.rebuilt",
            message="Reminder jobs rebuilt",
            payload={
                "planned_jobs": calculation.planned_count,
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "skipped_past": skipped_past,
                "cancelled": cancelled,
                "appointments": len(normalized_appointments),
                "validation": validation_result,
            },
        )
        return {
            "success": True,
            "version": "v1.3.5",
            "policy_key": policy.policy_key,
            "appointment_count": len(normalized_appointments),
            "planned_jobs": sum(1 for item in planned if item.status in self.ACTIVE_STATUSES),
            "skipped_past_jobs": calculation.skipped_count,
            "cancelled_jobs": cancelled,
            "jobs": [self._job_to_view(item).model_dump(mode="json") for item in planned],
            "validation": validation_result,
        }

    def plan_jobs(self, policy_key: str = "global") -> ReminderPlanningResult:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        appointments = self._normalized_appointments(self._list_appointments(policy.tenant_id, policy.policy_key, policy_record.id))
        calculation = calculator.calculate_schedule(policy, appointments, now_utc=time_utils.utcnow())
        appointment_map = {appointment.appointment_external_id: appointment for appointment in appointments}
        planned, created, updated, skipped, skipped_past, cancelled = self._plan_jobs(
            policy,
            appointments,
            calculation=calculation,
            policy_record_id=policy_record.id,
        )
        return ReminderPlanningResult(
            created_jobs=created,
            updated_jobs=updated,
            skipped_jobs=skipped,
            skipped_past_jobs=skipped_past,
            cancelled_jobs=cancelled,
            appointment_count=len(appointments),
            planned_preview=[self._preview_item_for_appointment(appointment_map[item.appointment_external_id], item) for item in calculation.items],
        )

    def dispatch_due_jobs(self, policy_key: str = "global") -> ReminderDispatchResult:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        dispatcher_registry = self._delivery_registry(policy)
        now = time_utils.utcnow()
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
        retryable_failures = 0
        terminal_failures = 0
        skipped = 0
        for job in due_jobs:
            try:
                # Claiming a job explicitly keeps worker cycles deterministic
                # and makes lock expiry / reclaim behavior observable.
                self._transition_job_state(
                    job,
                    ReminderStatus.DISPATCHING.value,
                    reason_code="dispatch_claimed",
                )
                job.locked_until_utc = now + timedelta(minutes=self.DEFAULT_LOCK_MINUTES)
                job.attempt_count += 1
                self.session.commit()
                self.session.refresh(job)

                dispatch_result = dispatcher_registry.dispatch(job, now_utc=now)
                was_dispatched, was_retryable = self._finalize_dispatch_result(
                    job,
                    dispatch_result,
                    now=now,
                    policy_record_id=policy_record.id,
                    policy_key=policy.policy_key,
                )
                if was_dispatched:
                    dispatched += 1
                elif was_retryable:
                    retryable_failures += 1
                else:
                    terminal_failures += 1
            except Exception as exc:  # pragma: no cover - defensive worker guard
                # Unexpected dispatcher errors are still classified using the
                # same retry rules as the normalized result path. That keeps
                # the worker resilient even if a new adapter raises before it
                # can return a structured failure object.
                job.failure_reason_code = "dispatch_error"
                job.failure_reason_text = str(exc)
                if job.attempt_count < job.max_attempts:
                    retryable_failures += 1
                    self._transition_job_state(
                        job,
                        ReminderStatus.PLANNED.value,
                        reason_code="dispatch_retryable",
                        clear_lock=True,
                    )
                    self._append_audit(
                        tenant_id=job.tenant_id,
                        policy_key=job.policy_name,
                        policy_record_id=policy_record.id,
                        job_id=job.job_id,
                        appointment_external_id=job.appointment_id,
                        event_type="job.failed_retryable",
                        message="Reminder dispatch failed but remains retryable",
                        reason_code="dispatch_error",
                        payload={
                            "attempt_count": job.attempt_count,
                            "max_attempts": job.max_attempts,
                            "error": str(exc),
                        },
                    )
                else:
                    terminal_failures += 1
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
            retryable_failures=retryable_failures,
            terminal_failures=terminal_failures,
            failed_jobs=retryable_failures + terminal_failures,
            skipped_jobs=skipped,
            reclaimed_jobs=reclaimed,
        )

    def health(self, policy_key: str = "global") -> ReminderHealthView:
        policy_record = self._get_policy_record(policy_key)
        policy = self._policy_record_to_input(policy_record)
        runtime_snapshot = build_reminder_runtime_health_snapshot(
            self.session,
            tenant_id=policy.tenant_id,
            policy_name=policy.policy_key,
            now_utc=time_utils.utcnow(),
        )
        return ReminderHealthView(
            scheduler_enabled=policy.enabled,
            db_status="ok",
            worker_status="ready" if policy.enabled else "disabled",
            policy_key=policy.policy_key,
            policy_ready=policy.enabled,
            policy_mode=policy.mode.value,
            reminder_count=policy.reminder_count,
            appointment_count=runtime_snapshot.appointment_count,
            job_counts=runtime_snapshot.job_counts,
            hold_counts=runtime_snapshot.hold_counts,
            message_counts=runtime_snapshot.message_counts,
            audit_counts=runtime_snapshot.audit_counts,
            next_due_at=runtime_snapshot.next_due_at_utc,
            reclaimed_locks=runtime_snapshot.reclaimable_lock_count,
            active_job_count=runtime_snapshot.active_job_count,
            last_job_activity_at=runtime_snapshot.last_job_activity_at_utc,
            last_message_activity_at=runtime_snapshot.last_message_activity_at_utc,
            last_audit_activity_at=runtime_snapshot.last_audit_activity_at_utc,
            health_notes=runtime_snapshot.health_notes,
        )


def get_default_service(session: Session) -> ReminderSchedulerService:
    return ReminderSchedulerService(session)
