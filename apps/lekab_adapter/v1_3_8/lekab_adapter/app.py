from __future__ import annotations

from typing import Any
from uuid import uuid4
import json
from urllib.parse import parse_qs

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from appointment_agent_shared.config import settings
from appointment_agent_shared.db import SessionLocal, get_session

from .service import LekabReplyActionService

router = APIRouter(tags=["lekab-adapter-v1.3.8"])
versioned_router = APIRouter(prefix="/api/lekab/v1.3.8", tags=["lekab-adapter-v1.3.8"])


class SaveRcsSettingsRequest(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


def get_service(session: Session = Depends(get_session)) -> LekabReplyActionService:
    return LekabReplyActionService(session, mock_mode=settings.lekab_mock_mode)


def _resolve_trace_id(request: Request) -> str:
    return request.headers.get("x-trace-id") or f"lekab-rcs-{uuid4().hex[:16]}"


@versioned_router.get("/help")
def help_view() -> dict[str, Any]:
    return {
        "module": "lekab_adapter",
        "version": "v1.3.8",
        "adapter_features": [
            "reply_to_action_engine",
            "bus_safe_callback_normalization",
            "appointment_action_candidate_mapping",
            "appointment_action_resolution_preview",
            "appointment_action_review_required_state",
            "communication_history_inbound_outbound_tracking",
            "message_monitor_action_preview",
            "webhook_callback_fetch_action",
            "verbose_connection_logging_toggle",
        ],
    }


@versioned_router.get("/settings/rcs")
def get_rcs_settings(
    request: Request,
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.get_rcs_settings(trace_id=_resolve_trace_id(request))


@versioned_router.post("/settings/rcs")
def save_rcs_settings(
    request: Request,
    payload: SaveRcsSettingsRequest,
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.save_rcs_settings(payload.values, trace_id=_resolve_trace_id(request))


@versioned_router.post("/settings/rcs/validate")
def validate_rcs_settings(
    request: Request,
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.validate_rcs_settings(trace_id=_resolve_trace_id(request))


@versioned_router.post("/settings/rcs/test-connection")
def test_rcs_connection(
    request: Request,
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.test_rcs_connection(trace_id=_resolve_trace_id(request))


@versioned_router.post("/settings/rcs/seturl")
def configure_rime_callback_urls(
    request: Request,
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.configure_provider_callback_urls(trace_id=_resolve_trace_id(request))


@versioned_router.post("/settings/rcs/fetch-latest-callback")
def fetch_latest_callback(
    request: Request,
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.fetch_latest_callback(trace_id=_resolve_trace_id(request))


@versioned_router.get("/monitor")
def get_monitor_payload(
    service: LekabReplyActionService = Depends(get_service),
) -> dict[str, Any]:
    return service.build_monitor_payload()


async def _extract_callback_payload(request: Request) -> dict[str, Any]:
    payload: dict[str, Any] = dict(request.query_params)
    if request.method.upper() != "POST":
        return payload

    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            body = {}
        if isinstance(body, dict):
            payload.update(body)
        return payload

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        payload.update({key: value for key, value in form.items()})
        return payload

    raw_body = (await request.body()).decode("utf-8", errors="ignore").strip()
    if not raw_body:
        return payload
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        parsed = parse_qs(raw_body, keep_blank_values=True)
        payload.update({key: values[-1] if values else "" for key, values in parsed.items()})
        payload["raw_body"] = raw_body
        return payload
    if isinstance(body, dict):
        payload.update(body)
    else:
        payload["raw_body"] = raw_body
    return payload


@router.api_route("/api/lekab/callback", methods=["GET", "POST"])
async def ingest_real_callback(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    trace_id = _resolve_trace_id(request)
    payload = await _extract_callback_payload(request)

    def _process_callback(callback_payload: dict[str, Any], callback_trace_id: str, headers: dict[str, Any], remote_ip: str | None) -> None:
        session = SessionLocal()
        try:
            service = LekabReplyActionService(session, mock_mode=settings.lekab_mock_mode)
            service.process_provider_callback(
                callback_payload,
                trace_id=callback_trace_id,
                headers=headers,
                remote_ip=remote_ip,
            )
        finally:
            session.close()

    background_tasks.add_task(
        _process_callback,
        payload,
        trace_id,
        dict(request.headers),
        request.client.host if request.client else None,
    )
    return {"accepted": True, "trace_id": trace_id, "processing": "background"}


router.include_router(versioned_router)
