from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session

from .service import AppointmentOrchestratorService

router = APIRouter(prefix="/api/orchestrator/v1.0.0", tags=["appointment-orchestrator-v1.0.0"])


def get_service(session: Session = Depends(get_session)) -> AppointmentOrchestratorService:
    return AppointmentOrchestratorService(session)


@router.get("/help")
def help_view() -> dict[str, object]:
    return {"module": "appointment_orchestrator", "version": "v1.0.0"}


@router.post("/journeys/start")
def start_journey(payload: dict, service: AppointmentOrchestratorService = Depends(get_service)) -> dict:
    return service.start_journey(payload)


@router.post("/journeys/plan")
def plan_journey(payload: dict, service: AppointmentOrchestratorService = Depends(get_service)) -> dict:
    return service.plan_journey(payload)


@router.post("/journeys/select")
def select_journey_slot(payload: dict, service: AppointmentOrchestratorService = Depends(get_service)) -> dict:
    return service.select_slot(payload)


@router.post("/journeys/confirm")
def confirm_journey(payload: dict, service: AppointmentOrchestratorService = Depends(get_service)) -> dict:
    return service.confirm_booking(payload)


@router.post("/journeys/remind")
def remind_journey(payload: dict, service: AppointmentOrchestratorService = Depends(get_service)) -> dict:
    return service.send_reminder(payload)


@router.post("/journeys/cancel")
def cancel_journey(payload: dict, service: AppointmentOrchestratorService = Depends(get_service)) -> dict:
    return service.cancel_journey(payload)
