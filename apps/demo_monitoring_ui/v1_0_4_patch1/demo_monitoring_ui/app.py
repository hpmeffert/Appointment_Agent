from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router
from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.scenarios import build_simulation_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.0.4-patch1"])

SOURCE_HTML = (
    Path(__file__).resolve().parents[2]
    / "v1_0_0"
    / "demo_monitoring_ui"
    / "static"
    / "index.html"
)


def _render_patch_html() -> str:
    html = SOURCE_HTML.read_text(encoding="utf-8")
    return html.replace("v1.0.0", "v1.0.4-patch1")


@router.get("/ui/demo-monitoring/v1.0.4-patch1")
def demo_ui() -> HTMLResponse:
    return HTMLResponse(_render_patch_html())


@router.get("/api/demo-monitoring/v1.0.4-patch1/help")
def help_view(lang: str = Query(default="en")) -> dict:
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.0.4-patch1",
        "modes": ["demo", "monitoring", "combined"],
        "scenarios": [scenario["id"] for scenario in build_simulation_payload(lang=lang)["scenarios"]],
    }


@router.get("/api/demo-monitoring/v1.0.4-patch1/scenarios")
def scenario_payload(lang: str = Query(default="en")) -> dict:
    return build_simulation_payload(lang=lang)


router.include_router(docs_router)
