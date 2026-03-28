from fastapi import FastAPI
from sqlalchemy import text

from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.app import router as demo_monitoring_router
from demo_monitoring_ui.v1_0_2.demo_monitoring_ui.app import router as demo_monitoring_router_v102
from demo_monitoring_ui.v1_0_4_patch1.demo_monitoring_ui.app import router as demo_monitoring_router_v104_patch1
from demo_monitoring_ui.v1_0_4_patch2.demo_monitoring_ui.app import router as demo_monitoring_router_v104_patch2
from appointment_orchestrator.v1_0_0.appointment_orchestrator.app import router as orchestrator_router
from appointment_orchestrator.v1_0_1.appointment_orchestrator.app import router as orchestrator_router_v101
from google_adapter.v1_0_0.google_adapter.app import router as google_router
from google_adapter.v1_0_1.google_adapter.app import router as google_router_v101
from lekab_adapter.v1_0_0.lekab_adapter.app import router as lekab_router
from microsoft_adapter.v1_0_0.microsoft_adapter.app import router as microsoft_router

from .config import settings
from .db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=f"{settings.app_name} {settings.app_version}")


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "help_path": "/help",
        "health_path": "/health",
        "demo_path": settings.demo_base_path,
        "silence_threshold_ms": settings.silence_threshold_ms,
    }


@app.get("/health")
def health_view() -> dict[str, object]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "version": settings.app_version,
        "default_language": settings.default_language,
        "demo_path": settings.demo_base_path,
    }


@app.get("/help")
def help_view() -> dict[str, object]:
    return {
        "header": f"{settings.app_name} {settings.app_version}",
        "silence_threshold_ms": settings.silence_threshold_ms,
        "demo_path": settings.demo_base_path,
        "docker_start": "docker compose up --build",
        "modules": [
            "lekab_adapter/v1_0_0",
            "demo_monitoring_ui/v1_0_0",
            "demo_monitoring_ui/v1_0_2",
            "demo_monitoring_ui/v1_0_4_patch1",
            "demo_monitoring_ui/v1_0_4_patch2",
            "appointment_orchestrator/v1_0_0",
            "appointment_orchestrator/v1_0_1",
            "google_adapter/v1_0_0",
            "google_adapter/v1_0_1",
            "microsoft_adapter/v1_0_0",
        ],
    }


app.include_router(lekab_router)
app.include_router(demo_monitoring_router)
app.include_router(demo_monitoring_router_v102)
app.include_router(demo_monitoring_router_v104_patch1)
app.include_router(demo_monitoring_router_v104_patch2)
app.include_router(orchestrator_router)
app.include_router(orchestrator_router_v101)
app.include_router(google_router)
app.include_router(google_router_v101)
app.include_router(microsoft_router)
