from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from .time_utils import canonicalize_datetime, utcnow


@dataclass
class NormalizedAppointmentSnapshot:
    external_appointment_id: str
    start_at_utc: datetime
    end_at_utc: datetime
    timezone: str
    status: str
    raw_payload_json: dict[str, Any]
    payload_hash: str


class CalendarAdapterProtocol(Protocol):
    adapter_name: str

    def fetch_upcoming_appointments(
        self,
        *,
        policy_key: str,
        preload_window_hours: int,
        now_utc: datetime | None = None,
    ) -> list[dict[str, Any]]:
        ...


@dataclass
class StubCalendarAdapter:
    """Deterministic provider-neutral adapter foundation for v1.3.4."""

    adapter_name: str = "stub"

    def fetch_upcoming_appointments(
        self,
        *,
        policy_key: str,
        preload_window_hours: int,
        now_utc: datetime | None = None,
    ) -> list[dict[str, Any]]:
        baseline = now_utc or utcnow()
        return [
            {
                "external_appointment_id": f"{policy_key}-stub-1",
                "title": "Reminder Scheduler Sync Demo",
                "start_time": baseline + timedelta(days=2, hours=3),
                "end_time": baseline + timedelta(days=2, hours=3, minutes=30),
                "timezone": "Europe/Berlin",
                "status": "scheduled",
                "customer_id": "customer-sync-1001",
                "email": "sync-demo@example.test",
                "phone": None,
                "metadata": {"provider": self.adapter_name, "policy_key": policy_key, "window_hours": preload_window_hours},
            },
            {
                "external_appointment_id": f"{policy_key}-stub-2",
                "title": "Reminder Scheduler Follow-up",
                "start_time": baseline + timedelta(days=4, hours=1),
                "end_time": baseline + timedelta(days=4, hours=1, minutes=45),
                "timezone": "Europe/Berlin",
                "status": "scheduled",
                "customer_id": "customer-sync-1002",
                "email": "sync-demo-2@example.test",
                "phone": None,
                "metadata": {"provider": self.adapter_name, "policy_key": policy_key, "window_hours": preload_window_hours},
            },
        ]


def normalize_appointment_snapshot(appointment: Any, *, policy_key: str) -> NormalizedAppointmentSnapshot:
    start_at_utc = canonicalize_datetime(
        getattr(appointment, "start_time"),
        timezone_name=getattr(appointment, "timezone", "Europe/Berlin"),
        field_name=f"{getattr(appointment, 'appointment_external_id', 'appointment')}.start_time",
    )
    end_at_utc = canonicalize_datetime(
        getattr(appointment, "end_time"),
        timezone_name=getattr(appointment, "timezone", "Europe/Berlin"),
        field_name=f"{getattr(appointment, 'appointment_external_id', 'appointment')}.end_time",
    )
    raw_payload = {
        "policy_key": policy_key,
        "title": getattr(appointment, "title", ""),
        "timezone": getattr(appointment, "timezone", "Europe/Berlin"),
        "status": getattr(appointment, "status", "scheduled"),
        "customer_id": getattr(appointment, "customer_id", None),
        "email": getattr(appointment, "email", None),
        "phone": getattr(appointment, "phone", None),
        "metadata": getattr(appointment, "metadata", {}) or {},
        "start_at_utc": start_at_utc.isoformat(),
        "end_at_utc": end_at_utc.isoformat(),
    }
    payload_hash = hashlib.sha256(
        json.dumps(raw_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return NormalizedAppointmentSnapshot(
        external_appointment_id=getattr(appointment, "appointment_external_id"),
        start_at_utc=start_at_utc,
        end_at_utc=end_at_utc,
        timezone=getattr(appointment, "timezone", "Europe/Berlin"),
        status=getattr(appointment, "status", "scheduled"),
        raw_payload_json=raw_payload,
        payload_hash=payload_hash,
    )
