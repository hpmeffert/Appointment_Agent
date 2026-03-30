from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_patch7_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.1.0-patch7"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.1.0-patch7")


@router.get("/ui/demo-monitoring/v1.1.0-patch7")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/demo-monitoring/v1.1.0-patch7/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_patch7_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.1.0-patch7",
        "pages": [page["id"] for page in payload["pages"]],
        "themes": ["day", "night"],
        "google_demo_control_features": [
            "top_header_menu",
            "dedicated_google_demo_control_page",
            "simulation_test_warning",
            "incident_ui_baseline",
            "date_range_selection",
            "appointment_type_dropdown",
        ],
        "communication_features": [
            "interactive_reply_buttons",
            "interactive_slot_buttons",
            "provider_neutral_message_envelope",
            "monitoring_updates_after_click",
        ],
        "design_baseline": "Incident Demo UI",
    }


@router.get("/api/demo-monitoring/v1.1.0-patch7/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_patch7_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
