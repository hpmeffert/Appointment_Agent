from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_v121_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.2.1"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return (
        HTML_PATH.read_text(encoding="utf-8")
        .replace("__VERSION__", "v1.2.1")
        .replace('const GOOGLE_API_VERSION = "v1.1.0-patch8b";', 'const GOOGLE_API_VERSION = "v1.2.0";')
    )


@router.get("/ui/demo-monitoring/v1.2.1")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/demo-monitoring/v1.2.1/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v121_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.2.1",
        "pages": [page["id"] for page in payload["pages"]],
        "themes": ["day", "night"],
        "communication_features": [
            "message_monitor_page",
            "incident_style_communications_list",
            "incident_style_report_cards",
            "provider_neutral_message_detail",
            "normalized_inbound_outbound_message_traffic",
        ],
        "lekab_features": [
            "rcs_send",
            "sms_send",
            "inbound_message_normalization",
            "status_tracking",
            "addressbook_lookup_direction",
        ],
        "design_baseline": "Incident Demo UI",
    }


@router.get("/api/demo-monitoring/v1.2.1/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v121_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
