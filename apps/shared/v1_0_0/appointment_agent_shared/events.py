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
