from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_v136_patch1_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.3.6-patch1"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html(*, initial_page: str = "dashboard", page_title: str = "Appointment Agent Cockpit") -> str:
    # Keep the served HTML explicit about the integrated module versions.
    # We still normalize the embedded constants here so older checked-out
    # templates cannot accidentally point the combined cockpit back to an
    # earlier adapter line.
    html = (
        HTML_PATH.read_text(encoding="utf-8")
        .replace("__VERSION__", "v1.3.6-patch1")
        .replace("__INITIAL_PAGE__", initial_page)
        .replace("__PAGE_TITLE__", page_title)
    )
    html = html.replace('const GOOGLE_API_VERSION = "v1.1.0-patch8b";', 'const GOOGLE_API_VERSION = "v1.3.6";')
    html = html.replace('const LEKAB_API_VERSION = "v1.2.1";', 'const LEKAB_API_VERSION = "v1.2.1-patch4";')
    return html


@router.get("/ui/demo-monitoring/v1.3.6-patch1")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/ui/reminder-cockpit/v1.3.7")
def reminder_cockpit_view() -> HTMLResponse:
    return HTMLResponse(
        _render_html(initial_page="appointment-reminders", page_title="Reminder Cockpit")
    )


@router.get("/api/demo-monitoring/v1.3.6-patch1/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v136_patch1_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.3.6-patch1",
        "pages": [page["id"] for page in payload["pages"]],
        "themes": ["day", "night"],
        "settings_features": [
            "settings_to_rcs_header_navigation",
            "persistent_rcs_config_save_and_reload",
            "masked_secret_fields",
            "readiness_validation",
            "test_connection_button",
            "day_mode_high_contrast_buttons",
        ],
        "demo_features": [
            "booking_story",
            "reschedule_story",
            "cancel_story",
            "callback_story",
            "slot_hold_story",
            "combined_google_to_reminder_demo",
            "embedded_v1_3_6_reminder_surface",
        ],
        "documentation_features": [
            "separate_release_notes",
            "platform_architecture_explanation",
            "parameter_explanations_with_examples",
            "simple_language_for_new_colleagues",
        ],
        "platform_features": [
            "platform_story_cards",
            "service_bus_explainer",
            "demo_storyboard_cards",
            "business_value_clarity",
            "google_to_reminder_bridge_page",
        ],
        "integrated_demo_features": [
            "appointment_source_visibility",
            "google_linkage_visibility",
            "reminder_policy_visibility",
            "reminder_preview_visibility",
            "reminder_jobs_visibility",
            "runtime_health_visibility",
            "open_full_reminder_cockpit_link",
            "standalone_reminder_cockpit_route",
        ],
        "design_baseline": "Incident Demo UI based on v1.2.1-patch4 with integrated v1.3.6 reminder menu",
    }


@router.get("/api/demo-monitoring/v1.3.6-patch1/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v136_patch1_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
