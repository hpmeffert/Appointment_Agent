from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session

from .service import AppointmentOrchestratorServiceV101

router = APIRouter(prefix="/api/orchestrator/v1.0.1", tags=["appointment-orchestrator-v1.0.1"])


def get_service(session: Session = Depends(get_session)) -> AppointmentOrchestratorServiceV101:
    return AppointmentOrchestratorServiceV101(session)


@router.get("/help")
def help_view() -> dict[str, object]:
    return {"module": "appointment_orchestrator", "version": "v1.0.1"}


@router.post("/journeys/start")
def start_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.start_journey(payload)


@router.post("/journeys/plan")
def plan_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.plan_journey(payload)


@router.post("/journeys/select")
def select_slot(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.select_slot(payload)


@router.post("/journeys/confirm")
def confirm_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.confirm_booking(payload)


@router.post("/journeys/remind")
def remind_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.send_reminder(payload)


@router.post("/journeys/reminder-action")
def reminder_action(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.handle_reminder_action(payload)


@router.post("/journeys/cancel")
def cancel_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.cancel_journey(payload)


@router.post("/journeys/reschedule")
def reschedule_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.start_reschedule(payload)


@router.post("/journeys/escalate")
def escalate_journey(payload: dict, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> dict:
    return service.escalate_journey(payload)


@router.get("/journeys/{journey_id}/audit")
def list_audit(journey_id: str, service: AppointmentOrchestratorServiceV101 = Depends(get_service)) -> list[dict]:
    return service.list_audit(journey_id)
