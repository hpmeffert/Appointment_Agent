from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from .validators import require_non_empty


class SearchSlotsCommand(BaseModel):
    tenant_id: str
    journey_id: str = "system"
    customer_id: Optional[str] = None
    service_type: str
    duration_minutes: int
    date_window_start: datetime
    date_window_end: datetime
    preferred_month: Optional[str] = None
    preferred_weekdays: list[str] = Field(default_factory=list)
    preferred_daypart: Optional[str] = None
    timezone: str
    resource_candidates: list[str] = Field(default_factory=list)
    location_type: Optional[str] = None
    max_slots: int = 5


class HoldSlotCommand(BaseModel):
    journey_id: str
    customer_id: Optional[str] = None
    slot_id: str
    hold_duration_minutes: int
    reason: Optional[str] = None


class ReleaseSlotHoldCommand(BaseModel):
    journey_id: str
    hold_id: str
    reason: Optional[str] = None


class CreateBookingCommand(BaseModel):
    tenant_id: str
    journey_id: str
    customer_id: Optional[str] = None
    booking_reference: Optional[str] = None
    slot_id: str
    calendar_target: str
    title: str
    description: Optional[str] = None
    attendees: list[Any] = Field(default_factory=list)
    timezone: str
    crm_reference: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateBookingCommand(BaseModel):
    booking_reference: str
    provider_reference: str
    new_start: Optional[datetime] = None
    new_end: Optional[datetime] = None
    new_title: Optional[str] = None
    new_description: Optional[str] = None
    attendees: list[Any] = Field(default_factory=list)
    reason: Optional[str] = None


class CancelBookingCommand(BaseModel):
    booking_reference: str
    provider_reference: str
    reason: Optional[str] = None
    requested_by: Optional[str] = None


class ResolveCustomerCommand(BaseModel):
    tenant_id: str
    phone: Optional[str] = None
    email: Optional[str] = None
    external_customer_id: Optional[str] = None
    crm_reference: Optional[str] = None
    channel: Optional[str] = None
    locale: Optional[str] = None
    mobile_number: Optional[str] = None

    @model_validator(mode="after")
    def ensure_lookup_field(self) -> "ResolveCustomerCommand":
        if not any([self.phone, self.email, self.external_customer_id, self.crm_reference, self.mobile_number]):
            raise ValueError("ResolveCustomerCommand requires at least one lookup field")
        return self


class UpsertCustomerCommand(BaseModel):
    tenant_id: str
    customer_id: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    consent_sms: bool = True
    consent_rcs: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class LaunchAppointmentWorkflowCommand(BaseModel):
    tenant_id: str
    correlation_id: str
    booking_reference: Optional[str] = None
    lekab_job_template_id: Optional[str] = None
    job_id: Optional[str] = None
    job_name: str
    message_text: Optional[str] = None
    message: Optional[str] = None
    recipient_phone_numbers: list[str] = Field(default_factory=list)
    to_numbers: list[str] = Field(default_factory=list)
    saved_tag_filters: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    custom_tag_filter: Optional[str] = None
    exclude_numbers: list[str] = Field(default_factory=list)
    exclude_filter: Optional[str] = None
    scheduled_start: Optional[str] = None
    response_goal: Optional[int] = None
    keep_existing_recipients: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_fields(self) -> "LaunchAppointmentWorkflowCommand":
        self.job_id = self.job_id or self.lekab_job_template_id or self.job_name
        self.message = self.message or self.message_text or ""
        self.to_numbers = self.to_numbers or self.recipient_phone_numbers
        require_non_empty(self.job_name, "job_name")
        return self


class HandleProviderCallbackCommand(BaseModel):
    provider: str
    raw_payload: dict[str, Any]
    headers: dict[str, Any] = Field(default_factory=dict)
    received_at_utc: str
    remote_ip: Optional[str] = None


class CallbackPayload(BaseModel):
    event_id: str
    event_type: str
    correlation_id: str
    job_id: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class LekabDispatchCommand(LaunchAppointmentWorkflowCommand):
    pass


class StartJourneyCommand(BaseModel):
    journey_id: str
    correlation_id: str
    tenant_id: str
    customer_id: str
    channel: str = "RCS"
    service_type: str
    locale: str = "en"
    timezone: str
    preferences: "AppointmentPreference" = Field(default_factory=lambda: AppointmentPreference())
    resource_candidates: list[str] = Field(default_factory=list)
    duration_minutes: int = 30


class SelectSlotCommand(BaseModel):
    journey_id: str
    correlation_id: str
    tenant_id: str
    slot_id: str
    actor: str = "customer"


class ConfirmJourneyCommand(BaseModel):
    tenant_id: str
    correlation_id: str
    booking: CreateBookingCommand
    dispatch: LaunchAppointmentWorkflowCommand


class ReminderCommand(BaseModel):
    journey_id: str
    correlation_id: str
    tenant_id: str
    message: str
    to_numbers: list[str]


class CancelJourneyCommand(BaseModel):
    journey_id: str
    correlation_id: str
    tenant_id: str
    reason: str
    requested_by: str


from .models import AppointmentPreference  # noqa: E402
