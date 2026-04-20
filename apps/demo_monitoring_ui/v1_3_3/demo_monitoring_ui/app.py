from pathlib import Path

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import HTMLResponse

from .payloads import build_v133_payload

router = APIRouter(tags=["reminder-scheduler-ui-v1.3.3"])
app = FastAPI(title="Appointment Agent Reminder Scheduler v1.3.3")

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.3.3")


@router.get("/ui/reminder-scheduler/v1.3.3")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/reminder-ui/v1.3.3/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v133_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.3",
        "pages": [page["id"] for page in payload["pages"]],
        "help_links": payload["help_links"],
        "guided_demo_features": [
            "setup_first",
            "three_demo_stories",
            "live_preview",
            "job_visibility",
            "lifecycle_states",
            "sync_strategy",
            "change_detection",
            "idempotency_guard",
            "reconciliation_visibility",
        ],
        "setup_features": [
            "manual_mode",
            "auto_distributed_mode",
            "channel_toggles",
            "validation_preview",
            "inline_explanations",
            "job_lifecycle_summary",
            "sync_window_notes",
        ],
        "docs_highlights": payload["docs_highlights"],
        "design_baseline": "Incident Setup UI",
    }


@router.get("/api/reminder-ui/v1.3.3/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v133_payload(lang="de" if lang == "de" else "en")


@router.get("/api/reminder-ui/v1.3.3/config")
def config_view(lang: str = Query(default="en")) -> dict:
    return build_v133_payload(lang="de" if lang == "de" else "en")["reminder_setup"]


@router.get("/api/reminder-ui/v1.3.3/config/preview")
def config_preview(lang: str = Query(default="en")) -> dict:
    payload = build_v133_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.3",
        "appointment_example": payload["appointment_example"],
        "validation_rules": payload["validation_rules"],
        "demo_stories": payload["demo_stories"],
        "lifecycle_states": payload["lifecycle_states"],
        "sync_awareness": payload["sync_awareness"],
    }


@router.get("/api/reminder-ui/v1.3.3/jobs")
def jobs_view(lang: str = Query(default="en")) -> dict:
    payload = build_v133_payload(lang="de" if lang == "de" else "en")
    jobs = payload["sample_jobs"]
    status_overview = {status: 0 for status in ["planned", "dispatching", "sent", "failed", "skipped", "cancelled"]}
    for job in jobs:
        status_overview[job["status"]] = status_overview.get(job["status"], 0) + 1
    return {
        "version": "v1.3.3",
        "jobs": jobs,
        "status_overview": status_overview,
    }


@router.get("/api/reminder-ui/v1.3.3/rebuild")
def rebuild_view() -> dict:
    return {
        "version": "v1.3.3",
        "success": True,
        "message": "Reminder jobs can be rebuilt from the current policy preview with lifecycle checks, sync reconciliation, and idempotency guards.",
    }


@router.get("/api/reminder-ui/v1.3.3/health")
def health_view() -> dict:
    return {
        "status": "ok",
        "version": "v1.3.3",
        "scheduler_enabled": True,
        "lifecycle_states": ["planned", "dispatching", "sent", "failed", "skipped", "cancelled"],
        "sync_awareness": {
            "adapter_name": "calendar-adapter",
            "sync_window_days": 7,
            "polling_interval_minutes": 30,
            "hash_detection_enabled": True,
            "idempotency_guard": True,
        },
    }


app.include_router(router)
