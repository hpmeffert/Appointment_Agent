import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session
from appointment_agent_shared.errors import ProviderError

from google_adapter.v1_1_0_patch1.google_adapter.service import (
    DemoCalendarPrepareRequest,
    GoogleAdapterException,
    GoogleAdapterServiceV110Patch1,
    GoogleConflictCheckRequest,
    GoogleLiveSyncRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google/v1.1.0-patch3", tags=["google-adapter-v1.1.0-patch3"])


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterServiceV110Patch1:
    return GoogleAdapterServiceV110Patch1(session)


def _raise_provider_error(error: ProviderError) -> None:
    raise HTTPException(status_code=400, detail=error.model_dump(mode="json"))


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "google_adapter",
        "version": "v1.1.0-patch3",
        "features": [
            "live_sync_status",
            "live_conflict_detection",
            "provider_reference_stale_detection",
            "safe_demo_calendar_actions",
        ],
    }


@router.get("/mode")
def mode_status(
    requested_mode: Optional[str] = Query(default=None),
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    normalized_mode = "test" if requested_mode == "test" else "simulation"
    return service.get_mode_status(normalized_mode).model_dump(mode="json")


@router.post("/demo-calendar/prepare")
def prepare_demo_calendar(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        return service.prepare_demo_calendar(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/prepare-preview")
def prepare_demo_preview(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "prepare"})
        return service.prepare_demo_calendar(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/generate")
def generate_demo_appointments(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "generate"})
        return service.prepare_demo_calendar(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/delete")
def delete_demo_appointments(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "delete"})
        return service.prepare_demo_calendar(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/reset")
def reset_demo_appointments(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        effective_request = request.model_copy(update={"action": "reset"})
        return service.prepare_demo_calendar(effective_request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/live-sync/status")
def live_sync_status(
    request: GoogleLiveSyncRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    logger.info("google_live_sync_status_requested mode=%s timeframe=%s", request.mode, request.timeframe)
    try:
        return service.get_live_sync_status(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/live-sync/conflict-check")
def conflict_check(
    request: GoogleConflictCheckRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    logger.info(
        "google_live_conflict_check_requested mode=%s start=%s end=%s provider_reference=%s",
        request.mode,
        request.start_time.isoformat(),
        request.end_time.isoformat(),
        request.provider_reference,
    )
    try:
        return service.check_live_conflict(request).model_dump(mode="json")
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.get("/contact-linking")
def contact_linking(service: GoogleAdapterServiceV110Patch1 = Depends(get_service)) -> dict:
    return service.get_contact_linking_preview().model_dump(mode="json")
