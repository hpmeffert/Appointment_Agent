from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router
from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.scenarios import build_simulation_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.1.0-patch2"])

SOURCE_HTML = (
    Path(__file__).resolve().parents[2]
    / "v1_0_0"
    / "demo_monitoring_ui"
    / "static"
    / "index.html"
)


def _render_patch_html() -> str:
    html = SOURCE_HTML.read_text(encoding="utf-8")
    html = html.replace("const GOOGLE_API_VERSION = \"v1.1.0-patch1\";", "const GOOGLE_API_VERSION = \"v1.1.0-patch2\";")
    html = html.replace("v1.0.0", "v1.1.0-patch2")
    html = html.replace("Release shown: v1.0.4 Patch 2", "Release shown: v1.1.0 Patch 2")
    html = html.replace("Gezeigter Release: v1.0.4 Patch 2", "Gezeigter Release: v1.1.0 Patch 2")
    return html


@router.get("/ui/demo-monitoring/v1.1.0-patch2")
def demo_ui() -> HTMLResponse:
    return HTMLResponse(_render_patch_html())


@router.get("/api/demo-monitoring/v1.1.0-patch2/help")
def help_view(lang: str = Query(default="en")) -> dict:
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.1.0-patch2",
        "modes": [mode["id"] for mode in build_simulation_payload(lang=lang)["modes"]],
        "google_operator_features": [
            "simulation_test_switch",
            "prepare_preview",
            "generate_demo_appointments",
            "delete_demo_appointments",
            "reset_demo_calendar",
            "visible_success_error_feedback",
        ],
        "root_cause_fixed": "Prepare was incorrectly mapped to generate and failed requests did not surface reliable UI feedback.",
    }


@router.get("/api/demo-monitoring/v1.1.0-patch2/scenarios")
def scenario_payload(lang: str = Query(default="en")) -> dict:
    return build_simulation_payload(lang=lang)


router.include_router(docs_router)
