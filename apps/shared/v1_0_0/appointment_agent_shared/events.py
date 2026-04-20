from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from .ids import new_id
from .validators import validate_iso_datetime


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    event_type: str
    payload_version: str = "v1.0.0"
    timestamp_utc: str = Field(default_factory=utc_now_iso)
    correlation_id: str
    causation_id: Optional[str] = None
    trace_id: str
    tenant_id: str
    journey_id: str = "system"
    source: str = "appointment-agent"
    idempotency_key: str = Field(default_factory=lambda: new_id("idem"))
    payload: Dict[str, Any]

    @field_validator("timestamp_utc")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        validate_iso_datetime(value, "timestamp_utc")
        return value


class CommandEnvelope(BaseModel):
    command_id: str = Field(default_factory=lambda: new_id("cmd"))
    command_type: str
    payload_version: str = "v1.0.0"
    timestamp_utc: str = Field(default_factory=utc_now_iso)
    correlation_id: str
    causation_id: Optional[str] = None
    trace_id: str
    tenant_id: str
    journey_id: str = "system"
    source: str = "appointment-agent"
    idempotency_key: str = Field(default_factory=lambda: new_id("idem"))
    payload: Dict[str, Any]

    @field_validator("timestamp_utc")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        validate_iso_datetime(value, "timestamp_utc")
        return value


class CommunicationReplyNormalized(BaseModel):
    message_id: str
    provider_message_id: Optional[str] = None
    trace_id: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    channel: str
    direction: str = "inbound"
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    status: str
    normalized_event_type: str
    reply_intent: Optional[str] = None
    reply_datetime_candidates: list[str] = Field(default_factory=list)
    action_candidate: dict[str, Any] = Field(default_factory=dict)
    interpretation_state: str = "review"
    interpretation_confidence: float = 0.0
    raw_text: str = ""
    provider_timestamp: Optional[str] = None


class AppointmentActionRequested(BaseModel):
    message_id: str
    trace_id: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    action_type: str
    interpretation_state: str = "review"
    interpretation_confidence: float = 0.0
    requires_review: bool = False
    reason: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReminderInteractionObserved(BaseModel):
    message_id: str
    trace_id: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    interaction_type: str
    channel: str
    status: str
    direction: str = "inbound"
    details: dict[str, Any] = Field(default_factory=dict)


class AddressRecordCreated(BaseModel):
    address_id: str
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    display_name: str


class AddressRecordUpdated(BaseModel):
    address_id: str
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    changed_fields: list[str] = Field(default_factory=list)


class AddressRecordDeactivated(BaseModel):
    address_id: str
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    reason: str = "manual_deactivate"


class AddressLinkedToAppointment(BaseModel):
    address_id: str
    appointment_external_id: str
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    booking_reference: Optional[str] = None
    calendar_ref: Optional[str] = None


class AddressAssignedToAppointment(BaseModel):
    """Bus-safe assignment event for the explicit operator link step.

    Phase 4 makes the address-to-appointment relationship a first-class demo
    action instead of an implicit side effect. This event lets other modules
    observe that the operator deliberately chose an address for one appointment.
    """

    address_id: str
    appointment_external_id: str
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    booking_reference: Optional[str] = None
    calendar_ref: Optional[str] = None
    assignment_source: str = "operator_assignment"


class AppointmentCreatedWithAddress(BaseModel):
    """Lightweight event for demo appointment creation with preserved address context."""

    appointment_external_id: str
    address_id: str
    correlation_ref: Optional[str] = None
    tenant_id: str = "default"
    booking_reference: Optional[str] = None
    calendar_ref: Optional[str] = None
    provider: Optional[str] = None


class AppointmentActionResolved(BaseModel):
    """Represents the resolved target and safety state of an interpreted reply."""

    message_id: str
    action_type: str
    trace_id: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    resolution_state: str = "review"
    interpretation_confidence: float = 0.0
    requires_review: bool = False
    target_summary: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None


class AppointmentActionExecutionRequested(BaseModel):
    """Emitted when a reply is safe enough to move into the next execution stage."""

    message_id: str
    action_type: str
    trace_id: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    target_summary: dict[str, Any] = Field(default_factory=dict)


class AppointmentActionReviewRequired(BaseModel):
    """Emitted when the system can interpret intent but should not auto-advance it."""

    message_id: str
    action_type: str
    trace_id: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    review_reason: str
    interpretation_confidence: float = 0.0
    parameters: dict[str, Any] = Field(default_factory=dict)
    target_summary: dict[str, Any] = Field(default_factory=dict)


class DemoScenarioRequested(BaseModel):
    scenario_id: str
    scenario_title: str
    mode: str
    input_text: str
    expected_action: str


class DemoScenarioStarted(BaseModel):
    scenario_id: str
    run_id: str
    mode: str
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None


class DemoScenarioContextPrepared(BaseModel):
    scenario_id: str
    mode: str
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    output_channel: Optional[str] = None
    status: str


class DemoScenarioStepUpdated(BaseModel):
    scenario_id: str
    run_id: str
    step_name: str
    detail: str
    payload: dict[str, Any] = Field(default_factory=dict)


class DemoScenarioFailed(BaseModel):
    scenario_id: str
    run_id: str
    mode: str
    error_code: str
    error_message: str
    artifact_directory: str


class DemoScenarioCompleted(BaseModel):
    scenario_id: str
    run_id: str
    mode: str
    success: bool = True
    action_type: str
    interpretation_state: str
    artifact_directory: str


class DemoProtocolWritten(BaseModel):
    scenario_id: str
    run_id: str
    protocol_markdown_path: str
    protocol_json_path: str
    demo_log_path: str
    summary_path: str


class DemoArtifactWritten(BaseModel):
    scenario_id: str
    run_id: str
    artifact_kind: str
    artifact_path: str


class AddressAssignedToGeneratedAppointment(BaseModel):
    address_id: str
    appointment_external_id: str
    correlation_ref: Optional[str] = None
    calendar_ref: Optional[str] = None
    booking_reference: Optional[str] = None
