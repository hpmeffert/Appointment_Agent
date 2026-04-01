from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
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
            "expanded_parameter_explanations",
        ],
    }


@router.get("/settings/rcs")
def get_rcs_settings(service: LekabMessagingSettingsService = Depends(get_service)) -> dict[str, Any]:
    return service.get_rcs_settings()


@router.post("/settings/rcs")
def save_rcs_settings(
    request: SaveRcsSettingsRequest,
    service: LekabMessagingSettingsService = Depends(get_service),
) -> dict[str, Any]:
    return service.save_rcs_settings(request.values)


@router.post("/settings/rcs/validate")
def validate_rcs_settings(service: LekabMessagingSettingsService = Depends(get_service)) -> dict[str, Any]:
    return service.validate_rcs_settings()


@router.post("/settings/rcs/test-connection")
def test_rcs_connection(service: LekabMessagingSettingsService = Depends(get_service)) -> dict[str, Any]:
    return service.test_rcs_connection()
