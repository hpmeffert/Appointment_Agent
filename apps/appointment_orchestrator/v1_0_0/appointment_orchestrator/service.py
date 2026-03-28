from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from appointment_agent_shared.config import settings
from appointment_agent_shared.contracts import (
    CancelJourneyCommand,
    ConfirmJourneyCommand,
    ConversationTurnPayload,
    CreateBookingCommand,
    EventEnvelope,
    LekabDispatchCommand,
    ReminderCommand,
    SearchSlotsCommand,
    SelectSlotCommand,
    StartJourneyCommand,
)
from appointment_agent_shared.event_bus import event_bus
from appointment_agent_shared.models import AppointmentJourneyRecord
from appointment_agent_shared.repositories import ConversationTurnRepository, JourneyRepository

from google_adapter.v1_0_0.google_adapter.service import GoogleAdapterService
from lekab_adapter.v1_0_0.lekab_adapter.service import LekabAdapterService


class PolicyEngine:
    allowed_selection_states = {"WAITING_FOR_SELECTION", "OFFERING_SLOTS"}
    allowed_confirm_states = {"WAITING_FOR_CONFIRMATION", "HOLDING_SLOT"}

    def validate_booking_window(self, search: SearchSlotsCommand) -> None:
        delta_days = (search.date_window_end - search.date_window_start).days
        if delta_days > settings.booking_window_days:
            raise ValueError("Booking window exceeds configured limit")

    def validate_selection(self, state: str) -> None:
        if state not in self.allowed_selection_states:
            raise ValueError("Slot selection is not allowed in the current state")

    def validate_confirmation(self, state: str) -> None:
        if state not in self.allowed_confirm_states:
            raise ValueError("Booking confirmation is not allowed in the current state")

    def validate_cancellation(self, state: str) -> None:
        if state not in {"BOOKED", "REMINDER_PENDING", "WAITING_FOR_CONFIRMATION"}:
            raise ValueError("Cancellation is not allowed in the current state")


class AppointmentOrchestratorService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.google = GoogleAdapterService(session)
        self.lekab = LekabAdapterService(session)
        self.journeys = JourneyRepository(session)
        self.turns = ConversationTurnRepository(session)
        self.policies = PolicyEngine()

    def _publish(self, correlation_id: str, tenant_id: str, journey_id: str, event_type: str, payload: dict) -> None:
        event_bus.publish(
            EventEnvelope(
                event_id=uuid4().hex,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                journey_id=journey_id,
                trace_id=uuid4().hex,
                event_type=event_type,
                payload=payload,
            )
        )

    def _append_turn(self, journey_id: str, direction: str, channel: str, message_type: str, payload: dict) -> None:
        self.turns.append(
            ConversationTurnPayload(
                turn_id=uuid4().hex,
                journey_id=journey_id,
                direction=direction,
                channel=channel,
                message_type=message_type,
                normalized_payload=payload,
            )
        )

    def start_journey(self, payload: dict) -> dict:
        command = StartJourneyCommand.model_validate(payload)
        record = self.journeys.upsert(
            journey_id=command.journey_id,
            correlation_id=command.correlation_id,
            tenant_id=command.tenant_id,
            customer_id=command.customer_id,
            channel=command.channel,
            current_state="IDENTIFYING_CUSTOMER",
            service_type=command.service_type,
            locale=command.locale,
            timezone=command.timezone,
            preference_payload=command.preferences.model_dump(mode="json"),
        )
        self._append_turn(record.journey_id, "inbound", record.channel, "journey_start", command.model_dump(mode="json"))
        self._publish(record.correlation_id, record.tenant_id, record.journey_id, "customer.identified", {"customer_id": record.customer_id})
        return self.plan_journey(
            {
                "tenant_id": command.tenant_id,
                "correlation_id": command.correlation_id,
                "journey_id": command.journey_id,
                "slot_search": {
                    "tenant_id": command.tenant_id,
                    "customer_id": command.customer_id,
                    "service_type": command.service_type,
                    "duration_minutes": command.duration_minutes,
                    "date_window_start": command.preferences.earliest_date or datetime.utcnow(),
                    "date_window_end": command.preferences.latest_date or datetime.utcnow(),
                    "timezone": command.timezone,
                    "preferred_daypart": command.preferences.preferred_daypart,
                    "resource_candidates": command.resource_candidates,
                    "max_slots": settings.max_slots_per_offer,
                },
            }
        )

    def plan_journey(self, payload: dict) -> dict:
        search = SearchSlotsCommand.model_validate(payload["slot_search"])
        journey_id = payload.get("journey_id") or uuid4().hex
        self.policies.validate_booking_window(search)
        existing = self.journeys.get(journey_id)
        if existing is None:
            existing = self.journeys.upsert(
                journey_id=journey_id,
                correlation_id=payload["correlation_id"],
                tenant_id=payload["tenant_id"],
                customer_id=search.customer_id,
                channel="RCS",
                current_state="SEARCHING_SLOTS",
                service_type=search.service_type,
                locale=settings.default_language,
                timezone=search.timezone,
                preference_payload={"preferred_daypart": search.preferred_daypart},
            )
        else:
            self.journeys.mark_state(journey_id, "SEARCHING_SLOTS")
        slots = self.google.search_slots(search)
        slot_payload = [slot.model_dump(mode="json") for slot in slots]
        state = "WAITING_FOR_SELECTION" if slots else "ESCALATED"
        self.journeys.store_candidate_slots(journey_id, slot_payload)
        journey = self.journeys.mark_state(journey_id, state)
        if not slots:
            journey.escalation_reason = "no_valid_slots"
            self.session.commit()
        self._append_turn(journey.journey_id, "outbound", journey.channel, "slot_offer", {"slot_count": len(slots)})
        self._publish(
            payload["correlation_id"],
            payload["tenant_id"],
            journey_id,
            "calendar.slots.found" if slots else "calendar.slots.not_found",
            {"slot_count": len(slots), "generated_at": datetime.utcnow().isoformat()},
        )
        return {
            "journey_id": journey_id,
            "journey_state": journey.current_state,
            "slot_options": slot_payload,
        }

    def select_slot(self, payload: dict) -> dict:
        command = SelectSlotCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        self.policies.validate_selection(journey.current_state)
        matching_slot = next((slot for slot in journey.candidate_slots if slot["slot_id"] == command.slot_id), None)
        if matching_slot is None:
            raise ValueError("Selected slot does not exist")
        self.journeys.store_selected_slot(command.journey_id, matching_slot)
        next_state = "WAITING_FOR_CONFIRMATION" if settings.ask_confirmation_before_commit else "BOOKING_APPOINTMENT"
        journey = self.journeys.mark_state(command.journey_id, next_state)
        self._append_turn(journey.journey_id, "inbound", journey.channel, "slot_selection", {"slot_id": command.slot_id, "actor": command.actor})
        self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "booking.slot.held", {"slot_id": command.slot_id})
        return {
            "journey_id": journey.journey_id,
            "journey_state": journey.current_state,
            "selected_slot": matching_slot,
        }

    def confirm_booking(self, payload: dict) -> dict:
        command = ConfirmJourneyCommand.model_validate(payload)
        booking = CreateBookingCommand.model_validate(command.booking)
        dispatch_command = LekabDispatchCommand.model_validate(command.dispatch.model_dump())
        journey = self.journeys.get(booking.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        self.policies.validate_confirmation(journey.current_state)
        self.journeys.mark_state(journey.journey_id, "BOOKING_APPOINTMENT")
        booking_result = self.google.create_booking(booking)
        dispatch = self.lekab.dispatch_workflow(dispatch_command)
        journey = self.journeys.get(journey.journey_id)
        journey.booking_reference = booking_result.booking_reference
        journey.current_state = "REMINDER_PENDING"
        self.session.commit()
        self._append_turn(journey.journey_id, "outbound", journey.channel, "booking_confirmation", booking_result.model_dump(mode="json"))
        self._publish(
            command.correlation_id,
            command.tenant_id,
            journey.journey_id,
            "booking.created",
            {"booking_reference": booking_result.booking_reference, "runtime_id": dispatch["runtime_id"]},
        )
        return {
            "journey_id": journey.journey_id,
            "journey_state": "booking_confirmed",
            "booking": booking_result.model_dump(mode="json"),
            "dispatch": dispatch,
        }

    def send_reminder(self, payload: dict) -> dict:
        command = ReminderCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        if journey.current_state not in {"REMINDER_PENDING", "BOOKED"}:
            raise ValueError("Reminder is not allowed in the current state")
        dispatch = self.lekab.launch_reminder(
            LekabDispatchCommand(
                tenant_id=command.tenant_id,
                correlation_id=command.correlation_id,
                job_id="reminder",
                job_name="Appointment Reminder",
                message=command.message,
                to_numbers=command.to_numbers,
            )
        )
        journey = self.journeys.mark_state(command.journey_id, "REMINDER_PENDING")
        self._append_turn(journey.journey_id, "outbound", journey.channel, "reminder", {"message": command.message})
        self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "appointment.reminder.schedule", dispatch)
        return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "dispatch": dispatch}

    def cancel_journey(self, payload: dict) -> dict:
        command = CancelJourneyCommand.model_validate(payload)
        journey = self.journeys.get(command.journey_id)
        if journey is None:
            raise ValueError("Journey not found")
        self.policies.validate_cancellation(journey.current_state)
        journey = self.journeys.mark_state(command.journey_id, "CANCELLATION_FLOW")
        self._append_turn(
            journey.journey_id,
            "inbound",
            journey.channel,
            "cancellation_request",
            {"reason": command.reason, "requested_by": command.requested_by},
        )
        journey = self.journeys.mark_state(command.journey_id, "CLOSED")
        self._publish(command.correlation_id, command.tenant_id, journey.journey_id, "booking.cancelled", {"reason": command.reason})
        return {"journey_id": journey.journey_id, "journey_state": journey.current_state, "status": "cancelled"}
