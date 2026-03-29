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
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google/v1.1.0-patch2", tags=["google-adapter-v1.1.0-patch2"])


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterServiceV110Patch1:
    return GoogleAdapterServiceV110Patch1(session)


def _raise_provider_error(error: ProviderError) -> None:
    raise HTTPException(status_code=400, detail=error.model_dump(mode="json"))


def _run_action(
    *,
    request: DemoCalendarPrepareRequest,
    forced_action: Optional[str],
    service: GoogleAdapterServiceV110Patch1,
) -> dict:
    effective_request = request.model_copy(update={"action": forced_action}) if forced_action else request
    logger.info(
        "google_demo_route_invoked version=v1.1.0-patch2 action=%s mode=%s timeframe=%s vertical=%s count=%s",
        effective_request.action,
        effective_request.mode,
        effective_request.timeframe,
        effective_request.vertical,
        effective_request.count,
    )
    return service.prepare_demo_calendar(effective_request).model_dump(mode="json")


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "google_adapter",
        "version": "v1.1.0-patch2",
        "features": [
            "simulation_test_mode_switch",
            "prepare_preview",
            "generate_demo_appointments",
            "delete_demo_appointments",
            "reset_demo_calendar",
            "manual_entry_contact_strategy",
        ],
        "root_cause_fixed": "The old UI mapped Prepare to Generate and did not show reliable action feedback.",
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
        return _run_action(request=request, forced_action=None, service=service)
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/prepare-preview")
def prepare_demo_preview(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        return _run_action(request=request, forced_action="prepare", service=service)
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/generate")
def generate_demo_appointments(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        return _run_action(request=request, forced_action="generate", service=service)
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/delete")
def delete_demo_appointments(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        return _run_action(request=request, forced_action="delete", service=service)
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.post("/demo-calendar/reset")
def reset_demo_calendar(
    request: DemoCalendarPrepareRequest,
    service: GoogleAdapterServiceV110Patch1 = Depends(get_service),
) -> dict:
    try:
        return _run_action(request=request, forced_action="reset", service=service)
    except GoogleAdapterException as error:
        _raise_provider_error(error.error)


@router.get("/contact-linking")
def contact_linking(service: GoogleAdapterServiceV110Patch1 = Depends(get_service)) -> dict:
    return service.get_contact_linking_preview().model_dump(mode="json")
