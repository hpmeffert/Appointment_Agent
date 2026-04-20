from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

ReminderMode = Literal["manual", "auto_distributed"]
ReminderChannel = Literal["email", "voice", "rcs_sms"]
ReminderStatus = Literal["planned", "due", "dispatching", "sent", "failed", "skipped", "cancelled"]


class ReminderPolicySchema(BaseModel):
    tenant_id: str = "default"
    policy_name: str = "default"
    enabled: bool = True
    mode: ReminderMode = "manual"
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
    updated_by: Optional[str] = None
    version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def normalize_identity(self) -> "ReminderPolicySchema":
        # The scheduler treats missing identifiers as a shared default scope.
        self.tenant_id = (self.tenant_id or "default").strip() or "default"
        self.policy_name = (self.policy_name or "default").strip() or "default"
        return self


class ReminderScheduleItem(BaseModel):
    reminder_sequence: int = Field(ge=1, le=3)
    hours_before_appointment: int = Field(ge=0)
    scheduled_for_utc: datetime
    channel: ReminderChannel
    status: ReminderStatus = "planned"
    reminder_label: Optional[str] = None


class ReminderPreviewRequest(BaseModel):
    tenant_id: str = "default"
    appointment_id: str
    appointment_start_utc: datetime
    policy: ReminderPolicySchema = Field(default_factory=ReminderPolicySchema)


class ReminderPreviewResponse(BaseModel):
    tenant_id: str
    appointment_id: str
    appointment_start_utc: datetime
    policy: ReminderPolicySchema
    items: list[ReminderScheduleItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReminderJobSchema(BaseModel):
    job_id: str
    tenant_id: str = "default"
    policy_name: str = "default"
    appointment_id: str
    external_appointment_id: str
    reminder_sequence: int = Field(ge=1, le=3)
    scheduled_for_utc: datetime
    appointment_start_at_utc: datetime
    appointment_timezone: Optional[str] = None
    channel: ReminderChannel
    target_ref: Optional[str] = None
    status: ReminderStatus = "planned"
    failure_reason_code: Optional[str] = None
    failure_reason_text: Optional[str] = None
    skip_reason_code: Optional[str] = None
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    dispatch_key: str
    locked_until_utc: Optional[datetime] = None
    dispatched_at_utc: Optional[datetime] = None
    provider_message_id: Optional[str] = None
    payload_json: dict[str, Any] = Field(default_factory=dict)


class ReminderAppointmentCacheSchema(BaseModel):
    tenant_id: str = "default"
    external_appointment_id: str
    calendar_source_type: str
    calendar_source_ref: str
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_at_utc: datetime
    end_at_utc: Optional[datetime] = None
    timezone: Optional[str] = None
    status: str = "scheduled"
    participant_ref: Optional[str] = None
    contact_ref: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    reminder_policy_id: Optional[int] = None
    raw_payload_json: dict[str, Any] = Field(default_factory=dict)
    source_hash: Optional[str] = None
    last_seen_at_utc: Optional[datetime] = None


class ReminderAuditSchema(BaseModel):
    audit_id: str
    tenant_id: str = "default"
    appointment_id: Optional[str] = None
    reminder_job_id: Optional[str] = None
    reminder_policy_id: Optional[int] = None
    event_type: str
    reason_code: Optional[str] = None
    human_readable_message: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    created_at_utc: Optional[datetime] = None
