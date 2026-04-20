from __future__ import annotations

from uuid import uuid4
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from appointment_agent_shared.config import settings
from appointment_agent_shared.db import get_session

from .service import LekabMessagingSettingsService

router = APIRouter(prefix="/api/lekab/v1.2.1-patch4", tags=["lekab-adapter-v1.2.1-patch4"])


class SaveRcsSettingsRequest(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


def get_service(session: Session = Depends(get_session)) -> LekabMessagingSettingsService:
    return LekabMessagingSettingsService(session, mock_mode=settings.lekab_mock_mode)


def _resolve_trace_id(request: Request) -> str:
    """Return a stable trace id for one operator action.

    The UI can pass its own trace id via header, but the backend should still
    produce one when the operator or a test client does not provide it. This
    keeps every log line and every response correlatable in Docker logs.
    """

    return request.headers.get("x-trace-id") or f"lekab-rcs-{uuid4().hex[:16]}"


@router.get("/help")
def help_view() -> dict[str, Any]:
    return {
        "module": "lekab_adapter",
        "version": "v1.2.1-patch4",
        "adapter_features": [
            "rcs_settings_page_backend",
            "persistent_config_save",
            "masked_secret_handling",
            "readiness_validation",
            "test_connection_action",
            "webhook_callback_fetch_action",
            "communication_history_monitor",
            "expanded_parameter_explanations",
            "verbose_connection_logging_toggle",
            "last_connection_test_diagnostics",
        ],
    }


@router.get("/settings/rcs")
def get_rcs_settings(
    request: Request,
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.get_rcs_settings(trace_id=_resolve_trace_id(request))


@router.post("/settings/rcs")
def save_rcs_settings(
    http_request: Request,
    payload: SaveRcsSettingsRequest,
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.save_rcs_settings(payload.values, trace_id=_resolve_trace_id(http_request))


@router.post("/settings/rcs/validate")
def validate_rcs_settings(
    request: Request,
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.validate_rcs_settings(trace_id=_resolve_trace_id(request))


@router.post("/settings/rcs/test-connection")
def test_rcs_connection(
    request: Request,
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.test_rcs_connection(trace_id=_resolve_trace_id(request))


@router.post("/settings/rcs/fetch-latest-callback")
def fetch_latest_callback(
    request: Request,
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.fetch_latest_callback(trace_id=_resolve_trace_id(request))


@router.get("/monitor")
def get_monitor_payload(
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.build_monitor_payload()
