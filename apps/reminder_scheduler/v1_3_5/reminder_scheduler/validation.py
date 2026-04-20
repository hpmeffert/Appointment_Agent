from __future__ import annotations

from datetime import datetime
from typing import Any

from .calculator import ReminderMode, resolve_reminder_hours
from .time_utils import canonicalize_datetime


def validate_policy(policy: Any) -> list[str]:
    """Validate the policy structure and emit operator-friendly warnings."""

    warnings: list[str] = []
    reminder_count = getattr(policy, "reminder_count", 0)
    if reminder_count > 3:
        raise ValueError("Reminder count cannot be larger than 3.")

    reminder_hours = resolve_reminder_hours(policy)
    if reminder_count != len(reminder_hours):
        raise ValueError("Reminder count does not match the configured reminder hours.")

    if getattr(policy, "mode", ReminderMode.MANUAL) == ReminderMode.MANUAL and reminder_count > 0:
        required_values = [getattr(policy, "first_reminder_hours_before", None)]
        if reminder_count >= 2:
            required_values.append(getattr(policy, "second_reminder_hours_before", None))
        if reminder_count >= 3:
            required_values.append(getattr(policy, "third_reminder_hours_before", None))
        if any(value is None for value in required_values):
            raise ValueError(
                "Manual reminder mode requires explicit reminder hour values for each configured reminder."
            )

    preload_window_hours = getattr(policy, "preload_window_hours", 0)
    if preload_window_hours < 1:
        raise ValueError("Preload window must be at least 1 hour.")

    if getattr(policy, "channel_email_enabled", False) and getattr(policy, "channel_voice_enabled", False) and getattr(
        policy, "channel_rcs_sms_enabled", False
    ):
        warnings.append("All reminder channels are enabled. Channel assignment will follow priority order.")
    if not any(
        [
            getattr(policy, "channel_email_enabled", False),
            getattr(policy, "channel_voice_enabled", False),
            getattr(policy, "channel_rcs_sms_enabled", False),
        ]
    ):
        warnings.append("No reminder channel is enabled. Email will be used as a safe fallback for previews.")
    return warnings


def normalize_appointment(appointment: Any) -> Any:
    """Return a reminder appointment with canonical UTC timestamps.

    Reminder planning and worker dispatch both compare UTC timestamps. This
    normalization step ensures all later code sees a single time representation
    even when the original request used a local timezone or a naive datetime.
    """

    timezone_name = getattr(appointment, "timezone", None)
    start_time = canonicalize_datetime(
        getattr(appointment, "start_time"),
        timezone_name=timezone_name,
        field_name=f"{getattr(appointment, 'appointment_external_id', 'appointment')}.start_time",
    )
    end_time = canonicalize_datetime(
        getattr(appointment, "end_time"),
        timezone_name=timezone_name,
        field_name=f"{getattr(appointment, 'appointment_external_id', 'appointment')}.end_time",
    )
    if end_time <= start_time:
        raise ValueError("Appointment end time must be after start time.")

    metadata = dict(getattr(appointment, "metadata", {}) or {})
    metadata.setdefault("timezone_strategy", "canonical_utc")
    metadata.setdefault("normalized_timezone", "UTC")

    return appointment.model_copy(
        update={
            "start_time": start_time,
            "end_time": end_time,
            "metadata": metadata,
        }
    )


def normalize_appointments(appointments: list[Any]) -> list[Any]:
    """Normalize a list of appointments in a single, well-defined place."""

    return [normalize_appointment(appointment) for appointment in appointments]

