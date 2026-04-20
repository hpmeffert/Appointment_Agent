from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router

from .payloads import build_v121_patch1_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.2.1-patch1"])

HTML_PATH = Path(__file__).resolve().parent / "static" / "cockpit.html"


def _render_html() -> str:
    return (
        HTML_PATH.read_text(encoding="utf-8")
        .replace("__VERSION__", "v1.2.1-patch1")
        .replace('const GOOGLE_API_VERSION = "v1.1.0-patch8b";', 'const GOOGLE_API_VERSION = "v1.2.0";')
        .replace('const LEKAB_API_VERSION = "v1.2.1";', 'const LEKAB_API_VERSION = "v1.2.1-patch1";')
    )


@router.get("/ui/demo-monitoring/v1.2.1-patch1")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html())


@router.get("/api/demo-monitoring/v1.2.1-patch1/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_v121_patch1_payload(lang="de" if lang == "de" else "en")
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.2.1-patch1",
        "pages": [page["id"] for page in payload["pages"]],
        "themes": ["day", "night"],
        "settings_features": [
            "settings_to_rcs_header_navigation",
            "persistent_rcs_config_save_and_reload",
            "masked_secret_fields",
            "readiness_validation",
            "test_connection_button",
        ],
        "design_baseline": "Incident Demo UI",
    }


@router.get("/api/demo-monitoring/v1.2.1-patch1/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_v121_patch1_payload(lang="de" if lang == "de" else "en")


router.include_router(docs_router)
