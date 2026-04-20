from pathlib import Path

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import HTMLResponse

from .payloads import build_v134_payload

router = APIRouter(tags=["reminder-scheduler-ui-v1.3.4"])
app = FastAPI(title="Appointment Agent Reminder Scheduler v1.3.4")

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.3.4")


@router.get("/ui/reminder-scheduler/v1.3.4")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/reminder-ui/v1.3.4/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v134_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "reminder_scheduler",
        "version": "v1.3.4",
        "pages": [page["id"] for page in payload["pages"]],
        "help_links": payload["help_links"],
        "guided_demo_features": [
            "delivery_channels",
            "validation_outcomes",
            "delivery_results",
            "three_demo_stories",
            "fallback_handling",
            "result_visibility",
            "simple_language",
        ],
        "setup_features": [
            "primary_channel",
            "fallback_channels",
            "retry_policy",
            "validate_recipient",
            "validate_channel",
            "message_length_limit",
            "operator_summary",
        ],
        "docs_highlights": payload["docs_highlights"],
        "design_baseline": "Incident Setup UI",
    }


@router.get("/api/reminder-ui/v1.3.4/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v134_payload(lang="de" if lang == "de" else "en")


@router.get("/api/reminder-ui/v1.3.4/config")
def config_view(lang: str = Query(default="en")) -> dict:
    return build_v134_payload(lang="de" if lang == "de" else "en")["delivery_setup"]


@router.get("/api/reminder-ui/v1.3.4/config/preview")
def config_preview(lang: str = Query(default="en")) -> dict:
    payload = build_v134_payload(lang="de" if lang == "de" else "en")
    return {
        "version": "v1.3.4",
        "delivery_example": payload["delivery_example"],
        "validation_rules": payload["validation_rules"],
        "delivery_channels": payload["delivery_channels"],
        "validation_outcomes": payload["validation_outcomes"],
        "delivery_results": payload["delivery_results"],
        "demo_stories": payload["demo_stories"],
        "operator_summary": payload["operator_summary"],
    }


@router.get("/api/reminder-ui/v1.3.4/results")
def results_view(lang: str = Query(default="en")) -> dict:
    payload = build_v134_payload(lang="de" if lang == "de" else "en")
    results = payload["delivery_results"]
    status_overview = {status: 0 for status in ["sent", "fallback_sent", "blocked", "retrying", "failed", "skipped"]}
    for result in results:
        status_overview[result["status"]] = status_overview.get(result["status"], 0) + 1
    return {
        "version": "v1.3.4",
        "results": results,
        "status_overview": status_overview,
        "result_overview": payload["result_overview"],
    }


@router.get("/api/reminder-ui/v1.3.4/jobs")
def jobs_view(lang: str = Query(default="en")) -> dict:
    return results_view(lang=lang)


@router.get("/api/reminder-ui/v1.3.4/health")
def health_view() -> dict:
    return {
        "status": "ok",
        "version": "v1.3.4",
        "scheduler_enabled": True,
        "delivery_ready": True,
        "delivery_states": ["sent", "fallback_sent", "blocked", "retrying", "failed", "skipped"],
        "channels": {
            "rcs_sms": True,
            "email": True,
            "voice": False,
        },
    }


app.include_router(router)
