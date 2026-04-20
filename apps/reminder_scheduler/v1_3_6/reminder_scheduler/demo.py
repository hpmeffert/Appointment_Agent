from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import asdict
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from google_adapter.v1_3_6.google_adapter.demo import (
    GoogleLinkageAppointmentSourceView,
    GoogleStoryScenario,
    NormalizedAppointmentView,
    build_google_linkage_demo_payload,
)

from . import calculator, validation
from .service import ReminderAppointmentInput, ReminderPolicyInput
from .time_utils import canonicalize_datetime


DEMO_REFERENCE_NOW_UTC = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)


class ReminderJobPreviewView(BaseModel):
    job_id: str
    appointment_external_id: str
    reminder_sequence: int
    channel: str
    reminder_hours_before: int
    scheduled_for_utc: datetime
    status: str
    target_ref: Optional[str] = None
    skip_reason_code: Optional[str] = None


class ReminderLinkageDemoPayload(BaseModel):
    version: str = "v1.3.6"
    appointment_source: GoogleLinkageAppointmentSourceView
    normalized_appointment: NormalizedAppointmentView
    reminder_policy: ReminderPolicyInput
    reminder_validation: list[str] = Field(default_factory=list)
    reminder_preview: list[dict[str, Any]] = Field(default_factory=list)
    reminder_jobs: list[ReminderJobPreviewView] = Field(default_factory=list)
    reminder_relevant_fields: dict[str, Any] = Field(default_factory=dict)
    stories: list[GoogleStoryScenario] = Field(default_factory=list)
    summary: list[str] = Field(default_factory=list)


def _build_policy(appointment_type: str) -> ReminderPolicyInput:
    channel_rcs_sms_enabled = appointment_type in {"dentist", "gas_meter"}
    channel_voice_enabled = appointment_type in {"wallbox", "water_meter"}
    return ReminderPolicyInput(
        tenant_id="demo-tenant",
        policy_key="google-linkage-demo",
        enabled=True,
        mode="manual",
        reminder_count=2,
        first_reminder_hours_before=24,
        second_reminder_hours_before=2,
        preload_window_hours=168,
        channel_email_enabled=True,
        channel_voice_enabled=channel_voice_enabled,
        channel_rcs_sms_enabled=channel_rcs_sms_enabled,
    )


def _to_reminder_appointment(normalized: NormalizedAppointmentView) -> ReminderAppointmentInput:
    return ReminderAppointmentInput(
        appointment_external_id=normalized.normalized_appointment_id,
        title=normalized.title,
        start_time=canonicalize_datetime(
            normalized.start_at_utc,
            timezone_name=normalized.timezone,
            field_name=f"{normalized.normalized_appointment_id}.start_time",
        ),
        end_time=canonicalize_datetime(
            normalized.end_at_utc,
            timezone_name=normalized.timezone,
            field_name=f"{normalized.normalized_appointment_id}.end_time",
        ),
        timezone=normalized.timezone,
        tenant_id="demo-tenant",
        customer_id=normalized.source_external_id,
        email=f"{normalized.appointment_type}@example.test",
        phone="+49 170 555 9999",
        address_id=normalized.address_id,
        correlation_ref=normalized.correlation_ref,
        status=normalized.status,
        metadata={
            "booking_reference": normalized.booking_reference,
            "source_ref": normalized.source_ref,
            "source_external_id": normalized.source_external_id,
            "reminder_relevant_fields": normalized.reminder_relevant_fields,
        },
    )


def build_reminder_linkage_demo_payload(appointment_type: str = "dentist") -> ReminderLinkageDemoPayload:
    google_payload = build_google_linkage_demo_payload(appointment_type)
    normalized = google_payload.normalized_appointment
    policy = _build_policy(appointment_type)
    reminder_validation = validation.validate_policy(policy)
    reminder_appointment = _to_reminder_appointment(normalized)
    calculated = calculator.calculate_schedule(policy, [reminder_appointment], now_utc=DEMO_REFERENCE_NOW_UTC)

    reminder_preview = [asdict(item) for item in calculated.items]
    reminder_jobs = [
        ReminderJobPreviewView(
            job_id=f"reminder-demo-{item.appointment_external_id}-{item.reminder_sequence}-{item.channel}",
            appointment_external_id=item.appointment_external_id,
            reminder_sequence=item.reminder_sequence,
            channel=item.channel,
            reminder_hours_before=item.reminder_hours_before,
            scheduled_for_utc=item.scheduled_for,
            status=item.status,
            target_ref=item.target_ref,
            skip_reason_code=item.skip_reason_code,
        )
        for item in calculated.items
    ]
    reminder_relevant_fields = {
        **normalized.reminder_relevant_fields,
        "reminder_mode": policy.mode.value,
        "reminder_count": policy.reminder_count,
        "reminder_channels": [
            channel
            for channel, enabled in (
                ("email", policy.channel_email_enabled),
                ("voice", policy.channel_voice_enabled),
                ("rcs_sms", policy.channel_rcs_sms_enabled),
            )
            if enabled
        ],
        "calculated_reminder_hours": calculated.reminder_hours,
        "planned_preview_count": calculated.planned_count,
        "skipped_preview_count": calculated.skipped_count,
        "first_preview_fire_utc": reminder_preview[0]["scheduled_for"].isoformat() if reminder_preview else None,
    }
    stories = [
        GoogleStoryScenario(
            story_key="new_appointment",
            title="A Google-linked appointment becomes reminder-ready",
            summary="The reminder helper can plan reminder jobs from the normalized appointment without provider-specific fields.",
            source_state="linked",
            normalized_state="scheduled",
            reminder_state="planned",
            changes={
                "appointment_external_id": reminder_appointment.appointment_external_id,
                "reminder_count": policy.reminder_count,
                "reminder_channels": reminder_relevant_fields["reminder_channels"],
            },
            visible_fields=["appointment_source", "normalized_appointment", "reminder_policy", "reminder_preview"],
        ),
        GoogleStoryScenario(
            story_key="reschedule",
            title="A reschedule moves the reminder preview",
            summary="When the appointment time changes, the reminder helper recalculates the planned fire time.",
            source_state="rescheduled",
            normalized_state="scheduled",
            reminder_state="replanned",
            changes={
                "start_at_utc_before": normalized.start_at_utc,
                "start_at_utc_after": normalized.start_at_utc + timedelta(days=1),
                "first_preview_fire_utc_after": normalized.start_at_utc + timedelta(days=1) - timedelta(hours=policy.first_reminder_hours_before or 0),
            },
            visible_fields=["start_at_utc", "reminder_preview", "reminder_jobs"],
        ),
        GoogleStoryScenario(
            story_key="cancel",
            title="A cancellation cancels the reminder path",
            summary="If the source appointment is cancelled, the reminder view can mark the corresponding jobs as cancelled.",
            source_state="cancelled",
            normalized_state="cancelled",
            reminder_state="cancelled",
            changes={
                "source_status_after": "cancelled",
                "normalized_status_after": "cancelled",
                "reminder_jobs_cancelled": True,
            },
            visible_fields=["source_status", "normalized_state", "reminder_preview", "reminder_jobs"],
        ),
    ]
    return ReminderLinkageDemoPayload(
        appointment_source=google_payload.appointment_source,
        normalized_appointment=normalized,
        reminder_policy=policy,
        reminder_validation=reminder_validation,
        reminder_preview=reminder_preview,
        reminder_jobs=reminder_jobs,
        reminder_relevant_fields=reminder_relevant_fields,
        stories=stories,
        summary=[
            "This view keeps the reminder story provider-neutral.",
            "The same normalized appointment feeds preview, planning, and cancel/reschedule explanations.",
            "Reminder-relevant fields stay visible for operators and demos.",
        ],
    )
