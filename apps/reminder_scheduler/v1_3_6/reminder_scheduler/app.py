from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from appointment_agent_shared.db import Base, engine, get_session

from .demo import build_reminder_linkage_demo_payload
from .service import (
    ReminderPolicyInput,
    ReminderPreviewRequest,
    ReminderRebuildRequest,
    ReminderSchedulerService,
    get_default_service,
)

Base.metadata.create_all(bind=engine)

# The v1.3.6 line keeps the stable reminder API surface from v1.3.5, but
# exposes it under the new release path so operators can test the combined
# Google-to-reminder demonstrator without mixing release URLs.
router = APIRouter(prefix="/api/reminders/v1.3.6", tags=["reminder-scheduler-v1.3.6"])
demo_router = APIRouter(tags=["reminder-scheduler-v1.3.6"])
app = FastAPI(title="Appointment Reminder Scheduler v1.3.6")


def _service(session: Session = Depends(get_session)) -> ReminderSchedulerService:
    return get_default_service(session)


def _validation_error(exc: ValueError) -> None:
    raise HTTPException(status_code=400, detail={"message": str(exc)})


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.6",
        "features": [
            "configurable_reminder_policies",
            "manual_and_auto_distributed_modes",
            "canonical_utc_schedule_calculation",
            "timezone_normalization_and_dst_checks",
            "normalized_appointment_sync_contract",
            "hash_based_change_detection",
            "sync_idempotency_and_reconciliation",
            "preview_of_scheduled_reminders",
            "persistent_appointment_cache",
            "job_planning_and_dispatch_loops",
            "dispatcher_based_delivery_layer",
            "target_validation_before_dispatch",
            "retryable_vs_terminal_delivery_failures",
            "runtime_health_snapshot",
            "last_activity_visibility",
            "release_ready_docs_and_routes",
            "past_reminders_are_skipped_explicitly",
            "cancelled_appointments_cancel_existing_reminders",
            "lifecycle_hardening",
        ],
        "endpoints": [
            "/config",
            "/config/preview",
            "/jobs",
            "/jobs/{job_id}",
            "/jobs/{job_id}/retry",
            "/jobs/{job_id}/cancel",
            "/rebuild",
            "/health",
        ],
    }


@router.get("/health")
def health_view(
    policy_key: str = Query(default="global"),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    payload = service.health(policy_key=policy_key).model_dump(mode="json")
    payload["version"] = "v1.3.6"
    return payload


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
    # Read-only previews are intentionally available via GET for operators and
    # tests that want to inspect the current UTC-normalized schedule without
    # mutating the cache.
    return service.get_config(policy_key=policy_key).model_dump(mode="json")


@router.get("/jobs")
def list_jobs(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    jobs = service.list_jobs(status=status, limit=limit)
    return {
        "version": "v1.3.6",
        "status": status,
        "limit": limit,
        "count": len(jobs),
        "jobs": [job.model_dump(mode="json") for job in jobs],
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str, service: ReminderSchedulerService = Depends(_service)) -> dict[str, object]:
    return service.get_job(job_id).model_dump(mode="json")


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, service: ReminderSchedulerService = Depends(_service)) -> dict[str, object]:
    try:
        return service.retry_job(job_id).model_dump(mode="json")
    except (ValueError, RuntimeError) as exc:
        _validation_error(ValueError(str(exc)))


@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    reason_code: str = Query(default="manual_cancel"),
    service: ReminderSchedulerService = Depends(_service),
) -> dict[str, object]:
    try:
        return service.cancel_job(job_id, reason_code=reason_code).model_dump(mode="json")
    except (ValueError, RuntimeError) as exc:
        _validation_error(ValueError(str(exc)))


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
        "version": "v1.3.6",
        "help_path": "/api/reminders/v1.3.6/help",
        "health_path": "/api/reminders/v1.3.6/health",
    }


@demo_router.get("/linkage/help")
def linkage_help() -> dict[str, object]:
    return {
        "module": "reminder_scheduler_linkage_demo",
        "version": "v1.3.6",
        "features": [
            "google_linked_appointment_source",
            "normalized_appointment_view",
            "reminder_policy_visibility",
            "reminder_preview_generation",
            "reschedule_story",
            "cancel_story",
        ],
        "endpoints": [
            "/linkage/demo",
            "/linkage/appointment-source",
            "/linkage/normalized-appointment",
            "/linkage/reminder-preview",
        ],
    }


@demo_router.get("/linkage/demo")
def linkage_demo(appointment_type: str = Query(default="dentist")) -> dict[str, object]:
    return build_reminder_linkage_demo_payload(appointment_type).model_dump(mode="json")


@demo_router.get("/linkage/appointment-source")
def linkage_appointment_source(appointment_type: str = Query(default="dentist")) -> dict[str, object]:
    payload = build_reminder_linkage_demo_payload(appointment_type)
    return payload.appointment_source.model_dump(mode="json")


@demo_router.get("/linkage/normalized-appointment")
def linkage_normalized_appointment(appointment_type: str = Query(default="dentist")) -> dict[str, object]:
    payload = build_reminder_linkage_demo_payload(appointment_type)
    return payload.normalized_appointment.model_dump(mode="json")


@demo_router.get("/linkage/reminder-preview")
def linkage_reminder_preview(appointment_type: str = Query(default="dentist")) -> dict[str, object]:
    payload = build_reminder_linkage_demo_payload(appointment_type)
    return {
        "version": payload.version,
        "reminder_policy": payload.reminder_policy.model_dump(mode="json"),
        "reminder_validation": payload.reminder_validation,
        "reminder_preview": payload.reminder_preview,
        "reminder_jobs": [job.model_dump(mode="json") for job in payload.reminder_jobs],
    }


# The shared top-level app imports only `router` from each release module.
# We nest the linkage demo router here so the exported router carries both the
# stable reminder API and the v1.3.6 demonstrator linkage endpoints.
router.include_router(demo_router)
app.include_router(router)
