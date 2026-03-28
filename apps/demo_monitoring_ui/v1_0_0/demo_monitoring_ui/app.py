from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from .docs_router import router as docs_router
from .scenarios import build_simulation_payload

router = APIRouter(tags=["demo-monitoring-ui-v1.0.0"])

STATIC_DIR = Path(__file__).resolve().parent / "static"


@router.get("/ui/demo-monitoring/v1.0.0")
def demo_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/api/demo-monitoring/v1.0.0/help")
def help_view() -> dict:
    return {
        "module": "demo_monitoring_ui",
        "version": "v1.0.0",
        "modes": ["demo", "monitoring", "combined"],
        "scenarios": [scenario["id"] for scenario in build_simulation_payload()["scenarios"]],
    }


@router.get("/api/demo-monitoring/v1.0.0/scenarios")
def scenario_payload() -> dict:
    return build_simulation_payload()


router.include_router(docs_router)
