from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_v138_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.3.8"])

HTML_PATH = (
    Path(__file__).resolve().parents[2]
    / "v1_3_6_patch1"
    / "demo_monitoring_ui"
    / "static"
    / "cockpit.html"
)


def _render_html(*, initial_page: str = "dashboard", page_title: str = "Appointment Agent Cockpit") -> str:
    html = (
        HTML_PATH.read_text(encoding="utf-8")
        .replace("__VERSION__", "v1.3.8")
        .replace("__INITIAL_PAGE__", initial_page)
        .replace("__PAGE_TITLE__", page_title)
    )
    html = html.replace('const GOOGLE_API_VERSION = "v1.1.0-patch8b";', 'const GOOGLE_API_VERSION = "v1.3.6";')
    html = html.replace('const LEKAB_API_VERSION = "v1.2.1-patch4";', 'const LEKAB_API_VERSION = "v1.3.8";')
    return html


@router.get("/ui/demo-monitoring/v1.3.8")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/ui/reminder-cockpit/v1.3.8")
def reminder_cockpit_view() -> HTMLResponse:
    return HTMLResponse(_render_html(initial_page="appointment-reminders", page_title="Reminder Cockpit"))


@router.get("/api/demo-monitoring/v1.3.8/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v138_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.3.8",
        "pages": [page["id"] for page in payload["pages"]],
        "integrated_features": [
            "reply_to_action_engine_visibility",
            "message_monitor_action_preview",
            "standalone_reminder_cockpit_route",
            "combined_google_to_reminder_demo",
            "communication_history_filters",
        ],
        "design_baseline": "Incident Demo UI based on v1.3.6-patch1 with v1.3.8 reply-to-action visibility",
    }


@router.get("/api/demo-monitoring/v1.3.8/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v138_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
