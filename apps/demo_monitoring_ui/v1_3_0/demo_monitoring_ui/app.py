from pathlib import Path

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import HTMLResponse

from .payloads import build_v130_payload

router = APIRouter(tags=["reminder-scheduler-ui-v1.3.0"])
app = FastAPI(title="Appointment Agent Reminder Scheduler v1.3.0")

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.3.0")


@router.get("/ui/reminder-scheduler/v1.3.0")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/reminder-ui/v1.3.0/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v130_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.0",
        "pages": [page["id"] for page in payload["pages"]],
        "help_links": payload["help_links"],
        "guided_demo_features": [
            "setup_first",
            "three_demo_stories",
            "live_preview",
            "job_visibility",
        ],
        "setup_features": [
            "manual_mode",
            "auto_distributed_mode",
            "channel_toggles",
            "validation_preview",
            "inline_explanations",
        ],
        "docs_highlights": payload["docs_highlights"],
        "design_baseline": "Incident Setup UI",
    }


@router.get("/api/reminder-ui/v1.3.0/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v130_payload(lang="de" if lang == "de" else "en")


@router.get("/api/reminder-ui/v1.3.0/config")
def config_view(lang: str = Query(default="en")) -> dict:
    return build_v130_payload(lang="de" if lang == "de" else "en")["reminder_setup"]


@router.get("/api/reminder-ui/v1.3.0/config/preview")
def config_preview(lang: str = Query(default="en")) -> dict:
    payload = build_v130_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.0",
        "appointment_example": payload["appointment_example"],
        "validation_rules": payload["validation_rules"],
        "demo_stories": payload["demo_stories"],
    }


@router.get("/api/reminder-ui/v1.3.0/jobs")
def jobs_view(lang: str = Query(default="en")) -> dict:
    payload = build_v130_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.0",
        "jobs": payload["sample_jobs"],
        "status_overview": {
            "planned": 2,
            "due": 1,
            "sent": 0,
            "failed": 0,
        },
    }


@router.get("/api/reminder-ui/v1.3.0/rebuild")
def rebuild_view() -> dict:
    return {
        "version": "v1.3.0",
        "success": True,
        "message": "Reminder jobs can be rebuilt from the current policy preview.",
    }


@router.get("/api/reminder-ui/v1.3.0/health")
def health_view() -> dict:
    return {
        "status": "ok",
        "version": "v1.3.0",
        "scheduler_enabled": True,
    }


app.include_router(router)
