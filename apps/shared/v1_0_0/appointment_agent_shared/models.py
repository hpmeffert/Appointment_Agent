from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, DateTime, Integer, String
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
