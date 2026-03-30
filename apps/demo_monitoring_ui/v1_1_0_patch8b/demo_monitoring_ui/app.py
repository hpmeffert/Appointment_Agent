from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_patch8b_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.1.0-patch8b"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8").replace("__VERSION__", "v1.1.0-patch8b")


@router.get("/ui/demo-monitoring/v1.1.0-patch8b")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/demo-monitoring/v1.1.0-patch8b/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_patch8b_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.1.0-patch8b",
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
            "end_to_end_booking_flow",
        ],
        "google_live_features": [
            "availability_slots",
            "availability_check",
            "real_booking_create_cancel_reschedule",
            "conflict_resolution_alternative_slots",
            "interactive_live_revalidation_before_booking",
        ],
        "slot_hold_features": [
            "slot_hold_minutes_visible_in_settings",
            "slot_hold_duration_adjustable",
            "temporary_reservation_explanation",
            "interactive_confirm_before_hold_expiry",
        ],
        "design_baseline": "Incident Demo UI",
    }


@router.get("/api/demo-monitoring/v1.1.0-patch8b/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_patch8b_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
