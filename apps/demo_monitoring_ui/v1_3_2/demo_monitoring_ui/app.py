from pathlib import Path

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import HTMLResponse

from .payloads import build_v132_payload

router = APIRouter(tags=["reminder-scheduler-ui-v1.3.2"])
app = FastAPI(title="Appointment Agent Reminder Scheduler v1.3.2")

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.3.2")


@router.get("/ui/reminder-scheduler/v1.3.2")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/reminder-ui/v1.3.2/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v132_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.2",
        "pages": [page["id"] for page in payload["pages"]],
        "help_links": payload["help_links"],
        "guided_demo_features": [
            "setup_first",
            "three_demo_stories",
            "live_preview",
            "job_visibility",
            "lifecycle_states",
            "timezone_awareness",
            "dst_guard",
            "near_term_reminders",
        ],
        "setup_features": [
            "manual_mode",
            "auto_distributed_mode",
            "channel_toggles",
            "validation_preview",
            "inline_explanations",
            "job_lifecycle_summary",
            "timezone_notes",
        ],
        "docs_highlights": payload["docs_highlights"],
        "design_baseline": "Incident Setup UI",
    }


@router.get("/api/reminder-ui/v1.3.2/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v132_payload(lang="de" if lang == "de" else "en")


@router.get("/api/reminder-ui/v1.3.2/config")
def config_view(lang: str = Query(default="en")) -> dict:
    return build_v132_payload(lang="de" if lang == "de" else "en")["reminder_setup"]


@router.get("/api/reminder-ui/v1.3.2/config/preview")
def config_preview(lang: str = Query(default="en")) -> dict:
    payload = build_v132_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.2",
        "appointment_example": payload["appointment_example"],
        "validation_rules": payload["validation_rules"],
        "demo_stories": payload["demo_stories"],
        "lifecycle_states": payload["lifecycle_states"],
        "time_awareness": payload["time_awareness"],
    }


@router.get("/api/reminder-ui/v1.3.2/jobs")
def jobs_view(lang: str = Query(default="en")) -> dict:
    payload = build_v132_payload(lang="de" if lang == "de" else "en")
    jobs = payload["sample_jobs"]
    status_overview = {status: 0 for status in ["planned", "dispatching", "sent", "failed", "skipped", "cancelled"]}
    for job in jobs:
        status_overview[job["status"]] = status_overview.get(job["status"], 0) + 1
    return {
        "version": "v1.3.2",
        "jobs": jobs,
        "status_overview": status_overview,
    }


@router.get("/api/reminder-ui/v1.3.2/rebuild")
def rebuild_view() -> dict:
    return {
        "version": "v1.3.2",
        "success": True,
        "message": "Reminder jobs can be rebuilt from the current policy preview with lifecycle state checks and timezone-aware timing.",
    }


@router.get("/api/reminder-ui/v1.3.2/health")
def health_view() -> dict:
    return {
        "status": "ok",
        "version": "v1.3.2",
        "scheduler_enabled": True,
        "lifecycle_states": ["planned", "dispatching", "sent", "failed", "skipped", "cancelled"],
        "time_awareness": {
            "timezone": "Europe/Berlin",
            "dst_guard": True,
            "near_term_window_hours": 24,
        },
    }


app.include_router(router)
