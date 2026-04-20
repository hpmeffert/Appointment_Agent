from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


DEMO_REFERENCE_NOW_UTC = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)

APPOINTMENT_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "dentist": {
        "title": "Dentist check-up",
        "appointment_type": "dentist",
        "customer_name": "Anna Becker",
        "customer_contact": "+49 170 555 0101",
        "location": "Dental practice",
        "source_ref": "google-linked-dentist-calendar",
        "source_name": "Google Dentist Demo Calendar",
        "source_external_id": "google-event-dentist-001",
        "booking_reference": "booking-gdemo-dentist-001",
        "start_at_utc": DEMO_REFERENCE_NOW_UTC + timedelta(days=3, hours=2),
        "duration_minutes": 30,
        "reminder_offsets_hours": [24, 2],
        "channel_priority": ["email", "rcs_sms"],
    },
    "wallbox": {
        "title": "Wallbox technical inspection",
        "appointment_type": "wallbox",
        "customer_name": "Markus Weber",
        "customer_contact": "+49 170 555 0202",
        "location": "Customer home",
        "source_ref": "google-linked-wallbox-calendar",
        "source_name": "Google Wallbox Demo Calendar",
        "source_external_id": "google-event-wallbox-001",
        "booking_reference": "booking-gdemo-wallbox-001",
        "start_at_utc": DEMO_REFERENCE_NOW_UTC + timedelta(days=4, hours=1),
        "duration_minutes": 45,
        "reminder_offsets_hours": [24, 4],
        "channel_priority": ["email", "voice"],
    },
    "gas_meter": {
        "title": "Gas meter inspection",
        "appointment_type": "gas_meter",
        "customer_name": "Petra Hoffmann",
        "customer_contact": "+49 170 555 0303",
        "location": "Building entrance",
        "source_ref": "google-linked-gas-calendar",
        "source_name": "Google Gas Meter Demo Calendar",
        "source_external_id": "google-event-gas-001",
        "booking_reference": "booking-gdemo-gas-001",
        "start_at_utc": DEMO_REFERENCE_NOW_UTC + timedelta(days=5, hours=3),
        "duration_minutes": 30,
        "reminder_offsets_hours": [48, 6],
        "channel_priority": ["email", "rcs_sms"],
    },
    "water_meter": {
        "title": "Water meter reading",
        "appointment_type": "water_meter",
        "customer_name": "Sabine Klein",
        "customer_contact": "+49 170 555 0404",
        "location": "Utility room",
        "source_ref": "google-linked-water-calendar",
        "source_name": "Google Water Meter Demo Calendar",
        "source_external_id": "google-event-water-001",
        "booking_reference": "booking-gdemo-water-001",
        "start_at_utc": DEMO_REFERENCE_NOW_UTC + timedelta(days=6, hours=1),
        "duration_minutes": 30,
        "reminder_offsets_hours": [48, 6],
        "channel_priority": ["email", "voice"],
    },
}


class GoogleLinkageAppointmentSourceView(BaseModel):
    provider: Literal["google"] = "google"
    source_type: Literal["google_linked_calendar"] = "google_linked_calendar"
    source_ref: str
    source_name: str
    source_external_id: str
    source_status: str
    sync_status: str
    last_sync_at_utc: datetime


class NormalizedAppointmentView(BaseModel):
    source_ref: str
    source_external_id: str
    normalized_appointment_id: str
    address_id: Optional[str] = None
    correlation_ref: Optional[str] = None
    appointment_type: str
    title: str
    customer_name: str
    customer_contact: str
    location: str
    start_at_utc: datetime
    end_at_utc: datetime
    timezone: str = "UTC"
    status: str = "scheduled"
    google_event_id: str
    booking_reference: str
    reminder_policy_key: str
    reminder_relevant_fields: dict[str, Any] = Field(default_factory=dict)


class GoogleStoryScenario(BaseModel):
    story_key: str
    title: str
    summary: str
    source_state: str
    normalized_state: str
    reminder_state: str
    changes: dict[str, Any] = Field(default_factory=dict)
    visible_fields: list[str] = Field(default_factory=list)


class GoogleLinkageDemoPayload(BaseModel):
    version: str = "v1.3.6"
    generated_at_utc: datetime
    appointment_source: GoogleLinkageAppointmentSourceView
    normalized_appointment: NormalizedAppointmentView
    stories: list[GoogleStoryScenario] = Field(default_factory=list)
    reminder_relevant_fields: dict[str, Any] = Field(default_factory=dict)
    operator_summary: list[str] = Field(default_factory=list)


def _blueprint(appointment_type: str) -> dict[str, Any]:
    return APPOINTMENT_BLUEPRINTS.get(appointment_type, APPOINTMENT_BLUEPRINTS["dentist"])


def _build_normalized_view(
    blueprint: dict[str, Any],
    selected_address: Optional[dict[str, Any]] = None,
) -> NormalizedAppointmentView:
    start_at_utc = blueprint["start_at_utc"]
    end_at_utc = start_at_utc + timedelta(minutes=blueprint["duration_minutes"])
    selected_address = dict(selected_address or {})
    location_text = ", ".join(
        part
        for part in [
            selected_address.get("street"),
            selected_address.get("house_number"),
            selected_address.get("postal_code"),
            selected_address.get("city"),
        ]
        if part
    )
    return NormalizedAppointmentView(
        source_ref=blueprint["source_ref"],
        source_external_id=blueprint["source_external_id"],
        normalized_appointment_id=f"normalized-{blueprint['appointment_type']}-001",
        address_id=selected_address.get("address_id") or "addr-demo-001",
        correlation_ref=selected_address.get("correlation_ref") or "corr-addr-demo-001",
        appointment_type=blueprint["appointment_type"],
        title=blueprint["title"],
        customer_name=selected_address.get("display_name") or blueprint["customer_name"],
        customer_contact=selected_address.get("phone") or blueprint["customer_contact"],
        location=location_text or blueprint["location"],
        start_at_utc=start_at_utc,
        end_at_utc=end_at_utc,
        timezone="UTC",
        status="scheduled",
        google_event_id=blueprint["source_external_id"],
        booking_reference=blueprint["booking_reference"],
        reminder_policy_key="google-linkage-demo",
        reminder_relevant_fields={
            "policy_key": "google-linkage-demo",
            "reminder_count": len(blueprint["reminder_offsets_hours"]),
            "channel_priority": blueprint["channel_priority"],
            "reminder_offsets_hours": blueprint["reminder_offsets_hours"],
            "next_reminder_at_utc": start_at_utc - timedelta(hours=blueprint["reminder_offsets_hours"][0]),
            "cancel_behavior": "cancelled appointments cancel reminder jobs",
            "reschedule_behavior": "rescheduled appointments rebuild reminder jobs",
            "selected_address_id": selected_address.get("address_id") or "",
        },
    )


def build_google_linkage_demo_payload(
    appointment_type: str = "dentist",
    *,
    selected_address: Optional[dict[str, Any]] = None,
) -> GoogleLinkageDemoPayload:
    blueprint = _blueprint(appointment_type)
    normalized = _build_normalized_view(blueprint, selected_address=selected_address)
    source = GoogleLinkageAppointmentSourceView(
        source_ref=blueprint["source_ref"],
        source_name=blueprint["source_name"],
        source_external_id=blueprint["source_external_id"],
        source_status="linked",
        sync_status="synced",
        last_sync_at_utc=DEMO_REFERENCE_NOW_UTC - timedelta(hours=6),
    )
    stories = [
        GoogleStoryScenario(
            story_key="new_appointment",
            title="Google-linked source becomes a normalized appointment",
            summary="The linked Google appointment is turned into a provider-neutral appointment view.",
            source_state="linked",
            normalized_state="scheduled",
            reminder_state="planned",
            changes={
                "google_event_id": normalized.google_event_id,
                "booking_reference": normalized.booking_reference,
                "reminder_offsets_hours": normalized.reminder_relevant_fields["reminder_offsets_hours"],
            },
            visible_fields=["source_ref", "source_external_id", "normalized_appointment_id", "booking_reference", "reminder_relevant_fields"],
        ),
        GoogleStoryScenario(
            story_key="reschedule",
            title="A reschedule keeps the booking identity but moves the appointment",
            summary="The Google event changes time, the booking reference stays stable, and reminder times are rebuilt.",
            source_state="rescheduled",
            normalized_state="scheduled",
            reminder_state="replanned",
            changes={
                "google_event_id_before": normalized.google_event_id,
                "google_event_id_after": f"{normalized.google_event_id}-rescheduled",
                "start_at_utc_before": normalized.start_at_utc,
                "start_at_utc_after": normalized.start_at_utc + timedelta(days=1),
                "booking_reference": normalized.booking_reference,
            },
            visible_fields=["google_event_id", "booking_reference", "start_at_utc", "end_at_utc", "reminder_relevant_fields"],
        ),
        GoogleStoryScenario(
            story_key="cancel",
            title="A cancellation clears the reminder path",
            summary="When the Google source is cancelled, reminder jobs can be cancelled with the same stable reference.",
            source_state="cancelled",
            normalized_state="cancelled",
            reminder_state="cancelled",
            changes={
                "google_event_id": normalized.google_event_id,
                "source_status_after": "cancelled",
                "normalized_status_after": "cancelled",
                "reminder_jobs_cancelled": True,
            },
            visible_fields=["source_status", "normalized_state", "booking_reference", "reminder_state"],
        ),
    ]
    return GoogleLinkageDemoPayload(
        generated_at_utc=DEMO_REFERENCE_NOW_UTC,
        appointment_source=source,
        normalized_appointment=normalized,
        stories=stories,
        reminder_relevant_fields=normalized.reminder_relevant_fields,
        operator_summary=[
            "Google is the appointment source, not the reminder engine.",
            "The normalized appointment keeps provider-specific noise out of the reminder flow.",
            "Reschedule and cancel stories stay visible through stable booking and source references.",
        ],
    )
