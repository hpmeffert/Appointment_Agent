from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from address_database.v1_3_9.address_database.service import AddressDatabaseService
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.events import (
    AddressAssignedToGeneratedAppointment,
    DemoArtifactWritten,
    DemoScenarioContextPrepared,
    DemoProtocolWritten,
    DemoScenarioCompleted,
    DemoScenarioFailed,
    DemoScenarioRequested,
    DemoScenarioStarted,
    DemoScenarioStepUpdated,
    EventEnvelope,
)
from appointment_agent_shared.repositories import JourneyRepository, MessageRepository
from appointment_agent_shared.config import settings
from lekab_adapter.v1_3_8.lekab_adapter.service import LekabReplyActionService

from .scenario_catalog import scenario_catalog
from .scenario_context import DemoScenarioContextService, DemoScenarioContextUpdate


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ARTIFACT_ROOT = PROJECT_ROOT / "runtime-artifacts" / "demo-scenarios" / "v1_3_9"


@dataclass
class ScenarioArtifacts:
    protocol_markdown: Path
    protocol_json: Path
    demo_log_markdown: Path
    summary_markdown: Path


class DemoScenarioTestingService:
    """Run one deterministic demo scenario and write operator-friendly evidence files.

    Phase 5 is not a production workflow engine. This service deliberately keeps
    the runner small, transparent, and file-oriented so operators can rerun a
    business story, inspect the result in the UI, and open the generated local
    protocol files afterwards.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.reply_service = LekabReplyActionService(session, mock_mode=settings.lekab_mock_mode)
        self.address_service = AddressDatabaseService(session)
        self.messages = MessageRepository(session)
        self.journeys = JourneyRepository(session)
        self.contexts = DemoScenarioContextService(session)

    def scenario_help(self, lang: str = "en") -> dict[str, Any]:
        return {
            "module": "demo_scenario_testing",
            "version": "v1.3.9-patch9",
            "artifact_directory": str(ARTIFACT_ROOT),
            "modes": ["simulation", "real"],
            "catalog": [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "expected_action": item["expected_action"],
                    "expected_state": item["expected_state"],
                }
                for item in scenario_catalog(lang)
            ],
            "features": [
                "file_based_protocols",
                "scenario_runner",
                "messages_and_customer_journey_execution",
                "simulation_and_real_modes",
                "latest_protocol_and_demo_log_lookup",
                "unified_demo_scenario_context",
                "interactive_reply_button_journey",
                "real_rcs_suggestion_payloads",
            ],
        }

    def run_scenario(
        self,
        *,
        scenario_id: str,
        mode: str = "simulation",
        lang: str = "en",
        address_id: str | None = None,
        output_channel: str | None = None,
        appointment_type: str = "dentist",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        scenario = next((item for item in scenario_catalog(lang) if item["id"] == scenario_id), None)
        if scenario is None:
            raise ValueError(f"Unknown scenario_id: {scenario_id}")
        if address_id:
            self.contexts.save_context(
                DemoScenarioContextUpdate(address_id=address_id)
            )
        run_mode = "real" if mode == "real" else "simulation"
        now = datetime.now(timezone.utc)
        run_id = f"demo-scn-{uuid4().hex[:10]}"
        trace_id = f"trace-{uuid4().hex[:16]}"
        journey_id = f"journey-{run_id}"
        shared_context = self.contexts.prepare_run_context(
            scenario_id=scenario["id"],
            mode=run_mode,
            appointment_type=appointment_type,
            from_date=from_date,
            to_date=to_date,
            output_channel=output_channel,
        )
        correlation_ref = shared_context.correlation_ref or f"corr-{run_id}"
        appointment_context = {
            "address_id": shared_context.address_id,
            "appointment_external_id": shared_context.appointment_id,
            "booking_reference": shared_context.booking_reference,
            "calendar_ref": shared_context.calendar_ref,
            "correlation_ref": shared_context.correlation_ref,
            "selected_address": shared_context.selected_address or {},
            "output_channel": shared_context.output_channel or "rcs_sms",
        }

        self._publish(
            "DemoScenarioRequested",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=DemoScenarioRequested(
                scenario_id=scenario["id"],
                scenario_title=scenario["title"],
                mode=run_mode,
                input_text=scenario["input_text"],
                expected_action=scenario["expected_action"],
            ).model_dump(mode="json"),
        )
        self._publish(
            "DemoScenarioContextPrepared",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=DemoScenarioContextPrepared(
                scenario_id=shared_context.scenario_id,
                mode=shared_context.mode,
                address_id=shared_context.address_id,
                appointment_id=shared_context.appointment_id,
                correlation_ref=shared_context.correlation_ref,
                output_channel=shared_context.output_channel,
                status=shared_context.status,
            ).model_dump(mode="json"),
        )
        self._publish(
            "DemoScenarioStarted",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=DemoScenarioStarted(
                scenario_id=scenario["id"],
                run_id=run_id,
                mode=run_mode,
                address_id=appointment_context["address_id"],
                appointment_id=appointment_context["appointment_external_id"],
                booking_reference=appointment_context["booking_reference"],
            ).model_dump(mode="json"),
        )

        step_log: list[dict[str, Any]] = []
        outbound_message = self._create_outbound_prompt(
            scenario=scenario,
            run_mode=run_mode,
            trace_id=trace_id,
            correlation_ref=correlation_ref,
            journey_id=journey_id,
            appointment_context=appointment_context,
        )
        step_log.append(
            self._step_entry(
                step="outbound_prompt",
                status="done",
                detail=f"Outbound reminder stored as {outbound_message.message_id}",
                payload={
                "message_id": outbound_message.message_id,
                "mode": run_mode,
                "channel": outbound_message.channel,
                "status": outbound_message.status,
                "suggestion_buttons": [item.model_dump(mode="json") for item in outbound_message.actions],
                "real_channel_payload": deepcopy(outbound_message.provider_payload),
                },
            )
        )
        self._publish_step(
            scenario_id=scenario["id"],
            run_id=run_id,
            step_name="outbound_prompt",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=step_log[-1],
        )
        expected_action = scenario["expected_action"]
        expected_intent = scenario["expected_intent"]
        expected_state = scenario["expected_state"]

        if run_mode == "real":
            journey_record = self.journeys.upsert(
                journey_id=journey_id,
                correlation_id=correlation_ref,
                tenant_id="demo",
                customer_id=appointment_context["address_id"] or "demo-customer",
                channel="RCS",
                current_state=JourneyState.REMINDER_PENDING.value,
                service_type=appointment_type,
                locale=lang,
                timezone="Europe/Berlin",
                preference_payload={
                    "address_id": appointment_context["address_id"],
                    "appointment_id": appointment_context["appointment_external_id"],
                    "booking_reference": appointment_context["booking_reference"],
                    "provider_reference": appointment_context["appointment_external_id"] or appointment_context["booking_reference"],
                    "appointment_type": appointment_type,
                },
                candidate_slots=[],
                selected_slot=None,
                booking_reference=appointment_context["booking_reference"],
                escalation_reason=None,
            )
            waiting_outcome = {
                "scenario_id": scenario["id"],
                "scenario_title": scenario["title"],
                "run_id": run_id,
                "mode": run_mode,
                "timestamp_utc": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "input_text": scenario["input_text"],
                "expected": {
                    "action": expected_action,
                    "intent": expected_intent,
                    "state": expected_state,
                },
                "actual": {
                    "action": None,
                    "intent": None,
                    "state": "waiting_for_real_callback",
                    "datetime_candidates": [],
                    "resolved_action": {},
                    "selected_button": None,
                },
                "status": "waiting_for_callback",
                "success": True,
                "correlation_ref": correlation_ref,
                "trace_id": trace_id,
                "journey_id": journey_record.journey_id,
                "address_id": appointment_context["address_id"],
                "appointment_id": appointment_context["appointment_external_id"],
                "booking_reference": appointment_context["booking_reference"],
                "channel": str(appointment_context["output_channel"]).upper(),
                "output_channel_mode": run_mode,
                "selected_address": appointment_context["selected_address"],
                "steps": step_log,
                "errors": [],
            }
            artifacts = self._write_artifacts(waiting_outcome)
            waiting_outcome["artifacts"] = self._artifact_payload(artifacts)
            self.contexts.save_context(
                DemoScenarioContextUpdate(
                    scenario_id=scenario["id"],
                    mode=run_mode,
                    address_id=appointment_context["address_id"],
                    appointment_id=appointment_context["appointment_external_id"],
                    booking_reference=appointment_context["booking_reference"],
                    correlation_ref=correlation_ref,
                    calendar_ref=appointment_context["calendar_ref"],
                    output_channel=appointment_context["output_channel"],
                    current_step="awaiting_real_callback",
                    status="waiting_for_real_callback",
                    latest_protocol_path=str(artifacts.protocol_markdown),
                    latest_demo_log_path=str(artifacts.demo_log_markdown),
                    latest_summary_path=str(artifacts.summary_markdown),
                    latest_run_id=run_id,
                    started_at_utc=now,
                    metadata={
                        "customer_journey_message": {
                            "text": scenario["outbound_text"],
                            "actions": deepcopy(scenario.get("suggestion_buttons") or []),
                            "suggestion_buttons": deepcopy(scenario.get("suggestion_buttons") or []),
                            "slot_options": [],
                            "journey_step_type": scenario.get("journey_step_type"),
                            "available_actions": deepcopy(scenario.get("available_actions") or []),
                            "next_step_map": deepcopy(scenario.get("next_step_map") or {}),
                            "real_channel_payload": deepcopy(scenario.get("real_channel_payload") or {}),
                            "address_id": appointment_context["address_id"],
                            "appointment_id": appointment_context["appointment_external_id"],
                            "correlation_ref": correlation_ref,
                            "phone_number": (appointment_context.get("selected_address") or {}).get("phone"),
                        },
                    },
                )
            )
            return waiting_outcome

        summary = self._build_reply_summary(
            scenario=scenario,
            trace_id=trace_id,
            appointment_context=appointment_context,
        )
        inbound_message = self._store_inbound_reply(
            scenario=scenario,
            trace_id=trace_id,
            journey_id=journey_id,
            appointment_context=appointment_context,
            summary=summary,
        )
        step_log.append(
            self._step_entry(
                step="reply_interpretation",
                status="done",
                detail=f"Inbound reply stored as {inbound_message.message_id}",
                payload={
                    "message_id": inbound_message.message_id,
                    "reply_intent": summary.get("reply_intent"),
                    "normalized_event_type": summary.get("normalized_event_type"),
                    "action_candidate": summary.get("action_candidate"),
                    "resolved_action": summary.get("resolved_action"),
                    "selected_button": summary.get("selected_button"),
                },
            )
        )
        self._publish_step(
            scenario_id=scenario["id"],
            run_id=run_id,
            step_name="reply_interpretation",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=step_log[-1],
        )

        actual_action = (summary.get("resolved_action") or {}).get("action_type") or (summary.get("action_candidate") or {}).get("action_type")
        actual_intent = summary.get("reply_intent")
        actual_state = (summary.get("resolved_action") or {}).get("resolution_state") or summary.get("interpretation_state")
        passed = (
            actual_action == expected_action
            and actual_intent == expected_intent
            and actual_state == expected_state
        )
        result_status = "passed" if passed else "failed"
        outcome = {
            "scenario_id": scenario["id"],
            "scenario_title": scenario["title"],
            "run_id": run_id,
            "mode": run_mode,
            "timestamp_utc": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "input_text": scenario["input_text"],
            "expected": {
                "action": expected_action,
                "intent": expected_intent,
                "state": expected_state,
            },
            "actual": {
                "action": actual_action,
                "intent": actual_intent,
                "state": actual_state,
                "datetime_candidates": list(summary.get("reply_datetime_candidates") or []),
                "resolved_action": summary.get("resolved_action") or {},
                "selected_button": summary.get("selected_button"),
            },
            "status": result_status,
            "success": passed,
            "correlation_ref": correlation_ref,
            "trace_id": trace_id,
            "journey_id": journey_id,
            "address_id": appointment_context["address_id"],
            "appointment_id": appointment_context["appointment_external_id"],
            "booking_reference": appointment_context["booking_reference"],
            "channel": str(appointment_context["output_channel"]).upper(),
            "output_channel_mode": run_mode,
            "selected_address": appointment_context["selected_address"],
            "steps": step_log,
            "errors": [] if passed else [
                {
                    "code": "scenario_assertion_failed",
                    "message": f"Expected {expected_action}/{expected_intent}/{expected_state}, got {actual_action}/{actual_intent}/{actual_state}",
                }
            ],
        }
        artifacts = self._write_artifacts(outcome)
        outcome["artifacts"] = self._artifact_payload(artifacts)
        self.contexts.save_context(
            DemoScenarioContextUpdate(
                scenario_id=scenario["id"],
                mode=run_mode,
                address_id=appointment_context["address_id"],
                appointment_id=appointment_context["appointment_external_id"],
                booking_reference=appointment_context["booking_reference"],
                correlation_ref=correlation_ref,
                calendar_ref=appointment_context["calendar_ref"],
                output_channel=appointment_context["output_channel"],
                current_step="artifacts_written",
                status=result_status,
                latest_protocol_path=str(artifacts.protocol_markdown),
                latest_demo_log_path=str(artifacts.demo_log_markdown),
                latest_summary_path=str(artifacts.summary_markdown),
                latest_run_id=run_id,
                started_at_utc=now,
                finished_at_utc=datetime.now(timezone.utc),
                metadata={
                    "latest_actual_action": actual_action,
                    "latest_actual_intent": actual_intent,
                    "latest_actual_state": actual_state,
                },
            )
        )
        self._publish(
            "DemoProtocolWritten",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=DemoProtocolWritten(
                scenario_id=scenario["id"],
                run_id=run_id,
                protocol_markdown_path=str(artifacts.protocol_markdown),
                protocol_json_path=str(artifacts.protocol_json),
                demo_log_path=str(artifacts.demo_log_markdown),
                summary_path=str(artifacts.summary_markdown),
            ).model_dump(mode="json"),
        )
        self._publish(
            "DemoArtifactWritten",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=DemoArtifactWritten(
                scenario_id=scenario["id"],
                run_id=run_id,
                artifact_kind="protocol_markdown",
                artifact_path=str(artifacts.protocol_markdown),
            ).model_dump(mode="json"),
        )
        if appointment_context["address_id"] and appointment_context["appointment_external_id"]:
            self._publish(
                "AddressAssignedToGeneratedAppointment",
                correlation_id=correlation_ref,
                trace_id=trace_id,
                payload=AddressAssignedToGeneratedAppointment(
                    address_id=appointment_context["address_id"],
                    appointment_external_id=appointment_context["appointment_external_id"],
                    correlation_ref=correlation_ref,
                    calendar_ref=appointment_context["calendar_ref"],
                    booking_reference=appointment_context["booking_reference"],
                ).model_dump(mode="json"),
            )
        self._publish(
            "DemoScenarioCompleted" if passed else "DemoScenarioFailed",
            correlation_id=correlation_ref,
            trace_id=trace_id,
            payload=(
                DemoScenarioCompleted(
                    scenario_id=scenario["id"],
                    run_id=run_id,
                    mode=run_mode,
                    success=passed,
                    action_type=actual_action or "unknown",
                    interpretation_state=actual_state or "review",
                    artifact_directory=str(ARTIFACT_ROOT),
                ).model_dump(mode="json")
                if passed
                else DemoScenarioFailed(
                    scenario_id=scenario["id"],
                    run_id=run_id,
                    mode=run_mode,
                    error_code="scenario_assertion_failed",
                    error_message=outcome["errors"][0]["message"],
                    artifact_directory=str(ARTIFACT_ROOT),
                ).model_dump(mode="json")
            ),
        )
        return outcome

    def latest_artifacts(self) -> dict[str, Any]:
        latest = self._latest_artifacts()
        if latest is None:
            return {
                "version": "v1.3.9-patch9",
                "artifact_directory": str(ARTIFACT_ROOT),
                "available": False,
            }
        protocol_json = json.loads(latest.protocol_json.read_text(encoding="utf-8"))
        return {
            "version": "v1.3.9-patch9",
            "artifact_directory": str(ARTIFACT_ROOT),
            "available": True,
            "scenario_id": protocol_json["scenario_id"],
            "scenario_title": protocol_json["scenario_title"],
            "mode": protocol_json["mode"],
            "status": protocol_json["status"],
            "timestamp_utc": protocol_json["timestamp_utc"],
            "trace_id": protocol_json["trace_id"],
            "correlation_ref": protocol_json["correlation_ref"],
            "artifacts": self._artifact_payload(latest),
        }

    def latest_artifact_text(self, kind: str) -> PlainTextResponse:
        latest = self._latest_artifacts()
        if latest is None:
            return PlainTextResponse("No scenario artifacts available yet.", status_code=404)
        path_map = {
            "protocol": latest.protocol_markdown,
            "demo-log": latest.demo_log_markdown,
            "summary": latest.summary_markdown,
            "protocol-json": latest.protocol_json,
        }
        target = path_map.get(kind)
        if target is None:
            return PlainTextResponse("Unknown artifact kind.", status_code=404)
        media_type = "application/json" if target.suffix == ".json" else "text/markdown"
        return PlainTextResponse(target.read_text(encoding="utf-8"), media_type=media_type)

    def _create_outbound_prompt(
        self,
        *,
        scenario: dict[str, Any],
        run_mode: str,
        trace_id: str,
        correlation_ref: str,
        journey_id: str,
        appointment_context: dict[str, str],
    ):
        suggestion_buttons = deepcopy(scenario.get("suggestion_buttons") or [])
        message_actions = [
            {
                "action_id": item["action_id"],
                "label": item["label"],
                "value": item["value"],
                "action_type": item.get("action_type", "reply"),
            }
            for item in suggestion_buttons
        ]
        real_channel_payload = deepcopy(scenario.get("real_channel_payload") or {})
        selected_address = appointment_context.get("selected_address") or {}
        target_phone = selected_address.get("phone") or "491705707716"
        output_channel = str(appointment_context.get("output_channel") or "rcs_sms").lower()
        provider_channel = "RCS" if output_channel == "rcs_sms" else output_channel.upper()
        if run_mode == "real":
            return self.reply_service.send_message(
                channel=provider_channel,
                tenant_id="demo",
                correlation_id=correlation_ref,
                phone_number=target_phone,
                body=scenario["outbound_text"],
                journey_id=journey_id,
                booking_reference=appointment_context["booking_reference"],
                message_type="reminder",
                actions=message_actions,
                metadata={
                    "scenario_id": scenario["id"],
                    "scenario_mode": run_mode,
                    "trace_id": trace_id,
                    "artifact_directory": str(ARTIFACT_ROOT),
                    "available_actions": deepcopy(scenario.get("available_actions") or []),
                    "journey_step_type": scenario.get("journey_step_type"),
                },
            )
        outbound = self.reply_service._build_normalized_message(
            message_id=f"msg-out-{uuid4().hex[:12]}",
            provider_message_id=f"scenario-out-{uuid4().hex[:10]}",
            provider_job_id=f"scenario-job-{uuid4().hex[:8]}",
            channel=provider_channel,
            direction="outbound",
            status="simulated",
            customer_id=None,
            contact_reference=None,
            phone_number=target_phone,
            address_id=appointment_context["address_id"],
            appointment_id=appointment_context["appointment_external_id"],
            correlation_ref=appointment_context["correlation_ref"],
            journey_id=journey_id,
            booking_reference=appointment_context["booking_reference"],
            message_type="reminder",
            body=scenario["outbound_text"],
            actions=message_actions,
            metadata={
                "scenario_id": scenario["id"],
                "scenario_mode": run_mode,
                "trace_id": trace_id,
                "artifact_directory": str(ARTIFACT_ROOT),
                "available_actions": deepcopy(scenario.get("available_actions") or []),
                "journey_step_type": scenario.get("journey_step_type"),
            },
            provider_payload={
                "kind": "simulation_outbound",
                "body": scenario["outbound_text"],
                "real_channel_payload": real_channel_payload,
                "suggestion_buttons": suggestion_buttons,
            },
        )
        self.reply_service._store_message(outbound)
        return outbound

    def _build_reply_summary(
        self,
        *,
        scenario: dict[str, Any],
        trace_id: str,
        appointment_context: dict[str, str],
    ) -> dict[str, Any]:
        reply_info = self.reply_service.reply_engine.analyze_reply(scenario["input_text"])
        summary = {
            "parsed_content_json": {"text": scenario["input_text"], "channel": "RCS"},
            "normalized_event_type": reply_info["normalized_event_type"],
            "reply_intent": reply_info["reply_intent"],
            "reply_datetime_candidates": reply_info["reply_datetime_candidates"],
            "action_candidate": deepcopy(reply_info.get("action_candidate") or {}),
            "interpretation_state": str((reply_info.get("action_candidate") or {}).get("interpretation_state") or "review"),
            "interpretation_confidence": float((reply_info.get("action_candidate") or {}).get("interpretation_confidence") or 0.0),
            "channel": "RCS",
            "from": "customer-demo",
            "to": (appointment_context.get("selected_address") or {}).get("phone") or "491705707716",
            "provider_message_id": f"reply-{uuid4().hex[:10]}",
            "provider_user_id": "demo-user",
            "status": "received",
            "body_text": scenario["input_text"],
            "provider_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "address_id": appointment_context["address_id"],
            "appointment_id": appointment_context["appointment_external_id"],
            "correlation_ref": appointment_context["correlation_ref"],
            "selected_button": scenario["input_text"],
        }
        summary["resolved_action"] = self.reply_service._resolve_action_candidate(summary)
        return summary

    def _store_inbound_reply(
        self,
        *,
        scenario: dict[str, Any],
        trace_id: str,
        journey_id: str,
        appointment_context: dict[str, str],
        summary: dict[str, Any],
    ):
        message = self.reply_service._build_normalized_message(
            message_id=f"msg-in-{uuid4().hex[:12]}",
            provider_message_id=summary["provider_message_id"],
            provider_job_id=None,
            channel="RCS" if str(appointment_context.get("output_channel") or "rcs_sms").lower() == "rcs_sms" else str(appointment_context.get("output_channel") or "rcs_sms").upper(),
            direction="inbound",
            status=str(summary["status"]),
            customer_id=None,
            contact_reference=None,
            phone_number=(appointment_context.get("selected_address") or {}).get("phone") or "491705707716",
            address_id=appointment_context["address_id"],
            appointment_id=appointment_context["appointment_external_id"],
            correlation_ref=appointment_context["correlation_ref"],
            journey_id=journey_id,
            booking_reference=appointment_context["booking_reference"],
            message_type="reply",
            body=scenario["input_text"],
            actions=[],
            metadata={
                "scenario_id": scenario["id"],
                "trace_id": trace_id,
                "normalized_event_type": summary["normalized_event_type"],
                "reply_intent": summary["reply_intent"],
                "reply_datetime_candidates": summary["reply_datetime_candidates"],
                "interpretation_state": summary["interpretation_state"],
                "interpretation_confidence": summary["interpretation_confidence"],
                "action_candidate": deepcopy(summary["action_candidate"]),
                "action_type": (summary["action_candidate"] or {}).get("action_type"),
                "resolved_action": deepcopy(summary["resolved_action"]),
                "artifact_directory": str(ARTIFACT_ROOT),
            },
            provider_payload={
                "kind": "scenario_reply",
                "input_text": scenario["input_text"],
            },
        )
        self.reply_service._store_message(message)
        self.reply_service._publish_reply_events(message_id=message.message_id, trace_id=trace_id, summary=summary)
        return message

    def _write_artifacts(self, outcome: dict[str, Any]) -> ScenarioArtifacts:
        ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        timestamp = outcome["timestamp_utc"].replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")
        base_name = f"{timestamp}_{outcome['scenario_id']}_{outcome['mode']}"
        protocol_md = ARTIFACT_ROOT / f"scenario_test_protocol_{base_name}.md"
        protocol_json = ARTIFACT_ROOT / f"scenario_test_protocol_{base_name}.json"
        demo_log_md = ARTIFACT_ROOT / f"demo_execution_log_{base_name}.md"
        summary_md = ARTIFACT_ROOT / f"demo_execution_summary_{base_name}.md"

        protocol_json.write_text(json.dumps(outcome, indent=2, ensure_ascii=True), encoding="utf-8")
        protocol_md.write_text(self._protocol_markdown(outcome), encoding="utf-8")
        demo_log_md.write_text(self._demo_log_markdown(outcome), encoding="utf-8")
        summary_md.write_text(self._summary_markdown(outcome), encoding="utf-8")
        return ScenarioArtifacts(
            protocol_markdown=protocol_md,
            protocol_json=protocol_json,
            demo_log_markdown=demo_log_md,
            summary_markdown=summary_md,
        )

    def _latest_artifacts(self) -> ScenarioArtifacts | None:
        if not ARTIFACT_ROOT.exists():
            return None
        protocol_files = sorted(ARTIFACT_ROOT.glob("scenario_test_protocol_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not protocol_files:
            return None
        latest_json = protocol_files[0]
        stem_suffix = latest_json.name.replace("scenario_test_protocol_", "").replace(".json", "")
        protocol_md = ARTIFACT_ROOT / f"scenario_test_protocol_{stem_suffix}.md"
        demo_log_md = ARTIFACT_ROOT / f"demo_execution_log_{stem_suffix}.md"
        summary_md = ARTIFACT_ROOT / f"demo_execution_summary_{stem_suffix}.md"
        return ScenarioArtifacts(
            protocol_markdown=protocol_md,
            protocol_json=latest_json,
            demo_log_markdown=demo_log_md,
            summary_markdown=summary_md,
        )

    def _artifact_payload(self, artifacts: ScenarioArtifacts) -> dict[str, str]:
        return {
            "protocol_markdown": str(artifacts.protocol_markdown),
            "protocol_json": str(artifacts.protocol_json),
            "demo_log_markdown": str(artifacts.demo_log_markdown),
            "summary_markdown": str(artifacts.summary_markdown),
        }

    def _step_entry(self, *, step: str, status: str, detail: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "step": step,
            "status": status,
            "detail": detail,
            "payload": payload,
        }

    def _publish_step(
        self,
        *,
        scenario_id: str,
        run_id: str,
        step_name: str,
        correlation_id: str,
        trace_id: str,
        payload: dict[str, Any],
    ) -> None:
        self._publish(
            "DemoScenarioStepUpdated",
            correlation_id=correlation_id,
            trace_id=trace_id,
            payload=DemoScenarioStepUpdated(
                scenario_id=scenario_id,
                run_id=run_id,
                step_name=step_name,
                detail=payload["detail"],
                payload=payload["payload"],
            ).model_dump(mode="json"),
        )

    def _publish(self, event_type: str, *, correlation_id: str, trace_id: str, payload: dict[str, Any]) -> None:
        event_bus.publish(
            EventEnvelope(
                event_type=event_type,
                correlation_id=correlation_id,
                tenant_id="demo",
                trace_id=trace_id,
                payload=payload,
            )
        )

    def _protocol_markdown(self, outcome: dict[str, Any]) -> str:
        return f"""# Scenario Test Protocol

- Timestamp: `{outcome['timestamp_utc']}`
- Scenario: `{outcome['scenario_title']}` (`{outcome['scenario_id']}`)
- Mode: `{outcome['mode']}`
- Status: `{outcome['status']}`
- Correlation Ref: `{outcome['correlation_ref']}`
- Trace ID: `{outcome['trace_id']}`
- Journey ID: `{outcome['journey_id']}`
- Address ID: `{outcome['address_id']}`
- Appointment ID: `{outcome['appointment_id']}`
- Booking Reference: `{outcome['booking_reference']}`

## Input

`{outcome['input_text']}`

## Expected

- Action: `{outcome['expected']['action']}`
- Intent: `{outcome['expected']['intent']}`
- Interpretation State: `{outcome['expected']['state']}`

## Actual

- Action: `{outcome['actual']['action']}`
- Intent: `{outcome['actual']['intent']}`
- Interpretation State: `{outcome['actual']['state']}`
- Date/Time Candidates: `{", ".join(outcome['actual']['datetime_candidates']) or "-"}`

## Steps

```json
{json.dumps(outcome['steps'], indent=2)}
```

## Errors

```json
{json.dumps(outcome['errors'], indent=2)}
```
"""

    def _demo_log_markdown(self, outcome: dict[str, Any]) -> str:
        return f"""# Demo Execution Log

The scenario `{outcome['scenario_id']}` ran in `{outcome['mode']}` mode.

## Step Trace

```json
{json.dumps(outcome['steps'], indent=2)}
```

## Actual Result

```json
{json.dumps(outcome['actual'], indent=2)}
```
"""

    def _summary_markdown(self, outcome: dict[str, Any]) -> str:
        verdict = "PASS" if outcome["success"] else "FAIL"
        return f"""# Demo Execution Summary

- Verdict: `{verdict}`
- Scenario: `{outcome['scenario_title']}`
- Mode: `{outcome['mode']}`
- Expected Action: `{outcome['expected']['action']}`
- Actual Action: `{outcome['actual']['action']}`
- Expected State: `{outcome['expected']['state']}`
- Actual State: `{outcome['actual']['state']}`
- Artifact Directory: `{ARTIFACT_ROOT}`
"""
