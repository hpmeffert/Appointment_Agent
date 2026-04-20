from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from appointment_agent_shared.commands import ReminderActionCommand
from appointment_agent_shared.config import settings
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.events import (
    AppointmentActionExecutionRequested,
    AppointmentActionRequested,
    AppointmentActionResolved,
    AppointmentActionReviewRequired,
    CommunicationReplyNormalized,
    ReminderInteractionObserved,
)
from appointment_agent_shared.repositories import AddressRepository, BookingRepository, CallbackRepository, JourneyRepository, LekabConfigRepository, MessageRepository
from appointment_agent_shared.shared_settings_store import SharedSettingsStoreService

from appointment_orchestrator.v1_0_1.appointment_orchestrator.service import AppointmentOrchestratorServiceV101
from demo_monitoring_ui.v1_3_9.demo_monitoring_ui.scenario_catalog import DATE_BUTTONS, INITIAL_BUTTONS, RELATIVE_BUTTONS, TIME_BUTTONS
from demo_monitoring_ui.v1_3_9.demo_monitoring_ui.scenario_context import DemoScenarioContextService, DemoScenarioContextUpdate
from google_adapter.v1_1_0_patch8a.google_adapter.service import (
    GoogleAvailabilitySlotsRequest,
    GoogleBookingCreateRequest,
    GoogleBookingRescheduleRequest,
)
from google_adapter.v1_3_6.google_adapter.service import GoogleAdapterServiceV136
from lekab_adapter.v1_2_1_patch4.lekab_adapter.service import LekabMessagingSettingsService

from .reply_engine import ReplyToActionEngine


class LekabReplyActionService(LekabMessagingSettingsService):
    """v1.3.8 adds a bus-safe reply interpretation layer on top of patch4.

    Patch4 already offered settings, provider test calls, callback fetching,
    and basic message history. This release turns inbound replies into stable
    action candidates and emits internal events without directly coupling UI
    callbacks to business side effects.
    """

    def __init__(self, session: Session, *, mock_mode: bool = True) -> None:
        super().__init__(session, mock_mode=mock_mode)
        self.session = session
        self.configs = _VersionedLekabConfigRepository(LekabConfigRepository(session), "rcs_settings_v1_3_8")
        self.reply_engine = ReplyToActionEngine()
        self.callback_receipts = CallbackRepository(session)
        self.journeys = JourneyRepository(session)
        self.messages = MessageRepository(session)
        self.bookings = BookingRepository(session)
        self.addresses = AddressRepository(session)
        self.shared_settings = SharedSettingsStoreService(session)
        self.contexts = DemoScenarioContextService(session)
        self.orchestrator = AppointmentOrchestratorServiceV101(session)
        self.google = GoogleAdapterServiceV136(session)

    def _with_version(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload["version"] = "v1.3.8"
        return payload

    def get_rcs_settings(self, *, trace_id: str | None = None) -> dict[str, Any]:
        return self._with_version(super().get_rcs_settings(trace_id=trace_id))

    def save_rcs_settings(self, payload: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        return self._with_version(super().save_rcs_settings(payload, trace_id=trace_id))

    def fetch_latest_callback(self, *, trace_id: str | None = None) -> dict[str, Any]:
        result = self._with_version(super().fetch_latest_callback(trace_id=trace_id))
        summary = self._summarize_webhook_callback(result.get("response_json"))
        linkage = self.address_linkage.resolve(
            tenant_id="default",
            booking_reference=(summary.get("action_candidate") or {}).get("parameters", {}).get("booking_reference"),
            appointment_id=(summary.get("action_candidate") or {}).get("parameters", {}).get("appointment_id"),
            correlation_ref=(summary.get("action_candidate") or {}).get("parameters", {}).get("correlation_ref"),
            phone_number=self._resolve_customer_phone(summary),
        )
        result["action_candidate"] = deepcopy(summary.get("action_candidate") or {})
        result["interpretation_state"] = summary.get("interpretation_state")
        result["interpretation_confidence"] = summary.get("interpretation_confidence")
        result["address_id"] = linkage.address_id
        result["appointment_id"] = linkage.appointment_id
        result["correlation_ref"] = linkage.correlation_ref
        summary["address_id"] = linkage.address_id
        summary["appointment_id"] = linkage.appointment_id
        summary["correlation_ref"] = linkage.correlation_ref
        result["resolved_action"] = self._resolve_action_candidate(summary)
        callback_payload = self._build_callback_payload_from_fetch_result(
            result=result,
            summary=summary,
            linkage=linkage,
        )
        if callback_payload is not None:
            result["real_callback_bridge"] = self.process_provider_callback(
                callback_payload,
                trace_id=trace_id,
                headers={"x-source": "webhook-fetch-bridge"},
                remote_ip="webhook.site",
            )
        processed_callbacks = self._process_unseen_webhook_callbacks(
            fetch_result=result,
            trace_id=trace_id,
        )
        if processed_callbacks:
            result["processed_callbacks"] = processed_callbacks
            last_processed = processed_callbacks[-1]
            result["response_json"] = deepcopy(last_processed["raw_callback_payload"])
            result["normalized_event_type"] = last_processed["normalized_event_type"]
            result["reply_intent"] = last_processed["reply_intent"]
            result["reply_datetime_candidates"] = deepcopy(last_processed["reply_datetime_candidates"])
            result["callback_transport"] = last_processed["callback_transport"]
            result["callback_source_method"] = last_processed["callback_source_method"]
            result["real_callback_bridge"] = deepcopy(last_processed["bridge_result"])
        return result

    def _process_unseen_webhook_callbacks(
        self,
        *,
        fetch_result: dict[str, Any],
        trace_id: str | None,
    ) -> list[dict[str, Any]]:
        raw_feed = fetch_result.get("raw_fetch_response_json")
        request_items: list[dict[str, Any]] = []
        if isinstance(raw_feed, dict):
            for key in ("data", "requests"):
                items = raw_feed.get(key)
                if isinstance(items, list):
                    request_items = [item for item in items if isinstance(item, dict)]
                    break
        elif isinstance(raw_feed, list):
            request_items = [item for item in raw_feed if isinstance(item, dict)]
        if not request_items:
            return []

        def _sort_key(item: dict[str, Any]) -> tuple[int, str]:
            sorting = int(item.get("sorting") or 0)
            created = str(item.get("created_at") or "")
            return (sorting, created)

        processed: list[dict[str, Any]] = []
        for item in sorted(request_items, key=_sort_key):
            event_id = str(item.get("uuid") or "")
            if not event_id or self.callback_receipts.exists(event_id):
                continue
            summary = self._summarize_webhook_callback(item)
            if summary.get("normalized_event_type") != "message.reply_received":
                continue
            linkage = self.address_linkage.resolve(
                tenant_id="default",
                booking_reference=(summary.get("action_candidate") or {}).get("parameters", {}).get("booking_reference"),
                appointment_id=(summary.get("action_candidate") or {}).get("parameters", {}).get("appointment_id"),
                correlation_ref=(summary.get("action_candidate") or {}).get("parameters", {}).get("correlation_ref"),
                phone_number=self._resolve_customer_phone(summary),
            )
            callback_payload = self._build_callback_payload_from_fetch_result(
                result={"success": True, "response_json": item},
                summary=summary,
                linkage=linkage,
            )
            if callback_payload is None:
                continue
            bridge_result = self.process_provider_callback(
                callback_payload,
                trace_id=trace_id,
                headers={"x-source": "webhook-fetch-bridge"},
                remote_ip="webhook.site",
            )
            processed.append(
                {
                    "event_id": event_id,
                    "raw_callback_payload": deepcopy(item),
                    "normalized_event_type": summary.get("normalized_event_type"),
                    "reply_intent": summary.get("reply_intent"),
                    "reply_datetime_candidates": deepcopy(summary.get("reply_datetime_candidates") or []),
                    "callback_transport": summary.get("callback_transport"),
                    "callback_source_method": summary.get("callback_source_method"),
                    "bridge_result": deepcopy(bridge_result),
                    "callback_payload": deepcopy(callback_payload),
                }
            )
        return processed

    def _resolve_customer_phone(self, summary: dict[str, Any]) -> str | None:
        for key in ("from", "to"):
            candidate = str(summary.get(key) or "").strip()
            if candidate and candidate != "None" and any(character.isdigit() for character in candidate):
                return candidate
        for key in ("from", "to"):
            candidate = str(summary.get(key) or "").strip()
            if candidate and candidate != "None":
                return candidate
        return None

    def _should_invoke_orchestrator_for_action(self, resolved_action: str | None) -> bool:
        return resolved_action in {"keep", "reschedule", "cancel", "call_me"}

    def _button_label(self, button_source: list[dict[str, Any]], value: str) -> str:
        for item in button_source:
            if str(item.get("value")) == value:
                return str(item.get("label_en") or item.get("label") or value)
        return value

    def _date_token_to_datetime(self, token: str) -> datetime | None:
        mapping = {
            "date_05_may": (5, 5),
            "date_06_may": (5, 6),
            "date_08_may": (5, 8),
            "date_12_may": (5, 12),
        }
        resolved = mapping.get(str(token or "").strip().lower())
        if resolved is None:
            return None
        month, day = resolved
        return datetime(year=2026, month=month, day=day, hour=0, minute=0)

    def _time_token_to_parts(self, token: str) -> tuple[int, int] | None:
        mapping = {
            "time_0900": (9, 0),
            "time_1130": (11, 30),
            "time_1600": (16, 0),
            "time_1830": (18, 30),
        }
        return mapping.get(str(token or "").strip().lower())

    def _is_dynamic_date_token(self, token: str | None) -> bool:
        return str(token or "").strip().lower().startswith("date_20")

    def _is_dynamic_time_token(self, token: str | None) -> bool:
        return str(token or "").strip().lower().startswith("time_20")

    def _parse_dynamic_date_token(self, token: str | None) -> date | None:
        raw = str(token or "").strip()
        if not self._is_dynamic_date_token(raw):
            return None
        try:
            return date.fromisoformat(raw.split("_", 1)[1])
        except ValueError:
            return None

    def _parse_dynamic_time_token(self, token: str | None) -> datetime | None:
        raw = str(token or "").strip()
        if not self._is_dynamic_time_token(raw):
            return None
        try:
            return datetime.fromisoformat(raw.split("_", 1)[1])
        except ValueError:
            return None

    def _display_timezone(self):
        timezone_name = self._runtime_timezone_name()
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return datetime.now(timezone.utc).astimezone().tzinfo or timezone.utc

    def _runtime_timezone_name(self, normalized: dict[str, Any] | None = None) -> str:
        context = self.contexts.get_context()
        context_address = context.selected_address or {}
        address_id = (
            (normalized or {}).get("address_id")
            or context.address_id
            or context_address.get("address_id")
        )
        selected_address = self.addresses.get(address_id) if address_id else None
        candidate = (
            self._address_value(selected_address, "timezone")
            or self._address_value(context_address, "timezone")
            or settings.google_default_timezone
        )
        return str(candidate or settings.google_default_timezone)

    def _format_date_label(self, value: date) -> str:
        return value.strftime("%d %b")

    def _format_time_label(self, value: datetime) -> str:
        return value.astimezone(self._display_timezone()).strftime("%H:%M")

    def _build_pending_slot(self, *, date_token: str | None, time_token: str | None) -> dict[str, Any] | None:
        dynamic_date = self._parse_dynamic_date_token(date_token)
        dynamic_time = self._parse_dynamic_time_token(time_token)
        if dynamic_date is not None and dynamic_time is not None:
            local_start = dynamic_time.astimezone(self._display_timezone())
            local_end = local_start + timedelta(minutes=settings.default_duration_minutes)
            date_label = self._format_date_label(dynamic_date)
            time_label = self._format_time_label(local_start)
            return {
                "slot_id": f"{date_token}_{time_token}",
                "date_token": date_token,
                "time_token": time_token,
                "date_label": date_label,
                "time_label": time_label,
                "label": f"{date_label}, {time_label}",
                "start": dynamic_time.isoformat(),
                "end": local_end.isoformat(),
            }
        base_date = self._date_token_to_datetime(date_token or "")
        time_parts = self._time_token_to_parts(time_token or "")
        if base_date is None or time_parts is None:
            return None
        start_time = base_date.replace(hour=time_parts[0], minute=time_parts[1])
        end_time = start_time + timedelta(minutes=settings.default_duration_minutes)
        date_label = self._button_label(DATE_BUTTONS, str(date_token or ""))
        time_label = self._button_label(TIME_BUTTONS, str(time_token or ""))
        return {
            "slot_id": f"{date_token}_{time_token}",
            "date_token": date_token,
            "time_token": time_token,
            "date_label": date_label,
            "time_label": time_label,
            "label": f"{date_label}, {time_label}",
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
        }

    def _date_range_for_relative_action(self, action: str) -> tuple[date, date]:
        today = datetime.now(self._display_timezone()).date()
        weekday = today.weekday()
        start_of_week = today - timedelta(days=weekday)
        if action == "this_week":
            start = today
            end = start_of_week + timedelta(days=6)
        elif action == "next_week":
            start = start_of_week + timedelta(days=7)
            end = start + timedelta(days=6)
        elif action == "this_month":
            start = today
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = next_month - timedelta(days=1)
        elif action == "next_month":
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            following_month = (next_month.replace(day=28) + timedelta(days=4)).replace(day=1)
            start = next_month
            end = following_month - timedelta(days=1)
        else:
            start = today
            end = today + timedelta(days=14)
        return start, end

    def _slot_button(
        self,
        *,
        label: str,
        value: str,
        canonical_action: str = "appointment.slot_selected",
        selection_kind: str,
        journey_target: str | None = None,
    ) -> dict[str, Any]:
        return {
            "action_id": value,
            "label_en": label,
            "label_de": label,
            "value": value,
            "action_type": "reply",
            "canonical_action": canonical_action,
            "selection_kind": selection_kind,
            "journey_target": journey_target,
        }

    def _load_dynamic_slots_for_range(self, *, from_date_value: date, to_date_value: date, appointment_type: str) -> list[dict[str, Any]]:
        mode = self._google_mode()
        result = self.google.get_available_slots_patch8(
            GoogleAvailabilitySlotsRequest(
                mode=mode,
                from_date=from_date_value,
                to_date=to_date_value,
                max_slots=10,
                duration_minutes=settings.default_duration_minutes,
                appointment_type=appointment_type,
                timezone=self._runtime_timezone_name(),
            )
        )
        return [slot for slot in result.slots if isinstance(slot, dict)]

    def _load_dynamic_slots(self, *, relative_action: str, appointment_type: str) -> list[dict[str, Any]]:
        from_date_value, to_date_value = self._date_range_for_relative_action(relative_action)
        return self._load_dynamic_slots_for_range(
            from_date_value=from_date_value,
            to_date_value=to_date_value,
            appointment_type=appointment_type,
        )

    def _date_buttons_from_slots(self, slots: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for slot in slots:
            try:
                start_value = datetime.fromisoformat(str(slot.get("start")))
            except ValueError:
                continue
            local_start = start_value.astimezone(self._display_timezone())
            date_key = local_start.date().isoformat()
            grouped.setdefault(date_key, []).append(slot)
        buttons: list[dict[str, Any]] = []
        for date_key in sorted(grouped.keys()):
            buttons.append(
                self._slot_button(
                    label=self._format_date_label(date.fromisoformat(date_key)),
                    value=f"date_{date_key}",
                    selection_kind="date",
                    journey_target="time_choice",
                )
            )
        return buttons, grouped

    def _time_buttons_for_date(self, grouped_slots: dict[str, list[dict[str, Any]]], date_token: str | None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        date_value = self._parse_dynamic_date_token(date_token)
        if date_value is None:
            return [], {}
        slots = grouped_slots.get(date_value.isoformat(), [])
        buttons: list[dict[str, Any]] = []
        slot_map: dict[str, dict[str, Any]] = {}
        for slot in slots:
            try:
                start_value = datetime.fromisoformat(str(slot.get("start")))
            except ValueError:
                continue
            token = f"time_{start_value.isoformat()}"
            buttons.append(
                self._slot_button(
                    label=self._format_time_label(start_value),
                    value=token,
                    selection_kind="time",
                )
            )
            slot_map[token] = deepcopy(slot)
        return buttons, slot_map

    def _google_mode(self) -> str:
        try:
            status = self.google.get_mode_status("test")
        except Exception:
            return "simulation"
        return "test" if getattr(status, "live_calendar_writes", False) else "simulation"

    def _address_value(self, address: Any, key: str) -> str | None:
        if address is None:
            return None
        if isinstance(address, dict):
            value = address.get(key)
        else:
            value = getattr(address, key, None)
        text = str(value or "").strip()
        return text or None

    def _compose_address_details(self, address: Any, fallback_name: str) -> str:
        lines: list[str] = []
        display_name = self._address_value(address, "display_name") or fallback_name
        if display_name:
            lines.append(display_name)

        street = self._address_value(address, "street")
        house_number = self._address_value(address, "house_number")
        street_line = " ".join(part for part in [street, house_number] if part)
        if street_line:
            lines.append(street_line)

        postal_code = self._address_value(address, "postal_code")
        city = self._address_value(address, "city")
        city_line = " ".join(part for part in [postal_code, city] if part)
        if city_line:
            lines.append(city_line)

        country = self._address_value(address, "country")
        if country:
            lines.append(country)

        return " | ".join(lines) if lines else fallback_name

    def _resolve_runtime_linkage(self, *, journey: Any, normalized: dict[str, Any]) -> dict[str, Any]:
        context = self.contexts.get_context()
        context_address = context.selected_address or {}
        address_id = (
            normalized.get("address_id")
            or context.address_id
            or context_address.get("address_id")
        )
        correlation_ref = (
            normalized.get("correlation_ref")
            or normalized.get("correlation_id")
            or context.correlation_ref
            or context_address.get("correlation_ref")
        )
        appointment_id = (
            normalized.get("appointment_id")
            or context.appointment_id
        )
        booking_reference = (
            normalized.get("booking_reference")
            or getattr(journey, "booking_reference", None)
            or context.booking_reference
        )
        selected_address = self.addresses.get(address_id) if address_id else None
        if selected_address is None and context_address:
            selected_address = context_address
        customer_name = (
            self._address_value(selected_address, "display_name")
            or self._address_value(selected_address, "company_name")
            or self._address_value(selected_address, "first_name")
            or self._address_value(context_address, "display_name")
            or self._address_value(context_address, "company_name")
            or "Demo Customer"
        )
        customer_mobile = self._address_value(selected_address, "phone") or self._address_value(context_address, "phone")
        customer_email = self._address_value(selected_address, "email") or self._address_value(context_address, "email")
        linked_contact_reference_id = (
            self._address_value(selected_address, "contact_reference_id")
            or self._address_value(selected_address, "external_ref")
            or self._address_value(context_address, "external_ref")
            or address_id
        )
        linked_address_full_details = self._compose_address_details(selected_address or context_address, customer_name)
        timezone_name = (
            self._address_value(selected_address, "timezone")
            or self._address_value(context_address, "timezone")
            or settings.google_default_timezone
        )
        return {
            "address_id": address_id,
            "correlation_ref": correlation_ref,
            "appointment_id": appointment_id,
            "booking_reference": booking_reference,
            "selected_address": selected_address,
            "customer_name": customer_name,
            "customer_mobile": customer_mobile,
            "customer_email": customer_email,
            "linked_contact_reference_id": linked_contact_reference_id,
            "linked_address_full_details": linked_address_full_details,
            "timezone": str(timezone_name),
        }

    def _commit_selected_slot(self, *, journey: Any, normalized: dict[str, Any], pending_slot: dict[str, Any]) -> dict[str, Any]:
        linkage = self._resolve_runtime_linkage(journey=journey, normalized=normalized)
        appointment_type = str(self.contexts.get_context().appointment_type or "dentist")
        start_time = datetime.fromisoformat(str(pending_slot["start"]))
        end_time = datetime.fromisoformat(str(pending_slot["end"]))
        mode = self._google_mode()
        existing_booking = self.bookings.get(journey.booking_reference) if journey.booking_reference else None
        if existing_booking is not None:
            return self.google.reschedule_booking_patch8(
                GoogleBookingRescheduleRequest(
                    mode=mode,
                    booking_reference=linkage["booking_reference"],
                    provider_reference=existing_booking.external_id,
                    slot_id=str(pending_slot["slot_id"]),
                    start_time=start_time,
                    end_time=end_time,
                    label=str(pending_slot["label"]),
                    appointment_type=appointment_type,
                    correlation_id=linkage["correlation_ref"],
                    appointment_id=linkage["appointment_id"],
                    address_id=linkage["address_id"],
                    linked_contact_reference_id=linkage["linked_contact_reference_id"],
                    linked_address_full_details=linkage["linked_address_full_details"],
                    customer_name=linkage["customer_name"],
                    customer_email=linkage["customer_email"],
                    customer_mobile=linkage["customer_mobile"],
                    context_label="Rescheduled appointment confirmed",
                    timezone=linkage["timezone"],
                )
            ).model_dump(mode="json")
        return self.google.create_booking_patch8(
            GoogleBookingCreateRequest(
                mode=mode,
                slot_id=str(pending_slot["slot_id"]),
                start_time=start_time,
                end_time=end_time,
                label=str(pending_slot["label"]),
                appointment_type=appointment_type,
                customer_name=linkage["customer_name"],
                customer_email=linkage["customer_email"],
                customer_mobile=linkage["customer_mobile"],
                booking_reference=linkage["booking_reference"],
                correlation_id=linkage["correlation_ref"],
                appointment_id=linkage["appointment_id"],
                address_id=linkage["address_id"],
                linked_contact_reference_id=linkage["linked_contact_reference_id"],
                linked_address_full_details=linkage["linked_address_full_details"],
                context_label="Rescheduled appointment confirmed",
                timezone=linkage["timezone"],
            )
        ).model_dump(mode="json")

    def test_rcs_connection(self, *, trace_id: str | None = None) -> dict[str, Any]:
        result = super().test_rcs_connection(trace_id=trace_id)
        result["version"] = "v1.3.8"
        return result

    def process_provider_callback(
        self,
        payload: dict[str, Any],
        *,
        trace_id: str | None = None,
        headers: dict[str, Any] | None = None,
        remote_ip: str | None = None,
    ) -> dict[str, Any]:
        callback_trace_id = trace_id or f"lekab-callback-{uuid4().hex[:16]}"
        event_id = self._callback_event_id(payload)
        if self.callback_receipts.exists(event_id):
            self.shared_settings.merge_namespace(
                "lekab",
                {},
                status_values={
                    "last_real_callback": {
                        "event_id": event_id,
                        "trace_id": callback_trace_id,
                        "duplicate": True,
                    }
                },
            )
            return {"accepted": True, "duplicate": True, "event_id": event_id, "trace_id": callback_trace_id}

        normalized = self._normalize_real_callback_payload(payload)
        correlation_ref = normalized["correlation_ref"]
        self.callback_receipts.record(
            event_id=event_id,
            event_type=normalized["event_type"],
            correlation_id=correlation_ref,
            payload={
                "raw_payload": deepcopy(payload),
                "headers": deepcopy(headers or {}),
                "remote_ip": remote_ip,
                "normalized": deepcopy(normalized),
            },
            is_duplicate=False,
        )

        resolved_action = normalized.get("resolved_action")
        orchestrator_result = None
        orchestrator_error = None
        google_booking_result = None
        journey = self.journeys.get_by_correlation_id(correlation_ref) if correlation_ref else None
        current_context = self.contexts.get_context()
        current_metadata = deepcopy(current_context.metadata or {})
        pending_slot = deepcopy(current_metadata.get("pending_slot") or {})
        dynamic_grouped_slots = deepcopy(current_metadata.get("dynamic_grouped_slots") or {})
        dynamic_slot_map = deepcopy(current_metadata.get("dynamic_slot_map") or {})
        if resolved_action in {"date_05_may", "date_06_may", "date_08_may", "date_12_may"} or self._is_dynamic_date_token(resolved_action):
            date_label = self._button_label(DATE_BUTTONS, normalized.get("incoming_data") or "")
            if self._is_dynamic_date_token(resolved_action):
                parsed_date = self._parse_dynamic_date_token(normalized.get("incoming_data"))
                date_label = self._format_date_label(parsed_date) if parsed_date is not None else str(
                    normalized.get("reply_label") or normalized.get("incoming_data") or ""
                )
            pending_slot.update(
                {
                    "date_token": normalized.get("incoming_data"),
                    "date_label": date_label,
                }
            )
        elif resolved_action in {"time_0900", "time_1130", "time_1600", "time_1830"} or self._is_dynamic_time_token(resolved_action):
            built_slot = None
            if self._is_dynamic_time_token(resolved_action):
                selected_slot = dynamic_slot_map.get(normalized.get("incoming_data") or "")
                if isinstance(selected_slot, dict):
                    try:
                        slot_start = datetime.fromisoformat(str(selected_slot.get("start")))
                        slot_end = datetime.fromisoformat(str(selected_slot.get("end")))
                    except ValueError:
                        slot_start = None
                        slot_end = None
                    if slot_start is not None and slot_end is not None:
                        local_start = slot_start.astimezone(self._display_timezone())
                        date_token = f"date_{local_start.date().isoformat()}"
                        time_token = normalized.get("incoming_data")
                        built_slot = {
                            "slot_id": str(selected_slot.get("slot_id") or f"{date_token}_{time_token}"),
                            "date_token": date_token,
                            "time_token": time_token,
                            "date_label": self._format_date_label(local_start.date()),
                            "time_label": self._format_time_label(slot_start),
                            "label": str(selected_slot.get("label") or f"{self._format_date_label(local_start.date())}, {self._format_time_label(slot_start)}"),
                            "start": slot_start.isoformat(),
                            "end": slot_end.isoformat(),
                        }
            if built_slot is None:
                built_slot = self._build_pending_slot(
                    date_token=str(pending_slot.get("date_token") or ""),
                    time_token=normalized.get("incoming_data"),
                )
            if built_slot is not None:
                pending_slot = built_slot
                if journey is not None:
                    self.journeys.store_selected_slot(journey.journey_id, deepcopy(built_slot))
                    journey = self.journeys.mark_state(journey.journey_id, JourneyState.WAITING_FOR_CONFIRMATION.value)

        if (
            journey is not None
            and resolved_action == "keep"
            and journey.current_state == JourneyState.WAITING_FOR_CONFIRMATION.value
            and pending_slot
        ):
            google_booking_result = self._commit_selected_slot(
                journey=journey,
                normalized=normalized,
                pending_slot=pending_slot,
            )
            journey = self.journeys.mark_state(journey.journey_id, JourneyState.BOOKED.value)
        elif journey is not None and self._should_invoke_orchestrator_for_action(resolved_action):
            try:
                orchestrator_result = self.orchestrator.handle_reminder_action(
                    ReminderActionCommand(
                        journey_id=journey.journey_id,
                        correlation_id=journey.correlation_id,
                        tenant_id=journey.tenant_id,
                        action=resolved_action,
                        requested_by="real_callback",
                        message=normalized["incoming_data"],
                    ).model_dump(mode="json")
                )
            except ValueError as exc:
                orchestrator_error = {
                    "error": exc.__class__.__name__,
                    "message": str(exc),
                    "resolved_action": resolved_action,
                    "journey_id": journey.journey_id,
                }
        if pending_slot:
            normalized["pending_slot"] = deepcopy(pending_slot)
        if dynamic_grouped_slots:
            normalized["dynamic_grouped_slots"] = deepcopy(dynamic_grouped_slots)
        if dynamic_slot_map:
            normalized["dynamic_slot_map"] = deepcopy(dynamic_slot_map)
        if google_booking_result is not None:
            normalized["google_booking_result"] = deepcopy(google_booking_result)
        follow_up = self._send_follow_up_message(
            normalized=normalized,
            journey=journey,
            correlation_ref=correlation_ref,
        )

        self.messages.upsert(
            message_id=f"msg-in-{event_id}",
            provider_message_id=event_id,
            provider_job_id=None,
            provider="lekab",
            channel="RCS",
            direction="inbound",
            status="received",
            customer_id=None,
            contact_reference=None,
            phone_number=normalized.get("phone_number"),
            address_id=normalized.get("address_id"),
            appointment_id=normalized.get("appointment_id"),
            correlation_ref=correlation_ref,
            journey_id=getattr(journey, "journey_id", None),
            booking_reference=normalized.get("booking_reference"),
            message_type="reply_button" if resolved_action else "callback",
            body=normalized["incoming_data"],
            preview_text=normalized["incoming_data"][:120],
            actions=[],
            provider_payload=deepcopy(payload),
            metadata={
                "source": "real_lekab_callback",
                "trace_id": callback_trace_id,
                "resolved_action": resolved_action,
                "callback_event": normalized["event_type"],
                "incoming_type": normalized["incoming_type"],
            },
        )

        selected_state = "selected" if resolved_action else "received"
        metadata = {
            "real_callback": {
                "event_id": event_id,
                "event_type": normalized["event_type"],
                "incoming_type": normalized["incoming_type"],
                "incoming_data": normalized["incoming_data"],
                "selected_action": resolved_action,
                "button_state": selected_state,
                "received_via": "lekab_callback",
                "journey_result": deepcopy(orchestrator_result or {}),
            }
        }
        if orchestrator_error is not None:
            metadata["real_callback"]["orchestrator_error"] = deepcopy(orchestrator_error)
        if google_booking_result is not None:
            metadata["real_callback"]["google_booking_result"] = deepcopy(google_booking_result)
        if pending_slot:
            metadata["pending_slot"] = deepcopy(pending_slot)
        if dynamic_grouped_slots:
            metadata["dynamic_grouped_slots"] = deepcopy(dynamic_grouped_slots)
        if dynamic_slot_map:
            metadata["dynamic_slot_map"] = deepcopy(dynamic_slot_map)
        if follow_up is not None:
            metadata["customer_journey_message"] = deepcopy(follow_up)
        self.contexts.save_context(
            DemoScenarioContextUpdate(
                mode="real",
                address_id=normalized.get("address_id"),
                appointment_id=normalized.get("appointment_id"),
                booking_reference=normalized.get("booking_reference"),
                correlation_ref=correlation_ref,
                current_step=normalized["current_step"],
                status=normalized["status"],
                metadata=metadata,
            )
        )
        self.shared_settings.merge_namespace(
            "lekab",
            {},
            status_values={
                "last_real_callback": {
                    "event_id": event_id,
                    "trace_id": callback_trace_id,
                    "duplicate": False,
                    "resolved_action": resolved_action,
                    "correlation_ref": correlation_ref,
                }
            },
        )
        return {
            "accepted": True,
            "duplicate": False,
            "event_id": event_id,
            "trace_id": callback_trace_id,
            "resolved_action": resolved_action,
            "normalized_callback": deepcopy(normalized),
            "journey_result": orchestrator_result,
            "orchestrator_error": deepcopy(orchestrator_error),
            "google_booking_result": deepcopy(google_booking_result),
            "follow_up_message": follow_up,
        }

    def _callback_event_id(self, payload: dict[str, Any]) -> str:
        explicit = payload.get("event_id") or payload.get("id") or payload.get("message_id")
        if explicit:
            return str(explicit)
        digest = sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return f"callback-{digest[:24]}"

    def _build_callback_payload_from_fetch_result(
        self,
        *,
        result: dict[str, Any],
        summary: dict[str, Any],
        linkage: Any,
    ) -> dict[str, Any] | None:
        if not result.get("success"):
            return None
        if summary.get("normalized_event_type") != "message.reply_received":
            return None
        incoming_data = self._resolve_callback_bridge_value(summary)
        if not incoming_data:
            return None
        response_json = result.get("response_json") if isinstance(result.get("response_json"), dict) else {}
        parsed_content = summary.get("parsed_content_json") if isinstance(summary.get("parsed_content_json"), dict) else {}
        return {
            "event_id": response_json.get("uuid") or summary.get("provider_message_id") or f"fetch-{uuid4().hex[:12]}",
            "event": "INCOMING",
            "incoming_type": str(summary.get("callback_transport") or "RESPONSE").upper(),
            "incoming_data": incoming_data,
            "correlation_id": linkage.correlation_ref,
            "correlation_ref": linkage.correlation_ref,
            "appointment_id": linkage.appointment_id,
            "booking_reference": getattr(linkage, "booking_reference", None),
            "address_id": linkage.address_id,
            "from": summary.get("from") or parsed_content.get("from"),
            "phone_number": summary.get("from") or parsed_content.get("from"),
            "reply_label": self._extract_reply_label(parsed_content),
            "callback_transport": summary.get("callback_transport"),
            "received_at": summary.get("provider_timestamp"),
            "source": "webhook_site_fetch_bridge",
        }

    def _resolve_callback_bridge_value(self, summary: dict[str, Any]) -> str | None:
        parsed_content = summary.get("parsed_content_json") if isinstance(summary.get("parsed_content_json"), dict) else {}
        direct_candidate = self._normalize_callback_bridge_candidate(
            self._extract_callback_bridge_candidate(parsed_content)
        )
        if direct_candidate:
            return direct_candidate

        resolved_action = summary.get("resolved_action") if isinstance(summary.get("resolved_action"), dict) else {}
        action_type = str(resolved_action.get("action_type") or (summary.get("action_candidate") or {}).get("action_type") or "").strip()
        action_map = {
            "appointment.confirm_requested": "confirm_appointment",
            "appointment.cancel_requested": "cancel_appointment",
            "appointment.reschedule_requested": "reschedule_appointment",
            "appointment.find_slot_this_week_requested": "this_week",
            "appointment.find_slot_next_week_requested": "next_week",
            "appointment.find_slot_this_month_requested": "this_month",
            "appointment.find_slot_next_month_requested": "next_month",
            "appointment.find_next_free_slot_requested": "next_free_slot",
        }
        if action_type in action_map:
            return action_map[action_type]
        return self._normalize_callback_bridge_candidate(str(summary.get("body_text") or ""))

    def _extract_callback_bridge_candidate(self, parsed_content: dict[str, Any]) -> str:
        for key in ("postbackData", "postback_data"):
            value = parsed_content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("reply", "text", "button", "value", "label", "title"):
            value = parsed_content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("selectedSuggestion", "selected_suggestion", "suggestionReply", "buttonReply"):
            value = parsed_content.get(key)
            if isinstance(value, dict):
                for nested_key in ("value", "label", "title", "text"):
                    nested_value = value.get(nested_key)
                    if isinstance(nested_value, str) and nested_value.strip():
                        return nested_value.strip()
        return ""

    def _extract_reply_label(self, parsed_content: dict[str, Any]) -> str | None:
        for key in ("label", "title", "text", "reply", "button"):
            value = parsed_content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("selectedSuggestion", "selected_suggestion", "suggestionReply", "buttonReply"):
            value = parsed_content.get(key)
            if isinstance(value, dict):
                for nested_key in ("label", "title", "text"):
                    nested_value = value.get(nested_key)
                    if isinstance(nested_value, str) and nested_value.strip():
                        return nested_value.strip()
        return None

    def _normalize_callback_bridge_candidate(self, candidate: str) -> str | None:
        token = str(candidate or "").strip().lower()
        if not token:
            return None
        allowed_values = {
            "confirm_appointment",
            "keep_appointment",
            "reschedule_appointment",
            "cancel_appointment",
            "call_me",
            "this_week",
            "next_week",
            "this_month",
            "next_month",
            "next_free_slot",
            "date_05_may",
            "date_06_may",
            "date_08_may",
            "date_12_may",
            "time_0900",
            "time_1130",
            "time_1600",
            "time_1830",
        }
        if token.startswith("date_20") or token.startswith("time_20"):
            return token
        return token if token in allowed_values else None

    def _normalize_real_callback_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        demo_namespace = self.shared_settings.get_namespace("demo")
        incoming_data = str(payload.get("incoming_data") or payload.get("text") or payload.get("reply") or "").strip()
        incoming_type = str(payload.get("incoming_type") or payload.get("type") or "UNKNOWN").strip().upper()
        event_type = str(payload.get("event") or payload.get("event_type") or "INCOMING").strip().upper()
        action_map = {
            "confirm_appointment": ("keep", "confirmation_complete", "confirmed"),
            "keep_appointment": ("keep", "confirmation_complete", "confirmed"),
            "reschedule_appointment": ("reschedule", "reschedule_requested", "action_requested"),
            "cancel_appointment": ("cancel", "cancellation_complete", "cancel_requested"),
            "call_me": ("call_me", "callback_requested", "callback_requested"),
            "this_week": ("this_week", "relative_choice_complete", "awaiting_date_choice"),
            "next_week": ("next_week", "relative_choice_complete", "awaiting_date_choice"),
            "this_month": ("this_month", "relative_choice_complete", "awaiting_date_choice"),
            "next_month": ("next_month", "relative_choice_complete", "awaiting_date_choice"),
            "next_free_slot": ("next_free_slot", "relative_choice_complete", "awaiting_date_choice"),
            "date_05_may": ("date_05_may", "date_choice_complete", "awaiting_time_choice"),
            "date_06_may": ("date_06_may", "date_choice_complete", "awaiting_time_choice"),
            "date_08_may": ("date_08_may", "date_choice_complete", "awaiting_time_choice"),
            "date_12_may": ("date_12_may", "date_choice_complete", "awaiting_time_choice"),
            "time_0900": ("time_0900", "slot_selected", "awaiting_confirmation"),
            "time_1130": ("time_1130", "slot_selected", "awaiting_confirmation"),
            "time_1600": ("time_1600", "slot_selected", "awaiting_confirmation"),
            "time_1830": ("time_1830", "slot_selected", "awaiting_confirmation"),
        }
        resolved_action, current_step, status = action_map.get(
            incoming_data.lower(),
            (None, "real_callback_received", "real_callback_received"),
        )
        if resolved_action is None and self._is_dynamic_date_token(incoming_data):
            resolved_action, current_step, status = incoming_data, "date_choice_complete", "awaiting_time_choice"
        elif resolved_action is None and self._is_dynamic_time_token(incoming_data):
            resolved_action, current_step, status = incoming_data, "slot_selected", "awaiting_confirmation"
        return {
            "event_type": event_type,
            "incoming_type": incoming_type,
            "incoming_data": incoming_data or "unknown_callback",
            "resolved_action": resolved_action,
            "current_step": current_step,
            "status": status,
            "correlation_ref": str(payload.get("correlation_id") or payload.get("correlation_ref") or demo_namespace.get("correlation_ref") or "lekab-callback"),
            "booking_reference": payload.get("booking_reference") or demo_namespace.get("booking_reference"),
            "appointment_id": payload.get("appointment_id") or demo_namespace.get("appointment_id"),
            "address_id": payload.get("address_id") or demo_namespace.get("address_id"),
            "phone_number": payload.get("phone_number") or payload.get("from") or payload.get("msisdn"),
            "journey_id": str(payload.get("correlation_id") or payload.get("correlation_ref") or demo_namespace.get("correlation_ref") or "lekab-callback"),
            "reply_payload": incoming_data or "unknown_callback",
            "reply_label": payload.get("reply_label") or incoming_data or "unknown_callback",
            "callback_transport": str(payload.get("callback_transport") or incoming_type or "unknown").strip().lower(),
            "received_at": payload.get("received_at"),
            "payload_version": "1.0",
            "source": str(payload.get("source") or "lekab_callback"),
        }

    def _localized_button_payload(self, button_source: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "action_id": item["action_id"],
                "label": item["label_en"],
                "value": item["value"],
                "action_type": item.get("action_type", "reply"),
                "canonical_action": item.get("canonical_action"),
                "selection_kind": item.get("selection_kind"),
                "journey_target": item.get("journey_target"),
            }
            for item in button_source
        ]

    def _real_channel_payload(self, text: str, button_source: list[dict[str, Any]], next_step_map: dict[str, str]) -> dict[str, Any]:
        return {
            "channel": "RCS",
            "message_type": "suggestion_buttons",
            "text": text,
            "suggestions": self._localized_button_payload(button_source),
            "next_step_map": deepcopy(next_step_map),
        }

    def _customer_journey_message(self, *, text: str, button_source: list[dict[str, Any]], next_step_map: dict[str, str], selected_button: str | None = None) -> dict[str, Any]:
        buttons = self._localized_button_payload(button_source)
        return {
            "text": text,
            "actions": deepcopy(buttons),
            "suggestion_buttons": deepcopy(buttons),
            "slot_options": [],
            "journey_step_type": "real_callback_follow_up",
            "selected_button": selected_button,
            "next_step_map": deepcopy(next_step_map),
            "real_channel_payload": self._real_channel_payload(text, button_source, next_step_map),
        }

    def _send_follow_up_message(self, *, normalized: dict[str, Any], journey: Any, correlation_ref: str | None) -> dict[str, Any] | None:
        phone_number = normalized.get("phone_number")
        if not phone_number:
            return None
        resolved_action = normalized.get("resolved_action")
        text = None
        button_source: list[dict[str, Any]] = []
        next_step_map: dict[str, str] = {}
        if resolved_action == "reschedule":
            text = "Choose the preferred scheduling window."
            button_source = RELATIVE_BUTTONS
            next_step_map = {
                "this_week": "date_choice",
                "next_week": "date_choice",
                "this_month": "date_choice",
                "next_month": "date_choice",
                "next_free_slot": "date_choice",
            }
        elif resolved_action in {"this_week", "next_week", "this_month", "next_month", "next_free_slot"}:
            text = "Choose one of the proposed dates."
            appointment_type = str(self.contexts.get_context().appointment_type or "dentist")
            dynamic_slots = self._load_dynamic_slots(relative_action=resolved_action, appointment_type=appointment_type)
            button_source, grouped_slots = self._date_buttons_from_slots(dynamic_slots)
            normalized["dynamic_grouped_slots"] = deepcopy(grouped_slots)
            next_step_map = {item["value"]: "time_choice" for item in button_source}
            if not button_source:
                text = "No free dates were found in the selected timeframe."
        elif resolved_action in {"date_05_may", "date_06_may", "date_08_may", "date_12_may"} or self._is_dynamic_date_token(resolved_action):
            text = "Choose one of the proposed times."
            if self._is_dynamic_date_token(resolved_action):
                appointment_type = str(self.contexts.get_context().appointment_type or "dentist")
                selected_date = self._parse_dynamic_date_token(normalized.get("incoming_data"))
                grouped_slots = {}
                if selected_date is not None:
                    slots = self._load_dynamic_slots_for_range(
                        from_date_value=selected_date,
                        to_date_value=selected_date,
                        appointment_type=appointment_type,
                    )
                    _, grouped_slots = self._date_buttons_from_slots(slots)
                button_source, slot_map = self._time_buttons_for_date(grouped_slots, normalized.get("incoming_data"))
                normalized["dynamic_slot_map"] = deepcopy(slot_map)
                next_step_map = {item["value"]: "slot_selected" for item in button_source}
            else:
                button_source = TIME_BUTTONS
                next_step_map = {
                    "time_0900": "slot_selected",
                    "time_1130": "slot_selected",
                    "time_1600": "slot_selected",
                    "time_1830": "slot_selected",
                }
            if not button_source:
                text = "No free times were found for the selected date."
        elif resolved_action in {"time_0900", "time_1130", "time_1600", "time_1830"} or self._is_dynamic_time_token(resolved_action):
            pending_slot = normalized.get("pending_slot") if isinstance(normalized.get("pending_slot"), dict) else {}
            slot_label = str(pending_slot.get("label") or normalized.get("reply_label") or "the selected slot")
            text = f"{slot_label} selected. Confirm to update the appointment, or choose Reschedule/Cancel."
            button_source = INITIAL_BUTTONS
            next_step_map = {
                "confirm": "confirmation_complete",
                "reschedule": "relative_choice",
                "cancel": "cancellation_complete",
            }
        elif resolved_action == "keep":
            google_booking_result = normalized.get("google_booking_result") if isinstance(normalized.get("google_booking_result"), dict) else {}
            if google_booking_result.get("success"):
                text = "Your appointment is confirmed and synced to Google Calendar."
            else:
                text = "Your appointment is confirmed."
        elif resolved_action == "cancel":
            text = "Your appointment cancellation was recorded."
            button_source = INITIAL_BUTTONS
        elif resolved_action == "call_me":
            text = "A callback request was recorded and will be handled by the team."
            button_source = INITIAL_BUTTONS
        if text is None:
            return None
        self.send_message(
            channel="RCS",
            tenant_id="demo",
            correlation_id=correlation_ref or "lekab-real",
            phone_number=phone_number,
            journey_id=getattr(journey, "journey_id", None),
            booking_reference=normalized.get("booking_reference"),
            body=text,
            message_type="reply_follow_up" if button_source else "text",
            actions=self._localized_button_payload(button_source),
            metadata={
                "source": "real_callback_follow_up",
                "resolved_action": resolved_action,
                "address_id": normalized.get("address_id"),
                "appointment_id": normalized.get("appointment_id"),
            },
        )
        return self._customer_journey_message(text=text, button_source=button_source, next_step_map=next_step_map, selected_button=normalized.get("incoming_data"))

    def _classify_reply_intent(self, text: str) -> dict[str, Any]:
        return self.reply_engine.analyze_reply(text)

    def _extract_reply_body_text(self, parsed_content_json: dict[str, Any] | None) -> str:
        payload = parsed_content_json or {}
        for key in ("postbackData", "postback_data"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("text", "body", "message", "reply", "suggestion", "button", "label", "title"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("selectedSuggestion", "selected_suggestion", "suggestionReply", "buttonReply"):
            value = payload.get(key)
            if isinstance(value, dict):
                for nested_key in ("postbackData", "postback_data", "text", "label", "title", "value"):
                    nested_value = value.get(nested_key)
                    if isinstance(nested_value, str) and nested_value.strip():
                        return nested_value.strip()
        return ""

    def _summarize_webhook_callback(self, response_json: Any) -> dict[str, Any]:
        payload = response_json if isinstance(response_json, dict) else {}
        parsed_content_json = self._extract_webhook_request_payload(payload)
        status_value = str((parsed_content_json or {}).get("status") or "").strip().upper()
        body_text = self._extract_reply_body_text(parsed_content_json)
        callback_method = str(payload.get("method") or ("GET" if (payload.get("query") or parsed_content_json.get("query")) else "POST")).strip().upper()
        callback_transport = "get" if callback_method == "GET" else "post"

        if status_value == "DELIVERED":
            normalized_event_type = "message.delivered"
            reply_intent = None
            datetime_candidates: list[str] = []
            action_candidate: dict[str, Any] = {}
            interpretation_state = "safe"
            interpretation_confidence = 1.0
        elif status_value in {"FAILED", "UNDELIVERABLE", "REJECTED"}:
            normalized_event_type = "message.failed"
            reply_intent = None
            datetime_candidates = []
            action_candidate = {}
            interpretation_state = "safe"
            interpretation_confidence = 1.0
        elif body_text:
            reply_info = self._classify_reply_intent(body_text)
            normalized_event_type = reply_info["normalized_event_type"]
            reply_intent = reply_info["reply_intent"]
            datetime_candidates = reply_info["reply_datetime_candidates"]
            action_candidate = deepcopy(reply_info.get("action_candidate") or {})
            interpretation_state = str(action_candidate.get("interpretation_state") or "review")
            interpretation_confidence = float(action_candidate.get("interpretation_confidence") or 0.0)
        else:
            normalized_event_type = "message.unknown"
            reply_intent = None
            datetime_candidates = []
            action_candidate = {}
            interpretation_state = "review"
            interpretation_confidence = 0.0

        return {
            "parsed_content_json": parsed_content_json,
            "normalized_event_type": normalized_event_type,
            "reply_intent": reply_intent,
            "reply_datetime_candidates": datetime_candidates,
            "action_candidate": action_candidate,
            "interpretation_state": interpretation_state,
            "interpretation_confidence": interpretation_confidence,
            "channel": (parsed_content_json or {}).get("channel") or "RCS",
            "from": (parsed_content_json or {}).get("from"),
            "to": (parsed_content_json or {}).get("to"),
            "provider_message_id": (parsed_content_json or {}).get("id"),
            "provider_user_id": (parsed_content_json or {}).get("userid"),
            "status": status_value.lower() if status_value else "received",
            "body_text": body_text if body_text else status_value or payload.get("content") or "",
            "provider_timestamp": (parsed_content_json or {}).get("time"),
            "callback_transport": callback_transport,
            "callback_source_method": callback_method,
        }

    def _resolve_action_candidate(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Turn one raw action candidate into a safe, operator-facing preview.

        The reply engine intentionally focuses on language interpretation. This
        resolver adds business context: which address and appointment would be
        affected, whether the target is precise enough, and whether the next
        step is an execution request or a review-needed preview.
        """

        candidate = deepcopy(summary.get("action_candidate") or {})
        if not candidate:
            return {}

        action_type = str(candidate.get("action_type") or "appointment.review_requested")
        parameters = deepcopy(candidate.get("parameters") or {})
        interpretation_state = str(candidate.get("interpretation_state") or "review")
        confidence = float(candidate.get("interpretation_confidence") or 0.0)
        address_id = summary.get("address_id")
        appointment_id = summary.get("appointment_id") or parameters.get("appointment_id")
        correlation_ref = summary.get("correlation_ref") or parameters.get("correlation_ref")
        booking_reference = parameters.get("booking_reference")

        review_reason = None
        resolution_state = interpretation_state

        if not appointment_id:
            resolution_state = "review"
            review_reason = "missing_appointment_context"
        elif not address_id:
            resolution_state = "review"
            review_reason = "missing_address_context"
        elif action_type == "appointment.slot_selected":
            has_specific_slot_value = bool(parameters.get("datetime_candidates") or parameters.get("ordinal_index"))
            if interpretation_state != "safe" or not has_specific_slot_value:
                resolution_state = "review"
                review_reason = "slot_selection_needs_operator_review"
        elif action_type == "appointment.review_requested":
            resolution_state = "review"
            review_reason = "free_text_requires_review"

        execution_requested = resolution_state == "safe"
        preview_headline = {
            "appointment.confirm_requested": "Confirm the linked appointment",
            "appointment.cancel_requested": "Cancel the linked appointment",
            "appointment.reschedule_requested": "Start a reschedule flow for the linked appointment",
            "appointment.find_slot_this_week_requested": "Search this-week slots for the linked appointment",
            "appointment.find_slot_next_week_requested": "Search next-week slots for the linked appointment",
            "appointment.find_slot_this_month_requested": "Search this-month slots for the linked appointment",
            "appointment.find_slot_next_month_requested": "Search next-month slots for the linked appointment",
            "appointment.find_next_free_slot_requested": "Search the next free slot for the linked appointment",
            "appointment.slot_selected": "Use the selected slot for the linked appointment",
        }.get(action_type, "Operator review is required for this reply")

        return {
            "action_type": action_type,
            "resolution_state": resolution_state,
            "interpretation_confidence": confidence,
            "requires_review": resolution_state != "safe",
            "execution_requested": execution_requested,
            "review_reason": review_reason,
            "preview_headline": preview_headline,
            "target_summary": {
                "address_id": address_id,
                "appointment_id": appointment_id,
                "correlation_ref": correlation_ref,
                "booking_reference": booking_reference,
                "channel": summary.get("channel"),
                "status": summary.get("status"),
            },
            "parameters": parameters,
        }

    def _publish_reply_events(self, *, message_id: str, trace_id: str | None, summary: dict[str, Any]) -> None:
        correlation_id = (
            summary.get("correlation_ref")
            or trace_id
            or summary.get("provider_message_id")
            or f"reply-{uuid4().hex[:12]}"
        )
        tenant_id = "demo"
        normalized_payload = CommunicationReplyNormalized(
            message_id=message_id,
            provider_message_id=summary.get("provider_message_id"),
            trace_id=trace_id,
            address_id=summary.get("address_id"),
            appointment_id=summary.get("appointment_id"),
            correlation_ref=summary.get("correlation_ref"),
            channel=str(summary.get("channel") or "RCS"),
            from_address=summary.get("from"),
            to_address=summary.get("to"),
            status=str(summary.get("status") or "received"),
            normalized_event_type=str(summary.get("normalized_event_type") or "message.unknown"),
            reply_intent=summary.get("reply_intent"),
            reply_datetime_candidates=list(summary.get("reply_datetime_candidates") or []),
            action_candidate=deepcopy(summary.get("action_candidate") or {}),
            interpretation_state=str(summary.get("interpretation_state") or "review"),
            interpretation_confidence=float(summary.get("interpretation_confidence") or 0.0),
            raw_text=str(summary.get("body_text") or ""),
            provider_timestamp=summary.get("provider_timestamp"),
        )
        self._publish_event(
            event_type="CommunicationReplyNormalized",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=normalized_payload.model_dump(mode="json"),
        )

        self._publish_event(
            event_type="ReminderInteractionObserved",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=ReminderInteractionObserved(
                message_id=message_id,
                trace_id=trace_id,
                address_id=summary.get("address_id"),
                appointment_id=summary.get("appointment_id"),
                correlation_ref=summary.get("correlation_ref"),
                interaction_type=str(summary.get("normalized_event_type") or "message.unknown"),
                channel=str(summary.get("channel") or "RCS"),
                status=str(summary.get("status") or "received"),
                details={
                    "reply_intent": summary.get("reply_intent"),
                    "reply_datetime_candidates": list(summary.get("reply_datetime_candidates") or []),
                },
            ).model_dump(mode="json"),
        )

        action_candidate = summary.get("action_candidate") or {}
        if not action_candidate:
            return
        resolved_action = self._resolve_action_candidate(summary)
        self._publish_event(
            event_type="AppointmentActionRequested",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=AppointmentActionRequested(
                message_id=message_id,
                trace_id=trace_id,
                address_id=summary.get("address_id"),
                appointment_id=summary.get("appointment_id"),
                correlation_ref=summary.get("correlation_ref"),
                action_type=str(action_candidate.get("action_type") or "appointment.review_requested"),
                interpretation_state=str(action_candidate.get("interpretation_state") or "review"),
                interpretation_confidence=float(action_candidate.get("interpretation_confidence") or 0.0),
                requires_review=bool(action_candidate.get("requires_review", False)),
                reason=action_candidate.get("reason"),
                parameters=deepcopy(action_candidate.get("parameters") or {}),
            ).model_dump(mode="json"),
        )
        self._publish_event(
            event_type="AppointmentActionResolved",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=AppointmentActionResolved(
                message_id=message_id,
                trace_id=trace_id,
                address_id=resolved_action.get("target_summary", {}).get("address_id"),
                appointment_id=resolved_action.get("target_summary", {}).get("appointment_id"),
                correlation_ref=resolved_action.get("target_summary", {}).get("correlation_ref"),
                action_type=str(resolved_action.get("action_type") or action_candidate.get("action_type") or "appointment.review_requested"),
                resolution_state=str(resolved_action.get("resolution_state") or "review"),
                interpretation_confidence=float(resolved_action.get("interpretation_confidence") or 0.0),
                requires_review=bool(resolved_action.get("requires_review", True)),
                target_summary=deepcopy(resolved_action.get("target_summary") or {}),
                parameters=deepcopy(resolved_action.get("parameters") or {}),
                reason=resolved_action.get("review_reason"),
            ).model_dump(mode="json"),
        )
        if resolved_action.get("execution_requested"):
            self._publish_event(
                event_type="AppointmentActionExecutionRequested",
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                payload=AppointmentActionExecutionRequested(
                    message_id=message_id,
                    trace_id=trace_id,
                    address_id=resolved_action.get("target_summary", {}).get("address_id"),
                    appointment_id=resolved_action.get("target_summary", {}).get("appointment_id"),
                    correlation_ref=resolved_action.get("target_summary", {}).get("correlation_ref"),
                    action_type=str(resolved_action.get("action_type") or action_candidate.get("action_type") or "appointment.review_requested"),
                    parameters=deepcopy(resolved_action.get("parameters") or {}),
                    target_summary=deepcopy(resolved_action.get("target_summary") or {}),
                ).model_dump(mode="json"),
            )
        else:
            self._publish_event(
                event_type="AppointmentActionReviewRequired",
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                payload=AppointmentActionReviewRequired(
                    message_id=message_id,
                    trace_id=trace_id,
                    address_id=resolved_action.get("target_summary", {}).get("address_id"),
                    appointment_id=resolved_action.get("target_summary", {}).get("appointment_id"),
                    correlation_ref=resolved_action.get("target_summary", {}).get("correlation_ref"),
                    action_type=str(resolved_action.get("action_type") or action_candidate.get("action_type") or "appointment.review_requested"),
                    review_reason=str(resolved_action.get("review_reason") or "review_required"),
                    interpretation_confidence=float(resolved_action.get("interpretation_confidence") or 0.0),
                    parameters=deepcopy(resolved_action.get("parameters") or {}),
                    target_summary=deepcopy(resolved_action.get("target_summary") or {}),
                ).model_dump(mode="json"),
            )

    def _store_callback_message(self, *, values: dict[str, Any], trace_id: str | None, result: dict[str, Any]) -> None:
        response_json = result.get("response_json") if isinstance(result.get("response_json"), dict) else {}
        summary = self._summarize_webhook_callback(response_json)
        callback_uuid = response_json.get("uuid") or f"callback-{uuid4().hex[:12]}"
        message_id = f"msg-in-{callback_uuid}"
        linkage = self.address_linkage.resolve(
            tenant_id="default",
            booking_reference=(summary.get("action_candidate") or {}).get("parameters", {}).get("booking_reference"),
            appointment_id=(summary.get("action_candidate") or {}).get("parameters", {}).get("appointment_id"),
            correlation_ref=(summary.get("action_candidate") or {}).get("parameters", {}).get("correlation_ref"),
            phone_number=self._resolve_customer_phone(summary),
        )
        summary["address_id"] = linkage.address_id
        summary["appointment_id"] = linkage.appointment_id
        summary["correlation_ref"] = linkage.correlation_ref
        resolved_action = self._resolve_action_candidate(summary)
        message = self._build_normalized_message(
            message_id=message_id,
            provider_message_id=summary.get("provider_message_id") or callback_uuid,
            provider_job_id=None,
            channel=str(summary.get("channel") or "RCS"),
            direction="inbound",
            status=str(summary.get("status") or "received"),
            customer_id=None,
            contact_reference=None,
            phone_number=self._resolve_customer_phone(summary),
            address_id=linkage.address_id,
            appointment_id=linkage.appointment_id,
            correlation_ref=linkage.correlation_ref,
            journey_id=None,
            booking_reference=None,
            message_type="status" if summary.get("normalized_event_type") in {"message.delivered", "message.failed"} else "reply",
            body=str(summary.get("body_text") or ""),
            actions=[],
            metadata={
                "source": "webhook_site_callback_fetch",
                "trace_id": trace_id,
                "normalized_event_type": summary.get("normalized_event_type"),
                "reply_intent": summary.get("reply_intent"),
                "reply_datetime_candidates": list(summary.get("reply_datetime_candidates") or []),
                "provider_timestamp": summary.get("provider_timestamp"),
                "provider_user_id": summary.get("provider_user_id"),
                "address_id": linkage.address_id,
                "appointment_id": linkage.appointment_id,
                "correlation_ref": linkage.correlation_ref,
                "interpretation_state": summary.get("interpretation_state"),
                "interpretation_confidence": summary.get("interpretation_confidence"),
                "action_candidate": deepcopy(summary.get("action_candidate") or {}),
                "action_type": (summary.get("action_candidate") or {}).get("action_type"),
                "requires_review": bool((summary.get("action_candidate") or {}).get("requires_review", False)),
                "resolved_action": resolved_action,
                "webhook_fetch_url": values.get("webhook_fetch_url"),
            },
            provider_payload={
                "webhook_json": response_json,
                "parsed_content_json": summary.get("parsed_content_json"),
                "request_preview": result.get("request_preview"),
            },
        )
        self._store_message(message)
        self._publish_reply_events(message_id=message_id, trace_id=trace_id, summary=summary)

    def build_monitor_payload(self) -> dict[str, Any]:
        payload = super().build_monitor_payload()
        messages = payload.get("messages") or []
        safe_actions = 0
        ambiguous_actions = 0
        review_actions = 0
        action_requested = 0
        execution_requests = 0
        for message in messages:
            metadata = message.get("metadata") or {}
            action_candidate = metadata.get("action_candidate") or {}
            resolved_action = metadata.get("resolved_action") or {}
            if action_candidate:
                action_requested += 1
                interpretation_state = (
                    resolved_action.get("resolution_state")
                    or action_candidate.get("interpretation_state")
                    or metadata.get("interpretation_state")
                )
                if interpretation_state == "safe":
                    safe_actions += 1
                elif interpretation_state == "ambiguous":
                    ambiguous_actions += 1
                else:
                    review_actions += 1
                if resolved_action.get("execution_requested"):
                    execution_requests += 1
        payload["summary_cards"] = list(payload.get("summary_cards") or []) + [
            {"label": "Action Candidates", "value": action_requested},
            {"label": "Safe Actions", "value": safe_actions},
            {"label": "Execution Requests", "value": execution_requests},
            {"label": "Needs Review", "value": ambiguous_actions + review_actions},
            {"label": "Linked Addresses", "value": sum(1 for message in messages if message.get("address_id"))},
        ]
        payload["report_cards"] = list(payload.get("report_cards") or []) + [
            {
                "title": "Reply To Action Engine",
                "text": "Inbound replies are normalized into stable internal action candidates so the operator can see what the platform would do next without hiding ambiguity.",
                "metrics": [
                    {"label": "Action candidates", "value": action_requested},
                    {"label": "Safe", "value": safe_actions},
                    {"label": "Execution requests", "value": execution_requests},
                    {"label": "Ambiguous / review", "value": ambiguous_actions + review_actions},
                ],
            }
        ]
        payload["filters"]["interpretation_states"] = ["ALL", "safe", "ambiguous", "review"]
        return payload


class _VersionedLekabConfigRepository:
    """Keep one release line from mutating another line's saved settings.

    The demonstrator keeps many release routes alive at the same time. By
    pinning v1.3.8 to its own config key we avoid accidental test pollution and
    we make it easier to compare release lines side by side.
    """

    def __init__(self, inner: LekabConfigRepository, config_key: str) -> None:
        self.inner = inner
        self.config_key = config_key

    def get(self):
        return self.inner.get(config_key=self.config_key)

    def save(self, *, config_payload: dict, secret_payload: dict, status_payload: dict):
        return self.inner.save(
            config_key=self.config_key,
            config_payload=config_payload,
            secret_payload=secret_payload,
            status_payload=status_payload,
        )
