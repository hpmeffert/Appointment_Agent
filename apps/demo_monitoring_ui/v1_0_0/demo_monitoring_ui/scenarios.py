from __future__ import annotations


SCENARIOS = [
    {
        "id": "standard-booking",
        "title": "Standard Booking",
        "summary": "A customer asks for an appointment, picks a free slot, and gets a real confirmation.",
        "presenter_intro": "On the left you see the customer. On the right you see what the system is doing.",
        "simple_explanation": "This feels simple for the customer, but several systems work together in the background.",
        "technical_explanation": "The message comes in through LEKAB, the Orchestrator starts the process, Google checks the slot, and CRM events are prepared.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Customer asks for an appointment",
                "journey_state": "IDENTIFYING_CUSTOMER",
                "active_component": "LEKAB",
                "selected_slot": None,
                "booking_reference": None,
                "provider_reference": None,
                "slot_hold_status": "pending",
                "escalated": False,
                "customer_message": "I want to book an appointment.",
                "platform_message": "Sure. I will look for free times for you.",
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "pending",
                    "Google Adapter": "pending",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "channel.message.received",
                    "appointment.search.requested",
                ],
                "audit_log": [
                    "Journey started and customer identified.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The message comes in via RCS or messaging and enters the system.",
                    "This is the first point where the workflow starts."
                ],
            },
            {
                "label": "Slots are found",
                "journey_state": "WAITING_FOR_SELECTION",
                "active_component": "Google Adapter",
                "selected_slot": None,
                "booking_reference": None,
                "provider_reference": None,
                "slot_hold_status": "active",
                "escalated": False,
                "customer_message": "I want to book an appointment.",
                "platform_message": "I found 3 possible slots. Please pick one.",
                "slot_options": ["Tomorrow 10:00", "Tomorrow 14:30", "Friday 09:15"],
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "active",
                    "Google Adapter": "done",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "calendar.slots.found",
                    "appointment.offer.send",
                ],
                "audit_log": [
                    "Offerable slots prepared.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "Now we connect to Google Calendar and check availability.",
                    "The system returns only real slots, not fake suggestions."
                ],
            },
            {
                "label": "Customer selects a slot",
                "journey_state": "WAITING_FOR_CONFIRMATION",
                "active_component": "Orchestrator",
                "selected_slot": "Tomorrow 10:00",
                "booking_reference": None,
                "provider_reference": None,
                "slot_hold_status": "active",
                "escalated": False,
                "customer_message": "Tomorrow 10:00",
                "platform_message": "Great. Please confirm this appointment.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "active",
                    "Google Adapter": "pending",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.slot.selected",
                    "booking.slot.held",
                ],
                "audit_log": [
                    "Customer selected a slot.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The user selects a slot. Now we have a concrete intent.",
                ],
            },
            {
                "label": "Booking is created",
                "journey_state": "REMINDER_PENDING",
                "active_component": "Google Adapter",
                "selected_slot": "Tomorrow 10:00",
                "booking_reference": "gbook-4810demo",
                "provider_reference": "google-evt-90210",
                "slot_hold_status": "consumed",
                "escalated": False,
                "customer_message": "Confirm",
                "platform_message": "Appointment confirmed for tomorrow at 10:00.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "done",
                },
                "event_stream": [
                    "appointment.booking.create.requested",
                    "calendar.booking.created",
                    "crm.booking.create.requested",
                ],
                "audit_log": [
                    "Booking committed successfully.",
                ],
                "crm_events": [
                    "crm.booking.create.requested",
                ],
                "speaker_notes": [
                    "Now we create a real booking and update backend systems.",
                    "This is not a chatbot. This is process automation."
                ],
            },
        ],
    },
    {
        "id": "reschedule",
        "title": "Reschedule",
        "summary": "An existing booking is changed to a new slot and the provider booking is updated.",
        "presenter_intro": "This scenario shows that the system can change an existing booking, not just create a new one.",
        "simple_explanation": "The customer asks for a different time and the system safely moves the appointment.",
        "technical_explanation": "The Orchestrator starts a reschedule flow, Google updates the provider booking, and CRM update events are prepared.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Existing booking is loaded",
                "journey_state": "BOOKED",
                "active_component": "Orchestrator",
                "selected_slot": "Friday 09:15",
                "booking_reference": "gbook-9482demo",
                "provider_reference": "google-evt-44881",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "I need a different time.",
                "platform_message": "No problem. I will search for replacement slots.",
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "active",
                    "Google Adapter": "pending",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.reschedule.requested",
                    "appointment.search.requested",
                ],
                "audit_log": [
                    "Reschedule flow started.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The Orchestrator understands this is not a new booking. It is a reschedule request.",
                ],
            },
            {
                "label": "Replacement slots are offered",
                "journey_state": "WAITING_FOR_SELECTION",
                "active_component": "Google Adapter",
                "selected_slot": None,
                "booking_reference": "gbook-9482demo",
                "provider_reference": "google-evt-44881",
                "slot_hold_status": "active",
                "escalated": False,
                "customer_message": "I need a different time.",
                "platform_message": "Here are 2 new times that work.",
                "slot_options": ["Monday 11:00", "Tuesday 15:30"],
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "active",
                    "Google Adapter": "done",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "calendar.slots.found",
                    "appointment.offer.send",
                ],
                "audit_log": [
                    "Replacement slots prepared.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The Google Adapter searches for replacement slots and sends them back in a normalized format.",
                ],
            },
            {
                "label": "Provider booking is updated",
                "journey_state": "REMINDER_PENDING",
                "active_component": "Google Adapter",
                "selected_slot": "Monday 11:00",
                "booking_reference": "gbook-9482demo",
                "provider_reference": "google-evt-44881",
                "slot_hold_status": "consumed",
                "escalated": False,
                "customer_message": "Monday 11:00",
                "platform_message": "Done. Your appointment was moved to Monday 11:00.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "done",
                },
                "event_stream": [
                    "appointment.booking.update.requested",
                    "calendar.booking.updated",
                    "crm.booking.update.requested",
                ],
                "audit_log": [
                    "Provider booking updated successfully.",
                ],
                "crm_events": [
                    "crm.booking.update.requested",
                ],
                "speaker_notes": [
                    "The provider-side booking is updated and the CRM gets a matching update event.",
                ],
            },
        ],
    },
    {
        "id": "cancellation",
        "title": "Cancellation",
        "summary": "The customer cancels an appointment and the provider booking is cancelled too.",
        "presenter_intro": "This scenario shows that cancellation is a real workflow with provider and CRM consequences.",
        "simple_explanation": "The customer asks to cancel and the system handles the cancellation end to end.",
        "technical_explanation": "The Orchestrator requests a provider cancellation, the Google Adapter confirms it, and CRM gets a cancel event.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Customer wants to cancel",
                "journey_state": "BOOKED",
                "active_component": "LEKAB",
                "selected_slot": "Thursday 14:00",
                "booking_reference": "gbook-1100demo",
                "provider_reference": "google-evt-2200",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "Please cancel my appointment.",
                "platform_message": "Okay. I am cancelling it now.",
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "active",
                    "Google Adapter": "pending",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.booking.cancel.requested",
                ],
                "audit_log": [
                    "Cancellation requested by customer.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The cancellation starts in messaging, but it has to finish cleanly in the backend too.",
                ],
            },
            {
                "label": "Booking is cancelled",
                "journey_state": "CLOSED",
                "active_component": "Google Adapter",
                "selected_slot": "Thursday 14:00",
                "booking_reference": "gbook-1100demo",
                "provider_reference": "google-evt-2200",
                "slot_hold_status": "released",
                "escalated": False,
                "customer_message": "Please cancel my appointment.",
                "platform_message": "Your appointment is cancelled.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "done",
                },
                "event_stream": [
                    "calendar.booking.cancelled",
                    "crm.booking.cancel.requested",
                ],
                "audit_log": [
                    "Journey cancelled and provider cancellation confirmed.",
                ],
                "crm_events": [
                    "crm.booking.cancel.requested",
                ],
                "speaker_notes": [
                    "The booking is cancelled in the provider and a CRM cancel request is emitted.",
                ],
            },
        ],
    },
    {
        "id": "no-slot-escalation",
        "title": "No Slot and Escalation",
        "summary": "No free slot is found, the system offers options, and a human handover is shown.",
        "presenter_intro": "This is important because good automation must know when it cannot solve the problem alone.",
        "simple_explanation": "When there is no free slot, the system does not get stuck. It offers alternatives or human help.",
        "technical_explanation": "The Orchestrator detects the no-slot outcome, writes audit data, and triggers escalation or callback logic.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "No slot is found",
                "journey_state": "ESCALATED",
                "active_component": "Orchestrator",
                "selected_slot": None,
                "booking_reference": None,
                "provider_reference": None,
                "slot_hold_status": "failed",
                "escalated": True,
                "customer_message": "I need an appointment next week.",
                "platform_message": "I could not find a free slot. Would you like next month or human help?",
                "slot_options": ["Next month", "Need human help", "Call me back"],
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "failed",
                    "CRM Event Layer": "active",
                },
                "event_stream": [
                    "appointment.no_slots.detected",
                    "appointment.escalation.requested",
                    "appointment.handover.target.pending",
                ],
                "audit_log": [
                    "No valid slots available; human handover requested.",
                ],
                "crm_events": [
                    "crm.activity.append.requested",
                ],
                "speaker_notes": [
                    "The system does not fail silently.",
                    "It offers next month, human help, or callback options."
                ],
            },
        ],
    },
    {
        "id": "provider-failure",
        "title": "Provider Failure",
        "summary": "A provider-side failure is shown clearly, together with the audit and escalation path.",
        "presenter_intro": "This scenario is useful for technical and management demos because it shows controlled failure handling.",
        "simple_explanation": "Even when the provider fails, the system still reacts in a clear and safe way.",
        "technical_explanation": "Provider errors become audit records, escalation events, and a clear handover path.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Provider update fails",
                "journey_state": "ESCALATED",
                "active_component": "Google Adapter",
                "selected_slot": "Tuesday 15:30",
                "booking_reference": "gbook-7755demo",
                "provider_reference": "google-evt-missing",
                "slot_hold_status": "failed",
                "escalated": True,
                "customer_message": "Please move my appointment.",
                "platform_message": "I ran into a problem and I am asking a human to help.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "active",
                    "Google Adapter": "failed",
                    "CRM Event Layer": "active",
                },
                "event_stream": [
                    "appointment.booking.update.requested",
                    "appointment.provider.error",
                    "appointment.escalation.requested",
                ],
                "audit_log": [
                    "Provider reference was missing or stale during update.",
                ],
                "crm_events": [
                    "crm.activity.append.requested",
                ],
                "speaker_notes": [
                    "A provider failure should not confuse the customer or hide technical details.",
                    "The platform keeps a clear error and escalation path."
                ],
            },
        ],
    },
]


def build_simulation_payload() -> dict:
    return {
        "modes": [
            {"id": "demo", "label": "Demo"},
            {"id": "monitoring", "label": "Monitoring"},
            {"id": "combined", "label": "Combined"},
        ],
        "statuses": ["pending", "active", "done", "failed", "escalated"],
        "scenarios": SCENARIOS,
    }
