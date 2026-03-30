from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_patch8a_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.1.0-patch8a"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.1.0-patch8a")


@router.get("/ui/demo-monitoring/v1.1.0-patch8a")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/demo-monitoring/v1.1.0-patch8a/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_patch8a_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.1.0-patch8a",
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
        "google_live_features": [
            "availability_slots",
            "availability_check",
            "real_booking_create_cancel_reschedule",
            "conflict_resolution_alternative_slots",
        ],
        "slot_hold_features": [
            "slot_hold_minutes_visible_in_settings",
            "slot_hold_duration_adjustable",
            "temporary_reservation_explanation",
        ],
        "design_baseline": "Incident Demo UI",
    }


@router.get("/api/demo-monitoring/v1.1.0-patch8a/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_patch8a_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
