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
from appointment_agent_shared.repositories import BookingRepository

from google_adapter.v1_1_0_patch1.google_adapter.service import (
    CUSTOMER_BLUEPRINTS,
    DEMO_MARKER_PREFIX,
    GoogleAdapterException,
    GoogleAdapterServiceV110Patch1,
    LiveSyncEventSummary,
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

    def _preview_events_patch6(
        self,
        request: DemoCalendarPatch6Request,
        window_start: datetime,
        window_end: datetime,
    ) -> list[dict[str, Any]]:
        preview_count = min(request.count, 5)
        blueprints = self._title_blueprints_for_type(request.appointment_type)
        customers = self._customer_blueprints_for_type(request.appointment_type)
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
                    "title": blueprint["title"],
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
                        "location": blueprint["location"] if request.include_location else "",
                        "preview_only": "true",
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
        customers = self._customer_blueprints_for_type(request.appointment_type)
        items: list[dict[str, Any]] = []
        for index in range(request.count):
            blueprint = blueprints[index % len(blueprints)]
            customer = customers[index % len(customers)]
            slot_start = self._spread_slot_start(window_start, window_end, index, request.count)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo6-book-{}".format(uuid4().hex[:8])
            description = self._build_description(
                blueprint=blueprint,
                customer=customer,
                booking_reference=booking_reference,
                include_description=request.include_description,
            )
            provider_reference = "simulation-{}".format(booking_reference)
            details = {
                "appointment_type": request.appointment_type,
                "purpose": blueprint["purpose"],
                "description": blueprint.get("description", ""),
                "location": blueprint["location"] if request.include_location else "",
                "category": blueprint.get("category", request.appointment_type),
                "scenario_label": blueprint.get("scenario_label", request.appointment_type),
                "customer_prompt": blueprint.get("customer_prompt", ""),
                "reminder_text": blueprint.get("reminder_text", ""),
                "follow_up_action": blueprint.get("follow_up_action", ""),
                "monitoring_label": blueprint.get("monitoring_label", ""),
            }
            if live_writes:
                event_result = self.gateway.create_demo_event(
                    title=blueprint["title"],
                    description=description,
                    location=blueprint["location"] if request.include_location else None,
                    start_time=slot_start,
                    end_time=slot_end,
                    metadata={
                        "appointment_agent_demo": "true",
                        "appointment_agent_release": "v1.1.0-patch6",
                        "appointment_agent_booking_reference": booking_reference,
                        "appointment_agent_customer_name": customer["name"],
                        "appointment_agent_appointment_type": request.appointment_type,
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
                title=blueprint["title"],
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
                    "title": blueprint["title"],
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


class GoogleAvailabilitySlotsRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    from_date: date
    to_date: date
    max_slots: int = Field(default=5, ge=1, le=20)
    duration_minutes: int = Field(default=45, ge=15, le=240)
    appointment_type: Literal["dentist", "wallbox", "gas_meter", "water_meter"] = "dentist"

    @model_validator(mode="after")
    def validate_range(self) -> "GoogleAvailabilitySlotsRequest":
        if self.from_date > self.to_date:
            raise ValueError("from_date must be before or equal to to_date.")
        if (self.to_date - self.from_date).days > settings.booking_window_days:
            raise ValueError(
                "The selected range is too large. Maximum supported range is {} days.".format(
                    settings.booking_window_days
                )
            )
        return self


class GoogleAvailabilityCheckRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    start_time: datetime
    end_time: datetime
    provider_reference: Optional[str] = None
    exclude_provider_reference: Optional[str] = None
    alternative_count: int = Field(default=3, ge=1, le=10)


class GoogleBookingCreateRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    slot_id: str
    start_time: datetime
    end_time: datetime
    label: str
    appointment_type: Literal["dentist", "wallbox", "gas_meter", "water_meter"] = "dentist"
    customer_name: str = "Demo Customer"
    customer_email: Optional[str] = None
    customer_mobile: Optional[str] = None
    booking_reference: Optional[str] = None


class GoogleBookingCancelRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    booking_reference: str
    provider_reference: Optional[str] = None
    reason: str = "customer_request"


class GoogleBookingRescheduleRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    booking_reference: str
    provider_reference: Optional[str] = None
    slot_id: str
    start_time: datetime
    end_time: datetime
    label: str
    appointment_type: Literal["dentist", "wallbox", "gas_meter", "water_meter"] = "dentist"


class GoogleAvailabilityResult(BaseModel):
    checked_at_utc: str
    mode: str
    google_source: Literal["simulation", "live"]
    slot_available: bool
    conflict_detected: bool
    message: str
    selected_slot: dict[str, Any]
    alternative_slots: list[dict[str, Any]] = Field(default_factory=list)
    monitoring_labels: list[str] = Field(default_factory=list)
    technical_reason: Optional[str] = None


class GoogleAvailabilitySlotsResult(BaseModel):
    checked_at_utc: str
    mode: str
    google_source: Literal["simulation", "live"]
    from_date: str
    to_date: str
    slot_count: int
    slots: list[dict[str, Any]] = Field(default_factory=list)
    monitoring_labels: list[str] = Field(default_factory=list)


class GoogleBookingActionResult(BaseModel):
    success: bool
    action: Literal["create", "cancel", "reschedule"]
    mode: str
    google_source: Literal["simulation", "live"]
    booking_reference: Optional[str] = None
    provider_reference: Optional[str] = None
    message: str
    status: str
    conflict_detected: bool = False
    selected_slot: Optional[dict[str, Any]] = None
    alternative_slots: list[dict[str, Any]] = Field(default_factory=list)
    monitoring_labels: list[str] = Field(default_factory=list)
    technical_reason: Optional[str] = None


class GoogleAdapterServiceV110Patch8(GoogleAdapterServiceV110Patch6):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.bookings = BookingRepository(session)

    def _require_supported_mode(self, requested_mode: str):
        status = self.get_mode_status(requested_mode)  # type: ignore[arg-type]
        if requested_mode == "test" and not status.live_calendar_writes:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="patch8_mode_guard",
                    error_category=ErrorCategory.VALIDATION,
                    message="Test mode is not available because the Google test calendar is not fully configured.",
                )
            )
        return status

    def _normalize_slot(self, start_time: datetime, end_time: datetime, *, slot_id: str, provider: str) -> dict[str, Any]:
        # The UI should not care whether the slot came from simulation, Google,
        # or a future Microsoft adapter. This normalized shape keeps that boundary stable.
        local_start = start_time.astimezone()
        return {
            "slot_id": slot_id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "label": local_start.strftime("%a, %d %b, %H:%M"),
            "available": True,
            "calendar_provider": provider,
        }

    def _candidate_windows(
        self,
        *,
        from_date_value: date,
        to_date_value: date,
        duration_minutes: int,
    ) -> list[tuple[datetime, datetime]]:
        tz = datetime.now(timezone.utc).astimezone().tzinfo or timezone.utc
        windows: list[tuple[datetime, datetime]] = []
        slot_hours = [9, 11, 14, 16]
        day_count = (to_date_value - from_date_value).days + 1
        for day_offset in range(max(day_count, 0)):
            slot_date = from_date_value + timedelta(days=day_offset)
            for hour in slot_hours:
                start_time = datetime.combine(slot_date, time(hour=hour, minute=0), tzinfo=tz)
                end_time = start_time + timedelta(minutes=duration_minutes)
                windows.append((start_time, end_time))
        return windows

    def _as_aware_datetime(self, value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    def _load_conflicts_for_window(
        self,
        *,
        status,
        start_time: datetime,
        end_time: datetime,
        exclude_provider_reference: Optional[str],
    ) -> list[LiveSyncEventSummary]:
        # Patch 8 compares simulation and live slots through one code path, so
        # we normalize every datetime first to avoid naive/aware mismatches.
        normalized_start = self._as_aware_datetime(start_time)
        normalized_end = self._as_aware_datetime(end_time)
        if not status.live_calendar_writes:
            conflicts: list[LiveSyncEventSummary] = []
            for record in self.demo_events.list_active(self._calendar_id()):
                provider_reference = record.provider_reference or record.event_id or record.booking_reference
                if exclude_provider_reference and provider_reference == exclude_provider_reference:
                    continue
                event_start = self._as_aware_datetime(record.start_time_utc)
                event_end = self._as_aware_datetime(record.end_time_utc)
                if event_start < normalized_end and event_end > normalized_start:
                    conflicts.append(
                        LiveSyncEventSummary(
                            provider_reference=provider_reference,
                            title=record.title,
                            start_time=event_start.isoformat(),
                            end_time=event_end.isoformat(),
                            source="simulation",
                            is_demo_generated=record.is_demo_generated,
                        )
                    )
            return conflicts
        events = self._load_occupancy_events(status=status, window_start=normalized_start, window_end=normalized_end)
        conflicts: list[LiveSyncEventSummary] = []
        for event in events:
            if exclude_provider_reference and event.provider_reference == exclude_provider_reference:
                continue
            event_start = datetime.fromisoformat(event.start_time.replace("Z", "+00:00")) if event.start_time else None
            event_end = datetime.fromisoformat(event.end_time.replace("Z", "+00:00")) if event.end_time else None
            if event_start is None or event_end is None:
                continue
            event_start = self._as_aware_datetime(event_start)
            event_end = self._as_aware_datetime(event_end)
            if event_start < normalized_end and event_end > normalized_start:
                conflicts.append(event)
        return conflicts

    def _slot_range_from_start(self, start_time: datetime, days: int = 3) -> tuple[date, date]:
        start_day = start_time.astimezone().date()
        return start_day, start_day + timedelta(days=days)

    def get_available_slots_patch8(self, request: GoogleAvailabilitySlotsRequest) -> GoogleAvailabilitySlotsResult:
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        slots: list[dict[str, Any]] = []
        for index, (start_time, end_time) in enumerate(
            self._candidate_windows(
                from_date_value=request.from_date,
                to_date_value=request.to_date,
                duration_minutes=request.duration_minutes,
            ),
            start=1,
        ):
            conflicts = self._load_conflicts_for_window(
                status=status,
                start_time=start_time,
                end_time=end_time,
                exclude_provider_reference=None,
            )
            if conflicts:
                continue
            slots.append(
                self._normalize_slot(
                    start_time,
                    end_time,
                    slot_id="patch8-slot-{}".format(index),
                    provider="google" if status.live_calendar_writes else "simulated",
                )
            )
            if len(slots) >= request.max_slots:
                break
        return GoogleAvailabilitySlotsResult(
            checked_at_utc=datetime.now(timezone.utc).isoformat(),
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            from_date=request.from_date.isoformat(),
            to_date=request.to_date.isoformat(),
            slot_count=len(slots),
            slots=slots,
            monitoring_labels=["slot.checked", "slot.list.generated", "google.source.live" if status.live_calendar_writes else "google.source.simulation"],
        )

    def check_availability_patch8(self, request: GoogleAvailabilityCheckRequest) -> GoogleAvailabilityResult:
        # Conflict detection runs before booking so the demo behaves like a real scheduling backend.
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        conflicts = self._load_conflicts_for_window(
            status=status,
            start_time=request.start_time,
            end_time=request.end_time,
            exclude_provider_reference=request.exclude_provider_reference,
        )
        selected_slot = self._normalize_slot(
            request.start_time,
            request.end_time,
            slot_id="selected-slot",
            provider="google" if status.live_calendar_writes else "simulated",
        )
        if conflicts:
            from_date_value, to_date_value = self._slot_range_from_start(request.start_time)
            alternatives = self.get_available_slots_patch8(
                GoogleAvailabilitySlotsRequest(
                    mode=request.mode,
                    from_date=from_date_value,
                    to_date=to_date_value,
                    max_slots=request.alternative_count,
                )
            ).slots
            return GoogleAvailabilityResult(
                checked_at_utc=datetime.now(timezone.utc).isoformat(),
                mode=status.mode,
                google_source="live" if status.live_calendar_writes else "simulation",
                slot_available=False,
                conflict_detected=True,
                message="Selected slot is no longer available.",
                selected_slot=selected_slot,
                alternative_slots=alternatives,
                monitoring_labels=["slot.checked", "slot.conflict_detected"],
                technical_reason="slot_occupied",
            )
        return GoogleAvailabilityResult(
            checked_at_utc=datetime.now(timezone.utc).isoformat(),
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            slot_available=True,
            conflict_detected=False,
            message="Selected slot is available.",
            selected_slot=selected_slot,
            alternative_slots=[],
            monitoring_labels=["slot.checked"],
        )

    def _booking_title(self, appointment_type: str) -> str:
        return self._title_blueprints_for_type(appointment_type)[0]["title"]

    def create_booking_patch8(self, request: GoogleBookingCreateRequest) -> GoogleBookingActionResult:
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        availability = self.check_availability_patch8(
            GoogleAvailabilityCheckRequest(
                mode=request.mode,
                start_time=request.start_time,
                end_time=request.end_time,
            )
        )
        if not availability.slot_available:
            return GoogleBookingActionResult(
                success=False,
                action="create",
                mode=status.mode,
                google_source=availability.google_source,
                message=availability.message,
                status="conflict",
                conflict_detected=True,
                selected_slot=availability.selected_slot,
                alternative_slots=availability.alternative_slots,
                monitoring_labels=["slot.checked", "slot.conflict_detected", "booking.failed"],
                technical_reason=availability.technical_reason,
            )
        booking_reference = request.booking_reference or "gpatch8-book-{}".format(uuid4().hex[:8])
        provider_reference = "simulation-{}".format(booking_reference)
        event_id = provider_reference
        description = "{}\n{} booking reference: {}".format(DEMO_MARKER_PREFIX, request.appointment_type, booking_reference)
        if status.live_calendar_writes:
            event_result = self.gateway.create_demo_event(
                title=self._booking_title(request.appointment_type),
                description=description,
                location=None,
                start_time=request.start_time,
                end_time=request.end_time,
                metadata={
                    "appointment_agent_demo": "true",
                    "appointment_agent_release": "v1.1.0-patch8",
                    "appointment_agent_booking_reference": booking_reference,
                    "appointment_agent_appointment_type": request.appointment_type,
                },
            )
            provider_reference = event_result.provider_reference
            event_id = event_result.event_id
        self.bookings.save(
            booking_reference=booking_reference,
            journey_id="patch8-google-journey",
            customer_id=request.customer_name or "demo-customer",
            provider="google",
            external_id=provider_reference,
            status="confirmed",
            payload={
                "slot_id": request.slot_id,
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "appointment_type": request.appointment_type,
                "provider_reference": {"external_id": provider_reference},
            },
        )
        self.demo_events.save(
            operation_id="patch8-booking-create",
            mode=request.mode,
            timeframe="patch8_booking",
            calendar_id=self._calendar_id(),
            event_id=event_id,
            booking_reference=booking_reference,
            title=self._booking_title(request.appointment_type),
            customer_name=request.customer_name,
            mobile_number=request.customer_mobile,
            start_time_utc=request.start_time.astimezone(timezone.utc).replace(tzinfo=None),
            end_time_utc=request.end_time.astimezone(timezone.utc).replace(tzinfo=None),
            timezone=settings.google_default_timezone,
            provider_reference=provider_reference,
            details={"label": request.label, "appointment_type": request.appointment_type},
            is_demo_generated=True,
        )
        return GoogleBookingActionResult(
            success=True,
            action="create",
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            booking_reference=booking_reference,
            provider_reference=provider_reference,
            message="Booking created successfully.",
            status="confirmed",
            selected_slot=self._normalize_slot(request.start_time, request.end_time, slot_id=request.slot_id, provider="google" if status.live_calendar_writes else "simulated"),
            monitoring_labels=["slot.checked", "booking.created"],
        )

    def cancel_booking_patch8(self, request: GoogleBookingCancelRequest) -> GoogleBookingActionResult:
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        record = self.bookings.get(request.booking_reference)
        if record is None:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="cancel_booking_patch8",
                    error_category=ErrorCategory.NOT_FOUND,
                    message="Booking reference was not found.",
                )
            )
        provider_reference = request.provider_reference or record.external_id
        if status.live_calendar_writes and provider_reference and self.gateway.get_event(provider_reference):
            self.gateway.delete_event(provider_reference)
        self.demo_events.mark_deleted([request.booking_reference])
        self.bookings.save(
            booking_reference=request.booking_reference,
            journey_id=record.journey_id,
            customer_id=record.customer_id,
            provider=record.provider,
            external_id=provider_reference or "",
            status="cancelled",
            payload={**(record.payload or {}), "cancelled_reason": request.reason},
        )
        return GoogleBookingActionResult(
            success=True,
            action="cancel",
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            booking_reference=request.booking_reference,
            provider_reference=provider_reference,
            message="Booking cancelled successfully.",
            status="cancelled",
            monitoring_labels=["booking.cancelled"],
        )

    def reschedule_booking_patch8(self, request: GoogleBookingRescheduleRequest) -> GoogleBookingActionResult:
        status = self._require_supported_mode(request.mode) if request.mode == "test" else self.get_mode_status(request.mode)
        record = self.bookings.get(request.booking_reference)
        if record is None:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="reschedule_booking_patch8",
                    error_category=ErrorCategory.NOT_FOUND,
                    message="Booking reference was not found.",
                )
            )
        current_provider_reference = request.provider_reference or record.external_id
        availability = self.check_availability_patch8(
            GoogleAvailabilityCheckRequest(
                mode=request.mode,
                start_time=request.start_time,
                end_time=request.end_time,
                exclude_provider_reference=current_provider_reference,
            )
        )
        if not availability.slot_available:
            return GoogleBookingActionResult(
                success=False,
                action="reschedule",
                mode=status.mode,
                google_source=availability.google_source,
                booking_reference=request.booking_reference,
                provider_reference=current_provider_reference,
                message=availability.message,
                status="conflict",
                conflict_detected=True,
                selected_slot=availability.selected_slot,
                alternative_slots=availability.alternative_slots,
                monitoring_labels=["slot.checked", "slot.conflict_detected", "booking.failed"],
                technical_reason=availability.technical_reason,
            )
        if status.live_calendar_writes and current_provider_reference and self.gateway.get_event(current_provider_reference):
            self.gateway.delete_event(current_provider_reference)
        provider_reference = "simulation-{}".format(request.booking_reference)
        event_id = provider_reference
        if status.live_calendar_writes:
            event_result = self.gateway.create_demo_event(
                title=self._booking_title(request.appointment_type),
                description="{} reschedule reference: {}".format(DEMO_MARKER_PREFIX, request.booking_reference),
                location=None,
                start_time=request.start_time,
                end_time=request.end_time,
                metadata={
                    "appointment_agent_demo": "true",
                    "appointment_agent_release": "v1.1.0-patch8",
                    "appointment_agent_booking_reference": request.booking_reference,
                    "appointment_agent_appointment_type": request.appointment_type,
                },
            )
            provider_reference = event_result.provider_reference
            event_id = event_result.event_id
        self.bookings.save(
            booking_reference=request.booking_reference,
            journey_id=record.journey_id,
            customer_id=record.customer_id,
            provider=record.provider,
            external_id=provider_reference,
            status="rescheduled",
            payload={
                **(record.payload or {}),
                "slot_id": request.slot_id,
                "start_time": request.start_time.isoformat(),
                "end_time": request.end_time.isoformat(),
                "appointment_type": request.appointment_type,
                "provider_reference": {"external_id": provider_reference},
            },
        )
        self.demo_events.save(
            operation_id="patch8-booking-reschedule",
            mode=request.mode,
            timeframe="patch8_booking",
            calendar_id=self._calendar_id(),
            event_id=event_id,
            booking_reference=request.booking_reference,
            title=self._booking_title(request.appointment_type),
            customer_name=record.customer_id,
            mobile_number=None,
            start_time_utc=request.start_time.astimezone(timezone.utc).replace(tzinfo=None),
            end_time_utc=request.end_time.astimezone(timezone.utc).replace(tzinfo=None),
            timezone=settings.google_default_timezone,
            provider_reference=provider_reference,
            details={"label": request.label, "appointment_type": request.appointment_type},
            is_demo_generated=True,
        )
        return GoogleBookingActionResult(
            success=True,
            action="reschedule",
            mode=status.mode,
            google_source="live" if status.live_calendar_writes else "simulation",
            booking_reference=request.booking_reference,
            provider_reference=provider_reference,
            message="Booking rescheduled successfully.",
            status="rescheduled",
            selected_slot=self._normalize_slot(request.start_time, request.end_time, slot_id=request.slot_id, provider="google" if status.live_calendar_writes else "simulated"),
            monitoring_labels=["slot.checked", "booking.rescheduled"],
        )
