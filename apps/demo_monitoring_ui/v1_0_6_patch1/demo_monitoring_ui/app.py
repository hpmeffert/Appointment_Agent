from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.docs_router import router as docs_router
from demo_monitoring_ui.v1_0_5.demo_monitoring_ui.payloads import build_cockpit_payload

router = APIRouter(tags=["demo-cockpit-v1.0.6-patch1"])

HTML_PATH = (
    Path(__file__).resolve().parents[2]
    / "v1_0_5"
    / "demo_monitoring_ui"
    / "static"
    / "cockpit.html"
)


def _render_html(version: str) -> str:
    html = HTML_PATH.read_text(encoding="utf-8")
    return html.replace("__VERSION__", version).replace("__VERTICALS_ENABLED__", "true")


@router.get("/ui/demo-monitoring/v1.0.6-patch1")
def ui_view() -> HTMLResponse:
    return HTMLResponse(_render_html("v1.0.6-patch1"))


@router.get("/api/demo-monitoring/v1.0.6-patch1/help")
def help_view(lang: str = Query(default="en")) -> dict:
    payload = build_cockpit_payload(version="v1.0.6-patch1", lang="de" if lang == "de" else "en", include_verticals=True)
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.0.6-patch1",
        "pages": [page["id"] for page in payload["pages"]],
        "verticals": [vertical["id"] for vertical in payload["verticals"]],
        "vertical_descriptions": {vertical["id"]: vertical["description"] for vertical in payload["verticals"]},
    }


@router.get("/api/demo-monitoring/v1.0.6-patch1/payload")
def payload_view(lang: str = Query(default="en")) -> dict:
    return build_cockpit_payload(version="v1.0.6-patch1", lang="de" if lang == "de" else "en", include_verticals=True)


router.include_router(docs_router)
