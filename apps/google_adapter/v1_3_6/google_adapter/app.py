import logging
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session
from appointment_agent_shared.errors import ProviderError
from address_database.v1_3_9.address_database.service import AddressDatabaseService

from google_adapter.v1_1_0_patch1.google_adapter.service import (
    GoogleAdapterException,
    GoogleConflictCheckRequest,
    GoogleLiveSyncRequest,
)
from google_adapter.v1_1_0_patch6.google_adapter.service import DemoCalendarPatch6Request
from google_adapter.v1_1_0_patch8.google_adapter.service import (
    GoogleAvailabilityCheckRequest,
    GoogleAvailabilitySlotsRequest,
    GoogleBookingCancelRequest,
    GoogleBookingCreateRequest,
    GoogleBookingRescheduleRequest,
)
from google_adapter.v1_1_0_patch8a.google_adapter.service import (
    GoogleSlotHoldCreateRequest,
    GoogleSlotHoldReleaseRequest,
)
from .service import GoogleAdapterServiceV136
from .demo import build_google_linkage_demo_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google/v1.3.6", tags=["google-adapter-v1.3.6"])
demo_router = APIRouter(tags=["google-linkage-demo-v1.3.6"])
app = FastAPI(title="Google Linkage Demo v1.3.6")


class GoogleBookingCreateWithHoldRequest(BaseModel):
    journey_id: str
    hold_id: str
    booking: GoogleBookingCreateRequest


class GoogleBookingRescheduleWithHoldRequest(BaseModel):
    journey_id: str
    hold_id: str
    booking: GoogleBookingRescheduleRequest


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterServiceV136:
    return GoogleAdapterServiceV136(session)


def _raise_provider_error(error: ProviderError) -> None:
    raise HTTPException(status_code=400, detail=error.model_dump(mode="json"))


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "google_adapter",
        "version": "v1.3.6",
        "features": [
            "slot_hold_creation",
            "parallel_booking_protection",
            "hold_expiry_handling",
            "configurable_hold_duration",
            "provider_revalidation_before_commit",
            "interactive_reply_to_booking_flow",
        ],
        "endpoints": [
            "/slot-hold/create",
            "/slot-hold/release",
            "/availability/slots",
            "/availability/check",
            "/booking/create",
            "/booking/cancel",
            "/booking/reschedule",
        ],
    }


@router.get("/mode")
def mode_status(
    requested_mode: Optional[str] = Query(default=None),
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    normalized_mode = "test" if requested_mode == "test" else "simulation"
    return service.get_mode_status(normalized_mode).model_dump(mode="json")


@router.post("/demo-calendar/prepare")
def prepare_demo_calendar(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.prepare_demo_calendar_patch6(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/prepare-preview")
def prepare_demo_preview(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "prepare"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/generate")
def generate_demo_appointments(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "generate"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/delete")
def delete_demo_appointments(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "delete"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/reset")
def reset_demo_appointments(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "reset"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/slot-hold/create")
def slot_hold_create(
    request: GoogleSlotHoldCreateRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.create_slot_hold_patch8a(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/slot-hold/release")
def slot_hold_release(
    request: GoogleSlotHoldReleaseRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.release_slot_hold_patch8a(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/availability/slots")
def availability_slots(
    request: GoogleAvailabilitySlotsRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.get_available_slots_patch8(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/availability/check")
def availability_check(
    request: GoogleAvailabilityCheckRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.check_availability_patch8(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/booking/create")
def booking_create(
    request: GoogleBookingCreateWithHoldRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.create_booking_patch8a(request.booking, journey_id=request.journey_id, hold_id=request.hold_id).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/booking/cancel")
def booking_cancel(
    request: GoogleBookingCancelRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.cancel_booking_patch8(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/booking/reschedule")
def booking_reschedule(
    request: GoogleBookingRescheduleWithHoldRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.reschedule_booking_patch8a(request.booking, journey_id=request.journey_id, hold_id=request.hold_id).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/live-sync/status")
def live_sync_status(
    request: GoogleLiveSyncRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.get_live_sync_status(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/live-sync/conflict-check")
def conflict_check(
    request: GoogleConflictCheckRequest,
    service: GoogleAdapterServiceV136 = Depends(get_service),
) -> dict:
    try:
        return service.check_live_conflict(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.get("/contact-linking")
def contact_linking(service: GoogleAdapterServiceV136 = Depends(get_service)) -> dict:
    return service.get_contact_linking_preview().model_dump(mode="json")


@demo_router.get("/linkage/help")
def linkage_help() -> dict[str, object]:
    return {
        "module": "google_linkage_demo",
        "version": "v1.3.6",
        "features": [
            "appointment_source_visibility",
            "normalized_appointment_view",
            "reschedule_story",
            "cancel_story",
            "reminder_relevant_fields",
            "stable_demo_payloads",
        ],
        "endpoints": [
            "/linkage/demo",
            "/linkage/appointment-source",
            "/linkage/normalized-appointment",
            "/linkage/stories",
        ],
    }


@demo_router.get("/linkage/demo")
def linkage_demo(
    appointment_type: str = Query(default="dentist"),
    address_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    record = AddressDatabaseService(session).get_address(address_id) if address_id else None
    address = record.model_dump(mode="json") if record is not None else None
    return build_google_linkage_demo_payload(appointment_type, selected_address=address).model_dump(mode="json")


@demo_router.get("/linkage/appointment-source")
def linkage_appointment_source(
    appointment_type: str = Query(default="dentist"),
    address_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    record = AddressDatabaseService(session).get_address(address_id) if address_id else None
    address = record.model_dump(mode="json") if record is not None else None
    payload = build_google_linkage_demo_payload(appointment_type, selected_address=address)
    return payload.appointment_source.model_dump(mode="json")


@demo_router.get("/linkage/normalized-appointment")
def linkage_normalized_appointment(
    appointment_type: str = Query(default="dentist"),
    address_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    record = AddressDatabaseService(session).get_address(address_id) if address_id else None
    address = record.model_dump(mode="json") if record is not None else None
    payload = build_google_linkage_demo_payload(appointment_type, selected_address=address)
    return payload.normalized_appointment.model_dump(mode="json")


@demo_router.get("/linkage/stories")
def linkage_stories(
    appointment_type: str = Query(default="dentist"),
    address_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    record = AddressDatabaseService(session).get_address(address_id) if address_id else None
    address = record.model_dump(mode="json") if record is not None else None
    payload = build_google_linkage_demo_payload(appointment_type, selected_address=address)
    return {
        "version": payload.version,
        "stories": [story.model_dump(mode="json") for story in payload.stories],
        "operator_summary": payload.operator_summary,
    }


# The shared top-level app imports only `router` from each release module.
# We nest the demo router here so both the operator API and the linkage demo
# API are available through the single exported router object.
router.include_router(demo_router)
app.include_router(router)
