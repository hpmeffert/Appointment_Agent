from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from appointment_agent_shared.db import Base, engine, get_session

from .service import (
    ReminderConfigView,
    ReminderHealthView,
    ReminderPolicyInput,
    ReminderPreviewRequest,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    get_default_service,
)

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/reminders/v1.3.0", tags=["reminder-scheduler-v1.3.0"])
app = FastAPI(title="Appointment Reminder Scheduler v1.3.0")


def _service(session: Session = Depends(get_session)) -> ReminderSchedulerService:
    return get_default_service(session)


def _validation_error(exc: ValueError) -> None:
    raise HTTPException(status_code=400, detail={"message": str(exc)})


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.0",
        "features": [
            "configurable_reminder_policies",
            "manual_and_auto_distributed_modes",
            "preview_of_scheduled_reminders",
            "persistent_appointment_cache",
            "job_planning_and_dispatch_loops",
            "health_and_rebuild_endpoints",
        ],
        "endpoints": [
            "/config",
            "/config/preview",
            "/jobs",
            "/rebuild",
            "/health",
        ],
    }


@router.get("/health")
def health_view(
    policy_key: str = Query(default="global"),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    return service.health(policy_key=policy_key).model_dump(mode="json")


@router.get("/config")
def get_config(
    policy_key: str = Query(default="global"),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    return service.get_config(policy_key=policy_key).model_dump(mode="json")


@router.post("/config")
def save_config(
    request: ReminderPolicyInput,
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    try:
        return service.save_config(request).model_dump(mode="json")
    except ValueError as exc:
        _validation_error(exc)


@router.post("/config/preview")
def preview_config(
    request: ReminderPreviewRequest,
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    try:
        return service.preview(request).model_dump(mode="json")
    except ValueError as exc:
        _validation_error(exc)


@router.get("/config/preview")
def preview_current_config(
    policy_key: str = Query(default="global"),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    # The GET alias keeps the preview accessible for read-only UI flows while
    # the POST endpoint remains available for explicit preview payloads.
    return service.get_config(policy_key=policy_key).model_dump(mode="json")


@router.get("/jobs")
def list_jobs(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    jobs = service.list_jobs(status=status, limit=limit)
    return {
        "version": "v1.3.0",
        "status": status,
        "limit": limit,
        "count": len(jobs),
        "jobs": [job.model_dump(mode="json") for job in jobs],
    }


@router.post("/rebuild")
def rebuild_jobs(
    request: ReminderRebuildRequest,
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    try:
        return service.rebuild(request)
    except ValueError as exc:
        _validation_error(exc)


@router.get("/")
def root_view() -> dict[str, object]:
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.0",
        "help_path": "/api/reminders/v1.3.0/help",
        "health_path": "/api/reminders/v1.3.0/health",
    }


app.include_router(router)
