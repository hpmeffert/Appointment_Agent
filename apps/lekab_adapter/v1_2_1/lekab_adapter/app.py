from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from appointment_agent_shared.db import get_session
from appointment_agent_shared.models import MessageAction
from appointment_agent_shared.config import settings

from .service import LekabMessagingService

router = APIRouter(prefix="/api/lekab/v1.2.1", tags=["lekab-adapter-v1.2.1"])


class SendMessageRequest(BaseModel):
    tenant_id: str = "demo"
    correlation_id: str
    phone_number: str
    body: str
    customer_id: Optional[str] = None
    contact_reference: Optional[str] = None
    journey_id: Optional[str] = None
    booking_reference: Optional[str] = None
    message_type: str = "text"
    actions: list[MessageAction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InboundMessageRequest(BaseModel):
    tenant_id: str = "demo"
    correlation_id: str
    phone_number: str
    body: str
    channel: str = "RCS"
    provider_message_id: Optional[str] = None
    customer_id: Optional[str] = None
    contact_reference: Optional[str] = None
    journey_id: Optional[str] = None
    booking_reference: Optional[str] = None
    message_type: str = "text"
    actions: list[MessageAction] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class MessageStatusRequest(BaseModel):
    tenant_id: str = "demo"
    correlation_id: str
    message_id: str
    status: str
    provider_payload: dict[str, Any] = Field(default_factory=dict)


def get_service(session: Session = Depends(get_session)) -> LekabMessagingService:
    return LekabMessagingService(session, mock_mode=settings.lekab_mock_mode)


@router.get("/help")
def help_view() -> dict[str, Any]:
    return {
        "module": "lekab_adapter",
        "version": "v1.2.1",
        "adapter_features": [
            "oauth_or_api_key_abstraction",
            "rcs_send",
            "sms_send",
            "inbound_message_normalization",
            "message_status_tracking",
            "addressbook_lookup_direction",
            "message_monitor_payload",
        ],
        "doc_basis": [
            "DispatchWebService",
            "SMSRESTWebService",
            "AddressbookWebService",
            "RimeRESTWebService",
        ],
    }


@router.post("/auth/token")
def auth_token(service: LekabMessagingService = Depends(get_service)) -> dict[str, Any]:
    return service.fetch_token()


@router.post("/addressbook/resolve")
def resolve_contact(
    tenant_id: str,
    phone_number: str,
    service: LekabMessagingService = Depends(get_service),
) -> dict[str, Any]:
    return service.resolve_contact(tenant_id=tenant_id, phone_number=phone_number)


@router.post("/messages/send/rcs")
def send_rcs(request: SendMessageRequest, service: LekabMessagingService = Depends(get_service)) -> dict[str, Any]:
    return service.send_message(
        channel="RCS",
        tenant_id=request.tenant_id,
        correlation_id=request.correlation_id,
        phone_number=request.phone_number,
        body=request.body,
        customer_id=request.customer_id,
        contact_reference=request.contact_reference,
        journey_id=request.journey_id,
        booking_reference=request.booking_reference,
        message_type=request.message_type,
        actions=[action.model_dump() for action in request.actions],
        metadata=request.metadata,
    ).model_dump(mode="json")


@router.post("/messages/send/sms")
def send_sms(request: SendMessageRequest, service: LekabMessagingService = Depends(get_service)) -> dict[str, Any]:
    return service.send_message(
        channel="SMS",
        tenant_id=request.tenant_id,
        correlation_id=request.correlation_id,
        phone_number=request.phone_number,
        body=request.body,
        customer_id=request.customer_id,
        contact_reference=request.contact_reference,
        journey_id=request.journey_id,
        booking_reference=request.booking_reference,
        message_type=request.message_type,
        actions=[action.model_dump() for action in request.actions],
        metadata=request.metadata,
    ).model_dump(mode="json")


@router.post("/messages/inbound")
def ingest_inbound(request: InboundMessageRequest, service: LekabMessagingService = Depends(get_service)) -> dict[str, Any]:
    return service.ingest_inbound_message(
        tenant_id=request.tenant_id,
        correlation_id=request.correlation_id,
        phone_number=request.phone_number,
        body=request.body,
        channel=request.channel,
        provider_message_id=request.provider_message_id,
        customer_id=request.customer_id,
        contact_reference=request.contact_reference,
        journey_id=request.journey_id,
        booking_reference=request.booking_reference,
        message_type=request.message_type,
        actions=[action.model_dump() for action in request.actions],
        raw_payload=request.raw_payload,
    ).model_dump(mode="json")


@router.post("/messages/status")
def update_message_status(
    request: MessageStatusRequest,
    service: LekabMessagingService = Depends(get_service),
) -> dict[str, Any]:
    message = service.update_message_status(
        message_id=request.message_id,
        correlation_id=request.correlation_id,
        tenant_id=request.tenant_id,
        status=request.status,
        provider_payload=request.provider_payload,
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message.model_dump(mode="json")


@router.get("/messages")
def list_messages(
    channel: Optional[str] = Query(default=None),
    direction: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    journey_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    service: LekabMessagingService = Depends(get_service),
) -> dict[str, Any]:
    messages = service.list_messages(
        channel=channel,
        direction=direction,
        status=status,
        journey_id=journey_id,
        limit=limit,
    )
    return {"messages": [message.model_dump(mode="json") for message in messages]}


@router.get("/messages/{message_id}")
def get_message(message_id: str, service: LekabMessagingService = Depends(get_service)) -> dict[str, Any]:
    message = service.get_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message.model_dump(mode="json")


@router.get("/monitor")
def monitor_view(service: LekabMessagingService = Depends(get_service)) -> dict[str, Any]:
    return service.build_monitor_payload()
