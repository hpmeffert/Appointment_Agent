from __future__ import annotations

from datetime import datetime, timedelta
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
from appointment_agent_shared.events import EventEnvelope
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.ids import new_id
from appointment_agent_shared.models import ConversationTurnPayload
from appointment_agent_shared.repositories import AuditRepository, ConversationTurnRepository, JourneyRepository

from google_adapter.v1_0_1.google_adapter.service import GoogleAdapterException, GoogleAdapterServiceV101
from lekab_adapter.v1_0_0.lekab_adapter.service import LekabAdapterService


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
        self.lekab = LekabAdapterService(session)
        self.journeys = JourneyRepository(session)
        self.turns = ConversationTurnRepository(session)
        self.audit = AuditRepository(session)
        self.policies = PolicyEngineV101()

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
            slots = self.google.search_slots(broadened)
            slot_payload = [slot.model_dump(mode="json") for slot in slots]
            self.journeys.store_candidate_slots(journey.journey_id, slot_payload)
            journey = self.journeys.mark_state(journey.journey_id, JourneyState.WAITING_FOR_SELECTION.value)
            retry_trace = self._publish(correlation_id, journey.tenant_id, journey.journey_id, "appointment.no_slots.retry_requested", {"window_days": 10})
            self._audit(journey.tenant_id, journey.journey_id, correlation_id, "no_slots_retry", "Retrying with broader window", {"slot_count": len(slots)}, "retry_broader_window", retry_trace)
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
            slots = [] if force_no_slots else self.google.search_slots(search)
        except GoogleAdapterException as error:
            return self._handle_provider_error(
                journey,
                payload["correlation_id"],
                "slot_search_error",
                "provider_slot_search_failed",
                error.error.message,
                error.error.model_dump(mode="json"),
            )
        if not slots:
            return self._handle_no_slots(journey, payload["correlation_id"], payload.get("no_slot_strategy", "ESCALATE_TO_HUMAN"), search)
        slot_payload = [slot.model_dump(mode="json") for slot in slots]
        self.journeys.store_candidate_slots(journey_id, slot_payload)
        journey = self.journeys.mark_state(journey_id, JourneyState.WAITING_FOR_SELECTION.value)
        self._append_turn(journey.journey_id, "outbound", journey.channel, "slot_offer", {"slot_count": len(slots)})
        trace_id = self._publish(payload["correlation_id"], payload["tenant_id"], journey_id, "calendar.slots.found", {"slot_count": len(slots)})
        self._audit(payload["tenant_id"], journey_id, payload["correlation_id"], "slot_offer", "Offerable slots prepared", {"slot_count": len(slots)}, "slots_found", trace_id)
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
                provider_reference = self._get_provider_reference(journey.journey_id)
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
                        booking_reference=journey.booking_reference,
                        provider_reference=provider_reference,
                        new_start=booking.metadata.get("new_start") if booking.metadata.get("new_start") else None,
                        new_end=booking.metadata.get("new_end") if booking.metadata.get("new_end") else None,
                        new_title=booking.title,
                        new_description=booking.description,
                        attendees=booking.attendees,
                    )
                )
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
        self._audit(command.tenant_id, journey.journey_id, command.correlation_id, "booking_commit", "Booking committed successfully", {"mode": mode, "booking_reference": booking_result.booking_reference}, "booking_committed", trace_id)
        self._set_journey_mode(journey.journey_id, "booking")
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
        if normalized_action == "keep":
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
                {"selected_action": normalized_action},
                "reminder_confirmed",
                trace_id,
            )
            return {
                "journey_id": journey.journey_id,
                "journey_state": journey.current_state,
                "selected_action": normalized_action,
                "status": "appointment_kept",
            }
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
        provider_reference = self._get_provider_reference(command.journey_id)
        if not provider_reference:
            return self._handle_provider_error(
                journey,
                command.correlation_id,
                "cancellation_error",
                "missing_provider_reference",
                "Provider reference is missing for cancellation",
                {"booking_reference": journey.booking_reference},
            )
        try:
            cancel_result = self.google.cancel_booking(
                CancelBookingCommand(
                    booking_reference=journey.booking_reference or "",
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
        self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "crm.booking.cancel.requested", {"booking_reference": journey.booking_reference, "reason": command.reason})
        self._audit(command.tenant_id, journey.journey_id, command.correlation_id, "cancellation", "Journey cancelled", cancel_result.model_dump(mode="json"), "cancellation", trace_id)
        self._set_provider_booking_state(journey.journey_id, cancel_result)
        journey = self.journeys.mark_state(command.journey_id, JourneyState.CLOSED.value)
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
