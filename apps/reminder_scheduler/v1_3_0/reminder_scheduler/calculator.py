from __future__ import annotations

from datetime import datetime, timedelta

from .schemas import ReminderPolicySchema, ReminderPreviewRequest, ReminderPreviewResponse, ReminderScheduleItem
from .validation import _enabled_channels, _ensure_timezone_aware_utc, _reminder_hours, validate_preview_request


def _select_channel_for_sequence(channels: list[str], reminder_sequence: int) -> str:
    # The scheduler keeps the channel strategy predictable: once the available
    # list is exhausted, the last channel remains active instead of wrapping
    # around. This mirrors the existing reminder service behavior and keeps the
    # preview stable for operators.
    return channels[min(reminder_sequence - 1, len(channels) - 1)]


def calculate_reminder_hours(policy: ReminderPolicySchema) -> list[int]:
    """Return the configured reminder offsets in hours before the appointment."""

    return _reminder_hours(policy)


def calculate_schedule_items(
    policy: ReminderPolicySchema,
    appointment_start_utc: datetime,
    *,
    appointment_id: str = "appointment",
) -> list[ReminderScheduleItem]:
    """Build the reminder timeline for one appointment.

    This function stays pure: it does not touch the database, worker state or
    any UI layer. That makes it safe to call from tests and preview endpoints.
    """

    appointment_start_utc = _ensure_timezone_aware_utc(appointment_start_utc, "appointment_start_utc")
    hours_before = calculate_reminder_hours(policy)
    channels = _enabled_channels(policy)

    items: list[ReminderScheduleItem] = []
    for reminder_sequence, reminder_hours_before in enumerate(hours_before, start=1):
        scheduled_for_utc = appointment_start_utc - timedelta(hours=reminder_hours_before)
        items.append(
            ReminderScheduleItem(
                reminder_sequence=reminder_sequence,
                hours_before_appointment=reminder_hours_before,
                scheduled_for_utc=scheduled_for_utc,
                channel=_select_channel_for_sequence(channels, reminder_sequence),
                status="planned",
                reminder_label=f"Reminder {reminder_sequence} for {appointment_id}",
            )
        )
    return items


def calculate_preview(request: ReminderPreviewRequest) -> ReminderPreviewResponse:
    """Return a complete preview response for the reminder scheduler UI."""

    warnings = validate_preview_request(request)
    items = calculate_schedule_items(
        request.policy,
        request.appointment_start_utc,
        appointment_id=request.appointment_id,
    )
    return ReminderPreviewResponse(
        tenant_id=request.tenant_id,
        appointment_id=request.appointment_id,
        appointment_start_utc=_ensure_timezone_aware_utc(request.appointment_start_utc, "appointment_start_utc"),
        policy=request.policy,
        items=items,
        warnings=warnings,
    )
