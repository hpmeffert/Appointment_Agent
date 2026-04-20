from __future__ import annotations

from datetime import datetime, timedelta
from typing import Union
from uuid import uuid4

from sqlalchemy.orm import Session

from appointment_agent_shared.contracts import CallbackPayload, EventEnvelope, LekabDispatchCommand
from appointment_agent_shared.config import settings
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.repositories import CallbackRepository


class LekabAdapterService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.callbacks = CallbackRepository(session)
        self._token_expires_at = datetime.utcnow()
        self._token_value = ""

    def fetch_token(self) -> dict[str, str]:
        if datetime.utcnow() >= self._token_expires_at:
            self._token_value = f"lekab-{uuid4().hex}"
            self._token_expires_at = datetime.utcnow() + timedelta(minutes=15)
            event_bus.publish(
                EventEnvelope(
                    event_id=uuid4().hex,
                    correlation_id="auth-refresh",
                    tenant_id="system",
                    trace_id=uuid4().hex,
                    event_type="lekab.auth.token.refreshed",
                    payload={"expires_at": self._token_expires_at.isoformat()},
                )
            )
        return {"access_token": self._token_value, "token_type": "Bearer"}

    def dispatch_workflow(self, command: LekabDispatchCommand) -> dict[str, str]:
        runtime_id = f"job-{uuid4().hex[:12]}"
        event_bus.publish(
            EventEnvelope(
                event_id=uuid4().hex,
                correlation_id=command.correlation_id,
                tenant_id=command.tenant_id,
                trace_id=uuid4().hex,
                event_type="lekab.dispatch.job.started",
                payload={"runtime_id": runtime_id, "job_id": command.job_id, "job_name": command.job_name},
            )
        )
        return {"runtime_id": runtime_id, "status": "accepted"}

    def launch_confirmation(self, command: LekabDispatchCommand) -> dict[str, str]:
        return self.dispatch_workflow(command)

    def launch_reminder(self, command: LekabDispatchCommand) -> dict[str, str]:
        dispatch = self.dispatch_workflow(command)
        from lekab_adapter.v1_2_1_patch4.lekab_adapter.service import LekabMessagingSettingsService

        sender = LekabMessagingSettingsService(self.session, mock_mode=settings.lekab_mock_mode)
        action_labels = command.metadata.get("interactive_actions") or ["Confirm", "Reschedule", "Cancel", "Call me"]
        action_values = command.metadata.get("interactive_action_values") or ["confirm", "reschedule", "cancel", "call_me"]
        actions = [
            {
                "action_id": f"reminder-{index}",
                "label": str(label),
                "value": str(action_values[index]) if index < len(action_values) else str(label).lower().replace(" ", "_"),
                "action_type": "reply",
                "canonical_action": str(action_values[index]) if index < len(action_values) else str(label).lower().replace(" ", "_"),
            }
            for index, label in enumerate(action_labels)
        ]
        recipient = command.to_numbers[0] if command.to_numbers else ""
        if recipient:
            message = sender.send_message(
                channel="RCS",
                tenant_id=command.tenant_id,
                correlation_id=command.correlation_id,
                phone_number=recipient,
                body=command.message,
                journey_id=command.metadata.get("journey_id"),
                booking_reference=command.metadata.get("booking_reference"),
                message_type="reminder",
                actions=actions,
                metadata={
                    "dispatch_runtime_id": dispatch["runtime_id"],
                    "interactive_actions": actions,
                    **command.metadata,
                },
            )
            dispatch["message_id"] = message.message_id
            dispatch["delivery_status"] = message.status
        return dispatch

    def ingest_callback(self, payload: CallbackPayload) -> dict[str, Union[str, bool]]:
        duplicate = self.callbacks.exists(payload.event_id)
        if not duplicate:
            self.callbacks.record(
                event_id=payload.event_id,
                event_type=payload.event_type,
                correlation_id=payload.correlation_id,
                payload=payload.model_dump(),
                is_duplicate=False,
            )
            mapped_type = {
                "JOB_START": "lekab.job.started",
                "JOB_ASSIGN": "lekab.job.assigned",
                "JOB_FINISH": "lekab.job.finished",
            }.get(payload.event_type, "lekab.callback.received")
            event_bus.publish(
                EventEnvelope(
                    event_id=uuid4().hex,
                    correlation_id=payload.correlation_id,
                    tenant_id="lekab",
                    trace_id=uuid4().hex,
                    event_type=mapped_type,
                    payload=payload.model_dump(),
                )
            )
        return {"accepted": True, "duplicate": duplicate}
