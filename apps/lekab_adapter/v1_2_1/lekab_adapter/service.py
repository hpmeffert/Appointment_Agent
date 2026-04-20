from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from appointment_agent_shared.commands import ResolveCustomerCommand
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.events import EventEnvelope
from appointment_agent_shared.models import MessageAction, NormalizedMessage
from appointment_agent_shared.repositories import AddressLinkageResolver, ContactRepository, MessageRepository


class LekabMessagingService:
    """Provider-facing adapter for LEKAB style messaging flows.

    The UI never receives raw provider-specific payloads directly. This service
    translates provider concepts such as Rime rich messaging, SMS delivery, and
    addressbook lookup into one normalized message model that later channels can
    reuse as well.
    """

    def __init__(self, session: Session, *, mock_mode: bool = True) -> None:
        self.session = session
        self.mock_mode = mock_mode
        self.contacts = ContactRepository(session)
        self.messages = MessageRepository(session)
        self.address_linkage = AddressLinkageResolver(session)
        self._token_value = ""
        self._token_expires_at = datetime.utcnow()

    def fetch_token(self) -> dict[str, Any]:
        """Return a cached token abstraction for later real OAuth/API-key usage.

        The LEKAB PDFs describe multiple authentication styles. For the
        demonstrator we keep the contract stable with one token endpoint and
        expose the auth method in the response so the platform can explain the
        adapter behavior during demos.
        """

        if datetime.utcnow() >= self._token_expires_at:
            self._token_value = f"lekab-v121-{uuid4().hex}"
            self._token_expires_at = datetime.utcnow() + timedelta(minutes=15)
            self._publish_event(
                event_type="lekab.auth.token.refreshed",
                correlation_id="lekab-auth-v121",
                tenant_id="system",
                payload={
                    "auth_style": "oauth_or_api_key_abstraction",
                    "expires_at": self._token_expires_at.isoformat(),
                },
            )
        return {
            "access_token": self._token_value,
            "token_type": "Bearer",
            "auth_style": "oauth_or_api_key_abstraction",
            "expires_at": self._token_expires_at.isoformat(),
            "mock_mode": self.mock_mode,
        }

    def resolve_contact(self, *, tenant_id: str, phone_number: str) -> dict[str, Any]:
        record = self.contacts.resolve(
            ResolveCustomerCommand(
                tenant_id=tenant_id,
                phone=phone_number,
                mobile_number=phone_number,
            )
        )
        return {
            "matched": record is not None,
            "customer_id": getattr(record, "customer_id", None),
            "contact_reference": getattr(record, "customer_id", None),
            "full_name": getattr(record, "full_name", None),
            "phone_number": phone_number,
            "source": "lekab_addressbook_abstraction",
        }

    def send_message(
        self,
        *,
        channel: str,
        tenant_id: str,
        correlation_id: str,
        phone_number: str,
        body: str,
        customer_id: Optional[str] = None,
        contact_reference: Optional[str] = None,
        journey_id: Optional[str] = None,
        booking_reference: Optional[str] = None,
        message_type: str = "text",
        actions: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> NormalizedMessage:
        """Send one normalized outbound message.

        RCS and SMS share the same internal structure. The only difference is the
        selected channel and the provider payload details stored for monitoring.
        """

        resolved_contact = None
        if not customer_id and not contact_reference:
            resolved_contact = self.resolve_contact(tenant_id=tenant_id, phone_number=phone_number)
            customer_id = resolved_contact["customer_id"] or customer_id
            contact_reference = resolved_contact["contact_reference"] or contact_reference

        provider_message_id = f"{channel.lower()}-{uuid4().hex[:14]}"
        provider_job_id = f"lekab-job-{uuid4().hex[:10]}"
        normalized = self._build_normalized_message(
            message_id=f"msg-{uuid4().hex[:12]}",
            provider_message_id=provider_message_id,
            provider_job_id=provider_job_id,
            channel=channel,
            direction="outbound",
            status="accepted" if self.mock_mode else "submitted",
            customer_id=customer_id,
            contact_reference=contact_reference,
            phone_number=phone_number,
            journey_id=journey_id,
            booking_reference=booking_reference,
            message_type=message_type,
            body=body,
            actions=actions or [],
            metadata={
                "provider_path": "rime_send" if channel == "RCS" else "sms_send",
                "contact_resolution": resolved_contact,
                **(metadata or {}),
            },
            provider_payload={
                "provider_path": "rime_send" if channel == "RCS" else "sms_send",
                "channel": channel,
                "recipient": phone_number,
                "body": body,
                "actions": actions or [],
            },
        )
        self._store_message(normalized)
        self._publish_event(
            event_type="lekab.message.outbound.accepted",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=normalized.model_dump(mode="json"),
        )
        return normalized

    def ingest_inbound_message(
        self,
        *,
        tenant_id: str,
        correlation_id: str,
        phone_number: str,
        body: str,
        channel: str = "RCS",
        provider_message_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        contact_reference: Optional[str] = None,
        journey_id: Optional[str] = None,
        booking_reference: Optional[str] = None,
        message_type: str = "text",
        actions: Optional[list[dict[str, Any]]] = None,
        raw_payload: Optional[dict[str, Any]] = None,
    ) -> NormalizedMessage:
        """Normalize inbound provider traffic into the shared internal message model."""

        resolved_contact = None
        if not customer_id and not contact_reference:
            resolved_contact = self.resolve_contact(tenant_id=tenant_id, phone_number=phone_number)
            customer_id = resolved_contact["customer_id"] or customer_id
            contact_reference = resolved_contact["contact_reference"] or contact_reference

        normalized = self._build_normalized_message(
            message_id=f"msg-{uuid4().hex[:12]}",
            provider_message_id=provider_message_id or f"inbound-{uuid4().hex[:14]}",
            provider_job_id=None,
            channel=channel,
            direction="inbound",
            status="received",
            customer_id=customer_id,
            contact_reference=contact_reference,
            phone_number=phone_number,
            journey_id=journey_id,
            booking_reference=booking_reference,
            message_type=message_type,
            body=body,
            actions=actions or [],
            metadata={
                "provider_path": "callback_or_inbound_webhook",
                "contact_resolution": resolved_contact,
            },
            provider_payload=raw_payload or {
                "channel": channel,
                "phone_number": phone_number,
                "body": body,
                "actions": actions or [],
            },
        )
        self._store_message(normalized)
        self._publish_event(
            event_type="lekab.message.inbound.received",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=normalized.model_dump(mode="json"),
        )
        return normalized

    def update_message_status(
        self,
        *,
        message_id: str,
        correlation_id: str,
        tenant_id: str,
        status: str,
        provider_payload: Optional[dict[str, Any]] = None,
    ) -> Optional[NormalizedMessage]:
        record = self.messages.get(message_id)
        if record is None:
            return None
        normalized = self._record_to_model(record)
        normalized.status = status
        normalized.updated_at = datetime.utcnow()
        normalized.provider_payload = {
            **normalized.provider_payload,
            **(provider_payload or {}),
        }
        self._store_message(normalized)
        self._publish_event(
            event_type="lekab.message.status.updated",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload={"message_id": message_id, "status": status},
        )
        return normalized

    def list_messages(
        self,
        *,
        channel: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        journey_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[NormalizedMessage]:
        self._seed_demo_messages_if_empty()
        records = self.messages.list_messages(
            channel=channel,
            direction=direction,
            status=status,
            journey_id=journey_id,
            limit=limit,
        )
        return [self._record_to_model(record) for record in records]

    def get_message(self, message_id: str) -> Optional[NormalizedMessage]:
        self._seed_demo_messages_if_empty()
        record = self.messages.get(message_id)
        if record is None:
            return None
        return self._record_to_model(record)

    def build_monitor_payload(self) -> dict[str, Any]:
        """Shape monitor-ready data for the Incident-style UI.

        The UI receives one already normalized structure with totals, a selected
        detail item, and report cards. This keeps the browser code focused on
        presentation instead of provider translation.
        """

        # The monitor acts as a communication history view, not just a tiny
        # dashboard sample. A higher cap keeps recent inbound callback tests,
        # outbound diagnostics, and scenario-run evidence visible together.
        messages = self.list_messages(limit=250)
        selected = messages[0] if messages else None
        outbound = sum(1 for message in messages if message.direction == "outbound")
        inbound = sum(1 for message in messages if message.direction == "inbound")
        rcs = sum(1 for message in messages if message.channel == "RCS")
        sms = sum(1 for message in messages if message.channel == "SMS")
        replies = sum(
            1
            for message in messages
            if (message.metadata or {}).get("normalized_event_type") == "message.reply_received"
        )
        delivered = sum(1 for message in messages if message.status in {"delivered", "received", "accepted"})
        failed = sum(1 for message in messages if message.status in {"failed", "rejected"})
        journeys = sorted({message.journey_id for message in messages if message.journey_id})
        return {
            "messages": [message.model_dump(mode="json") for message in messages],
            "selected_message": selected.model_dump(mode="json") if selected else None,
            "summary_cards": [
                {"label": "Total Messages", "value": len(messages)},
                {"label": "Outbound", "value": outbound},
                {"label": "Inbound", "value": inbound},
                {"label": "RCS", "value": rcs},
                {"label": "SMS", "value": sms},
                {"label": "Delivered/Accepted", "value": delivered},
                {"label": "Failed", "value": failed},
            ],
            "report_cards": [
                {
                    "title": "Communication History",
                    "text": "This monitor keeps incoming and outgoing communication in one timeline so the operator can explain the whole appointment story from first send to latest reply.",
                    "metrics": [
                        {"label": "Incoming messages", "value": inbound},
                        {"label": "Outgoing messages", "value": outbound},
                    ],
                },
                {
                    "title": "Delivery And Replies",
                    "text": "Delivery callbacks and customer replies are normalized into the same history so you can filter by direction, channel, and current status without reading raw provider payloads.",
                    "metrics": [
                        {"label": "Delivered or received", "value": delivered},
                        {"label": "Reply detected", "value": replies},
                    ],
                },
                {
                    "title": "Routing And Context",
                    "text": "Every message stores provider ids, customer context, and parsed reply hints so follow-up automation such as cancel, reschedule, or date parsing can happen on stable internal data.",
                    "metrics": [
                        {"label": "Journeys visible", "value": len(journeys)},
                        {"label": "Latest message", "value": selected.message_id if selected else "demo-msg-001"},
                    ],
                },
            ],
            "filters": {
                "channels": ["ALL", "RCS", "SMS"],
                "directions": ["ALL", "outbound", "inbound"],
                "statuses": ["ALL", "accepted", "submitted", "delivered", "received", "failed", "rejected"],
            },
        }

    def _seed_demo_messages_if_empty(self) -> None:
        if self.messages.list_messages(limit=1):
            return

        now = datetime.utcnow()
        sample_messages = [
            self._build_normalized_message(
                message_id="demo-msg-001",
                provider_message_id="rime-demo-001",
                provider_job_id="lekab-demo-job-001",
                channel="RCS",
                direction="outbound",
                status="delivered",
                customer_id="cust-demo-001",
                contact_reference="cust-demo-001",
                phone_number="+491701234567",
                address_id="addr-demo-001",
                appointment_id="demo-appointment-1",
                correlation_ref="corr-addr-demo-001",
                journey_id="journey-demo-001",
                booking_reference="booking-demo-001",
                message_type="card",
                body="Your appointment options are ready. Please choose a time slot.",
                actions=[
                    {"action_id": "slot-1", "label": "09:00", "value": "slot_0900", "action_type": "reply"},
                    {"action_id": "slot-2", "label": "11:00", "value": "slot_1100", "action_type": "reply"},
                ],
                metadata={"demo_seed": True, "customer_name": "Alex Schneider"},
                provider_payload={"provider_path": "rime_send", "suggestions": 2},
                created_at=now - timedelta(minutes=22),
                updated_at=now - timedelta(minutes=21),
            ),
            self._build_normalized_message(
                message_id="demo-msg-002",
                provider_message_id="rime-demo-002",
                provider_job_id=None,
                channel="RCS",
                direction="inbound",
                status="received",
                customer_id="cust-demo-001",
                contact_reference="cust-demo-001",
                phone_number="+491701234567",
                address_id="addr-demo-001",
                appointment_id="demo-appointment-1",
                correlation_ref="corr-addr-demo-001",
                journey_id="journey-demo-001",
                booking_reference="booking-demo-001",
                message_type="reply",
                body="I want the 11:00 slot.",
                actions=[],
                metadata={"demo_seed": True, "customer_name": "Alex Schneider"},
                provider_payload={"provider_path": "inbound_webhook", "reply_value": "slot_1100"},
                created_at=now - timedelta(minutes=20),
                updated_at=now - timedelta(minutes=20),
            ),
            self._build_normalized_message(
                message_id="demo-msg-003",
                provider_message_id="sms-demo-003",
                provider_job_id="lekab-demo-job-003",
                channel="SMS",
                direction="outbound",
                status="accepted",
                customer_id="cust-demo-002",
                contact_reference="cust-demo-002",
                phone_number="+491709876543",
                address_id="addr-demo-002",
                appointment_id="demo-appointment-2",
                correlation_ref="corr-addr-demo-002",
                journey_id="journey-demo-002",
                booking_reference="booking-demo-002",
                message_type="text",
                body="Reminder: your technician visit is tomorrow at 14:00.",
                actions=[],
                metadata={"demo_seed": True, "customer_name": "Maria Hoffmann"},
                provider_payload={"provider_path": "sms_send"},
                created_at=now - timedelta(minutes=11),
                updated_at=now - timedelta(minutes=11),
            ),
            self._build_normalized_message(
                message_id="demo-msg-004",
                provider_message_id="sms-demo-004",
                provider_job_id=None,
                channel="SMS",
                direction="inbound",
                status="received",
                customer_id="cust-demo-002",
                contact_reference="cust-demo-002",
                phone_number="+491709876543",
                address_id="addr-demo-002",
                appointment_id="demo-appointment-2",
                correlation_ref="corr-addr-demo-002",
                journey_id="journey-demo-002",
                booking_reference="booking-demo-002",
                message_type="text",
                body="Please call me back instead.",
                actions=[],
                metadata={"demo_seed": True, "customer_name": "Maria Hoffmann"},
                provider_payload={"provider_path": "sms_callback"},
                created_at=now - timedelta(minutes=8),
                updated_at=now - timedelta(minutes=8),
            ),
        ]
        for message in sample_messages:
            self._store_message(message)

    def _build_normalized_message(
        self,
        *,
        message_id: str,
        provider_message_id: Optional[str],
        provider_job_id: Optional[str],
        channel: str,
        direction: str,
        status: str,
        customer_id: Optional[str],
        contact_reference: Optional[str],
        phone_number: Optional[str],
        journey_id: Optional[str] = None,
        booking_reference: Optional[str] = None,
        message_type: str,
        body: str,
        actions: list[dict[str, Any]],
        metadata: dict[str, Any],
        provider_payload: dict[str, Any],
        address_id: Optional[str] = None,
        appointment_id: Optional[str] = None,
        correlation_ref: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> NormalizedMessage:
        preview = body if len(body) <= 120 else f"{body[:117]}..."
        linkage = self.address_linkage.resolve(
            tenant_id="default",
            address_id=address_id,
            appointment_id=appointment_id,
            booking_reference=booking_reference,
            correlation_ref=correlation_ref,
            phone_number=phone_number,
        )
        return NormalizedMessage(
            message_id=message_id,
            provider_message_id=provider_message_id,
            provider_job_id=provider_job_id,
            provider="lekab",
            channel=channel,
            direction=direction,
            status=status,
            customer_id=customer_id,
            contact_reference=contact_reference,
            phone_number=phone_number,
            address_id=linkage.address_id,
            appointment_id=linkage.appointment_id,
            correlation_ref=linkage.correlation_ref,
            journey_id=journey_id,
            booking_reference=linkage.booking_reference,
            message_type=message_type,
            body=body,
            preview_text=preview,
            actions=[MessageAction(**action) for action in actions],
            provider_payload=provider_payload,
            metadata=metadata,
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )

    def _record_to_model(self, record) -> NormalizedMessage:
        return NormalizedMessage(
            message_id=record.message_id,
            provider_message_id=record.provider_message_id,
            provider_job_id=record.provider_job_id,
            provider=record.provider,
            channel=record.channel,
            direction=record.direction,
            status=record.status,
            customer_id=record.customer_id,
            contact_reference=record.contact_reference,
            phone_number=record.phone_number,
            address_id=record.address_id,
            appointment_id=record.appointment_id,
            correlation_ref=record.correlation_ref,
            journey_id=record.journey_id,
            booking_reference=record.booking_reference,
            message_type=record.message_type,
            body=record.body,
            preview_text=record.preview_text,
            actions=[MessageAction(**action) for action in (record.actions or [])],
            provider_payload=record.provider_payload or {},
            metadata=record.metadata_payload or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _store_message(self, message: NormalizedMessage) -> None:
        # The repository is the single write path so future providers can share
        # the same persistence and monitoring behavior.
        self.messages.upsert(
            message_id=message.message_id,
            provider_message_id=message.provider_message_id,
            provider_job_id=message.provider_job_id,
            provider=message.provider,
            channel=message.channel,
            direction=message.direction,
            status=message.status,
            customer_id=message.customer_id,
            contact_reference=message.contact_reference,
            phone_number=message.phone_number,
            address_id=message.address_id,
            appointment_id=message.appointment_id,
            correlation_ref=message.correlation_ref,
            journey_id=message.journey_id,
            booking_reference=message.booking_reference,
            message_type=message.message_type,
            body=message.body,
            preview_text=message.preview_text,
            actions=[action.model_dump() for action in message.actions],
            provider_payload=message.provider_payload,
            metadata=message.metadata,
        )

    def _publish_event(
        self,
        *,
        event_type: str,
        correlation_id: str,
        tenant_id: str,
        payload: dict[str, Any],
    ) -> None:
        event_bus.publish(
            EventEnvelope(
                event_id=uuid4().hex,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                trace_id=uuid4().hex,
                event_type=event_type,
                payload=payload,
            )
        )
