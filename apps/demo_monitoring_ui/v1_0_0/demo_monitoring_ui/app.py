from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from .docs_router import router as docs_router
from .scenarios import build_simulation_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.0.0"])

STATIC_DIR = Path(__file__).resolve().parent / "static"


@router.get("/ui/demo-monitoring/v1.0.0")
def demo_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/api/demo-monitoring/v1.0.0/help")
def help_view(lang: str = Query(default="en")) -> dict:
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.0.0",
        "modes": ["demo", "monitoring", "combined"],
        "scenarios": [scenario["id"] for scenario in build_simulation_payload(lang=lang)["scenarios"]],
    }


@router.get("/api/demo-monitoring/v1.0.0/scenarios")
def scenario_payload(lang: str = Query(default="en")) -> dict:
    return build_simulation_payload(lang=lang)


router.include_router(docs_router)
