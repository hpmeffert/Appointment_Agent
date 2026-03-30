import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session
from appointment_agent_shared.errors import ProviderError

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
    GoogleAdapterServiceV110Patch8A,
    GoogleSlotHoldCreateRequest,
    GoogleSlotHoldReleaseRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google/v1.1.0-patch8a", tags=["google-adapter-v1.1.0-patch8a"])


class GoogleBookingCreateWithHoldRequest(BaseModel):
    journey_id: str
    hold_id: str
    booking: GoogleBookingCreateRequest


class GoogleBookingRescheduleWithHoldRequest(BaseModel):
    journey_id: str
    hold_id: str
    booking: GoogleBookingRescheduleRequest


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterServiceV110Patch8A:
    return GoogleAdapterServiceV110Patch8A(session)


def _raise_provider_error(error: ProviderError) -> None:
    raise HTTPException(status_code=400, detail=error.model_dump(mode="json"))


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "google_adapter",
        "version": "v1.1.0-patch8a",
        "features": [
            "slot_hold_creation",
            "parallel_booking_protection",
            "hold_expiry_handling",
            "configurable_hold_duration",
            "provider_revalidation_before_commit",
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
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    normalized_mode = "test" if requested_mode == "test" else "simulation"
    return service.get_mode_status(normalized_mode).model_dump(mode="json")


@router.post("/demo-calendar/prepare")
def prepare_demo_calendar(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.prepare_demo_calendar_patch6(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/prepare-preview")
def prepare_demo_preview(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "prepare"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/generate")
def generate_demo_appointments(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "generate"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/delete")
def delete_demo_appointments(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "delete"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/reset")
def reset_demo_appointments(
    request: DemoCalendarPatch6Request,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "reset"})
        return service.prepare_demo_calendar_patch6(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/slot-hold/create")
def slot_hold_create(
    request: GoogleSlotHoldCreateRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.create_slot_hold_patch8a(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/slot-hold/release")
def slot_hold_release(
    request: GoogleSlotHoldReleaseRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.release_slot_hold_patch8a(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/availability/slots")
def availability_slots(
    request: GoogleAvailabilitySlotsRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.get_available_slots_patch8(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/availability/check")
def availability_check(
    request: GoogleAvailabilityCheckRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.check_availability_patch8(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/booking/create")
def booking_create(
    request: GoogleBookingCreateWithHoldRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.create_booking_patch8a(request.booking, journey_id=request.journey_id, hold_id=request.hold_id).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/booking/cancel")
def booking_cancel(
    request: GoogleBookingCancelRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.cancel_booking_patch8(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/booking/reschedule")
def booking_reschedule(
    request: GoogleBookingRescheduleWithHoldRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.reschedule_booking_patch8a(request.booking, journey_id=request.journey_id, hold_id=request.hold_id).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/live-sync/status")
def live_sync_status(
    request: GoogleLiveSyncRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.get_live_sync_status(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/live-sync/conflict-check")
def conflict_check(
    request: GoogleConflictCheckRequest,
    service: GoogleAdapterServiceV110Patch8A = Depends(get_service),
) -> dict:
    try:
        return service.check_live_conflict(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.get("/contact-linking")
def contact_linking(service: GoogleAdapterServiceV110Patch8A = Depends(get_service)) -> dict:
    return service.get_contact_linking_preview().model_dump(mode="json")
