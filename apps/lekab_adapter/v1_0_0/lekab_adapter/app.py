from typing import Union

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from appointment_agent_shared.contracts import CallbackPayload, LekabDispatchCommand
from appointment_agent_shared.db import get_session

from .service import LekabAdapterService

router = APIRouter(prefix="/api/lekab/v1.0.0", tags=["lekab-adapter-v1.0.0"])


def get_service(session: Session = Depends(get_session)) -> LekabAdapterService:
    return LekabAdapterService(session)


@router.get("/help")
def help_view() -> dict[str, object]:
    return {"module": "lekab_adapter", "version": "v1.0.0"}


@router.post("/auth/token")
def auth_token(service: LekabAdapterService = Depends(get_service)) -> dict[str, str]:
    return service.fetch_token()


@router.post("/dispatch")
def dispatch(command: LekabDispatchCommand, service: LekabAdapterService = Depends(get_service)) -> dict[str, str]:
    return service.dispatch_workflow(command)


@router.post("/callbacks")
def callback(payload: CallbackPayload, service: LekabAdapterService = Depends(get_service)) -> dict[str, Union[str, bool]]:
    return service.ingest_callback(payload)
