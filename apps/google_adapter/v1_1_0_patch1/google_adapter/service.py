from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import logging
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from appointment_agent_shared.config import settings
from appointment_agent_shared.enums import ErrorCategory
from appointment_agent_shared.errors import ProviderError
from appointment_agent_shared.repositories import ContactRepository, GoogleDemoEventRepository

DEMO_MARKER_PREFIX = "[Appointment Agent Demo]"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"
logger = logging.getLogger(__name__)

GENERAL_TITLE_BLUEPRINTS = [
    {
        "title": "Dentist Appointment - Dr. Zahn (Check-up)",
        "type": "Dentist Check-up",
        "location": "SmileCare Berlin",
        "purpose": "Routine preventive visit",
    },
    {
        "title": "Heating Maintenance - Annual Inspection",
        "type": "Technical Visit",
        "location": "Customer Property",
        "purpose": "Annual heating system inspection",
    },
    {
        "title": "Insurance Consultation - Policy Review",
        "type": "Consultation",
        "location": "Remote Call",
        "purpose": "Review open policy questions",
    },
    {
        "title": "Property Visit - Technician Appointment",
        "type": "Field Service",
        "location": "Customer Property",
        "purpose": "Technician checks an open issue",
    },
    {
        "title": "Electricity Meter Service Visit - Stadtwerke",
        "type": "Utility Service",
        "location": "Building Entrance",
        "purpose": "Meter verification and handover",
    },
    {
        "title": "Customer Consultation - Contract Review",
        "type": "Contract Review",
        "location": "Service Office",
        "purpose": "Discuss contract options",
    },
]

VERTICAL_TITLE_BLUEPRINTS = {
    "dentist": [
        {
            "title": "Dental Check-up - Dr. Zahn",
            "type": "Dental Check-up",
            "location": "Dental Practice",
            "purpose": "Routine preventive check-up",
            "description": "Routine dental check-up for an existing patient at Dr. Zahn's practice.",
            "category": "Dentist",
            "scenario_label": "Dentist",
            "customer_prompt": "I would like to book a dental check-up.",
            "reminder_text": "Reminder: You have a dental check-up tomorrow at 10:00 with Dr. Zahn.",
            "follow_up_action": "Would you like to keep, reschedule, or cancel your appointment?",
            "monitoring_label": "dentist.checkup.search.requested",
        },
        {
            "title": "Tooth Cleaning - Dr. Zahn",
            "type": "Dental Cleaning",
            "location": "Dental Practice",
            "purpose": "Professional tooth cleaning",
            "description": "Professional tooth cleaning for a regular patient.",
            "category": "Dentist",
            "scenario_label": "Dentist",
            "customer_prompt": "I want to schedule a tooth cleaning.",
            "reminder_text": "Reminder: You have a tooth cleaning tomorrow at 11:30 with Dr. Zahn.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or speak to someone?",
            "monitoring_label": "dentist.cleaning.search.requested",
        },
        {
            "title": "Follow-up Appointment - Dr. Zahn",
            "type": "Follow-up Visit",
            "location": "Dental Practice",
            "purpose": "Review treatment progress",
            "description": "Follow-up appointment after a recent treatment at the dental practice.",
            "category": "Dentist",
            "scenario_label": "Dentist",
            "customer_prompt": "I need a follow-up appointment with Dr. Zahn.",
            "reminder_text": "Reminder: You have a follow-up appointment tomorrow at 09:00 with Dr. Zahn.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or speak to someone?",
            "monitoring_label": "dentist.followup.search.requested",
        },
        {
            "title": "Consultation - Sensitive Tooth Pain",
            "type": "Consultation",
            "location": "Dental Practice",
            "purpose": "Clarify a new pain issue before treatment.",
            "description": "Consultation visit because of sensitive tooth pain.",
            "category": "Dentist",
            "scenario_label": "Dentist",
            "customer_prompt": "I have sensitive tooth pain and need an appointment.",
            "reminder_text": "Reminder: Your dental consultation is scheduled for tomorrow at 15:00.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or speak to someone?",
            "monitoring_label": "dentist.consultation.search.requested",
        },
        {
            "title": "X-Ray Follow-up - Dr. Zahn",
            "type": "X-Ray Follow-up",
            "location": "Dental Practice",
            "purpose": "Review X-ray results with the dentist.",
            "description": "Follow-up visit to discuss X-ray results and next steps.",
            "category": "Dentist",
            "scenario_label": "Dentist",
            "customer_prompt": "I would like to book my X-ray follow-up.",
            "reminder_text": "Reminder: Your X-ray follow-up with Dr. Zahn is tomorrow at 13:00.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or speak to someone?",
            "monitoring_label": "dentist.xray_followup.search.requested",
        },
    ],
    "wallbox": [
        {
            "title": "Wallbox Inspection - Home Visit",
            "type": "Wallbox Inspection",
            "location": "Customer Home",
            "purpose": "Check wallbox installation status",
            "description": "Utility technician visits the customer home to inspect the installed wallbox.",
            "category": "Stadtwerke Wallbox",
            "scenario_label": "Wallbox",
            "customer_prompt": "I want to schedule a wallbox inspection.",
            "reminder_text": "Reminder: Your wallbox inspection is scheduled for tomorrow at 14:00.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "wallbox.inspection.search.requested",
        },
        {
            "title": "EV Charging Check - Technician Appointment",
            "type": "Charging Check",
            "location": "Customer Home",
            "purpose": "Technician validates charging setup",
            "description": "Technician appointment to validate charging performance and safety at the customer site.",
            "category": "Stadtwerke Wallbox",
            "scenario_label": "Wallbox",
            "customer_prompt": "I want to schedule an EV charger safety check.",
            "reminder_text": "Reminder: A technician can visit you tomorrow at 14:00 for the EV charging check.",
            "follow_up_action": "Would you like to confirm this appointment?",
            "monitoring_label": "wallbox.safety_check.search.requested",
        },
        {
            "title": "Wallbox Commissioning Review",
            "type": "Commissioning Review",
            "location": "Customer Home",
            "purpose": "Final review before operation handover",
            "description": "Commissioning review before the wallbox is handed over for regular usage.",
            "category": "Stadtwerke Wallbox",
            "scenario_label": "Wallbox",
            "customer_prompt": "I need a commissioning review for the new wallbox.",
            "reminder_text": "Reminder: Your wallbox commissioning review is tomorrow at 09:30.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "wallbox.commissioning.search.requested",
        },
        {
            "title": "Charging Station Maintenance Visit",
            "type": "Maintenance Visit",
            "location": "Customer Home",
            "purpose": "Maintenance visit for a customer-side charging station.",
            "description": "Technician visit to perform maintenance on the charging station.",
            "category": "Stadtwerke Wallbox",
            "scenario_label": "Wallbox",
            "customer_prompt": "I need a maintenance visit for the charging station.",
            "reminder_text": "Reminder: Your charging station maintenance visit is tomorrow at 08:30.",
            "follow_up_action": "Would you like to confirm, move, cancel, or request a call?",
            "monitoring_label": "wallbox.maintenance.search.requested",
        },
        {
            "title": "Technician Visit - Wallbox Status Check",
            "type": "Status Check",
            "location": "Customer Home",
            "purpose": "Check wallbox status after a reported issue.",
            "description": "Technician visit to review the current wallbox status after an issue report.",
            "category": "Stadtwerke Wallbox",
            "scenario_label": "Wallbox",
            "customer_prompt": "I need a technician visit for a wallbox status check.",
            "reminder_text": "Reminder: Your wallbox status check is scheduled for tomorrow at 16:00.",
            "follow_up_action": "Would you like to keep, reschedule, cancel, or request a call?",
            "monitoring_label": "wallbox.status_check.search.requested",
        },
    ],
    "district_heating": [
        {
            "title": "District Heating Transfer Station Inspection",
            "type": "District Heating Inspection",
            "location": "Building Utility Room",
            "purpose": "Inspect transfer station safety and settings",
            "description": "Inspection visit for the district heating transfer station in the building utility room.",
            "category": "District Heating",
            "scenario_label": "District Heating",
            "customer_prompt": "I want to schedule an inspection for the district heating transfer station.",
            "reminder_text": "Reminder: Your district heating transfer station inspection is scheduled for tomorrow at 09:00.",
            "follow_up_action": "Would you like to confirm, move, cancel, or speak to an agent?",
            "monitoring_label": "district_heating.inspection.search.requested",
        },
        {
            "title": "Nahwaerme Uebergabestation Check",
            "type": "Transfer Station Check",
            "location": "Building Utility Room",
            "purpose": "Check the district heating transfer station",
            "description": "Technician check for the Nahwaerme transfer station and interface components.",
            "category": "District Heating",
            "scenario_label": "District Heating",
            "customer_prompt": "I need a check for the Nahwaerme transfer station.",
            "reminder_text": "Reminder: Your Nahwaerme transfer station check is tomorrow at 10:30.",
            "follow_up_action": "Would you like to confirm, move, cancel, or speak to an agent?",
            "monitoring_label": "district_heating.transfer_station.search.requested",
        },
        {
            "title": "Heat Transfer Unit Service Visit",
            "type": "Heat Unit Service",
            "location": "Building Utility Room",
            "purpose": "Service visit for the heating transfer unit",
            "description": "Service visit to maintain and review the heat transfer unit.",
            "category": "District Heating",
            "scenario_label": "District Heating",
            "customer_prompt": "I want to schedule a service visit for the heat transfer unit.",
            "reminder_text": "Reminder: Your heat transfer unit service visit is scheduled for tomorrow at 11:00.",
            "follow_up_action": "Would you like to confirm, move, cancel, or speak to an agent?",
            "monitoring_label": "heat_transfer.service_visit.search.requested",
        },
        {
            "title": "Heating Interface Maintenance Visit",
            "type": "Maintenance Visit",
            "location": "Building Utility Room",
            "purpose": "Maintenance on the heating interface and related components.",
            "description": "Maintenance visit for the heating interface in the customer building.",
            "category": "District Heating",
            "scenario_label": "District Heating",
            "customer_prompt": "I need a maintenance visit for the heating interface.",
            "reminder_text": "Reminder: Your heating interface maintenance visit is tomorrow at 08:00.",
            "follow_up_action": "Would you like to confirm, move, cancel, or speak to an agent?",
            "monitoring_label": "district_heating.maintenance.search.requested",
        },
        {
            "title": "Technician Appointment - Heat Transfer Review",
            "type": "Technician Review",
            "location": "Building Utility Room",
            "purpose": "Review technical status and explain next maintenance steps.",
            "description": "Technician appointment to review the heat transfer setup and next actions.",
            "category": "District Heating",
            "scenario_label": "District Heating",
            "customer_prompt": "I need a technician appointment for a heat transfer review.",
            "reminder_text": "Reminder: Your heat transfer review is scheduled for tomorrow at 13:30.",
            "follow_up_action": "Would you like to confirm, move, cancel, or speak to an agent?",
            "monitoring_label": "heat_transfer.review.search.requested",
        },
    ],
}

CUSTOMER_BLUEPRINTS = [
    {"name": "Lea Fischer", "mobile": "+491701230010", "email": "lea.fischer@example.com"},
    {"name": "Noah Becker", "mobile": "+491701230011", "email": "noah.becker@example.com"},
    {"name": "Mila Wagner", "mobile": "+491701230012", "email": "mila.wagner@example.com"},
    {"name": "Ben Schulz", "mobile": "", "email": "ben.schulz@example.com"},
    {"name": "Emma Koch", "mobile": "+491701230014", "email": "emma.koch@example.com"},
    {"name": "Jonas Hartmann", "mobile": "+491701230015", "email": ""},
]

VERTICAL_CUSTOMER_BLUEPRINTS = {
    "dentist": [
        {"name": "Anna Becker", "mobile": "+491701230101", "email": "anna.becker@example.com", "context": "Private patient"},
        {"name": "Julia Hoffmann", "mobile": "+491701230102", "email": "julia.hoffmann@example.com", "context": "Existing patient"},
        {"name": "Markus Weber", "mobile": "+491701230103", "email": "markus.weber@example.com", "context": "Recall appointment"},
    ],
    "wallbox": [
        {"name": "Familie Schneider", "mobile": "+491701230201", "email": "schneider.family@example.com", "context": "Household with wallbox installation"},
        {"name": "Julia Hoffmann", "mobile": "+491701230202", "email": "julia.hoffmann@example.com", "context": "Owner of a home charging setup"},
        {"name": "Markus Weber", "mobile": "+491701230203", "email": "markus.weber@example.com", "context": "Single-family home visit"},
    ],
    "district_heating": [
        {"name": "Familie Schneider", "mobile": "+491701230301", "email": "district.schneider@example.com", "context": "Household with utility-room access"},
        {"name": "Hausverwaltung Nordblick", "mobile": "+491701230302", "email": "nordblick@example.com", "context": "Building management contact"},
        {"name": "Anna Becker", "mobile": "+491701230303", "email": "anna.becker@example.com", "context": "Residential service account"},
    ],
}


class GoogleModeStatus(BaseModel):
    mode: Literal["simulation", "test"]
    requested_mode: Literal["simulation", "test"]
    live_calendar_writes: bool
    test_mode_available: bool
    calendar_id: Optional[str] = None
    calendar_id_masked: Optional[str] = None
    calendar_summary: Optional[str] = None
    warning: str
    runtime_flags: dict[str, Any] = Field(default_factory=dict)


class DemoCalendarPrepareRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    timeframe: Literal["day", "week", "month"] = "day"
    action: Literal["prepare", "generate", "delete", "reset"] = "generate"
    count: int = Field(default=6, ge=1, le=30)
    vertical: Literal["general", "dentist", "wallbox", "district_heating"] = "general"
    include_customer_name: bool = True
    include_description: bool = True
    include_location: bool = True


class DemoCalendarItem(BaseModel):
    booking_reference: str
    provider_reference: str
    title: str
    customer_name: str
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    start_time: str
    end_time: str
    timeframe: str
    mode: str
    live_written: bool
    link_state: str
    description_marker: str
    details: dict[str, Any] = Field(default_factory=dict)


class DemoCalendarPrepareResult(BaseModel):
    operation_id: str
    action: str
    mode: str
    timeframe: str
    vertical: str
    live_calendar_writes: bool
    target_calendar_id: str
    target_calendar_summary: str
    warning: str
    generated_count: int
    deleted_count: int
    preview_only: bool = False
    message: str = ""
    items: list[DemoCalendarItem] = Field(default_factory=list)


class LiveSyncEventSummary(BaseModel):
    provider_reference: str
    title: str
    start_time: str
    end_time: str
    source: str
    is_demo_generated: bool = False


class GoogleConflictResult(BaseModel):
    checked_at_utc: str
    google_source: Literal["simulation", "live"]
    conflict_detected: bool
    conflict_type: Optional[str] = None
    message: str
    provider_reference: Optional[str] = None
    next_actions: list[str] = Field(default_factory=list)
    monitoring_labels: list[str] = Field(default_factory=list)
    conflicting_events: list[LiveSyncEventSummary] = Field(default_factory=list)


class GoogleLiveSyncStatus(BaseModel):
    checked_at_utc: str
    google_source: Literal["simulation", "live"]
    mode: Literal["simulation", "test"]
    target_calendar_id: str
    target_calendar_summary: str
    warning: str
    last_sync_status: str
    occupied_count: int
    occupied_events: list[LiveSyncEventSummary] = Field(default_factory=list)
    monitoring_labels: list[str] = Field(default_factory=list)


class GoogleLiveSyncRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    timeframe: Literal["day", "week", "month"] = "day"


class GoogleConflictCheckRequest(BaseModel):
    mode: Literal["simulation", "test"] = "simulation"
    start_time: datetime
    end_time: datetime
    timeframe: Literal["day", "week", "month"] = "day"
    provider_reference: Optional[str] = None
    exclude_provider_reference: Optional[str] = None


class ContactLinkingPreview(BaseModel):
    workspace_state: str
    current_workspace_owner: str
    future_workspace_target: str
    generated_appointments_rule: str
    manual_appointments_rule: str
    contact_lookup_sources: list[str]
    contact_fields: list[str]
    fallback_states: list[str]
    example_links: list[dict[str, str]]


class GoogleAdapterException(Exception):
    def __init__(self, error: ProviderError) -> None:
        super().__init__(error.message)
        self.error = error


@dataclass
class CalendarMetadata:
    calendar_id: str
    summary: str


@dataclass
class CalendarEventResult:
    event_id: str
    provider_reference: str
    html_link: Optional[str]


class GoogleCalendarGateway:
    def __init__(self) -> None:
        self._service = None

    def _build_service(self):
        if self._service is not None:
            return self._service
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:  # pragma: no cover - exercised only when deps are missing
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="build_client",
                    error_category=ErrorCategory.VALIDATION,
                    message="Google dependencies are missing. Run `pip install -e '.[google]'`.",
                )
            ) from exc
        credentials = Credentials(
            token=None,
            refresh_token=settings.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=[CALENDAR_SCOPE],
        )
        credentials.refresh(Request())
        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    def get_calendar_metadata(self) -> CalendarMetadata:
        service = self._build_service()
        payload = service.calendars().get(calendarId=settings.google_calendar_id).execute()
        return CalendarMetadata(
            calendar_id=settings.google_calendar_id,
            summary=payload.get("summary") or settings.google_calendar_id,
        )

    def create_demo_event(
        self,
        *,
        title: str,
        description: str,
        location: Optional[str],
        start_time: datetime,
        end_time: datetime,
        metadata: dict[str, str],
        timezone_name: Optional[str] = None,
    ) -> CalendarEventResult:
        service = self._build_service()
        event_timezone = str(timezone_name or settings.google_default_timezone).strip() or settings.google_default_timezone
        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time.isoformat(), "timeZone": event_timezone},
            "end": {"dateTime": end_time.isoformat(), "timeZone": event_timezone},
            "extendedProperties": {"private": metadata},
        }
        if location:
            event_body["location"] = location
        created = service.events().insert(calendarId=settings.google_calendar_id, body=event_body).execute()
        event_id = created.get("id") or uuid4().hex
        return CalendarEventResult(
            event_id=event_id,
            provider_reference=event_id,
            html_link=created.get("htmlLink"),
        )

    def list_demo_events(self, start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
        service = self._build_service()
        events_result = service.events().list(
            calendarId=settings.google_calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        ).execute()
        items = events_result.get("items", [])
        return [
            item
            for item in items
            if ((item.get("extendedProperties") or {}).get("private") or {}).get("appointment_agent_demo") == "true"
            or DEMO_MARKER_PREFIX in (item.get("description") or "")
        ]

    def list_events_range(self, start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
        service = self._build_service()
        events_result = service.events().list(
            calendarId=settings.google_calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        ).execute()
        return events_result.get("items", [])

    def get_event(self, event_id: str) -> Optional[dict[str, Any]]:
        service = self._build_service()
        try:
            return service.events().get(calendarId=settings.google_calendar_id, eventId=event_id).execute()
        except Exception:
            return None

    def delete_event(self, event_id: str) -> None:
        service = self._build_service()
        service.events().delete(calendarId=settings.google_calendar_id, eventId=event_id).execute()


class GoogleAdapterServiceV110Patch1:
    def __init__(self, session: Session, gateway: Optional[GoogleCalendarGateway] = None) -> None:
        self.session = session
        self.contacts = ContactRepository(session)
        self.demo_events = GoogleDemoEventRepository(session)
        self.gateway = gateway or GoogleCalendarGateway()

    def _calendar_id(self) -> str:
        return settings.google_calendar_id or "simulation-calendar"

    def _calendar_summary(self) -> str:
        return "Configured Google Test Calendar" if settings.google_calendar_id else "Simulation Calendar"

    def _mask_calendar_id(self, calendar_id: Optional[str]) -> Optional[str]:
        if not calendar_id:
            return None
        if len(calendar_id) <= 10:
            return calendar_id
        return "{}...{}".format(calendar_id[:4], calendar_id[-4:])

    def _test_mode_available(self) -> bool:
        return bool(settings.google_real_integration_enabled and not settings.google_mock_mode and settings.google_calendar_id)

    def get_mode_status(self, requested_mode: Optional[Literal["simulation", "test"]] = None) -> GoogleModeStatus:
        requested = requested_mode or settings.google_test_mode_default
        live_writes = requested == "test" and self._test_mode_available()
        calendar_summary = self._calendar_summary()
        if live_writes:
            try:
                calendar_summary = self.gateway.get_calendar_metadata().summary
            except GoogleAdapterException:
                calendar_summary = self._calendar_summary()
        warning = (
            "Test mode writes to the real configured Google test calendar."
            if requested == "test"
            else "Simulation mode uses fake data and does not change Google Calendar."
        )
        if requested == "test" and not self._test_mode_available():
            warning = "Test mode was requested, but the real Google test calendar is not fully configured yet."
        return GoogleModeStatus(
            mode="test" if live_writes else "simulation",
            requested_mode=requested,
            live_calendar_writes=live_writes,
            test_mode_available=self._test_mode_available(),
            calendar_id=self._calendar_id(),
            calendar_id_masked=self._mask_calendar_id(self._calendar_id()),
            calendar_summary=calendar_summary,
            warning=warning,
            runtime_flags={
                "APPOINTMENT_AGENT_GOOGLE_MOCK_MODE": settings.google_mock_mode,
                "GOOGLE_REAL_INTEGRATION_ENABLED": settings.google_real_integration_enabled,
                "GOOGLE_CONTACTS_ENABLED": settings.google_contacts_enabled,
                "GOOGLE_TEST_MODE_DEFAULT": settings.google_test_mode_default,
            },
        )

    def prepare_demo_calendar(self, request: DemoCalendarPrepareRequest) -> DemoCalendarPrepareResult:
        logger.info(
            "google_demo_calendar_action_started mode=%s timeframe=%s action=%s vertical=%s count=%s target_calendar=%s",
            request.mode,
            request.timeframe,
            request.action,
            request.vertical,
            request.count,
            self._mask_calendar_id(self._calendar_id()),
        )
        status = self.get_mode_status(request.mode)
        if request.mode == "test" and not status.test_mode_available:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="prepare_demo_calendar",
                    error_category=ErrorCategory.VALIDATION,
                    message="Test mode is not available because the real Google configuration is incomplete.",
                )
            )
        operation_id = "gdemo-{}".format(uuid4().hex[:10])
        window_start, window_end = self._time_window(request.timeframe)
        deleted_count = 0
        items: list[DemoCalendarItem] = []
        preview_only = request.action == "prepare"
        if request.action in {"delete", "reset"}:
            deleted_count = self._delete_demo_events(
                mode=request.mode,
                timeframe=request.timeframe,
                window_start=window_start,
                window_end=window_end,
            )
        if request.action == "prepare":
            items = self._preview_demo_events(
                request=request,
                window_start=window_start,
            )
        elif request.action in {"generate", "reset"}:
            items = self._generate_demo_events(
                operation_id=operation_id,
                request=request,
                window_start=window_start,
                live_writes=status.live_calendar_writes,
            )
        message = self._action_message(
            action=request.action,
            generated_count=len(items),
            deleted_count=deleted_count,
            live_writes=status.live_calendar_writes,
        )
        logger.info(
            "google_demo_calendar_action_finished mode=%s timeframe=%s action=%s vertical=%s generated=%s deleted=%s live_writes=%s",
            status.mode,
            request.timeframe,
            request.action,
            request.vertical,
            len(items),
            deleted_count,
            status.live_calendar_writes,
        )
        return DemoCalendarPrepareResult(
            operation_id=operation_id,
            action=request.action,
            mode=status.mode,
            timeframe=request.timeframe,
            vertical=request.vertical,
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

    def get_live_sync_status(self, request: GoogleLiveSyncRequest) -> GoogleLiveSyncStatus:
        status = self.get_mode_status(request.mode)
        window_start, window_end = self._time_window(request.timeframe)
        checked_at = datetime.now(timezone.utc).isoformat()
        events = self._load_occupancy_events(status=status, window_start=window_start, window_end=window_end)
        return GoogleLiveSyncStatus(
            checked_at_utc=checked_at,
            google_source="live" if status.live_calendar_writes else "simulation",
            mode=status.mode,
            target_calendar_id=status.calendar_id or self._calendar_id(),
            target_calendar_summary=status.calendar_summary or self._calendar_summary(),
            warning=status.warning,
            last_sync_status="ok",
            occupied_count=len(events),
            occupied_events=events,
            monitoring_labels=[
                "google.sync.read.started",
                "google.sync.read.completed",
                "google.source.live" if status.live_calendar_writes else "google.source.simulation",
            ],
        )

    def check_live_conflict(self, request: GoogleConflictCheckRequest) -> GoogleConflictResult:
        status = self.get_mode_status(request.mode)
        checked_at = datetime.now(timezone.utc).isoformat()
        conflicting_events = self._load_conflicts_for_window(
            status=status,
            start_time=request.start_time,
            end_time=request.end_time,
            exclude_provider_reference=request.exclude_provider_reference,
        )
        if conflicting_events:
            return GoogleConflictResult(
                checked_at_utc=checked_at,
                google_source="live" if status.live_calendar_writes else "simulation",
                conflict_detected=True,
                conflict_type="slot_occupied",
                message="Conflict: slot no longer available.",
                provider_reference=request.provider_reference,
                next_actions=["try_alternative_slots", "broaden_window", "escalate_to_human"],
                monitoring_labels=[
                    "calendar.slot.revalidated",
                    "calendar.slot.conflict_detected",
                    "appointment.booking.blocked_by_conflict",
                    "google.conflict.detected",
                ],
                conflicting_events=conflicting_events,
            )
        if request.provider_reference:
            stale = self._provider_reference_stale(status=status, provider_reference=request.provider_reference)
            if stale:
                return GoogleConflictResult(
                    checked_at_utc=checked_at,
                    google_source="live" if status.live_calendar_writes else "simulation",
                    conflict_detected=True,
                    conflict_type="provider_reference_stale",
                    message="Conflict: Google event no longer exists or was changed externally.",
                    provider_reference=request.provider_reference,
                    next_actions=["refresh_booking_state", "retry_search", "escalate_to_human"],
                    monitoring_labels=[
                        "google.provider_reference.stale",
                        "google.conflict.detected",
                    ],
                    conflicting_events=[],
                )
        return GoogleConflictResult(
            checked_at_utc=checked_at,
            google_source="live" if status.live_calendar_writes else "simulation",
            conflict_detected=False,
            message="Live Google check succeeded. No conflict detected.",
            provider_reference=request.provider_reference,
            next_actions=["proceed"],
            monitoring_labels=[
                "google.sync.read.started",
                "google.sync.read.completed",
                "calendar.slot.revalidated",
            ],
            conflicting_events=[],
        )

    def get_contact_linking_preview(self) -> ContactLinkingPreview:
        return ContactLinkingPreview(
            workspace_state="Current testing uses the personal Google workspace. Future production use should move to a LEKAB-controlled workspace.",
            current_workspace_owner="Personal Google workspace for controlled demos",
            future_workspace_target="LEKAB Google workspace with controlled calendar and contact ownership",
            generated_appointments_rule="Generated demo appointments already know the demo customer, so the system can show name, mobile number, and whether SMS/RCS would be possible.",
            manual_appointments_rule="Manual Google Calendar entries can be displayed, but they need attendee, title, email, or description hints before the system can try to link them to a contact.",
            contact_lookup_sources=[
                "Local demo contact state for generated appointments",
                "Google People API search path for future workspace lookup",
                "Attendee email or description hints for manual entries",
            ],
            contact_fields=["display_name", "mobile_number", "email", "contact_source", "link_state"],
            fallback_states=[
                "linked_with_mobile",
                "linked_without_mobile",
                "not_linked_manual_entry",
                "people_lookup_not_enabled_yet",
            ],
            example_links=[
                {
                    "case": "Generated appointment",
                    "result": "linked_with_mobile",
                    "what_it_means": "The system already knows the demo person and can show that SMS/RCS would be possible.",
                },
                {
                    "case": "Manual calendar entry with attendee email",
                    "result": "linked_without_mobile",
                    "what_it_means": "The system can identify a person, but not every contact has a mobile number yet.",
                },
                {
                    "case": "Manual entry with no useful hints",
                    "result": "not_linked_manual_entry",
                    "what_it_means": "The system can show the appointment, but it cannot safely start a message flow.",
                },
            ],
        )

    def _time_window(self, timeframe: Literal["day", "week", "month"]) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc).astimezone()
        start_of_day = datetime.combine(now.date(), time(hour=8, minute=0), tzinfo=now.tzinfo)
        if timeframe == "day":
            return start_of_day, start_of_day + timedelta(days=1)
        if timeframe == "week":
            weekday_start = start_of_day - timedelta(days=start_of_day.weekday())
            return weekday_start, weekday_start + timedelta(days=7)
        month_start = start_of_day.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        return month_start, next_month

    def _generate_demo_events(
        self,
        *,
        operation_id: str,
        request: DemoCalendarPrepareRequest,
        window_start: datetime,
        live_writes: bool,
    ) -> list[DemoCalendarItem]:
        items: list[DemoCalendarItem] = []
        spacing = {"day": 2, "week": 1, "month": 3}[request.timeframe]
        title_blueprints = self._title_blueprints_for_vertical(request.vertical)
        customer_blueprints = self._customer_blueprints_for_vertical(request.vertical)
        for index in range(request.count):
            blueprint = title_blueprints[index % len(title_blueprints)]
            customer = customer_blueprints[index % len(customer_blueprints)]
            slot_start = self._slot_start(window_start, request.timeframe, index, spacing)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo-book-{}".format(uuid4().hex[:8])
            customer_name = customer["name"] if request.include_customer_name else "Demo Customer"
            title = blueprint["title"]
            description = self._build_description(
                blueprint=blueprint,
                customer=customer,
                booking_reference=booking_reference,
                include_description=request.include_description,
            )
            provider_reference = "simulation-{}".format(booking_reference)
            details: dict[str, Any] = {
                "appointment_type": blueprint["type"],
                "purpose": blueprint["purpose"],
                "description": blueprint.get("description", ""),
                "location": blueprint["location"] if request.include_location else "",
                "contact_lookup_state": "linked_with_mobile" if customer["mobile"] else "linked_without_mobile",
                "manual_entry_rule": "Manual entries need title, attendee, or description hints before contact linking can happen.",
                "vertical": request.vertical,
                "category": blueprint.get("category", request.vertical),
                "scenario_label": blueprint.get("scenario_label", request.vertical),
                "customer_prompt": blueprint.get("customer_prompt", ""),
                "reminder_text": blueprint.get("reminder_text", ""),
                "follow_up_action": blueprint.get("follow_up_action", ""),
                "monitoring_label": blueprint.get("monitoring_label", ""),
                "customer_context": customer.get("context", ""),
            }
            if live_writes:
                event_result = self.gateway.create_demo_event(
                    title=title,
                    description=description,
                    location=blueprint["location"] if request.include_location else None,
                    start_time=slot_start,
                    end_time=slot_end,
                    metadata={
                        "appointment_agent_demo": "true",
                        "appointment_agent_release": settings.app_version,
                        "appointment_agent_booking_reference": booking_reference,
                        "appointment_agent_customer_name": customer_name,
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
                timeframe=request.timeframe,
                calendar_id=self._calendar_id(),
                event_id=event_id,
                booking_reference=booking_reference,
                title=title,
                customer_name=customer_name,
                mobile_number=customer["mobile"] or None,
                start_time_utc=slot_start.astimezone(timezone.utc).replace(tzinfo=None),
                end_time_utc=slot_end.astimezone(timezone.utc).replace(tzinfo=None),
                timezone=settings.google_default_timezone,
                provider_reference=provider_reference,
                details=details,
            )
            items.append(
                DemoCalendarItem(
                    booking_reference=booking_reference,
                    provider_reference=provider_reference,
                    title=title,
                    customer_name=customer_name,
                    mobile_number=customer["mobile"] or None,
                    email=customer["email"] or None,
                    start_time=slot_start.isoformat(),
                    end_time=slot_end.isoformat(),
                    timeframe=request.timeframe,
                    mode=request.mode,
                    live_written=live_writes,
                    link_state=details["contact_lookup_state"],
                    description_marker=DEMO_MARKER_PREFIX,
                    details=details,
                )
            )
        return items

    def _preview_demo_events(
        self,
        *,
        request: DemoCalendarPrepareRequest,
        window_start: datetime,
    ) -> list[DemoCalendarItem]:
        items: list[DemoCalendarItem] = []
        spacing = {"day": 2, "week": 1, "month": 3}[request.timeframe]
        title_blueprints = self._title_blueprints_for_vertical(request.vertical)
        customer_blueprints = self._customer_blueprints_for_vertical(request.vertical)
        preview_count = min(request.count, 5)
        for index in range(preview_count):
            blueprint = title_blueprints[index % len(title_blueprints)]
            customer = customer_blueprints[index % len(customer_blueprints)]
            slot_start = self._slot_start(window_start, request.timeframe, index, spacing)
            slot_end = slot_start + timedelta(minutes=45)
            booking_reference = "gdemo-preview-{}".format(uuid4().hex[:8])
            customer_name = customer["name"] if request.include_customer_name else "Demo Customer"
            items.append(
                DemoCalendarItem(
                    booking_reference=booking_reference,
                    provider_reference="preview-{}".format(booking_reference),
                    title=blueprint["title"],
                    customer_name=customer_name,
                    mobile_number=customer["mobile"] or None,
                    email=customer["email"] or None,
                    start_time=slot_start.isoformat(),
                    end_time=slot_end.isoformat(),
                    timeframe=request.timeframe,
                    mode=request.mode,
                    live_written=False,
                    link_state="preview_only",
                    description_marker=DEMO_MARKER_PREFIX,
                    details={
                        "appointment_type": blueprint["type"],
                        "purpose": blueprint["purpose"],
                        "description": blueprint.get("description", ""),
                        "location": blueprint["location"] if request.include_location else "",
                        "vertical": request.vertical,
                        "category": blueprint.get("category", request.vertical),
                        "scenario_label": blueprint.get("scenario_label", request.vertical),
                        "customer_prompt": blueprint.get("customer_prompt", ""),
                        "reminder_text": blueprint.get("reminder_text", ""),
                        "follow_up_action": blueprint.get("follow_up_action", ""),
                        "monitoring_label": blueprint.get("monitoring_label", ""),
                        "customer_context": customer.get("context", ""),
                        "preview_only": "true",
                    },
                )
            )
        return items

    def _load_occupancy_events(
        self,
        *,
        status: GoogleModeStatus,
        window_start: datetime,
        window_end: datetime,
    ) -> list[LiveSyncEventSummary]:
        if status.live_calendar_writes:
            events = self.gateway.list_events_range(window_start, window_end)
            summaries: list[LiveSyncEventSummary] = []
            for event in events[:20]:
                start_time = ((event.get("start") or {}).get("dateTime")) or ((event.get("start") or {}).get("date")) or ""
                end_time = ((event.get("end") or {}).get("dateTime")) or ((event.get("end") or {}).get("date")) or ""
                private = ((event.get("extendedProperties") or {}).get("private")) or {}
                summaries.append(
                    LiveSyncEventSummary(
                        provider_reference=event.get("id") or "unknown-event",
                        title=event.get("summary") or "Google Calendar Event",
                        start_time=start_time,
                        end_time=end_time,
                        source="live",
                        is_demo_generated=private.get("appointment_agent_demo") == "true" or DEMO_MARKER_PREFIX in (event.get("description") or ""),
                    )
                )
            return summaries
        local_records = self.demo_events.list_active(self._calendar_id())
        summaries = []
        for record in local_records[:20]:
            summaries.append(
                LiveSyncEventSummary(
                    provider_reference=record.provider_reference or record.event_id or record.booking_reference,
                    title=record.title,
                    start_time=record.start_time_utc.isoformat(),
                    end_time=record.end_time_utc.isoformat(),
                    source="simulation",
                    is_demo_generated=record.is_demo_generated,
                )
            )
        return summaries

    def _load_conflicts_for_window(
        self,
        *,
        status: GoogleModeStatus,
        start_time: datetime,
        end_time: datetime,
        exclude_provider_reference: Optional[str],
    ) -> list[LiveSyncEventSummary]:
        events = self._load_occupancy_events(status=status, window_start=start_time, window_end=end_time)
        conflicts: list[LiveSyncEventSummary] = []
        for event in events:
            if exclude_provider_reference and event.provider_reference == exclude_provider_reference:
                continue
            event_start = datetime.fromisoformat(event.start_time.replace("Z", "+00:00")) if event.start_time else None
            event_end = datetime.fromisoformat(event.end_time.replace("Z", "+00:00")) if event.end_time else None
            if event_start and event_end and event_start < end_time and event_end > start_time:
                conflicts.append(event)
        return conflicts

    def _provider_reference_stale(self, *, status: GoogleModeStatus, provider_reference: str) -> bool:
        if status.live_calendar_writes:
            return self.gateway.get_event(provider_reference) is None
        local_records = self.demo_events.list_active(self._calendar_id())
        return not any((record.provider_reference or record.event_id) == provider_reference for record in local_records)

    def _title_blueprints_for_vertical(self, vertical: str) -> list[dict[str, str]]:
        if vertical == "general":
            return GENERAL_TITLE_BLUEPRINTS
        return VERTICAL_TITLE_BLUEPRINTS.get(vertical, GENERAL_TITLE_BLUEPRINTS)

    def _customer_blueprints_for_vertical(self, vertical: str) -> list[dict[str, str]]:
        return VERTICAL_CUSTOMER_BLUEPRINTS.get(vertical, CUSTOMER_BLUEPRINTS)

    def _delete_demo_events(self, *, mode: str, timeframe: str, window_start: datetime, window_end: datetime) -> int:
        local_records = self.demo_events.list_active(self._calendar_id(), timeframe)
        deleted_booking_refs: list[str] = []
        if mode == "test":
            google_events = {
                event.get("id"): event for event in self.gateway.list_demo_events(window_start, window_end)
            }
            for record in local_records:
                if not record.is_demo_generated or record.is_deleted:
                    continue
                event_id = record.event_id
                if event_id and event_id in google_events:
                    self.gateway.delete_event(event_id)
                    deleted_booking_refs.append(record.booking_reference)
        else:
            deleted_booking_refs = [
                record.booking_reference for record in local_records if record.is_demo_generated and not record.is_deleted
            ]
        self.demo_events.mark_deleted(deleted_booking_refs)
        return len(deleted_booking_refs)

    def _action_message(self, *, action: str, generated_count: int, deleted_count: int, live_writes: bool) -> str:
        if action == "prepare":
            return "Prepared {} demo appointments as a preview. No calendar entries were written.".format(generated_count)
        if action == "generate":
            mode_note = " in the Google test calendar" if live_writes else " in simulation mode"
            return "Created {} demo appointments{}.".format(generated_count, mode_note)
        if action == "delete":
            return "Deleted {} demo appointments.".format(deleted_count)
        if action == "reset":
            mode_note = " in the Google test calendar" if live_writes else " in simulation mode"
            return "Reset demo calendar state. Deleted {} and created {} demo appointments{}.".format(
                deleted_count,
                generated_count,
                mode_note,
            )
        return "Google demo action finished."

    def _slot_start(self, window_start: datetime, timeframe: str, index: int, spacing: int) -> datetime:
        if timeframe == "day":
            return window_start + timedelta(hours=1 + (index * spacing))
        if timeframe == "week":
            day_offset = index % 5
            hour_offset = 9 if index % 2 == 0 else 14
            return window_start + timedelta(days=day_offset, hours=hour_offset)
        day_offset = (index * spacing) % 24
        hour_offset = 9 if index % 2 == 0 else 15
        return window_start + timedelta(days=day_offset, hours=hour_offset)

    def _build_description(self, *, blueprint: dict[str, str], customer: dict[str, str], booking_reference: str, include_description: bool) -> str:
        lines = [
            DEMO_MARKER_PREFIX,
            "Booking reference: {}".format(booking_reference),
            "Demo customer: {}".format(customer["name"]),
            "Purpose: {}".format(blueprint["purpose"]),
        ]
        if customer["mobile"]:
            lines.append("Mobile available for SMS/RCS demo follow-up.")
        else:
            lines.append("No mobile number available. Show fallback state in demo.")
        if not include_description:
            return lines[0]
        return "\n".join(lines)
