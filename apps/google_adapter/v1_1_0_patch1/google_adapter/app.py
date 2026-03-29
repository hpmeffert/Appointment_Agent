from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session
from appointment_agent_shared.errors import ProviderError

from .service import (
    DemoCalendarPrepareRequest,
    GoogleAdapterException,
    GoogleAdapterServiceV110Patch1,
)

router = APIRouter(prefix="/api/google/v1.1.0-patch1", tags=["google-adapter-v1.1.0-patch1"])


def get_service(session: Session = Depends(get_session)) -> GoogleAdapterServiceV110Patch1:
    return GoogleAdapterServiceV110Patch1(session)


def _raise_provider_error(error: ProviderError) -> None:
    status_code = 400
    raise HTTPException(status_code=status_code, detail=error.model_dump(mode="json"))


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "google_adapter",
        "version": "v1.1.0-patch1",
        "features": [
            "simulation_test_mode_switch",
            "demo_calendar_prepare",
            "demo_calendar_cleanup",
            "google_contacts_prep",
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


@router.get("/contact-linking")
def contact_linking(service: GoogleAdapterServiceV110Patch1 = Depends(get_service)) -> dict:
    return service.get_contact_linking_preview().model_dump(mode="json")
