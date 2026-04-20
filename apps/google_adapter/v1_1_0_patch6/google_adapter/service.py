from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import logging
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from appointment_agent_shared.config import settings
from appointment_agent_shared.enums import ErrorCategory
from appointment_agent_shared.errors import ProviderError

from google_adapter.v1_1_0_patch1.google_adapter.service import (
    CUSTOMER_BLUEPRINTS,
    DEMO_MARKER_PREFIX,
    GoogleAdapterException,
    GoogleAdapterServiceV110Patch1,
)

logger = logging.getLogger(__name__)

APPOINTMENT_TYPE_BLUEPRINTS = {
    "dentist": [
        {
            "title": "Dentist Appointment - Checkup",
            "type": "Dentist Appointment",
            "location": "Dental Practice",
            "purpose": "Routine dental check-up",
            "description": "Routine check-up for a dental patient.",
            "category": "Dentist Appointment",
            "scenario_label": "dentist",
            "customer_prompt": "I want to book a dentist appointment.",
            "reminder_text": "Reminder: Your dentist appointment is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, or cancel?",
            "monitoring_label": "dentist.checkup.search.requested",
        },
        {
            "title": "Dentist Appointment - Tooth Cleaning",
            "type": "Dentist Appointment",
            "location": "Dental Practice",
            "purpose": "Professional tooth cleaning",
            "description": "Professional cleaning appointment.",
            "category": "Dentist Appointment",
            "scenario_label": "dentist",
            "customer_prompt": "I would like a tooth cleaning appointment.",
            "reminder_text": "Reminder: Your dentist cleaning appointment is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, or cancel?",
            "monitoring_label": "dentist.cleaning.search.requested",
        },
    ],
    "wallbox": [
        {
            "title": "Wallbox Technical Inspection",
            "type": "Wallbox Check",
            "location": "Customer Home",
            "purpose": "Wallbox technical inspection",
            "description": "Field visit for a wallbox technical inspection.",
            "category": "Wallbox Check",
            "scenario_label": "wallbox",
            "customer_prompt": "I want a wallbox inspection.",
            "reminder_text": "Reminder: Your wallbox technical inspection is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "wallbox.inspection.search.requested",
        },
        {
            "title": "Electricity - Wallbox Check",
            "type": "Wallbox Check",
            "location": "Customer Home",
            "purpose": "Electric utility wallbox control visit",
            "description": "Electric utility visit for a wallbox check.",
            "category": "Wallbox Check",
            "scenario_label": "wallbox",
            "customer_prompt": "I need an electricity utility wallbox check.",
            "reminder_text": "Reminder: Your electricity wallbox check is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "wallbox.utility.search.requested",
        },
    ],
    "gas_meter": [
        {
            "title": "Gas Meter Inspection",
            "type": "Gas Meter Check",
            "location": "Building Entrance",
            "purpose": "Gas meter inspection",
            "description": "Utility visit for a gas meter inspection.",
            "category": "Gas Meter Check",
            "scenario_label": "gas_meter",
            "customer_prompt": "I need a gas meter inspection.",
            "reminder_text": "Reminder: Your gas meter inspection is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "gas_meter.inspection.search.requested",
        },
        {
            "title": "Gas - Meter Check",
            "type": "Gas Meter Check",
            "location": "Basement Meter Room",
            "purpose": "Gas utility meter check",
            "description": "Gas utility technician checks the gas meter.",
            "category": "Gas Meter Check",
            "scenario_label": "gas_meter",
            "customer_prompt": "I need a gas utility meter check.",
            "reminder_text": "Reminder: Your gas meter check is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "gas_meter.utility.search.requested",
        },
    ],
    "water_meter": [
        {
            "title": "Water Meter Reading",
            "type": "Water Meter Reading",
            "location": "Meter Access Point",
            "purpose": "Water meter reading",
            "description": "Water utility visit for a meter reading.",
            "category": "Water Meter Reading",
            "scenario_label": "water_meter",
            "customer_prompt": "I need a water meter reading.",
            "reminder_text": "Reminder: Your water meter reading is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "water_meter.reading.search.requested",
        },
        {
            "title": "Water - Meter Reading",
            "type": "Water Meter Reading",
            "location": "Building Utility Room",
            "purpose": "Water works meter reading visit",
            "description": "Water works visit for reading the water meter.",
            "category": "Water Meter Reading",
            "scenario_label": "water_meter",
            "customer_prompt": "I need a water works meter reading.",
            "reminder_text": "Reminder: Your water meter reading visit is scheduled soon.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "water_meter.utility.search.requested",
        },
    ],
}


class DemoCalendarPatch6Request(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    action: Literal["prepare", "generate", "delete", "reset"] = "generate"
    count: int = Field(default=6, ge=1, le=30)
    appointment_type: Literal["dentist", "wallbox", "gas_meter", "water_meter"] = "dentist"
    from_date: date
    to_date: date
    include_customer_name: bool = True
    include_description: bool = True
    include_location: bool = True
    linked_address_id: Optional[str] = None
    linked_address_name: Optional[str] = None
    linked_contact_phone: Optional[str] = None
    linked_contact_email: Optional[str] = None
    linked_correlation_ref: Optional[str] = None
    linked_location_text: Optional[str] = None
    linked_contact_reference_id: Optional[str] = None
    linked_address_full_details: Optional[str] = None

    @model_validator(mode="after")
    def validate_range(self) -> "DemoCalendarPatch6Request":
        if self.from_date > self.to_date:
            raise ValueError("from_date must be before or equal to to_date.")
        if (self.to_date - self.from_date).days > settings.booking_window_days:
            raise ValueError(
                "The selected range is too large. Maximum supported range is {} days.".format(
                    settings.booking_window_days
                )
            )
        return self


class DemoCalendarPatch6Result(BaseModel):
    operation_id: str
    action: str
    mode: str
    timeframe: str
    appointment_type: str
    from_date: str
    to_date: str
    live_calendar_writes: bool
    target_calendar_id: str
    target_calendar_summary: str
    warning: str
    generated_count: int
    deleted_count: int
    preview_only: bool = False
    message: str = ""
    items: list[dict[str, Any]] = Field(default_factory=list)


class GoogleAdapterServiceV110Patch6(GoogleAdapterServiceV110Patch1):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def prepare_demo_calendar_patch6(self, request: DemoCalendarPatch6Request) -> DemoCalendarPatch6Result:
        logger.info(
            "google_demo_patch6_action_started mode=%s action=%s appointment_type=%s from_date=%s to_date=%s count=%s",
            request.mode,
            request.action,
            request.appointment_type,
            request.from_date.isoformat(),
            request.to_date.isoformat(),
            request.count,
        )
        status = self.get_mode_status(request.mode)
        if request.mode == "test" and not status.test_mode_available:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="prepare_demo_calendar_patch6",
                    error_category=ErrorCategory.VALIDATION,
                    message="Test mode is not available because the real Google configuration is incomplete.",
                )
            )
        operation_id = "gdemo6-{}".format(uuid4().hex[:10])
        window_start, window_end = self._date_window(request.from_date, request.to_date)
        deleted_count = 0
        if request.action in {"delete", "reset"}:
            deleted_count = self._delete_demo_events_in_range(
                mode=request.mode,
                window_start=window_start,
                window_end=window_end,
            )
        items: list[dict[str, Any]] = []
        preview_only = request.action == "prepare"
        if request.action == "prepare":
            items = self._preview_events_patch6(request, window_start, window_end)
        elif request.action in {"generate", "reset"}:
            items = self._generate_events_patch6(
                operation_id=operation_id,
                request=request,
                window_start=window_start,
                window_end=window_end,
                live_writes=status.live_calendar_writes,
            )
        message = self._action_message_patch6(
            action=request.action,
            appointment_type=request.appointment_type,
            generated_count=len(items),
            deleted_count=deleted_count,
            from_date=request.from_date,
            to_date=request.to_date,
            live_writes=status.live_calendar_writes,
        )
        return DemoCalendarPatch6Result(
            operation_id=operation_id,
            action=request.action,
            mode=status.mode,
            timeframe="custom_range",
            appointment_type=request.appointment_type,
            from_date=request.from_date.isoformat(),
            to_date=request.to_date.isoformat(),
            live_calendar_writes=status.live_calendar_writes,
            target_calendar_id=status.calendar_id or self._calendar_id(),
            target_calendar_summary=status.calendar_summary or self._calendar_summary(),
            warning=status.warning,
            generated_count=len(items),
            deleted_count=deleted_count,
            preview_only=preview_only,
            message=message,
            items=items,
        )

    def _date_window(self, from_date: date, to_date: date) -> tuple[datetime, datetime]:
        tz = datetime.now(timezone.utc).astimezone().tzinfo or timezone.utc
        start = datetime.combine(from_date, time(hour=8, minute=0), tzinfo=tz)
        end = datetime.combine(to_date, time(hour=20, minute=0), tzinfo=tz)
        return start, end

    def _spread_slot_start(
        self,
        window_start: datetime,
        window_end: datetime,
        index: int,
        count: int,
    ) -> datetime:
        total_days = max((window_end.date() - window_start.date()).days + 1, 1)
        day_offset = min(index % total_days, total_days - 1)
        slot_date = window_start.date() + timedelta(days=day_offset)
        hour_sequence = [9, 11, 14, 16]
        slot_hour = hour_sequence[index % len(hour_sequence)]
        return datetime.combine(slot_date, time(hour=slot_hour, minute=0), tzinfo=window_start.tzinfo)

    def _title_blueprints_for_type(self, appointment_type: str) -> list[dict[str, str]]:
        return APPOINTMENT_TYPE_BLUEPRINTS[appointment_type]

    def _customer_blueprints_for_type(self, appointment_type: str) -> list[dict[str, str]]:
        if appointment_type == "dentist":
            return CUSTOMER_BLUEPRINTS[:4]
        return CUSTOMER_BLUEPRINTS

    def _resolved_customer_blueprints(
        self,
        request: DemoCalendarPatch6Request,
    ) -> list[dict[str, str]]:
        """Prefer the operator-selected address over generic demo blueprints.

        Patch 1 turns the selected Address Database record into the source of
        truth for demo generation. When address data is present we keep using
        the appointment-type blueprint for title/purpose, but the generated
        customer identity comes from the selected address instead of a generic
        fallback name.
        """

        if request.linked_address_id:
            return [
                {
                    "name": request.linked_address_name or "Selected Address",
                    "mobile": request.linked_contact_phone or "",
                    "email": request.linked_contact_email or "",
                }
            ]
        return self._customer_blueprints_for_type(request.appointment_type)

    def _resolved_event_title(
        self,
        *,
        request: DemoCalendarPatch6Request,
        blueprint: dict[str, str],
        customer: dict[str, str],
    ) -> str:
        if request.linked_address_id or request.linked_address_name:
            identity = (request.linked_address_name or customer.get("name") or "Selected Address").strip()
            base_title = (blueprint.get("type") or blueprint.get("category") or blueprint["title"]).strip()
            return f"{base_title} - {identity}"
        return blueprint["title"]

    def _build_patch6_description(
        self,
        *,
        blueprint: dict[str, str],
        customer: dict[str, str],
        booking_reference: str,
        request: DemoCalendarPatch6Request,
    ) -> str:
        base_description = self._build_description(
            blueprint=blueprint,
            customer=customer,
            booking_reference=booking_reference,
            include_description=request.include_description,
        )
        linkage_lines = [
            f"Linked address id: {request.linked_address_id or '-'}",
            f"Linked address name: {request.linked_address_name or customer.get('name') or '-'}",
            f"Linked correlation ref: {request.linked_correlation_ref or '-'}",
            f"Linked contact phone: {request.linked_contact_phone or customer.get('mobile') or '-'}",
            f"Linked contact email: {request.linked_contact_email or customer.get('email') or '-'}",
        ]
        if not request.include_description:
            return "\n".join([base_description, linkage_lines[0], linkage_lines[2]])
        return "\n".join([base_description, *linkage_lines])

    def _preview_events_patch6(
        self,
        request: DemoCalendarPatch6Request,
        window_start: datetime,
        window_end: datetime,
    ) -> list[dict[str, Any]]:
        preview_count = min(request.count, 5)
        blueprints = self._title_blueprints_for_type(request.appointment_type)
        customers = self._resolved_customer_blueprints(request)
        items: list[dict[str, Any]] = []
        for index in range(preview_count):
            blueprint = blueprints[index % len(blueprints)]
            customer = customers[index % len(customers)]
            slot_start = self._spread_slot_start(window_start, window_end, index, preview_count)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo6-preview-{}".format(uuid4().hex[:8])
            items.append(
                {
                    "booking_reference": booking_reference,
                    "provider_reference": "preview-{}".format(booking_reference),
                    "title": self._resolved_event_title(request=request, blueprint=blueprint, customer=customer),
                    "customer_name": customer["name"] if request.include_customer_name else "Demo Customer",
                    "mobile_number": customer.get("mobile") or None,
                    "email": customer.get("email") or None,
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "timeframe": "custom_range",
                    "mode": request.mode,
                    "live_written": False,
                    "link_state": "preview_only",
                    "description_marker": DEMO_MARKER_PREFIX,
                    "details": {
                        "appointment_type": request.appointment_type,
                        "purpose": blueprint["purpose"],
                        "description": blueprint.get("description", ""),
                        "location": (request.linked_location_text or blueprint["location"]) if request.include_location else "",
                        "preview_only": "true",
                        "linked_address_id": request.linked_address_id or "",
                        "linked_address_name": request.linked_address_name or customer["name"],
                        "linked_contact_phone": request.linked_contact_phone or customer.get("mobile") or "",
                        "linked_contact_email": request.linked_contact_email or customer.get("email") or "",
                        "linked_correlation_ref": request.linked_correlation_ref or "",
                        "title_strategy": "appointment_type_plus_selected_address" if request.linked_address_id or request.linked_address_name else "blueprint_title",
                    },
                }
            )
        return items

    def _generate_events_patch6(
        self,
        *,
        operation_id: str,
        request: DemoCalendarPatch6Request,
        window_start: datetime,
        window_end: datetime,
        live_writes: bool,
    ) -> list[dict[str, Any]]:
        blueprints = self._title_blueprints_for_type(request.appointment_type)
        customers = self._resolved_customer_blueprints(request)
        items: list[dict[str, Any]] = []
        for index in range(request.count):
            blueprint = blueprints[index % len(blueprints)]
            customer = customers[index % len(customers)]
            slot_start = self._spread_slot_start(window_start, window_end, index, request.count)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo6-book-{}".format(uuid4().hex[:8])
            title = self._resolved_event_title(request=request, blueprint=blueprint, customer=customer)
            description = self._build_patch6_description(
                blueprint=blueprint,
                customer=customer,
                booking_reference=booking_reference,
                request=request,
            )
            provider_reference = "simulation-{}".format(booking_reference)
            details = {
                "appointment_type": request.appointment_type,
                "purpose": blueprint["purpose"],
                "description": blueprint.get("description", ""),
                "location": (request.linked_location_text or blueprint["location"]) if request.include_location else "",
                "category": blueprint.get("category", request.appointment_type),
                "scenario_label": blueprint.get("scenario_label", request.appointment_type),
                "title": title,
                "customer_prompt": blueprint.get("customer_prompt", ""),
                "reminder_text": blueprint.get("reminder_text", ""),
                "follow_up_action": blueprint.get("follow_up_action", ""),
                "monitoring_label": blueprint.get("monitoring_label", ""),
                "linked_address_id": request.linked_address_id or "",
                "linked_address_name": request.linked_address_name or customer["name"],
                "linked_contact_phone": request.linked_contact_phone or customer.get("mobile") or "",
                "linked_contact_email": request.linked_contact_email or customer.get("email") or "",
                "linked_correlation_ref": request.linked_correlation_ref or "",
                "title_strategy": "appointment_type_plus_selected_address" if request.linked_address_id or request.linked_address_name else "blueprint_title",
            }
            if live_writes:
                event_result = self.gateway.create_demo_event(
                    title=title,
                    description=description,
                    location=(request.linked_location_text or blueprint["location"]) if request.include_location else None,
                    start_time=slot_start,
                    end_time=slot_end,
                    metadata={
                        "appointment_agent_demo": "true",
                        "appointment_agent_release": "v1.1.0-patch6",
                        "appointment_agent_booking_reference": booking_reference,
                        "appointment_agent_customer_name": customer["name"],
                        "appointment_agent_appointment_type": request.appointment_type,
                        "appointment_agent_address_id": request.linked_address_id or "",
                        "appointment_agent_address_name": request.linked_address_name or customer["name"],
                        "appointment_agent_contact_phone": request.linked_contact_phone or customer.get("mobile") or "",
                        "appointment_agent_contact_email": request.linked_contact_email or customer.get("email") or "",
                        "appointment_agent_correlation_ref": request.linked_correlation_ref or "",
                    },
                )
                provider_reference = event_result.provider_reference
                details["html_link"] = event_result.html_link or ""
                event_id = event_result.event_id
            else:
                event_id = "simulation-{}".format(booking_reference)
            self.demo_events.save(
                operation_id=operation_id,
                mode=request.mode,
                timeframe="custom_range",
                calendar_id=self._calendar_id(),
                event_id=event_id,
                booking_reference=booking_reference,
                title=title,
                customer_name=customer["name"] if request.include_customer_name else "Demo Customer",
                mobile_number=customer.get("mobile") or None,
                start_time_utc=slot_start.astimezone(timezone.utc).replace(tzinfo=None),
                end_time_utc=slot_end.astimezone(timezone.utc).replace(tzinfo=None),
                timezone=settings.google_default_timezone,
                provider_reference=provider_reference,
                details=details,
            )
            items.append(
                {
                    "booking_reference": booking_reference,
                    "provider_reference": provider_reference,
                    "title": title,
                    "customer_name": customer["name"] if request.include_customer_name else "Demo Customer",
                    "mobile_number": customer.get("mobile") or None,
                    "email": customer.get("email") or None,
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "timeframe": "custom_range",
                    "mode": request.mode,
                    "live_written": live_writes,
                    "link_state": "linked_with_mobile" if customer.get("mobile") else "linked_without_mobile",
                    "description_marker": DEMO_MARKER_PREFIX,
                    "details": details,
                }
            )
        return items

    def _delete_demo_events_in_range(self, *, mode: str, window_start: datetime, window_end: datetime) -> int:
        local_records = self.demo_events.list_active(self._calendar_id())
        records_in_range = [
            record
            for record in local_records
            if record.start_time_utc >= window_start.astimezone(timezone.utc).replace(tzinfo=None)
            and record.end_time_utc <= window_end.astimezone(timezone.utc).replace(tzinfo=None)
        ]
        deleted_booking_refs: list[str] = []
        if mode == "test":
            google_events = {event.get("id"): event for event in self.gateway.list_demo_events(window_start, window_end)}
            for record in records_in_range:
                event_id = record.event_id
                if event_id and event_id in google_events:
                    self.gateway.delete_event(event_id)
                    deleted_booking_refs.append(record.booking_reference)
        else:
            deleted_booking_refs = [record.booking_reference for record in records_in_range]
        self.demo_events.mark_deleted(deleted_booking_refs)
        return len(deleted_booking_refs)

    def _action_message_patch6(
        self,
        *,
        action: str,
        appointment_type: str,
        generated_count: int,
        deleted_count: int,
        from_date: date,
        to_date: date,
        live_writes: bool,
    ) -> str:
        range_text = "{} and {}".format(from_date.isoformat(), to_date.isoformat())
        if action == "prepare":
            return "Prepared a preview for {} appointments between {}. No calendar entries were written.".format(
                appointment_type,
                range_text,
            )
        if action == "generate":
            suffix = " in the Google test calendar" if live_writes else " in simulation mode"
            return "{} appointments created between {}{}.".format(generated_count, range_text, suffix)
        if action == "delete":
            return "{} appointments deleted between {}.".format(deleted_count, range_text)
        return "Reset finished for {}. Deleted {} and created {} appointments between {}.".format(
            appointment_type,
            deleted_count,
            generated_count,
            range_text,
        )
