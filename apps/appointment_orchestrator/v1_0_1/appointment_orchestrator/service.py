from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from datetime import timezone
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.orm import Session

from appointment_agent_shared.commands import (
    CancelBookingCommand,
    CancelJourneyCommand,
    ConfirmJourneyCommand,
    LekabDispatchCommand,
    ReminderActionCommand,
    ReminderCommand,
    SearchSlotsCommand,
    SelectSlotCommand,
    StartJourneyCommand,
    UpdateBookingCommand,
)
from appointment_agent_shared.config import settings
from appointment_agent_shared.enums import JourneyState
from appointment_agent_shared.enums import ErrorCategory
from appointment_agent_shared.errors import ProviderError
from appointment_agent_shared.events import EventEnvelope
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.ids import new_id
from appointment_agent_shared.models import BookingResult, ConversationTurnPayload
from appointment_agent_shared.repositories import AuditRepository, ConversationTurnRepository, JourneyRepository

from google_adapter.v1_0_1.google_adapter.service import GoogleAdapterException, GoogleAdapterServiceV101
from google_adapter.v1_1_0_patch8a.google_adapter.service import GoogleBookingRescheduleRequest
from google_adapter.v1_3_6.google_adapter.service import GoogleAdapterServiceV136
from lekab_adapter.v1_0_0.lekab_adapter.service import LekabAdapterService

from .appointment_mutation_policy import (
    AppointmentMutationContext,
    MutationDecision,
    determine_mutation_strategy,
)
from .appointment_resolution import (
    AppointmentCandidate,
    AppointmentResolutionContext,
    AppointmentResolutionResult,
    ExistingBookingResolver,
)


class PolicyEngineV101:
    def validate_booking_window(self, search: SearchSlotsCommand) -> None:
        delta_days = (search.date_window_end - search.date_window_start).days
        if delta_days > settings.booking_window_days:
            raise ValueError("Booking window exceeds configured limit")

    def validate_selection(self, state: str) -> None:
        if state not in {JourneyState.WAITING_FOR_SELECTION.value, JourneyState.OFFERING_SLOTS.value}:
            raise ValueError("Slot selection is not allowed in the current state")

    def validate_confirmation(self, state: str) -> None:
        if state not in {JourneyState.WAITING_FOR_CONFIRMATION.value, JourneyState.HOLDING_SLOT.value}:
            raise ValueError("Booking confirmation is not allowed in the current state")

    def validate_cancellation(self, state: str) -> None:
        if state not in {JourneyState.BOOKED.value, JourneyState.REMINDER_PENDING.value, JourneyState.WAITING_FOR_CONFIRMATION.value}:
            raise ValueError("Cancellation is not allowed in the current state")

    def validate_reschedule(self, state: str) -> None:
        if state not in {JourneyState.BOOKED.value, JourneyState.REMINDER_PENDING.value}:
            raise ValueError("Rescheduling is not allowed in the current state")


class AppointmentOrchestratorServiceV101:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.google = GoogleAdapterServiceV101(session)
        self.google_v136 = GoogleAdapterServiceV136(session)
        self.lekab = LekabAdapterService(session)
        self.journeys = JourneyRepository(session)
        self.turns = ConversationTurnRepository(session)
        self.audit = AuditRepository(session)
        self.policies = PolicyEngineV101()
        self.resolver = ExistingBookingResolver(session)

    def _publish(self, correlation_id: str, tenant_id: str, journey_id: str, event_type: str, payload: dict) -> str:
        trace_id = new_id("trace")
        event_bus.publish(
            EventEnvelope(
                event_type=event_type,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                journey_id=journey_id,
                trace_id=trace_id,
                payload=payload,
            )
        )
        return trace_id

    def _audit(
        self,
        tenant_id: str,
        journey_id: str,
        correlation_id: str,
        decision_type: str,
        message: str,
        payload: dict,
        reason_code: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        self.audit.append(
            audit_id=new_id("audit"),
            tenant_id=tenant_id,
            journey_id=journey_id,
            correlation_id=correlation_id,
            trace_id=trace_id or new_id("trace"),
            decision_type=decision_type,
            reason_code=reason_code,
            human_readable_message=message,
            payload=payload,
        )

    def _append_turn(self, journey_id: str, direction: str, channel: str, message_type: str, payload: dict) -> None:
        self.turns.append(
            ConversationTurnPayload(
                turn_id=new_id("turn"),
                journey_id=journey_id,
                direction=direction,
                channel=channel,
                message_type=message_type,
                normalized_payload=payload,
            )
        )

    def _set_journey_mode(self, journey_id: str, mode: str) -> None:
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        payload = dict(journey.preference_payload or {})
        payload["journey_mode"] = mode
        journey.preference_payload = payload
        self.session.commit()

    def _set_provider_booking_state(self, journey_id: str, booking_result) -> None:
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        payload = dict(journey.preference_payload or {})
        payload.update(
            {
                "provider": booking_result.provider,
                "provider_reference": booking_result.provider_reference,
                "booking_status": str(booking_result.status),
                "calendar_target": booking_result.calendar_target,
                "start_time": booking_result.start_time.isoformat() if booking_result.start_time else None,
                "end_time": booking_result.end_time.isoformat() if booking_result.end_time else None,
            }
        )
        journey.preference_payload = payload
        self.session.commit()

    def _update_preference_payload(self, journey_id: str, values: dict) -> None:
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        payload = dict(journey.preference_payload or {})
        payload.update(values)
        journey.preference_payload = payload
        self.session.commit()

    def _get_journey_mode(self, journey_id: str) -> str:
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        return (journey.preference_payload or {}).get("journey_mode", "booking")

    def _get_provider_reference(self, journey_id: str) -> str | None:
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        return (journey.preference_payload or {}).get("provider_reference")

    def _build_resolution_context(
        self,
        *,
        journey,
        requested_action: str,
        raw_input_text: str | None = None,
        payload: dict | None = None,
    ) -> AppointmentResolutionContext:
        payload = payload or {}
        preference_payload = dict(journey.preference_payload or {})
        selected_target = dict(preference_payload.get("selected_target_pending") or {})
        return AppointmentResolutionContext(
            booking_reference=payload.get("booking_reference")
            or selected_target.get("booking_reference")
            or journey.booking_reference,
            reservation_ref=payload.get("reservation_ref")
            or selected_target.get("reservation_ref")
            or payload.get("booking_reference")
            or selected_target.get("booking_reference")
            or journey.booking_reference,
            appointment_id=payload.get("appointment_id")
            or selected_target.get("appointment_id")
            or preference_payload.get("appointment_id"),
            correlation_id=payload.get("correlation_id")
            or selected_target.get("correlation_id")
            or journey.correlation_id,
            provider_event_ref=payload.get("provider_event_ref")
            or selected_target.get("provider_event_ref")
            or preference_payload.get("provider_reference"),
            customer_phone=payload.get("customer_phone")
            or selected_target.get("customer_phone")
            or preference_payload.get("customer_phone")
            or preference_payload.get("customer_mobile"),
            customer_number=payload.get("customer_number")
            or selected_target.get("customer_number")
            or preference_payload.get("customer_number"),
            contact_id=payload.get("contact_id") or selected_target.get("contact_id") or journey.customer_id,
            customer_name=payload.get("customer_name")
            or selected_target.get("customer_name")
            or preference_payload.get("customer_name")
            or journey.customer_id,
            appointment_type=payload.get("appointment_type")
            or selected_target.get("appointment_type")
            or preference_payload.get("appointment_type")
            or journey.service_type,
            address_id=payload.get("address_id")
            or selected_target.get("address_id")
            or preference_payload.get("address_id"),
            requested_action=requested_action,
            requested_datetime_hint=payload.get("requested_datetime_hint"),
            locale=journey.locale,
            timezone=journey.timezone,
            raw_input_text=raw_input_text,
            metadata={
                "journey_id": journey.journey_id,
                "tenant_id": journey.tenant_id,
                "current_journey": {
                    "booking_reference": journey.booking_reference,
                    "provider_reference": preference_payload.get("provider_reference"),
                    "appointment_id": preference_payload.get("appointment_id"),
                    "correlation_id": journey.correlation_id,
                    "customer_name": preference_payload.get("customer_name") or journey.customer_id,
                    "customer_phone": preference_payload.get("customer_phone") or preference_payload.get("customer_mobile"),
                    "customer_number": preference_payload.get("customer_number"),
                    "appointment_type": preference_payload.get("appointment_type") or journey.service_type,
                    "starts_at": preference_payload.get("start_time"),
                    "ends_at": preference_payload.get("end_time"),
                    "address_id": preference_payload.get("address_id"),
                    "reservation_ref": journey.booking_reference,
                    "status": journey.current_state,
                },
            },
        )

    def _future_slot_cutoff(self, timezone_name: str | None = None) -> datetime:
        tz_name = timezone_name or settings.google_default_timezone
        try:
            local_now = datetime.now(self.google_v136._resolve_zoneinfo(tz_name))
        except Exception:
            local_now = datetime.now(timezone.utc)
        return local_now + timedelta(minutes=settings.minimum_lead_time_minutes)

    def _is_future_slot(self, slot: dict, timezone_name: str | None = None) -> bool:
        raw_start = slot.get("start") or slot.get("start_time")
        if not raw_start:
            return False
        try:
            start_time = datetime.fromisoformat(str(raw_start))
        except ValueError:
            return False
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        return start_time >= self._future_slot_cutoff(timezone_name)

    def _search_slots_future_safe(self, search: SearchSlotsCommand) -> list[dict]:
        target_tz = self.google_v136._resolve_zoneinfo(search.timezone)
        start_value = (
            search.date_window_start
            if search.date_window_start.tzinfo is not None
            else search.date_window_start.replace(tzinfo=timezone.utc)
        )
        end_value = (
            search.date_window_end
            if search.date_window_end.tzinfo is not None
            else search.date_window_end.replace(tzinfo=timezone.utc)
        )
        from_date_value = start_value.astimezone(target_tz).date()
        to_date_value = end_value.astimezone(target_tz).date()
        result = self.google_v136.get_available_slots_patch8(
            SimpleNamespace(
                mode=settings.google_test_mode_default,
                from_date=from_date_value,
                to_date=to_date_value,
                max_slots=search.max_slots,
                duration_minutes=search.duration_minutes,
                appointment_type=search.service_type,
                timezone=search.timezone,
            )
        )
        normalized_slots: list[dict] = []
        for slot in result.slots:
            if not self._is_future_slot(slot, search.timezone):
                continue
            normalized = dict(slot)
            if normalized.get("start") and "start_time" not in normalized:
                normalized["start_time"] = normalized["start"]
            if normalized.get("end") and "end_time" not in normalized:
                normalized["end_time"] = normalized["end"]
            normalized_slots.append(normalized)
        return normalized_slots

    def _classify_appointment_intent(self, *, action: str, message: str | None = None) -> str:
        normalized = f"{action} {message or ''}".strip().lower()
        if any(
            phrase in normalized
            for phrase in (
                "all appointments",
                "all future appointments",
                "cancel all",
                "delete all",
                "alle termine",
                "alle zukünftigen termine",
                "alle zukunftigen termine",
                "alle termine löschen",
                "alle termine loeschen",
                "alle termine absagen",
            )
        ):
            return "bulk_action_requested"
        if any(phrase in normalized for phrase in ("show my appointments", "show appointments", "meine termine", "zeige termine")):
            return "show_appointments"
        if any(phrase in normalized for phrase in ("show future appointments", "future appointments", "zukünftige termine", "zukunftige termine")):
            return "show_future_appointments"
        if action == "keep":
            return "confirm_one_appointment"
        if action == "reschedule":
            return "reschedule_one_appointment"
        if action == "cancel":
            return "cancel_one_appointment"
        return "edit_one_appointment"

    def _store_resolution_state(
        self,
        *,
        journey_id: str,
        requested_action: str,
        requested_action_category: str,
        resolution: AppointmentResolutionResult,
    ) -> None:
        payload = {
            "resolution_status": resolution.resolution_status,
            "candidate_appointments": [asdict(candidate) for candidate in resolution.candidates],
            "selected_target_pending": asdict(resolution.selected) if resolution.selected is not None else None,
            "awaiting_appointment_selection": resolution.resolution_status == "multiple_matches",
            "pending_requested_action": requested_action,
            "requested_action_category": requested_action_category,
            "disambiguation_payload": asdict(resolution.disambiguation_payload)
            if resolution.disambiguation_payload is not None
            else None,
            "appointment_list_payload": asdict(resolution.appointment_list_payload)
            if resolution.appointment_list_payload is not None
            else None,
            "resolution_match_basis": list(resolution.match_basis),
            "resolution_notes": list(resolution.notes),
            "future_appointments_requested": requested_action_category in {"show_appointments", "show_future_appointments"},
            "bulk_action_requested": requested_action_category == "bulk_action_requested",
            "blocked_bulk_action": False,
        }
        if resolution.disambiguation_payload is not None:
            option_map = {
                option["option_id"]: candidate
                for option, candidate in zip(
                    payload["disambiguation_payload"]["options"],
                    payload["candidate_appointments"],
                )
            }
            payload["appointment_selection_options"] = option_map
        else:
            payload["appointment_selection_options"] = {}
        self._update_preference_payload(journey_id, payload)

    def _clear_resolution_state(self, journey_id: str) -> None:
        self._update_preference_payload(
            journey_id,
            {
                "resolution_status": None,
                "candidate_appointments": [],
                "selected_target_pending": None,
                "awaiting_appointment_selection": False,
                "pending_requested_action": None,
                "requested_action_category": None,
                "disambiguation_payload": None,
                "appointment_list_payload": None,
                "appointment_selection_options": {},
                "resolution_match_basis": [],
                "resolution_notes": [],
                "future_appointments_requested": False,
                "bulk_action_requested": False,
                "blocked_bulk_action": False,
                "user_selected_option_id": None,
                "resumed_action": None,
            },
        )

    def _apply_resolved_target(self, journey_id: str, candidate: AppointmentCandidate) -> None:
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        journey.booking_reference = candidate.booking_reference or journey.booking_reference
        self.session.commit()
        self._update_preference_payload(
            journey_id,
            {
                "provider_reference": candidate.provider_event_ref,
                "appointment_id": candidate.appointment_id,
                "address_id": candidate.address_id,
                "customer_name": candidate.customer_name,
                "appointment_type": candidate.appointment_type,
                "selected_target_pending": asdict(candidate),
                "selected_target_match_basis": list(candidate.match_basis),
            },
        )

    def _mutation_policy_context(
        self,
        *,
        journey,
        requested_action: str,
        selected_target: dict,
        booking_payload,
    ) -> AppointmentMutationContext:
        metadata = dict(getattr(booking_payload, "metadata", {}) or {})
        return AppointmentMutationContext(
            requested_action=requested_action,
            has_new_schedule=bool(metadata.get("new_start") and metadata.get("new_end")),
            force_replace_existing=bool(
                metadata.get("force_replace_existing") or metadata.get("mutation_strategy") == "replace_existing"
            ),
            provider_requires_replace=bool(metadata.get("provider_requires_replace")),
            current_provider_reference=selected_target.get("provider_event_ref")
            or (journey.preference_payload or {}).get("provider_reference"),
            booking_reference=selected_target.get("booking_reference") or journey.booking_reference,
            appointment_id=selected_target.get("appointment_id") or (journey.preference_payload or {}).get("appointment_id"),
            correlation_id=journey.correlation_id,
            metadata=metadata,
        )

    def _record_mutation_decision(
        self,
        *,
        journey,
        correlation_id: str,
        decision: MutationDecision,
        selected_target: dict,
        before_provider_reference: str | None,
        after_provider_reference: str | None = None,
        outcome: str | None = None,
    ) -> None:
        self._update_preference_payload(
            journey.journey_id,
            {
                "mutation_strategy": decision.strategy,
                "mutation_strategy_reason": decision.reason,
                "mutation_strategy_notes": list(decision.notes),
                "mutation_before_provider_reference": before_provider_reference,
                "mutation_after_provider_reference": after_provider_reference,
                "mutation_outcome": outcome,
            },
        )
        self._audit(
            journey.tenant_id,
            journey.journey_id,
            correlation_id,
            "mutation_strategy",
            "Mutation strategy decision recorded",
            {
                "strategy": decision.strategy,
                "reason": decision.reason,
                "notes": list(decision.notes),
                "selected_target": selected_target,
                "provider_reference_before": before_provider_reference,
                "provider_reference_after": after_provider_reference,
                "mutation_outcome": outcome,
            },
            decision.reason,
        )

    def _execute_replace_reschedule(self, *, journey, booking, selected_target: dict) -> BookingResult:
        metadata = dict(booking.metadata or {})
        new_start = metadata.get("new_start")
        new_end = metadata.get("new_end")
        if new_start is None or new_end is None:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="replace_reschedule",
                    error_category=ErrorCategory.VALIDATION,
                    message="Replace reschedule requires new_start and new_end.",
                )
            )
        booking_reference = selected_target.get("booking_reference") or journey.booking_reference
        provider_reference = selected_target.get("provider_event_ref") or (journey.preference_payload or {}).get("provider_reference")
        request = GoogleBookingRescheduleRequest(
            mode=str(metadata.get("google_mode") or "simulation"),
            booking_reference=booking_reference or "",
            provider_reference=provider_reference,
            slot_id=booking.slot_id,
            start_time=new_start,
            end_time=new_end,
            label=new_start.strftime("%a, %d %b, %H:%M"),
            appointment_type=selected_target.get("appointment_type") or journey.service_type or "dentist",
            correlation_id=selected_target.get("correlation_id") or journey.correlation_id,
            appointment_id=selected_target.get("appointment_id") or (journey.preference_payload or {}).get("appointment_id"),
            address_id=selected_target.get("address_id") or (journey.preference_payload or {}).get("address_id"),
            linked_contact_reference_id=(journey.preference_payload or {}).get("customer_name"),
            linked_address_full_details=(journey.preference_payload or {}).get("linked_address_full_details"),
            customer_name=selected_target.get("customer_name") or (journey.preference_payload or {}).get("customer_name") or journey.customer_id,
            customer_mobile=(journey.preference_payload or {}).get("customer_phone") or (journey.preference_payload or {}).get("customer_mobile"),
            context_label="Rescheduled appointment confirmed",
            timezone=journey.timezone,
        )
        result = self.google_v136.reschedule_booking_patch8(request)
        if not result.success:
            raise GoogleAdapterException(
                ProviderError(
                    provider="google",
                    provider_operation="replace_reschedule",
                    error_category=ErrorCategory.PROVIDER,
                    message=result.message,
                )
            )
        return BookingResult(
            booking_reference=result.booking_reference or booking_reference or "",
            provider="google",
            external_calendar_id=result.provider_reference,
            provider_reference=result.provider_reference,
            status="RESCHEDULED",
            start_time=new_start,
            end_time=new_end,
            timezone=journey.timezone,
            calendar_target=result.target_calendar_summary,
            attendees=booking.attendees,
            metadata={
                "mutation_strategy": "replace_existing",
                "html_link": result.html_link,
                "target_calendar_id": result.target_calendar_id,
                "target_calendar_summary": result.target_calendar_summary,
            },
        )

    def _audit_resolution_result(
        self,
        *,
        journey,
        correlation_id: str,
        requested_action: str,
        requested_action_category: str,
        resolution: AppointmentResolutionResult,
    ) -> None:
        self._audit(
            journey.tenant_id,
            journey.journey_id,
            correlation_id,
            "appointment_resolution",
            f"Resolver evaluated target for {requested_action}",
            {
                "requested_action": requested_action,
                "requested_action_category": requested_action_category,
                "resolution_status": resolution.resolution_status,
                "candidate_count": len(resolution.candidates),
                "match_basis": list(resolution.match_basis),
                "clarification_required": resolution.clarification_required,
                "clarification_reason": resolution.clarification_reason,
                "selected_target": asdict(resolution.selected) if resolution.selected is not None else None,
                "notes": list(resolution.notes),
                "appointment_list_payload": asdict(resolution.appointment_list_payload)
                if resolution.appointment_list_payload is not None
                else None,
            },
            f"resolution_{resolution.resolution_status}",
        )

    def _multiple_match_response(self, *, journey, requested_action: str, requested_action_category: str, resolution: AppointmentResolutionResult) -> dict:
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "status": "clarification_required",
            "requested_action": requested_action,
            "requested_action_category": requested_action_category,
            "resolution_status": resolution.resolution_status,
            "candidate_count": len(resolution.candidates),
            "disambiguation_payload": asdict(resolution.disambiguation_payload) if resolution.disambiguation_payload else None,
            "appointment_list_payload": asdict(resolution.appointment_list_payload) if resolution.appointment_list_payload else None,
        }

    def _no_match_response(self, *, journey, requested_action: str, requested_action_category: str, resolution: AppointmentResolutionResult) -> dict:
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "status": "appointment_not_resolved",
            "requested_action": requested_action,
            "requested_action_category": requested_action_category,
            "resolution_status": resolution.resolution_status,
            "notes": list(resolution.notes),
            "appointment_list_payload": asdict(resolution.appointment_list_payload) if resolution.appointment_list_payload else None,
        }

    def _bulk_action_boundary_response(self, *, journey, intent_category: str, action_text: str, locale: str) -> dict:
        is_german = locale.lower().startswith("de")
        message = (
            "Mehrere Termine gleichzeitig zu ändern oder zu löschen wird aktuell noch nicht automatisch unterstützt."
            if is_german
            else "Editing or cancelling multiple appointments at once is not automatically supported yet."
        )
        self._update_preference_payload(
            journey.journey_id,
            {
                "bulk_action_requested": True,
                "blocked_bulk_action": True,
                "pending_requested_action": None,
                "requested_action_category": intent_category,
                "future_appointments_requested": "future" in action_text.lower() or "zukunft" in action_text.lower(),
            },
        )
        self._audit(
            journey.tenant_id,
            journey.journey_id,
            journey.correlation_id,
            "bulk_action_boundary",
            "Bulk appointment action was requested and blocked",
            {
                "intent_category": intent_category,
                "action_text": action_text,
                "message": message,
            },
            "bulk_action_blocked",
        )
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "status": "bulk_action_not_supported",
            "requested_action_category": intent_category,
            "message": message,
        }

    def _show_appointments_response(self, *, journey, command: ReminderActionCommand, intent_category: str) -> dict:
        context = self._build_resolution_context(
            journey=journey,
            requested_action=intent_category,
            raw_input_text=command.message or command.action,
            payload={},
        )
        result = self.resolver.list_appointments(context)
        self._update_preference_payload(
            journey.journey_id,
            {
                "requested_action_category": intent_category,
                "candidate_appointments": [asdict(candidate) for candidate in result.candidates],
                "appointment_list_payload": asdict(result.appointment_list_payload) if result.appointment_list_payload else None,
                "future_appointments_requested": True,
                "bulk_action_requested": False,
                "blocked_bulk_action": False,
            },
        )
        self._audit(
            journey.tenant_id,
            journey.journey_id,
            command.correlation_id,
            "show_appointments",
            "Appointment list was prepared for the user",
            {
                "intent_category": intent_category,
                "candidate_count": len(result.candidates),
                "appointment_list_payload": asdict(result.appointment_list_payload) if result.appointment_list_payload else None,
            },
            "show_appointments",
        )
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "status": "appointments_listed",
            "requested_action_category": intent_category,
            "appointment_list_payload": asdict(result.appointment_list_payload) if result.appointment_list_payload else None,
            "candidate_count": len(result.candidates),
        }

    def _resolve_existing_appointment_gate(
        self,
        *,
        journey,
        requested_action: str,
        requested_action_category: str,
        correlation_id: str,
        raw_input_text: str | None = None,
        payload: dict | None = None,
    ) -> tuple[bool, dict | None]:
        resolution = self.resolver.resolve(
            self._build_resolution_context(
                journey=journey,
                requested_action=requested_action,
                raw_input_text=raw_input_text,
                payload=payload,
            )
        )
        self._store_resolution_state(
            journey_id=journey.journey_id,
            requested_action=requested_action,
            requested_action_category=requested_action_category,
            resolution=resolution,
        )
        self._audit_resolution_result(
            journey=journey,
            correlation_id=correlation_id,
            requested_action=requested_action,
            requested_action_category=requested_action_category,
            resolution=resolution,
        )
        if resolution.resolution_status == "single_match" and resolution.selected is not None:
            self._apply_resolved_target(journey.journey_id, resolution.selected)
            return True, None
        if resolution.resolution_status == "multiple_matches":
            return False, self._multiple_match_response(
                journey=journey,
                requested_action=requested_action,
                requested_action_category=requested_action_category,
                resolution=resolution,
            )
        return False, self._no_match_response(
            journey=journey,
            requested_action=requested_action,
            requested_action_category=requested_action_category,
            resolution=resolution,
        )

    def _resume_pending_appointment_selection(self, command: ReminderActionCommand, journey) -> dict | None:
        payload = dict(journey.preference_payload or {})
        if not payload.get("awaiting_appointment_selection"):
            return None
        normalized_option = command.action.lower().strip()
        option_map = dict(payload.get("appointment_selection_options") or {})
        selected = option_map.get(normalized_option) or option_map.get(command.action)
        if selected is None:
            return None
        candidate = AppointmentCandidate(**selected)
        self._apply_resolved_target(journey.journey_id, candidate)
        requested_action = payload.get("pending_requested_action") or "keep"
        self._update_preference_payload(
            journey.journey_id,
            {
                "awaiting_appointment_selection": False,
                "pending_requested_action": None,
                "resolution_status": "single_match",
                "selected_target_pending": asdict(candidate),
                "user_selected_option_id": command.action,
                "resumed_action": requested_action,
            },
        )
        self._audit(
            command.tenant_id,
            journey.journey_id,
            command.correlation_id,
            "appointment_selection",
            "Customer selected one appointment candidate after disambiguation",
            {
                "requested_action": requested_action,
                "selected_option": command.action,
                "selected_target": asdict(candidate),
            },
            "appointment_selection_resolved",
        )
        if requested_action == "keep":
            return self._handle_keep_existing(command, journey)
        if requested_action == "reschedule":
            return self.start_reschedule(
                {
                    "journey_id": journey.journey_id,
                    "tenant_id": command.tenant_id,
                    "correlation_id": command.correlation_id,
                    "resolution_gate_passed": True,
                    "reason": command.reason or "appointment_selection_reschedule",
                    "message": command.message or "Customer selected a target appointment for reschedule",
                    "date_window_start": command.date_window_start or datetime.utcnow(),
                    "date_window_end": command.date_window_end or datetime.utcnow() + timedelta(days=7),
                    "duration_minutes": command.duration_minutes or settings.default_duration_minutes,
                    "resource_candidates": command.resource_candidates,
                    "no_slot_strategy": command.no_slot_strategy,
                    "force_no_slots": command.force_no_slots,
                }
            )
        if requested_action == "cancel":
            result = self.cancel_journey(
                {
                    "journey_id": journey.journey_id,
                    "tenant_id": command.tenant_id,
                    "correlation_id": command.correlation_id,
                    "resolution_gate_passed": True,
                    "reason": command.reason or "appointment_selection_cancel",
                    "requested_by": command.requested_by,
                }
            )
            result["selected_action"] = "cancel"
            return result
        return None

    def _handle_keep_existing(self, command: ReminderActionCommand, journey) -> dict:
        can_proceed, response = self._resolve_existing_appointment_gate(
            journey=journey,
            requested_action="keep",
            requested_action_category="confirm_one_appointment",
            correlation_id=command.correlation_id,
            raw_input_text=command.message or command.action,
            payload={},
        )
        if not can_proceed:
            return response or {}
        refreshed = self.journeys.get(journey.journey_id)
        selected_target = dict((refreshed.preference_payload or {}).get("selected_target_pending") or {})
        decision = determine_mutation_strategy(
            AppointmentCandidate(**selected_target) if selected_target else None,
            "keep",
            self._mutation_policy_context(
                journey=refreshed,
                requested_action="keep",
                selected_target=selected_target,
                booking_payload=SimpleNamespace(metadata={}),
            ),
        )
        self._record_mutation_decision(
            journey=refreshed,
            correlation_id=command.correlation_id,
            decision=decision,
            selected_target=selected_target,
            before_provider_reference=selected_target.get("provider_event_ref"),
            after_provider_reference=selected_target.get("provider_event_ref"),
            outcome="no_mutation",
        )
        trace_id = self._publish(
            command.correlation_id,
            command.tenant_id,
            journey.journey_id,
            "appointment.reminder.confirmed",
            {"booking_reference": journey.booking_reference, "requested_by": command.requested_by},
        )
        journey = self.journeys.mark_state(journey.journey_id, JourneyState.BOOKED.value)
        self._publish(
            command.correlation_id,
            command.tenant_id,
            journey.journey_id,
            "crm.activity.append.requested",
            {"kind": "reminder_confirmed", "message": "Customer kept the existing appointment"},
        )
        self._audit(
            command.tenant_id,
            journey.journey_id,
            command.correlation_id,
            "reminder_confirmation",
            "Customer confirmed the appointment will stay as booked",
            {
                "selected_action": "keep",
                "resolved_target": dict((journey.preference_payload or {}).get("selected_target_pending") or {}),
            },
            "reminder_confirmed",
            trace_id,
        )
        self._clear_resolution_state(journey.journey_id)
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "selected_action": "keep",
            "status": "appointment_kept",
        }

    def _emit_crm_activity(self, journey, correlation_id: str, message: str, kind: str) -> None:
        trace_id = self._publish(
            correlation_id,
            journey.tenant_id,
            journey.journey_id,
            "crm.activity.append.requested",
            {"kind": kind, "message": message, "booking_reference": journey.booking_reference},
        )
        self._audit(journey.tenant_id, journey.journey_id, correlation_id, "crm_activity", message, {"kind": kind}, kind, trace_id)

    def _escalate(self, journey, correlation_id: str, reason: str, message: str) -> dict:
        journey.current_state = JourneyState.ESCALATED.value
        journey.escalation_reason = reason
        self.session.commit()
        trace_id = self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.escalation.requested", {"reason": reason})
        self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.escalated", {"reason": reason})
        self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.handover.target.pending", {"reason": reason})
        self._emit_crm_activity(journey, correlation_id, message, "escalation")
        self._audit(journey.tenant_id, journey.journey_id, correlation_id, "escalation", message, {"reason": reason}, reason, trace_id)
        return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "escalation_reason": reason}

    def _handle_provider_error(self, journey, correlation_id: str, decision_type: str, reason: str, message: str, payload: dict) -> dict:
        trace_id = self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.provider.error", {"reason": reason, **payload})
        self._audit(journey.tenant_id, journey.journey_id, correlation_id, decision_type, message, payload, reason, trace_id)
        return self._escalate(journey, correlation_id, reason, message)

    def _handle_no_slots(self, journey, correlation_id: str, strategy: str, search: SearchSlotsCommand) -> dict:
        trace_id = self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.no_slots.detected", {"strategy": strategy})
        self._audit(
            journey.tenant_id,
            journey.journey_id,
            correlation_id,
            "no_slots",
            "No valid slots were found",
            {"strategy": strategy},
            "no_slots",
            trace_id,
        )
        if strategy == "RETRY_WITH_BROADER_WINDOW":
            broadened = SearchSlotsCommand.model_validate(
                {
                    **search.model_dump(mode="json"),
                    "date_window_end": search.date_window_end + timedelta(days=10),
                }
            )
            slot_payload = self._search_slots_future_safe(broadened)
            self.journeys.store_candidate_slots(journey.journey_id, slot_payload)
            journey = self.journeys.mark_state(journey.journey_id, JourneyState.WAITING_FOR_SELECTION.value)
            retry_trace = self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.no_slots.retry_requested", {"window_days": 10})
            self._audit(journey.tenant_id, journey.journey_id, correlation_id, "no_slots_retry", "Retrying with broader window", {"slot_count": len(slot_payload)}, "retry_broader_window", retry_trace)
            return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "slot_options": slot_payload, "no_slot_action": strategy}
        if strategy in {"ASK_FOR_MONTH", "ASK_FOR_DAYPART"}:
            journey = self.journeys.mark_state(journey.journey_id, JourneyState.COLLECTING_PREFERENCES.value)
            reason = "ask_for_month" if strategy == "ASK_FOR_MONTH" else "ask_for_daypart"
            self._audit(journey.tenant_id, journey.journey_id, correlation_id, "preference_refinement", "More customer preference detail is required", {"strategy": strategy}, reason)
            return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "no_slot_action": strategy}
        if strategy == "OFFER_CALLBACK":
            self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.callback.offer.requested", {"reason": "no_slots"})
            self._emit_crm_activity(journey, correlation_id, "Callback fallback offered after no-slot outcome", "callback_offer")
            journey = self.journeys.mark_state(journey.journey_id, JourneyState.CLOSED.value)
            return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "no_slot_action": strategy}
        if strategy == "CLOSE_WITH_NO_BOOKING":
            journey = self.journeys.mark_state(journey.journey_id, JourneyState.CLOSED.value)
            return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "no_slot_action": strategy}
        return self._escalate(journey, correlation_id, "no_slots", "No valid slots available; human handover requested")

    def start_journey(self, payload: dict) -> dict:
        command = StartJourneyCommand.model_validate(payload)
        record = self.journeys.upsert(
            journey_id=command.journey_id,
            correlation_id=command.correlation_id,
            tenant_id=command.tenant_id,
            customer_id=command.customer_id,
            channel=command.channel,
            current_state=JourneyState.IDENTIFYING_CUSTOMER.value,
            service_type=command.service_type,
            locale=command.locale,
            timezone=command.timezone,
            preference_payload={**command.preferences.model_dump(mode="json"), "journey_mode": "booking"},
        )
        self._append_turn(record.journey_id, "inbound", record.channel, "journey_start", command.model_dump(mode="json"))
        trace_id = self._publish(record.correlation_id, record.tenant_id, record.journey_id, "customer.identified", {"customer_id": record.customer_id})
        self._audit(record.tenant_id, record.journey_id, record.correlation_id, "state_transition", "Journey started and customer identified", {"state": record.current_state}, "customer_identified", trace_id)
        return self.plan_journey(
            {
                "tenant_id": command.tenant_id,
                "correlation_id": command.correlation_id,
                "journey_id": command.journey_id,
                "slot_search": {
                    "tenant_id": command.tenant_id,
                    "journey_id": command.journey_id,
                    "customer_id": command.customer_id,
                    "service_type": command.service_type,
                    "duration_minutes": command.duration_minutes,
                    "date_window_start": command.preferences.earliest_date or datetime.utcnow(),
                    "date_window_end": command.preferences.latest_date or datetime.utcnow() + timedelta(days=1),
                    "timezone": command.timezone,
                    "preferred_daypart": command.preferences.preferred_daypart,
                    "resource_candidates": command.resource_candidates,
                    "max_slots": settings.max_slots_per_offer,
                },
                "no_slot_strategy": payload.get("no_slot_strategy", "ESCALATE_TO_HUMAN"),
                "force_no_slots": payload.get("force_no_slots", False),
            }
        )

    def plan_journey(self, payload: dict) -> dict:
        search = SearchSlotsCommand.model_validate(payload["slot_search"])
        journey_id = payload.get("journey_id") or search.journey_id or new_id("journey")
        self.policies.validate_booking_window(search)
        journey = self.journeys.get(journey_id)
        if journey is None:
            journey = self.journeys.upsert(
                journey_id=journey_id,
                correlation_id=payload["correlation_id"],
                tenant_id=payload["tenant_id"],
                customer_id=search.customer_id or "unknown",
                channel="RCS",
                current_state=JourneyState.SEARCHING_SLOTS.value,
                service_type=search.service_type,
                locale=settings.default_language,
                timezone=search.timezone,
                preference_payload={"preferred_daypart": search.preferred_daypart, "journey_mode": "booking"},
            )
        else:
            journey = self.journeys.mark_state(journey_id, JourneyState.SEARCHING_SLOTS.value)
        search_trace = self._publish(payload["correlation_id"], payload["tenant_id"], journey_id, "appointment.search.requested", search.model_dump(mode="json"))
        self._audit(payload["tenant_id"], journey_id, payload["correlation_id"], "slot_search", "Slot search requested", search.model_dump(mode="json"), "slot_search", search_trace)
        force_no_slots = payload.get("force_no_slots", False) or "no-slots" in search.resource_candidates
        try:
            slot_payload = [] if force_no_slots else self._search_slots_future_safe(search)
        except GoogleAdapterException as error:
            return self._handle_provider_error(
                journey,
                payload["correlation_id"],
                "slot_search_error",
                "provider_slot_search_failed",
                error.error.message,
                error.error.model_dump(mode="json"),
            )
        if not slot_payload:
            return self._handle_no_slots(journey, payload["correlation_id"], payload.get("no_slot_strategy", "ESCALATE_TO_HUMAN"), search)
        self.journeys.store_candidate_slots(journey_id, slot_payload)
        journey = self.journeys.mark_state(journey_id, JourneyState.WAITING_FOR_SELECTION.value)
        self._append_turn(journey.journey_id, "outbound", journey.channel, "slot_offer", {"slot_count": len(slot_payload)})
        trace_id = self._publish(payload["correlation_id"], payload["tenant_id"], journey_id, "calendar.slots.found", {"slot_count": len(slot_payload)})
        self._audit(payload["tenant_id"], journey_id, payload["correlation_id"], "slot_offer", "Offerable slots prepared", {"slot_count": len(slot_payload)}, "slots_found", trace_id)
        return {"journey_id": journey_id, "journey_state": journey.current_state, "slot_options": slot_payload}

    def select_slot(self, payload: dict) -> dict:
        command = SelectSlotCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        self.policies.validate_selection(journey.current_state)
        matching_slot = next((slot for slot in journey.candidate_slots if slot["slot_id"] == command.slot_id), None)
        if matching_slot is None:
            return self._escalate(journey, command.correlation_id, "stale_slot", "Selected slot was no longer available")
        if not self._is_future_slot(matching_slot, journey.timezone):
            return self._escalate(journey, command.correlation_id, "stale_slot", "Selected slot is no longer a valid future slot")
        self.journeys.store_selected_slot(command.journey_id, matching_slot)
        journey = self.journeys.mark_state(command.journey_id, JourneyState.WAITING_FOR_CONFIRMATION.value if settings.ask_confirmation_before_commit else JourneyState.BOOKING_APPOINTMENT.value)
        self._append_turn(journey.journey_id, "inbound", journey.channel, "slot_selection", {"slot_id": command.slot_id, "actor": command.actor})
        trace_id = self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "booking.slot.held", {"slot_id": command.slot_id})
        self._audit(command.tenant_id, journey.journey_id, command.correlation_id, "slot_selection", "Customer selected a slot", {"slot_id": command.slot_id}, "slot_selected", trace_id)
        return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "selected_slot": matching_slot}

    def confirm_booking(self, payload: dict) -> dict:
        command = ConfirmJourneyCommand.model_validate(payload)
        booking = command.booking
        dispatch_command = LekabDispatchCommand.model_validate(command.dispatch.model_dump())
        journey = self.journeys.get(booking.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        self.policies.validate_confirmation(journey.current_state)
        self.journeys.mark_state(journey.journey_id, JourneyState.BOOKING_APPOINTMENT.value)
        mode = self._get_journey_mode(journey.journey_id)
        try:
            if mode == "reschedule":
                can_proceed, response = self._resolve_existing_appointment_gate(
                    journey=journey,
                    requested_action="reschedule",
                    requested_action_category="reschedule_one_appointment",
                    correlation_id=command.correlation_id,
                    raw_input_text="confirm_reschedule",
                    payload={
                        "booking_reference": journey.booking_reference,
                        "provider_event_ref": self._get_provider_reference(journey.journey_id),
                    },
                )
                if not can_proceed:
                    return response or {}
                refreshed = self.journeys.get(journey.journey_id)
                selected_target = dict((refreshed.preference_payload or {}).get("selected_target_pending") or {})
                provider_reference = selected_target.get("provider_event_ref") or self._get_provider_reference(journey.journey_id)
                booking_reference = selected_target.get("booking_reference") or refreshed.booking_reference
                decision = determine_mutation_strategy(
                    AppointmentCandidate(**selected_target) if selected_target else None,
                    "reschedule",
                    self._mutation_policy_context(
                        journey=refreshed,
                        requested_action="reschedule",
                        selected_target=selected_target,
                        booking_payload=booking,
                    ),
                )
                self._record_mutation_decision(
                    journey=refreshed,
                    correlation_id=command.correlation_id,
                    decision=decision,
                    selected_target=selected_target,
                    before_provider_reference=provider_reference,
                    outcome="pending",
                )
                if decision.strategy == "abort_due_to_risk":
                    return self._handle_provider_error(
                        journey,
                        command.correlation_id,
                        "reschedule_error",
                        decision.reason,
                        "Reschedule mutation was aborted because the resolved target was not safe enough.",
                        {"journey_mode": mode, "mutation_decision": decision.strategy, "notes": decision.notes},
                    )
                if decision.strategy == "replace_existing":
                    booking_result = self._execute_replace_reschedule(
                        journey=refreshed,
                        booking=booking,
                        selected_target=selected_target,
                    )
                else:
                    if not provider_reference:
                        return self._handle_provider_error(
                            journey,
                            command.correlation_id,
                            "reschedule_error",
                            "missing_provider_reference",
                            "Provider reference is missing for reschedule",
                            {"journey_mode": mode},
                        )
                    booking_result = self.google.update_booking(
                        UpdateBookingCommand(
                            booking_reference=booking_reference,
                            provider_reference=provider_reference,
                            new_start=booking.metadata.get("new_start") if booking.metadata.get("new_start") else None,
                            new_end=booking.metadata.get("new_end") if booking.metadata.get("new_end") else None,
                            new_title=booking.title,
                            new_description=booking.description,
                            attendees=booking.attendees,
                        )
                    )
                    booking_result.metadata["mutation_strategy"] = "patch_existing"
                    booking_result.metadata["mutation_strategy_reason"] = decision.reason
            else:
                booking_result = self.google.create_booking(booking)
        except GoogleAdapterException as error:
            return self._handle_provider_error(
                journey,
                command.correlation_id,
                "booking_error" if mode == "booking" else "reschedule_error",
                "provider_booking_failed",
                error.error.message,
                error.error.model_dump(mode="json"),
            )
        dispatch = self.lekab.dispatch_workflow(dispatch_command)
        journey = self.journeys.get(journey.journey_id)
        journey.booking_reference = booking_result.booking_reference
        journey.current_state = JourneyState.BOOKED.value
        self.session.commit()
        self._set_provider_booking_state(journey.journey_id, booking_result)
        self._append_turn(journey.journey_id, "outbound", journey.channel, "booking_confirmation", booking_result.model_dump(mode="json"))
        booking_event = "appointment.booking.rescheduled" if mode == "reschedule" else "booking.created"
        crm_event = "crm.booking.update.requested" if mode == "reschedule" else "crm.booking.create.requested"
        trace_id = self._publish(command.correlation_id, command.tenant_id, journey.journey_id, booking_event, {"booking_reference": booking_result.booking_reference, "runtime_id": dispatch["runtime_id"]})
        self._publish(command.correlation_id, command.tenant_id, journey.journey_id, crm_event, {"booking_reference": booking_result.booking_reference, "provider": booking_result.provider})
        if mode == "reschedule":
            refreshed = self.journeys.get(journey.journey_id)
            selected_target = dict((refreshed.preference_payload or {}).get("selected_target_pending") or {})
            strategy = str((booking_result.metadata or {}).get("mutation_strategy") or "patch_existing")
            self._update_preference_payload(
                journey.journey_id,
                {
                    "mutation_after_provider_reference": booking_result.provider_reference,
                    "mutation_outcome": "success",
                    "mutation_strategy": strategy,
                },
            )
        self._audit(
            command.tenant_id,
            journey.journey_id,
            command.correlation_id,
            "booking_commit",
            "Booking committed successfully",
            {
                "mode": mode,
                "booking_reference": booking_result.booking_reference,
                "mutation_strategy": (booking_result.metadata or {}).get("mutation_strategy") or ("patch_existing" if mode == "reschedule" else "create"),
                "mutation_strategy_reason": (journey.preference_payload or {}).get("mutation_strategy_reason"),
                "provider_reference_before": (journey.preference_payload or {}).get("provider_reference"),
                "provider_reference_after": booking_result.provider_reference,
                "resolved_target": (journey.preference_payload or {}).get("selected_target_pending"),
            },
            "booking_committed",
            trace_id,
        )
        self._set_journey_mode(journey.journey_id, "booking")
        self._clear_resolution_state(journey.journey_id)
        journey = self.journeys.mark_state(journey.journey_id, JourneyState.REMINDER_PENDING.value)
        return {"journey_id": journey.journey_id, "journey_state": "booking_confirmed", "booking": booking_result.model_dump(mode="json"), "dispatch": dispatch}

    def send_reminder(self, payload: dict) -> dict:
        command = ReminderCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        if journey.current_state not in {JourneyState.REMINDER_PENDING.value, JourneyState.BOOKED.value}:
            raise ValueError("Reminder is not allowed in the current state")
        reminder_message = command.message or self._build_reminder_message(journey, command)
        appointment_date = command.appointment_date or self._derive_appointment_date(journey)
        appointment_time = command.appointment_time or self._derive_appointment_time(journey)
        appointment_type = command.appointment_type or journey.service_type
        booking_reference = command.booking_reference or journey.booking_reference
        dispatch = self.lekab.launch_reminder(
            LekabDispatchCommand(
                tenant_id=command.tenant_id,
                correlation_id=command.correlation_id,
                job_name="Appointment Reminder",
                message=reminder_message,
                to_numbers=command.to_numbers,
                metadata={
                    "journey_id": command.journey_id,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "appointment_type": appointment_type,
                    "booking_reference": booking_reference,
                    "interactive_actions": ["Confirm", "Reschedule", "Cancel", "Call me"],
                    "interactive_action_values": ["confirm_appointment", "reschedule_appointment", "cancel_appointment", "call_me"],
                },
            )
        )
        journey = self.journeys.mark_state(command.journey_id, JourneyState.REMINDER_PENDING.value)
        self._update_preference_payload(
            journey.journey_id,
            {
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "appointment_type": appointment_type,
                "selected_action": None,
                "last_reminder_message": reminder_message,
            },
        )
        self._append_turn(
            journey.journey_id,
            "outbound",
            journey.channel,
            "reminder",
            {
                "message": reminder_message,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "appointment_type": appointment_type,
                "booking_reference": booking_reference,
            },
        )
        trace_id = self._publish(
            command.correlation_id,
            command.tenant_id,
            journey.journey_id,
            "appointment.reminder.sent",
            {
                "dispatch": dispatch,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "appointment_type": appointment_type,
                "booking_reference": booking_reference,
            },
        )
        self._audit(
            command.tenant_id,
            journey.journey_id,
            command.correlation_id,
            "reminder",
            "Reminder sent with appointment details and next actions",
            {
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "appointment_type": appointment_type,
                "booking_reference": booking_reference,
                "runtime_id": dispatch["runtime_id"],
            },
            "reminder_sent",
            trace_id,
        )
        self._publish(
            command.correlation_id,
            command.tenant_id,
            journey.journey_id,
            "crm.activity.append.requested",
            {"kind": "reminder", "message": reminder_message, "booking_reference": booking_reference},
        )
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "dispatch": dispatch,
            "message": reminder_message,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "appointment_type": appointment_type,
            "booking_reference": booking_reference,
            "available_actions": ["keep", "reschedule", "cancel", "call_me"],
        }

    def _derive_appointment_date(self, journey) -> str | None:
        payload = journey.preference_payload or {}
        if payload.get("start_time"):
            return payload["start_time"][:10]
        return None

    def _derive_appointment_time(self, journey) -> str | None:
        payload = journey.preference_payload or {}
        if payload.get("start_time"):
            return payload["start_time"][11:16]
        return None

    def _build_reminder_message(self, journey, command: ReminderCommand) -> str:
        appointment_date = command.appointment_date or self._derive_appointment_date(journey) or "tomorrow"
        appointment_time = command.appointment_time or self._derive_appointment_time(journey) or "10:00"
        appointment_type = command.appointment_type or journey.service_type or "appointment"
        booking_reference = command.booking_reference or journey.booking_reference
        base = f"Reminder: You have a {appointment_type} appointment on {appointment_date} at {appointment_time}."
        if booking_reference:
            base += f" Booking reference: {booking_reference}."
        base += " What would you like to do: keep it, reschedule, cancel, or ask for a call?"
        return base

    def handle_reminder_action(self, payload: dict) -> dict:
        command = ReminderActionCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        pending_selection_result = self._resume_pending_appointment_selection(command, journey)
        if pending_selection_result is not None:
            return pending_selection_result
        if journey.current_state not in {JourneyState.REMINDER_PENDING.value, JourneyState.BOOKED.value}:
            raise ValueError("Reminder action is not allowed in the current state")
        normalized_action = command.action.lower().strip()
        self._update_preference_payload(journey.journey_id, {"selected_action": normalized_action})
        self._append_turn(
            journey.journey_id,
            "inbound",
            journey.channel,
            "reminder_action",
            {"action": normalized_action, "requested_by": command.requested_by},
        )
        intent_category = self._classify_appointment_intent(action=normalized_action, message=command.message)
        if intent_category == "bulk_action_requested":
            return self._bulk_action_boundary_response(
                journey=journey,
                intent_category=intent_category,
                action_text=command.message or command.action,
                locale=journey.locale,
            )
        if intent_category in {"show_appointments", "show_future_appointments"}:
            return self._show_appointments_response(journey=journey, command=command, intent_category=intent_category)
        if normalized_action == "keep":
            return self._handle_keep_existing(command, journey)
        if normalized_action == "reschedule":
            trace_id = self._publish(
                command.correlation_id,
                command.tenant_id,
                journey.journey_id,
                "appointment.reminder.reschedule.requested",
                {"requested_by": command.requested_by},
            )
            self._audit(
                command.tenant_id,
                journey.journey_id,
                command.correlation_id,
                "reminder_action",
                "Customer entered the reschedule path from the reminder",
                {"selected_action": normalized_action},
                "reminder_reschedule",
                trace_id,
            )
            return self.start_reschedule(
                {
                    "journey_id": journey.journey_id,
                    "tenant_id": command.tenant_id,
                    "correlation_id": command.correlation_id,
                    "reason": command.reason or "reminder_reschedule",
                    "message": command.message or "Customer selected reschedule from reminder",
                    "date_window_start": command.date_window_start or datetime.utcnow(),
                    "date_window_end": command.date_window_end or datetime.utcnow() + timedelta(days=7),
                    "duration_minutes": command.duration_minutes or settings.default_duration_minutes,
                    "resource_candidates": command.resource_candidates,
                    "no_slot_strategy": command.no_slot_strategy,
                    "force_no_slots": command.force_no_slots,
                }
            )
        if normalized_action == "cancel":
            trace_id = self._publish(
                command.correlation_id,
                command.tenant_id,
                journey.journey_id,
                "appointment.reminder.cancel.requested",
                {"requested_by": command.requested_by},
            )
            self._audit(
                command.tenant_id,
                journey.journey_id,
                command.correlation_id,
                "reminder_action",
                "Customer entered the cancellation path from the reminder",
                {"selected_action": normalized_action},
                "reminder_cancel",
                trace_id,
            )
            result = self.cancel_journey(
                {
                    "journey_id": journey.journey_id,
                    "tenant_id": command.tenant_id,
                    "correlation_id": command.correlation_id,
                    "reason": command.reason or "reminder_cancel",
                    "requested_by": command.requested_by,
                }
            )
            result["selected_action"] = normalized_action
            return result
        if normalized_action in {"call_me", "call me", "human", "speak_to_someone"}:
            trace_id = self._publish(
                command.correlation_id,
                command.tenant_id,
                journey.journey_id,
                "appointment.reminder.call_me.requested",
                {"requested_by": command.requested_by},
            )
            self._audit(
                command.tenant_id,
                journey.journey_id,
                command.correlation_id,
                "reminder_action",
                "Customer asked for a human handover from the reminder",
                {"selected_action": "call_me"},
                "reminder_call_me",
                trace_id,
            )
            result = self.escalate_journey(
                {
                    "journey_id": journey.journey_id,
                    "tenant_id": command.tenant_id,
                    "correlation_id": command.correlation_id,
                    "reason": command.reason or "reminder_call_me",
                    "message": command.message or "Customer asked to speak to someone from the reminder flow",
                }
            )
            result["selected_action"] = "call_me"
            return result
        raise ValueError("Unknown reminder action")

    def cancel_journey(self, payload: dict) -> dict:
        command = CancelJourneyCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        self.policies.validate_cancellation(journey.current_state)
        if not payload.get("resolution_gate_passed"):
            can_proceed, response = self._resolve_existing_appointment_gate(
                journey=journey,
                requested_action="cancel",
                requested_action_category="cancel_one_appointment",
                correlation_id=command.correlation_id,
                raw_input_text=command.reason,
                payload=payload,
            )
            if not can_proceed:
                return response or {}
        refreshed = self.journeys.get(command.journey_id)
        selected_target = dict((refreshed.preference_payload or {}).get("selected_target_pending") or {})
        booking_reference = selected_target.get("booking_reference") or refreshed.booking_reference
        provider_reference = selected_target.get("provider_event_ref") or self._get_provider_reference(command.journey_id)
        decision = determine_mutation_strategy(
            AppointmentCandidate(**selected_target) if selected_target else None,
            "cancel",
            self._mutation_policy_context(
                journey=refreshed,
                requested_action="cancel",
                selected_target=selected_target,
                booking_payload=SimpleNamespace(metadata={}),
            ),
        )
        self._record_mutation_decision(
            journey=refreshed,
            correlation_id=command.correlation_id,
            decision=decision,
            selected_target=selected_target,
            before_provider_reference=provider_reference,
            outcome="pending",
        )
        if decision.strategy == "abort_due_to_risk":
            return self._handle_provider_error(
                journey,
                command.correlation_id,
                "cancellation_error",
                decision.reason,
                "Cancellation mutation was aborted because the resolved target was not safe enough.",
                {"notes": decision.notes, "booking_reference": booking_reference},
            )
        if not provider_reference:
            return self._handle_provider_error(
                journey,
                command.correlation_id,
                "cancellation_error",
                "missing_provider_reference",
                "Provider reference is missing for cancellation",
                {"booking_reference": booking_reference},
            )
        try:
            cancel_result = self.google.cancel_booking(
                CancelBookingCommand(
                    booking_reference=booking_reference or "",
                    provider_reference=provider_reference,
                    reason=command.reason,
                    requested_by=command.requested_by,
                )
            )
        except GoogleAdapterException as error:
            return self._handle_provider_error(
                journey,
                command.correlation_id,
                "cancellation_error",
                "provider_cancellation_failed",
                error.error.message,
                error.error.model_dump(mode="json"),
            )
        journey = self.journeys.mark_state(command.journey_id, JourneyState.CANCELLATION_FLOW.value)
        self._append_turn(journey.journey_id, "inbound", journey.channel, "cancellation_request", {"reason": command.reason, "requested_by": command.requested_by})
        trace_id = self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "booking.cancelled", {"reason": command.reason})
        self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "crm.booking.cancel.requested", {"booking_reference": booking_reference, "reason": command.reason})
        self._audit(
            command.tenant_id,
            journey.journey_id,
            command.correlation_id,
            "cancellation",
            "Journey cancelled",
            {
                **cancel_result.model_dump(mode="json"),
                "mutation_strategy": decision.strategy,
                "mutation_strategy_reason": decision.reason,
                "resolved_target": selected_target,
                "provider_reference_before": provider_reference,
                "provider_reference_after": cancel_result.provider_reference,
            },
            "cancellation",
            trace_id,
        )
        self._update_preference_payload(
            journey.journey_id,
            {
                "mutation_after_provider_reference": cancel_result.provider_reference,
                "mutation_outcome": "success",
            },
        )
        self._set_provider_booking_state(journey.journey_id, cancel_result)
        journey = self.journeys.mark_state(command.journey_id, JourneyState.CLOSED.value)
        self._clear_resolution_state(journey.journey_id)
        return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "status": "cancelled"}

    def start_reschedule(self, payload: dict) -> dict:
        journey_id = payload["journey_id"]
        correlation_id = payload["correlation_id"]
        tenant_id = payload["tenant_id"]
        journey = self.journeys.get(journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        try:
            self.policies.validate_reschedule(journey.current_state)
        except ValueError:
            trace_id = self._publish(correlation_id, tenant_id, journey_id, "appointment.reschedule.rejected", {"state": journey.current_state})
            self._audit(tenant_id, journey_id, correlation_id, "reschedule", "Reschedule request rejected by policy", {"state": journey.current_state}, "reschedule_rejected", trace_id)
            raise
        if not payload.get("resolution_gate_passed"):
            can_proceed, response = self._resolve_existing_appointment_gate(
                journey=journey,
                requested_action="reschedule",
                requested_action_category="reschedule_one_appointment",
                correlation_id=correlation_id,
                raw_input_text=str(payload.get("message") or payload.get("reason") or "reschedule"),
                payload=payload,
            )
            if not can_proceed:
                return response or {}
        self.journeys.mark_state(journey_id, JourneyState.RESCHEDULE_FLOW.value)
        self._set_journey_mode(journey_id, "reschedule")
        trace_id = self._publish(correlation_id, tenant_id, journey_id, "appointment.reschedule.requested", {"reason": payload.get("reason", "customer_request")})
        self._publish(correlation_id, tenant_id, journey_id, "appointment.reschedule.allowed", {"booking_reference": journey.booking_reference})
        self._audit(tenant_id, journey_id, correlation_id, "reschedule", "Reschedule flow started", {"booking_reference": journey.booking_reference}, "reschedule_allowed", trace_id)
        return self.plan_journey(
            {
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "journey_id": journey_id,
                "slot_search": {
                    "tenant_id": tenant_id,
                    "journey_id": journey_id,
                    "customer_id": journey.customer_id,
                    "service_type": journey.service_type,
                    "duration_minutes": payload.get("duration_minutes", settings.default_duration_minutes),
                    "date_window_start": payload.get("date_window_start", datetime.utcnow()),
                    "date_window_end": payload.get("date_window_end", datetime.utcnow() + timedelta(days=7)),
                    "timezone": journey.timezone,
                    "resource_candidates": payload.get("resource_candidates", []),
                    "max_slots": settings.max_slots_per_offer,
                },
                "no_slot_strategy": payload.get("no_slot_strategy", "ESCALATE_TO_HUMAN"),
                "force_no_slots": payload.get("force_no_slots", False),
            }
        )

    def escalate_journey(self, payload: dict) -> dict:
        journey = self.journeys.get(payload["journey_id"])
        if journey is None:
            raise ValueError("Journey not found")
        reason = payload.get("reason", "help_requested")
        message = payload.get("message", "Customer requested human assistance")
        return self._escalate(journey, payload["correlation_id"], reason, message)

    def list_audit(self, journey_id: str) -> list[dict]:
        return [
            {
                "audit_id": row.audit_id,
                "decision_type": row.decision_type,
                "reason_code": row.reason_code,
                "human_readable_message": row.human_readable_message,
            }
            for row in self.audit.list_for_journey(journey_id)
        ]
