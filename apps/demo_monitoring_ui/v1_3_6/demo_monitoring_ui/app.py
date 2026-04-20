from pathlib import Path

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import HTMLResponse

from .payloads import build_v136_payload

router = APIRouter(tags=["reminder-scheduler-ui-v1.3.6"])
app = FastAPI(title="Appointment Agent Reminder Scheduler v1.3.6")

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.3.6")


def _demo_config(lang: str) -> dict[str, object]:
    payload = build_v136_payload(lang=lang)
    return {
        "version": "v1.3.6",
        "enabled": True,
        "silence_threshold_ms": 1300,
        "reminder_offsets_minutes": [1440, 120, 30],
        "primary_channel": "rcs_sms",
        "fallback_channels": ["email"],
        "google_calendar_id": "appointment-agent-test-calendar",
        "appointment_type": payload["appointment_details"]["metrics"][1]["value"],
        "quiet_hours": "20:00-08:00",
        "result_retention_days": 30,
    }


@router.get("/ui/reminder-scheduler/v1.3.6")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/reminder-ui/v1.3.6/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v136_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.6",
        "pages": [
            "appointment_source",
            "google_linkage",
            "appointment_details",
            "reminder_policy",
            "reminder_preview",
            "reminder_jobs",
            "runtime_health",
            "help",
        ],
        "help_links": payload["help_links"],
        "guided_demo_features": [
            "appointment_source",
            "google_linkage",
            "appointment_details",
            "reminder_policy",
            "reminder_preview",
            "reminder_jobs",
            "runtime_health_visibility",
            "three_demo_stories",
            "simple_language",
        ],
        "setup_features": [
            "silence_threshold_ms",
            "reminder_offsets_minutes",
            "google_calendar_id",
            "appointment_type",
            "quiet_hours",
            "channel_fallback",
            "job_status_visibility",
            "operator_summary",
        ],
        "docs_highlights": payload["docs_highlights"],
        "design_baseline": "Incident-style combined reminder cockpit",
    }


@router.get("/api/reminder-ui/v1.3.6/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v136_payload(lang="de" if lang == "de" else "en")


@router.get("/api/reminder-ui/v1.3.6/config")
def config_view(lang: str = Query(default="en")) -> dict:
    return _demo_config(lang="de" if lang == "de" else "en")


@router.get("/api/reminder-ui/v1.3.6/config/preview")
def config_preview(lang: str = Query(default="en")) -> dict:
    payload = build_v136_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.6",
        "appointment_source": payload["appointment_source"],
        "google_linkage": payload["google_linkage"],
        "appointment_details": payload["appointment_details"],
        "reminder_policy": payload["reminder_policy"],
        "reminder_preview": payload["reminder_preview"],
        "reminder_jobs": payload["reminder_jobs"],
        "runtime_health": payload["runtime_health"],
        "demo_stories": payload["demo_stories"],
        "operator_summary": payload["operator_summary"],
    }


@router.get("/api/reminder-ui/v1.3.6/results")
def results_view(lang: str = Query(default="en")) -> dict:
    payload = build_v136_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.6",
        "results": payload["reminder_jobs"]["jobs"],
        "status_overview": payload["status_overview"],
        "result_overview": payload["status_overview"],
    }


@router.get("/api/reminder-ui/v1.3.6/jobs")
def jobs_view(lang: str = Query(default="en")) -> dict:
    return results_view(lang=lang)


@router.get("/api/reminder-ui/v1.3.6/health")
def health_view() -> dict:
    payload = build_v136_payload(lang="en")
    return {
        "status": "ok",
        "version": "v1.3.6",
        "db_status": "ok",
        "worker_status": "ready",
        "scheduler_enabled": True,
        "reminder_ready": True,
        "pages": [page["id"] for page in payload["pages"]],
        "runtime_health": payload["runtime_health"],
    }


app.include_router(router)
