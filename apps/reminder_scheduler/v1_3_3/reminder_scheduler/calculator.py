from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .time_utils import utcnow


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


@dataclass
class CalculatedReminderItem:
    """A pure calculation result for one reminder slot.

    The calculator is intentionally free of database concerns. It only decides
    whether a reminder should be planned or skipped and at which canonical UTC
    instant it would fire. The service layer converts these items into API
    models and persistence records.
    """

    appointment_external_id: str
    reminder_sequence: int
    channel: str
    reminder_hours_before: int
    scheduled_for: datetime
    appointment_start_at: datetime
    appointment_timezone: str
    target_ref: str | None
    status: str
    skip_reason_code: str | None = None


@dataclass
class ReminderCalculationResult:
    items: list[CalculatedReminderItem]
    planned_count: int
    skipped_count: int
    reference_now_utc: datetime
    reminder_hours: list[int]
    channels: list[str]


def enabled_channels(policy: Any) -> list[str]:
    channels: list[str] = []
    if getattr(policy, "channel_email_enabled", False):
        channels.append(ReminderChannel.EMAIL.value)
    if getattr(policy, "channel_rcs_sms_enabled", False):
        channels.append(ReminderChannel.RCS_SMS.value)
    if getattr(policy, "channel_voice_enabled", False):
        channels.append(ReminderChannel.VOICE.value)
    if not channels:
        # Demos stay useful even if no explicit channel is enabled yet.
        channels.append(ReminderChannel.EMAIL.value)
    return channels


def resolve_reminder_hours(policy: Any) -> list[int]:
    """Resolve the reminder offsets once and reuse them everywhere.

    Centralizing the reminder-hour logic means the service, worker, and tests
    all observe the same schedule shape. That is especially important when
    policy mode switches between manually configured offsets and auto-
    distributed reminders.
    """

    reminder_count = getattr(policy, "reminder_count", 0)
    if reminder_count == 0:
        return []

    mode = getattr(policy, "mode", ReminderMode.MANUAL)
    if isinstance(mode, str):
        mode = ReminderMode(mode)

    if mode == ReminderMode.AUTO_DISTRIBUTED:
        last_gap = getattr(policy, "last_reminder_gap_before_appointment_hours", 0) or 0
        if reminder_count == 1:
            values = [last_gap]
        else:
            span = getattr(policy, "max_span_between_first_and_last_reminder_hours", 0)
            step = span / max(reminder_count - 1, 1)
            values = [
                int(round(last_gap + (step * (reminder_count - 1 - index))))
                for index in range(reminder_count)
            ]
    else:
        values = [getattr(policy, "first_reminder_hours_before", 0) or 0]
        if reminder_count >= 2:
            values.append(getattr(policy, "second_reminder_hours_before", 0) or 0)
        if reminder_count >= 3:
            values.append(getattr(policy, "third_reminder_hours_before", 0) or 0)

    if len(values) != len(set(values)):
        raise ValueError("Reminder hour values must be unique.")
    if values != sorted(values, reverse=True):
        raise ValueError("Reminder hour values must be sorted from earliest to latest notification.")

    max_span = getattr(policy, "max_span_between_first_and_last_reminder_hours", 0)
    enforce_max_span = getattr(policy, "enforce_max_span", True)
    if enforce_max_span and values:
        span = values[0] - values[-1]
        if span > max_span:
            raise ValueError("Reminder span exceeds the configured maximum span.")

    return values


def calculate_schedule(
    policy: Any,
    appointments: list[Any],
    *,
    now_utc: datetime | None = None,
) -> ReminderCalculationResult:
    """Build reminder candidates from canonical UTC appointments.

    The service layer is responsible for validation and normalization. This
    calculator then performs the pure business rule evaluation exactly once so
    preview and worker planning stay aligned.
    """

    reference_now_utc = now_utc or utcnow()
    reminder_hours = resolve_reminder_hours(policy)
    channels = enabled_channels(policy)
    items: list[CalculatedReminderItem] = []
    planned_count = 0
    skipped_count = 0

    for appointment in appointments:
        for index, reminder_hours_before in enumerate(reminder_hours, start=1):
            channel = channels[min(index - 1, len(channels) - 1)]
            scheduled_for = appointment.start_time - timedelta(hours=reminder_hours_before)
            is_past = scheduled_for <= reference_now_utc
            status = ReminderStatus.SKIPPED.value if is_past else ReminderStatus.PLANNED.value
            skip_reason_code = "past_reminder" if is_past else None
            if is_past:
                skipped_count += 1
            else:
                planned_count += 1
            items.append(
                CalculatedReminderItem(
                    appointment_external_id=appointment.appointment_external_id,
                    reminder_sequence=index,
                    channel=channel,
                    reminder_hours_before=reminder_hours_before,
                    scheduled_for=scheduled_for,
                    appointment_start_at=appointment.start_time,
                    appointment_timezone=getattr(appointment, "timezone", "UTC"),
                    target_ref=getattr(appointment, "email", None) or getattr(appointment, "phone", None),
                    status=status,
                    skip_reason_code=skip_reason_code,
                )
            )

    return ReminderCalculationResult(
        items=items,
        planned_count=planned_count,
        skipped_count=skipped_count,
        reference_now_utc=reference_now_utc,
        reminder_hours=reminder_hours,
        channels=channels,
    )
