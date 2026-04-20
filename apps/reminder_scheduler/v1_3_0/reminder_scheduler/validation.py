from __future__ import annotations

from datetime import datetime, timezone

from appointment_agent_shared.validators import require_non_empty

from .schemas import ReminderPolicySchema, ReminderPreviewRequest


def _ensure_timezone_aware_utc(moment: datetime, field_name: str) -> datetime:
    """Normalize a timestamp to UTC and fail fast on naive datetimes.

    The reminder scheduler stores and compares times in UTC. Accepting naive
    datetimes here would make the resulting job timestamps ambiguous, so we
    reject them instead of guessing a timezone.
    """

    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware UTC datetime")
    return moment.astimezone(timezone.utc)


def _enabled_channels(policy: ReminderPolicySchema) -> list[str]:
    channels: list[str] = []
    if policy.channel_email_enabled:
        channels.append("email")
    if policy.channel_rcs_sms_enabled:
        channels.append("rcs_sms")
    if policy.channel_voice_enabled:
        channels.append("voice")
    if not channels:
        # The UI can still preview jobs even if no channel is enabled yet, so
        # we fall back to email rather than breaking the configuration flow.
        channels.append("email")
    return channels


def _manual_hours(policy: ReminderPolicySchema) -> list[int]:
    hours: list[int] = []
    if policy.reminder_count <= 0:
        return hours

    required_hours = [
        policy.first_reminder_hours_before,
        policy.second_reminder_hours_before,
        policy.third_reminder_hours_before,
    ][: policy.reminder_count]

    if any(value is None for value in required_hours):
        raise ValueError(
            "Manual reminder mode requires explicit reminder hour values for each configured reminder."
        )

    hours = [int(value) for value in required_hours if value is not None]
    return hours


def _auto_distributed_hours(policy: ReminderPolicySchema) -> list[int]:
    hours: list[int] = []
    if policy.reminder_count <= 0:
        return hours

    # The last reminder always anchors to the configured minimum gap before the
    # appointment. Additional reminders are distributed evenly between that gap
    # and the configured maximum span.
    gap = policy.last_reminder_gap_before_appointment_hours
    if policy.reminder_count == 1:
        return [gap]

    span = policy.max_span_between_first_and_last_reminder_hours
    if span < policy.reminder_count - 1:
        raise ValueError(
            "Auto distributed reminder mode needs a larger span to keep reminder times unique."
        )

    step = span / max(policy.reminder_count - 1, 1)
    hours = [
        int(round(gap + (step * (policy.reminder_count - 1 - index))))
        for index in range(policy.reminder_count)
    ]
    return hours


def _reminder_hours(policy: ReminderPolicySchema) -> list[int]:
    if policy.mode == "auto_distributed":
        hours = _auto_distributed_hours(policy)
    else:
        hours = _manual_hours(policy)

    if len(hours) != len(set(hours)):
        raise ValueError("Reminder hour values must be unique.")
    if hours != sorted(hours, reverse=True):
        raise ValueError("Reminder hour values must be sorted from earliest to latest notification.")
    if policy.reminder_count != len(hours):
        raise ValueError("Reminder count does not match the configured reminder hours.")
    return hours


def validate_policy(policy: ReminderPolicySchema) -> list[str]:
    """Validate the reminder policy and return non-fatal warnings.

    Hard failures are raised as ValueError so the caller can surface a clear
    configuration error back to the user or the API layer.
    """

    warnings: list[str] = []

    require_non_empty(policy.tenant_id, "tenant_id")
    require_non_empty(policy.policy_name, "policy_name")

    if policy.reminder_count < 0 or policy.reminder_count > 3:
        raise ValueError("Reminder count must be between 0 and 3.")
    if policy.preload_window_hours < 1:
        raise ValueError("Preload window must be at least 1 hour.")

    hours = _reminder_hours(policy)
    if policy.enabled is False and hours:
        warnings.append("Policy is disabled; reminder jobs will not be planned.")

    if policy.reminder_count > 0 and hours:
        closest_reminder = hours[-1]
        if closest_reminder < policy.last_reminder_gap_before_appointment_hours:
            raise ValueError("The closest reminder is inside the configured last reminder gap.")
        reminder_span = hours[0] - hours[-1]
        if policy.enforce_max_span and reminder_span > policy.max_span_between_first_and_last_reminder_hours:
            raise ValueError("Reminder span exceeds the configured maximum span.")

    if policy.channel_email_enabled and policy.channel_voice_enabled and policy.channel_rcs_sms_enabled:
        warnings.append("All reminder channels are enabled. Channel assignment will follow a fixed priority order.")

    if not any([policy.channel_email_enabled, policy.channel_voice_enabled, policy.channel_rcs_sms_enabled]):
        warnings.append("No reminder channel is enabled. Email will be used as a safe fallback for previews.")

    return warnings


def validate_preview_request(request: ReminderPreviewRequest) -> list[str]:
    """Validate a preview request before the calculator builds schedule items."""

    require_non_empty(request.tenant_id, "tenant_id")
    require_non_empty(request.appointment_id, "appointment_id")
    _ensure_timezone_aware_utc(request.appointment_start_utc, "appointment_start_utc")
    return validate_policy(request.policy)
