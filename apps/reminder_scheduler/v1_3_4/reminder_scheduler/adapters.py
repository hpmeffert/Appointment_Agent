from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from pydantic import BaseModel, Field

from .time_utils import canonicalize_datetime, utcnow


class NormalizedAppointment(BaseModel):
    """Provider-neutral appointment shape for scheduler sync.

    The reminder core should not need to know whether an appointment came from
    Google, Microsoft, or a stub source. This model keeps only the fields that
    matter for sync, change detection, and reminder planning.
    """

    external_appointment_id: str
    title: str
    start_at: datetime
    end_at: datetime
    timezone: str = "Europe/Berlin"
    status: str = "scheduled"
    contact_ref: str | None = None
    email: str | None = None
    phone: str | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    def canonical(self) -> "NormalizedAppointment":
        return self.model_copy(
            update={
                "start_at": canonicalize_datetime(self.start_at, timezone_name=self.timezone, field_name="start_at"),
                "end_at": canonicalize_datetime(self.end_at, timezone_name=self.timezone, field_name="end_at"),
            }
        )


class CalendarAdapterProtocol(Protocol):
    adapter_name: str

    def fetch_upcoming_appointments(
        self,
        *,
        policy_key: str,
        preload_window_hours: int,
        now_utc: datetime | None = None,
    ) -> list[NormalizedAppointment]:
        ...


@dataclass
class StubCalendarAdapter:
    """Simple deterministic adapter used until real providers are injected."""

    adapter_name: str = "stub"
    seeded_appointments: list[NormalizedAppointment] | None = None

    def fetch_upcoming_appointments(
        self,
        *,
        policy_key: str,
        preload_window_hours: int,
        now_utc: datetime | None = None,
    ) -> list[NormalizedAppointment]:
        baseline = now_utc or utcnow()
        if self.seeded_appointments is not None:
            return [appointment.canonical() for appointment in self.seeded_appointments]

        return [
            NormalizedAppointment(
                external_appointment_id=f"{policy_key}-stub-1",
                title="Reminder Scheduler Sync Demo",
                start_at=baseline + timedelta(days=2, hours=3),
                end_at=baseline + timedelta(days=2, hours=3, minutes=30),
                timezone="Europe/Berlin",
                status="scheduled",
                contact_ref="customer-sync-1001",
                email="sync-demo@example.test",
                source_metadata={"provider": "stub", "policy_key": policy_key, "window_hours": preload_window_hours},
            ).canonical(),
            NormalizedAppointment(
                external_appointment_id=f"{policy_key}-stub-2",
                title="Reminder Scheduler Follow-up",
                start_at=baseline + timedelta(days=4, hours=1),
                end_at=baseline + timedelta(days=4, hours=1, minutes=45),
                timezone="Europe/Berlin",
                status="scheduled",
                contact_ref="customer-sync-1002",
                email="sync-demo-2@example.test",
                source_metadata={"provider": "stub", "policy_key": policy_key, "window_hours": preload_window_hours},
            ).canonical(),
        ]


def build_appointment_hash(appointment: NormalizedAppointment) -> str:
    """Build a stable fingerprint from the fields that affect reminders."""

    payload = {
        "external_appointment_id": appointment.external_appointment_id,
        "title": appointment.title,
        "start_at": appointment.start_at.isoformat(),
        "end_at": appointment.end_at.isoformat(),
        "timezone": appointment.timezone,
        "status": appointment.status,
        "contact_ref": appointment.contact_ref,
        "email": appointment.email,
        "phone": appointment.phone,
        "source_metadata": appointment.source_metadata,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
