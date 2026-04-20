from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from address_database.v1_3_9.address_database.service import AddressDatabaseService, AddressInput, AddressLinkInput
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.events import DemoScenarioContextPrepared, EventEnvelope
from appointment_agent_shared.repositories import DemoScenarioContextRepository
from appointment_agent_shared.shared_settings_store import SharedSettingsStoreService


CONTEXT_KEY = "demo-monitoring-v1.3.9"
DEFAULT_CALENDAR_REF = "appointment-agent-test-calendar"


class DemoScenarioContextUpdate(BaseModel):
    scenario_id: Optional[str] = None
    mode: Optional[str] = None
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None
    correlation_ref: Optional[str] = None
    calendar_ref: Optional[str] = None
    output_channel: Optional[str] = None
    appointment_type: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    current_step: Optional[str] = None
    status: Optional[str] = None
    latest_protocol_path: Optional[str] = None
    latest_demo_log_path: Optional[str] = None
    latest_summary_path: Optional[str] = None
    latest_run_id: Optional[str] = None
    started_at_utc: Optional[datetime] = None
    finished_at_utc: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DemoScenarioContextPayload(BaseModel):
    version: str = "v1.3.9-patch9"
    context_key: str = CONTEXT_KEY
    scenario_id: str
    mode: str
    address_id: Optional[str] = None
    appointment_id: Optional[str] = None
    booking_reference: Optional[str] = None
    correlation_ref: Optional[str] = None
    calendar_ref: Optional[str] = None
    output_channel: Optional[str] = None
    appointment_type: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    current_step: Optional[str] = None
    status: str
    latest_protocol_path: Optional[str] = None
    latest_demo_log_path: Optional[str] = None
    latest_summary_path: Optional[str] = None
    latest_run_id: Optional[str] = None
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None
    selected_address: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DemoScenarioContextService:
    """Persist one shared demo context for the entire v1.3.9 patch line.

    The cockpit previously kept separate UI-only state for scenario, address,
    Google assignment, and reminder assignment. This service gives every view
    and the scenario runner one SQLite-backed context so the operator sees the
    same source of truth everywhere.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = DemoScenarioContextRepository(session)
        self.addresses = AddressDatabaseService(session)
        self.shared_settings = SharedSettingsStoreService(session)

    def _iso(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.replace(microsecond=0).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _default_address(self) -> Optional[dict[str, Any]]:
        seeded = self.addresses.get_address("addr-demo-001")
        if seeded is not None:
            return seeded.model_dump(mode="json")
        existing = self.addresses.list_addresses(is_active=True, limit=1)
        if existing:
            return existing[0].model_dump(mode="json")
        created = self.addresses.save_address(
            AddressInput(
                address_id="addr-demo-001",
                display_name="Anna Berger",
                city="Berlin",
                phone="491705707716",
                email="anna.berger@example.com",
                timezone="Europe/Berlin",
                preferred_channel="rcs_sms",
                correlation_ref="corr-addr-demo-001",
            )
        )
        return created.model_dump(mode="json")

    def _address_payload(self, address_id: Optional[str]) -> Optional[dict[str, Any]]:
        if not address_id:
            return self._default_address()
        address = self.addresses.get_address(address_id)
        if address is not None:
            return address.model_dump(mode="json")
        return self._default_address()

    def _to_payload(self, record) -> DemoScenarioContextPayload:
        address_payload = self._address_payload(record.address_id)
        return DemoScenarioContextPayload(
            scenario_id=record.scenario_id or "confirm-appointment",
            mode=record.mode or "simulation",
            address_id=record.address_id,
            appointment_id=record.appointment_id,
            booking_reference=record.booking_reference,
            correlation_ref=record.correlation_ref,
            calendar_ref=record.calendar_ref,
            output_channel=record.output_channel,
            appointment_type=record.appointment_type,
            from_date=record.from_date,
            to_date=record.to_date,
            current_step=record.current_step,
            status=record.status or "idle",
            latest_protocol_path=record.latest_protocol_path,
            latest_demo_log_path=record.latest_demo_log_path,
            latest_summary_path=record.latest_summary_path,
            latest_run_id=record.latest_run_id,
            started_at_utc=self._iso(record.started_at_utc),
            finished_at_utc=self._iso(record.finished_at_utc),
            selected_address=address_payload,
            metadata=dict(record.metadata_payload or {}),
        )

    def get_context(self) -> DemoScenarioContextPayload:
        record = self.repo.get(CONTEXT_KEY)
        if record is None:
            address = self._default_address()
            return self.save_context(
                DemoScenarioContextUpdate(
                    scenario_id="confirm-appointment",
                    mode="simulation",
                    address_id=address.get("address_id") if address else None,
                    correlation_ref=address.get("correlation_ref") if address else None,
                    calendar_ref=DEFAULT_CALENDAR_REF,
                    output_channel=address.get("preferred_channel") if address else "rcs_sms",
                    appointment_type="dentist",
                    status="idle",
                    metadata={"origin": "default_context"},
                )
            )
        return self._to_payload(record)

    def save_context(self, update: DemoScenarioContextUpdate) -> DemoScenarioContextPayload:
        current = self.get_context() if self.repo.get(CONTEXT_KEY) is not None else None
        address_payload = self._address_payload(update.address_id or (current.address_id if current else None))
        mode = update.mode or (current.mode if current else "simulation")
        output_channel = (
            update.output_channel
            or (current.output_channel if current else None)
            or (address_payload or {}).get("preferred_channel")
            or "rcs_sms"
        )
        correlation_ref = (
            update.correlation_ref
            or (current.correlation_ref if current else None)
            or (address_payload or {}).get("correlation_ref")
            or (f"corr-{(address_payload or {}).get('address_id')}" if address_payload else None)
        )
        record = self.repo.save(
            context_key=CONTEXT_KEY,
            version="v1.3.9-patch9",
            scenario_id=update.scenario_id or (current.scenario_id if current else "confirm-appointment"),
            mode=mode,
            address_id=(address_payload or {}).get("address_id"),
            appointment_id=update.appointment_id or (current.appointment_id if current else None),
            booking_reference=update.booking_reference or (current.booking_reference if current else None),
            correlation_ref=correlation_ref,
            calendar_ref=update.calendar_ref or (current.calendar_ref if current else DEFAULT_CALENDAR_REF),
            output_channel=output_channel,
            appointment_type=update.appointment_type or (current.appointment_type if current else "dentist"),
            from_date=update.from_date or (current.from_date if current else None),
            to_date=update.to_date or (current.to_date if current else None),
            current_step=update.current_step or (current.current_step if current else "context_ready"),
            status=update.status or (current.status if current else "idle"),
            latest_protocol_path=update.latest_protocol_path or (current.latest_protocol_path if current else None),
            latest_demo_log_path=update.latest_demo_log_path or (current.latest_demo_log_path if current else None),
            latest_summary_path=update.latest_summary_path or (current.latest_summary_path if current else None),
            latest_run_id=update.latest_run_id or (current.latest_run_id if current else None),
            metadata={**(current.metadata if current else {}), **(update.metadata or {})},
            started_at_utc=update.started_at_utc or (datetime.fromisoformat(current.started_at_utc.replace("Z", "+00:00")) if current and current.started_at_utc else None),
            finished_at_utc=update.finished_at_utc or (datetime.fromisoformat(current.finished_at_utc.replace("Z", "+00:00")) if current and current.finished_at_utc else None),
        )
        payload = self._to_payload(record)
        self.shared_settings.merge_namespace(
            "demo",
            {
                "scenario_id": payload.scenario_id,
                "mode": payload.mode,
                "address_id": payload.address_id,
                "appointment_id": payload.appointment_id,
                "booking_reference": payload.booking_reference,
                "correlation_ref": payload.correlation_ref,
                "calendar_ref": payload.calendar_ref,
                "output_channel": payload.output_channel,
                "appointment_type": payload.appointment_type,
                "from_date": payload.from_date,
                "to_date": payload.to_date,
                "current_step": payload.current_step,
                "status": payload.status,
                "selected_address": deepcopy(address_payload) if address_payload else None,
                "metadata": deepcopy(payload.metadata),
            },
            status_values={
                "started_at_utc": payload.started_at_utc,
                "finished_at_utc": payload.finished_at_utc,
                "latest_protocol_path": payload.latest_protocol_path,
                "latest_demo_log_path": payload.latest_demo_log_path,
                "latest_summary_path": payload.latest_summary_path,
                "latest_run_id": payload.latest_run_id,
            },
        )
        event_bus.publish(
            EventEnvelope(
                event_type="DemoScenarioContextPrepared",
                correlation_id=payload.correlation_ref or "demo-context",
                trace_id=f"demo-context-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:16]}",
                tenant_id="default",
                source="demo_monitoring_ui",
                payload=DemoScenarioContextPrepared(
                    scenario_id=payload.scenario_id,
                    mode=payload.mode,
                    address_id=payload.address_id,
                    appointment_id=payload.appointment_id,
                    correlation_ref=payload.correlation_ref,
                    output_channel=payload.output_channel,
                    status=payload.status,
                ).model_dump(mode="json"),
            )
        )
        return payload

    def prepare_run_context(
        self,
        *,
        scenario_id: str,
        mode: str,
        appointment_type: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        output_channel: Optional[str] = None,
    ) -> DemoScenarioContextPayload:
        current = self.get_context()
        address_payload = self._address_payload(current.address_id)
        if address_payload is None:
            raise ValueError("A selected address is required before a demo scenario can run.")

        existing_links = self.addresses.list_links_for_address(address_payload["address_id"])
        primary_link = existing_links[0] if existing_links else None
        appointment_id = primary_link["appointment_external_id"] if primary_link else f"demo-appointment-{address_payload['address_id']}"
        booking_reference = primary_link.get("booking_reference") if primary_link else f"booking-{address_payload['address_id']}"
        calendar_ref = primary_link.get("calendar_ref") if primary_link else DEFAULT_CALENDAR_REF
        correlation_ref = primary_link.get("correlation_ref") if primary_link else (address_payload.get("correlation_ref") or f"corr-{address_payload['address_id']}")

        if primary_link is None:
            # We create the explicit link up front so every later module can read
            # the same appointment/address relation instead of inferring it from
            # UI state or from generated log text.
            self.addresses.link_address_to_appointment(
                AddressLinkInput(
                    address_id=address_payload["address_id"],
                    appointment_external_id=appointment_id,
                    booking_reference=booking_reference,
                    calendar_ref=calendar_ref,
                    correlation_ref=correlation_ref,
                )
            )

        return self.save_context(
            DemoScenarioContextUpdate(
                scenario_id=scenario_id,
                mode=mode,
                address_id=address_payload["address_id"],
                appointment_id=appointment_id,
                booking_reference=booking_reference,
                correlation_ref=correlation_ref,
                calendar_ref=calendar_ref,
                output_channel=output_channel or current.output_channel,
                appointment_type=appointment_type,
                from_date=from_date or current.from_date,
                to_date=to_date or current.to_date,
                current_step="context_prepared",
                status="ready",
                metadata={"selected_address": address_payload},
            )
        )
