from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha1


SCENARIOS = [
    {
        "id": "appointment-reminder-keep",
        "title": "Appointment Reminder Keep",
        "summary": "A reminder is sent and the customer keeps the appointment.",
        "presenter_intro": "This scenario shows the simple but high-value reminder path before an appointment.",
        "simple_explanation": "The system reminds the customer and the customer says the appointment should stay as it is.",
        "technical_explanation": "The Orchestrator sends a reminder, records the keep action, writes audit data, and prepares a CRM activity.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Reminder is sent",
                "journey_state": "REMINDER_PENDING",
                "active_component": "LEKAB",
                "selected_slot": "Tomorrow 10:00",
                "booking_reference": "gbook-10425",
                "provider_reference": "google-evt-10425",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "",
                "platform_message": "Reminder: You have an appointment tomorrow at 10:00. Booking reference: gbook-10425. Keep, reschedule, cancel, or call me?",
                "slot_options": ["Keep Appointment", "Reschedule", "Cancel", "Call Me"],
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "active",
                    "Google Adapter": "done",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.reminder.sent",
                    "crm.activity.append.requested",
                ],
                "audit_log": [
                    "Reminder sent with appointment details and next actions.",
                ],
                "crm_events": [
                    "crm.activity.append.requested",
                ],
                "speaker_notes": [
                    "This is easy to understand for every customer: tomorrow you have an appointment, what do you want to do?",
                    "The system is not waiting passively. It actively reduces no-shows."
                ],
            },
            {
                "label": "Customer keeps the appointment",
                "journey_state": "BOOKED",
                "active_component": "Orchestrator",
                "selected_slot": "Tomorrow 10:00",
                "booking_reference": "gbook-10425",
                "provider_reference": "google-evt-10425",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "Keep appointment",
                "platform_message": "Perfect. Your appointment stays tomorrow at 10:00.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "done",
                },
                "event_stream": [
                    "appointment.reminder.confirmed",
                    "crm.activity.append.requested",
                ],
                "audit_log": [
                    "Customer confirmed the appointment will stay as booked.",
                ],
                "crm_events": [
                    "crm.activity.append.requested",
                ],
                "speaker_notes": [
                    "A very common real-world action is simply confirming that the appointment still fits.",
                ],
            },
        ],
    },
    {
        "id": "appointment-reminder-reschedule",
        "title": "Appointment Reminder Reschedule",
        "summary": "A reminder is sent and the customer moves the appointment to a new slot.",
        "presenter_intro": "This reminder flow is powerful because it turns a possible no-show into a controlled reschedule.",
        "simple_explanation": "The customer gets reminded, sees the appointment, and asks for a different time.",
        "technical_explanation": "The reminder action enters the reschedule path, new slots are offered, and the provider booking is updated.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Reminder offers actions",
                "journey_state": "REMINDER_PENDING",
                "active_component": "LEKAB",
                "selected_slot": "Thursday 14:30",
                "booking_reference": "gbook-22001",
                "provider_reference": "google-evt-22001",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "",
                "platform_message": "Reminder: You have an appointment tomorrow at 14:30. What do you want to do?",
                "slot_options": ["Keep Appointment", "Reschedule", "Cancel", "Call Me"],
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "active",
                    "Google Adapter": "done",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.reminder.sent",
                ],
                "audit_log": [
                    "Reminder sent with appointment details and next actions.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The reminder already gives the most important next actions directly."
                ],
            },
            {
                "label": "Reminder enters reschedule path",
                "journey_state": "WAITING_FOR_SELECTION",
                "active_component": "Orchestrator",
                "selected_slot": None,
                "booking_reference": "gbook-22001",
                "provider_reference": "google-evt-22001",
                "slot_hold_status": "active",
                "escalated": False,
                "customer_message": "Reschedule",
                "platform_message": "Here are 2 new time options for you.",
                "slot_options": ["Friday 09:00", "Friday 11:30"],
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "active",
                    "Google Adapter": "active",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.reminder.reschedule.requested",
                    "appointment.reschedule.requested",
                    "calendar.slots.found",
                ],
                "audit_log": [
                    "Customer entered the reschedule path from the reminder.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "This is where reminder logic and scheduling logic connect together."
                ],
            },
            {
                "label": "New booking time is confirmed",
                "journey_state": "REMINDER_PENDING",
                "active_component": "Google Adapter",
                "selected_slot": "Friday 09:00",
                "booking_reference": "gbook-22001",
                "provider_reference": "google-evt-22001",
                "slot_hold_status": "consumed",
                "escalated": False,
                "customer_message": "Friday 09:00",
                "platform_message": "Done. Your appointment was moved to Friday 09:00.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "done",
                },
                "event_stream": [
                    "appointment.booking.rescheduled",
                    "crm.booking.update.requested",
                ],
                "audit_log": [
                    "Booking committed successfully.",
                ],
                "crm_events": [
                    "crm.booking.update.requested",
                ],
                "speaker_notes": [
                    "The system keeps the same journey context while still moving the provider-side booking."
                ],
            },
        ],
    },
    {
        "id": "appointment-reminder-cancel",
        "title": "Appointment Reminder Cancel",
        "summary": "A reminder is sent and the customer cancels from the reminder itself.",
        "presenter_intro": "This shows how a reminder can immediately turn into a backend cancellation workflow.",
        "simple_explanation": "The customer gets reminded and decides to cancel before the appointment happens.",
        "technical_explanation": "The reminder action triggers provider cancellation, audit, and CRM cancel preparation.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Reminder is received",
                "journey_state": "REMINDER_PENDING",
                "active_component": "LEKAB",
                "selected_slot": "Monday 16:00",
                "booking_reference": "gbook-33002",
                "provider_reference": "google-evt-33002",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "",
                "platform_message": "Reminder: You have an appointment Monday at 16:00. Keep, reschedule, cancel, or call me?",
                "slot_options": ["Keep Appointment", "Reschedule", "Cancel", "Call Me"],
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "active",
                    "Google Adapter": "done",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.reminder.sent",
                ],
                "audit_log": [
                    "Reminder sent with appointment details and next actions.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "The reminder is not just informational. It offers direct workflow actions."
                ],
            },
            {
                "label": "Cancellation completes",
                "journey_state": "CLOSED",
                "active_component": "Google Adapter",
                "selected_slot": "Monday 16:00",
                "booking_reference": "gbook-33002",
                "provider_reference": "google-evt-33002",
                "slot_hold_status": "released",
                "escalated": False,
                "customer_message": "Cancel",
                "platform_message": "Your appointment is cancelled.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "done",
                },
                "event_stream": [
                    "appointment.reminder.cancel.requested",
                    "booking.cancelled",
                    "crm.booking.cancel.requested",
                ],
                "audit_log": [
                    "Journey cancelled.",
                ],
                "crm_events": [
                    "crm.booking.cancel.requested",
                ],
                "speaker_notes": [
                    "That gives the customer a fast way out and still keeps the backend state clean."
                ],
            },
        ],
    },
    {
        "id": "appointment-reminder-call-me",
        "title": "Appointment Reminder Call Me",
        "summary": "A reminder is sent and the customer asks for a human follow-up.",
        "presenter_intro": "A good reminder flow also knows when to hand the case to a human.",
        "simple_explanation": "The customer does not want to click through options and asks for a call instead.",
        "technical_explanation": "The reminder action triggers escalation, audit logging, and CRM activity preparation.",
        "starting_mode": "combined",
        "steps": [
            {
                "label": "Reminder asks what to do",
                "journey_state": "REMINDER_PENDING",
                "active_component": "LEKAB",
                "selected_slot": "Wednesday 08:30",
                "booking_reference": "gbook-44003",
                "provider_reference": "google-evt-44003",
                "slot_hold_status": "done",
                "escalated": False,
                "customer_message": "",
                "platform_message": "Reminder: You have an appointment Wednesday at 08:30. Keep, reschedule, cancel, or call me?",
                "slot_options": ["Keep Appointment", "Reschedule", "Cancel", "Call Me"],
                "flow_steps": {
                    "LEKAB": "active",
                    "Orchestrator": "active",
                    "Google Adapter": "done",
                    "CRM Event Layer": "pending",
                },
                "event_stream": [
                    "appointment.reminder.sent",
                ],
                "audit_log": [
                    "Reminder sent with appointment details and next actions.",
                ],
                "crm_events": [],
                "speaker_notes": [
                    "Sometimes the best automation step is a clean handover."
                ],
            },
            {
                "label": "Human handover is triggered",
                "journey_state": "ESCALATED",
                "active_component": "Orchestrator",
                "selected_slot": "Wednesday 08:30",
                "booking_reference": "gbook-44003",
                "provider_reference": "google-evt-44003",
                "slot_hold_status": "done",
                "escalated": True,
                "customer_message": "Call me",
                "platform_message": "Okay. I will ask a person to contact you.",
                "flow_steps": {
                    "LEKAB": "done",
                    "Orchestrator": "done",
                    "Google Adapter": "done",
                    "CRM Event Layer": "active",
                },
                "event_stream": [
                    "appointment.reminder.call_me.requested",
                    "appointment.escalation.requested",
                    "crm.activity.append.requested",
                ],
                "audit_log": [
                    "Customer asked for a human handover from the reminder.",
                ],
                "crm_events": [
                    "crm.activity.append.requested",
                ],
                "speaker_notes": [
                    "This is a safe path for people who want human contact instead of self-service."
                ],
            },
        ],
    },
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


TRANSLATIONS = {
    "de": {
        "Demo": "Demo",
        "Monitoring": "Monitoring",
        "Combined": "Kombiniert",
        "Appointment Reminder Keep": "Termin-Erinnerung Behalten",
        "A reminder is sent and the customer keeps the appointment.": "Eine Erinnerung wird gesendet und der Kunde behaelt den Termin.",
        "This scenario shows the simple but high-value reminder path before an appointment.": "Dieses Szenario zeigt den einfachen, aber sehr wertvollen Erinnerungsweg vor einem Termin.",
        "The system reminds the customer and the customer says the appointment should stay as it is.": "Das System erinnert den Kunden und der Kunde sagt, dass der Termin so bleiben soll.",
        "The Orchestrator sends a reminder, records the keep action, writes audit data, and prepares a CRM activity.": "Der Orchestrator sendet eine Erinnerung, erfasst die Bestaetigung, schreibt Audit-Daten und bereitet eine CRM-Aktivitaet vor.",
        "Reminder is sent": "Erinnerung wird gesendet",
        "Reminder: You have an appointment tomorrow at 10:00. Booking reference: gbook-10425. Keep, reschedule, cancel, or call me?": "Erinnerung: Du hast morgen um 10:00 einen Termin. Buchungsreferenz: gbook-10425. Behalten, verschieben, absagen oder rueckrufen lassen?",
        "Keep Appointment": "Termin behalten",
        "Reschedule": "Verschieben",
        "Cancel": "Absagen",
        "Call Me": "Ruf mich an",
        "Reminder sent with appointment details and next actions.": "Erinnerung mit Termindetails und naechsten Aktionen wurde gesendet.",
        "This is easy to understand for every customer: tomorrow you have an appointment, what do you want to do?": "Das versteht jeder Kunde sofort: Morgen hast du einen Termin, was moechtest du tun?",
        "The system is not waiting passively. It actively reduces no-shows.": "Das System wartet nicht passiv. Es reduziert aktiv No-Shows.",
        "Customer keeps the appointment": "Kunde behaelt den Termin",
        "Keep appointment": "Termin behalten",
        "Perfect. Your appointment stays tomorrow at 10:00.": "Perfekt. Dein Termin bleibt morgen um 10:00.",
        "Customer confirmed the appointment will stay as booked.": "Der Kunde hat bestaetigt, dass der Termin wie gebucht bestehen bleibt.",
        "A very common real-world action is simply confirming that the appointment still fits.": "Eine sehr haeufige reale Aktion ist einfach zu bestaetigen, dass der Termin noch passt.",
        "Appointment Reminder Reschedule": "Termin-Erinnerung Verschieben",
        "A reminder is sent and the customer moves the appointment to a new slot.": "Eine Erinnerung wird gesendet und der Kunde verschiebt den Termin auf einen neuen Slot.",
        "This reminder flow is powerful because it turns a possible no-show into a controlled reschedule.": "Dieser Erinnerungsablauf ist stark, weil er einen moeglichen No-Show in eine kontrollierte Verschiebung verwandelt.",
        "The customer gets reminded, sees the appointment, and asks for a different time.": "Der Kunde wird erinnert, sieht den Termin und bittet um eine andere Uhrzeit.",
        "The reminder action enters the reschedule path, new slots are offered, and the provider booking is updated.": "Die Erinnerungsaktion startet den Verschiebeweg, neue Slots werden angeboten und die Provider-Buchung wird aktualisiert.",
        "Reminder offers actions": "Erinnerung bietet Aktionen an",
        "Reminder: You have an appointment tomorrow at 14:30. What do you want to do?": "Erinnerung: Du hast morgen um 14:30 einen Termin. Was moechtest du tun?",
        "The reminder already gives the most important next actions directly.": "Die Erinnerung bietet direkt die wichtigsten naechsten Aktionen an.",
        "Reminder enters reschedule path": "Erinnerung startet Verschiebeweg",
        "Here are 2 new time options for you.": "Hier sind 2 neue Zeitoptionen fuer dich.",
        "Customer entered the reschedule path from the reminder.": "Der Kunde ist aus der Erinnerung in den Verschiebeweg gewechselt.",
        "This is where reminder logic and scheduling logic connect together.": "Hier verbinden sich Erinnerungslogik und Terminlogik.",
        "New booking time is confirmed": "Neue Terminzeit wird bestaetigt",
        "Done. Your appointment was moved to Friday 09:00.": "Fertig. Dein Termin wurde auf Freitag 09:00 verschoben.",
        "The system keeps the same journey context while still moving the provider-side booking.": "Das System behaelt denselben Journey-Kontext, waehrend die Provider-Buchung verschoben wird.",
        "Appointment Reminder Cancel": "Termin-Erinnerung Absagen",
        "A reminder is sent and the customer cancels from the reminder itself.": "Eine Erinnerung wird gesendet und der Kunde sagt direkt aus der Erinnerung heraus ab.",
        "This shows how a reminder can immediately turn into a backend cancellation workflow.": "Das zeigt, wie eine Erinnerung sofort in einen Backend-Absageablauf wechseln kann.",
        "The customer gets reminded and decides to cancel before the appointment happens.": "Der Kunde wird erinnert und entscheidet sich vor dem Termin fuer eine Absage.",
        "The reminder action triggers provider cancellation, audit, and CRM cancel preparation.": "Die Erinnerungsaktion startet die Provider-Absage, Audit und die CRM-Vorbereitung fuer die Absage.",
        "Reminder is received": "Erinnerung wird empfangen",
        "Reminder: You have an appointment Monday at 16:00. Keep, reschedule, cancel, or call me?": "Erinnerung: Du hast am Montag um 16:00 einen Termin. Behalten, verschieben, absagen oder rueckrufen lassen?",
        "The reminder is not just informational. It offers direct workflow actions.": "Die Erinnerung ist nicht nur informativ. Sie bietet direkte Workflow-Aktionen an.",
        "Cancellation completes": "Absage wird abgeschlossen",
        "Your appointment is cancelled.": "Dein Termin ist abgesagt.",
        "Journey cancelled.": "Journey wurde abgesagt.",
        "That gives the customer a fast way out and still keeps the backend state clean.": "Das gibt dem Kunden einen schnellen Ausweg und haelt den Backend-Status trotzdem sauber.",
        "Appointment Reminder Call Me": "Termin-Erinnerung Ruf mich an",
        "A reminder is sent and the customer asks for a human follow-up.": "Eine Erinnerung wird gesendet und der Kunde bittet um menschliche Rueckmeldung.",
        "A good reminder flow also knows when to hand the case to a human.": "Ein guter Erinnerungsablauf weiss auch, wann ein Fall an einen Menschen uebergeben werden muss.",
        "The customer does not want to click through options and asks for a call instead.": "Der Kunde moechte sich nicht durch Optionen klicken und bittet stattdessen um einen Rueckruf.",
        "The reminder action triggers escalation, audit logging, and CRM activity preparation.": "Die Erinnerungsaktion startet Eskalation, Audit-Protokollierung und CRM-Aktivitaetsvorbereitung.",
        "Reminder asks what to do": "Erinnerung fragt nach der naechsten Aktion",
        "Reminder: You have an appointment Wednesday at 08:30. Keep, reschedule, cancel, or call me?": "Erinnerung: Du hast am Mittwoch um 08:30 einen Termin. Behalten, verschieben, absagen oder rueckrufen lassen?",
        "Sometimes the best automation step is a clean handover.": "Manchmal ist der beste Automatisierungsschritt eine saubere Uebergabe.",
        "Human handover is triggered": "Menschliche Uebergabe wird gestartet",
        "Okay. I will ask a person to contact you.": "Okay. Ich bitte eine Person, dich zu kontaktieren.",
        "Customer asked for a human handover from the reminder.": "Der Kunde hat aus der Erinnerung heraus um menschliche Uebergabe gebeten.",
        "This is a safe path for people who want human contact instead of self-service.": "Das ist ein sicherer Weg fuer Menschen, die lieber persoenlichen Kontakt statt Self-Service wollen.",
        "Standard Booking": "Standard-Terminbuchung",
        "A customer asks for an appointment, picks a free slot, and gets a real confirmation.": "Ein Kunde fragt nach einem Termin, waehlt einen freien Slot und bekommt eine echte Bestaetigung.",
        "On the left you see the customer. On the right you see what the system is doing.": "Links siehst du den Kunden. Rechts siehst du, was das System macht.",
        "This feels simple for the customer, but several systems work together in the background.": "Fuer den Kunden wirkt es einfach, aber im Hintergrund arbeiten mehrere Systeme zusammen.",
        "The message comes in through LEKAB, the Orchestrator starts the process, Google checks the slot, and CRM events are prepared.": "Die Nachricht kommt ueber LEKAB rein, der Orchestrator startet den Prozess, Google prueft den Slot und CRM-Events werden vorbereitet.",
        "Customer asks for an appointment": "Kunde fragt nach einem Termin",
        "I want to book an appointment.": "Ich moechte einen Termin buchen.",
        "Sure. I will look for free times for you.": "Klar. Ich suche freie Zeiten fuer dich.",
        "Journey started and customer identified.": "Journey gestartet und Kunde identifiziert.",
        "The message comes in via RCS or messaging and enters the system.": "Die Nachricht kommt ueber RCS oder Messaging ins System.",
        "This is the first point where the workflow starts.": "Das ist der erste Punkt, an dem der Workflow startet.",
        "Slots are found": "Slots werden gefunden",
        "I found 3 possible slots. Please pick one.": "Ich habe 3 moegliche Slots gefunden. Bitte waehle einen aus.",
        "Tomorrow 10:00": "Morgen 10:00",
        "Tomorrow 14:30": "Morgen 14:30",
        "Friday 09:15": "Freitag 09:15",
        "Offerable slots prepared.": "Angebotene Slots wurden vorbereitet.",
        "Now we connect to Google Calendar and check availability.": "Jetzt verbinden wir uns mit Google Calendar und pruefen die Verfuegbarkeit.",
        "The system returns only real slots, not fake suggestions.": "Das System liefert nur echte Slots, keine erfundenen Vorschlaege.",
        "Customer selects a slot": "Kunde waehlt einen Slot",
        "Great. Please confirm this appointment.": "Super. Bitte bestaetige diesen Termin.",
        "Customer selected a slot.": "Der Kunde hat einen Slot ausgewaehlt.",
        "The user selects a slot. Now we have a concrete intent.": "Der Nutzer waehlt einen Slot. Jetzt haben wir eine konkrete Absicht.",
        "Booking is created": "Buchung wird erstellt",
        "Confirm": "Bestaetigen",
        "Appointment confirmed for tomorrow at 10:00.": "Termin fuer morgen um 10:00 bestaetigt.",
        "Booking committed successfully.": "Buchung erfolgreich geschrieben.",
        "Now we create a real booking and update backend systems.": "Jetzt erstellen wir eine echte Buchung und aktualisieren die Backendsysteme.",
        "This is not a chatbot. This is process automation.": "Das ist kein Chatbot. Das ist Prozessautomatisierung.",
        "Reschedule": "Verschiebung",
        "An existing booking is changed to a new slot and the provider booking is updated.": "Eine bestehende Buchung wird auf einen neuen Slot verschoben und die Provider-Buchung wird aktualisiert.",
        "This scenario shows that the system can change an existing booking, not just create a new one.": "Dieses Szenario zeigt, dass das System eine bestehende Buchung aendern und nicht nur eine neue erstellen kann.",
        "The customer asks for a different time and the system safely moves the appointment.": "Der Kunde fragt nach einer anderen Zeit und das System verschiebt den Termin sicher.",
        "The Orchestrator starts a reschedule flow, Google updates the provider booking, and CRM update events are prepared.": "Der Orchestrator startet einen Verschiebeablauf, Google aktualisiert die Provider-Buchung und CRM-Updates werden vorbereitet.",
        "Existing booking is loaded": "Bestehende Buchung wird geladen",
        "Friday 09:15": "Freitag 09:15",
        "I need a different time.": "Ich brauche eine andere Zeit.",
        "No problem. I will search for replacement slots.": "Kein Problem. Ich suche Ersatz-Slots.",
        "Reschedule flow started.": "Verschiebeablauf gestartet.",
        "The Orchestrator understands this is not a new booking. It is a reschedule request.": "Der Orchestrator versteht, dass das keine neue Buchung ist. Es ist eine Verschiebungsanfrage.",
        "Replacement slots are offered": "Ersatz-Slots werden angeboten",
        "Here are 2 new times that work.": "Hier sind 2 neue passende Zeiten.",
        "Monday 11:00": "Montag 11:00",
        "Tuesday 15:30": "Dienstag 15:30",
        "Replacement slots prepared.": "Ersatz-Slots wurden vorbereitet.",
        "The Google Adapter searches for replacement slots and sends them back in a normalized format.": "Der Google Adapter sucht Ersatz-Slots und gibt sie in einem normalisierten Format zurueck.",
        "Provider booking is updated": "Provider-Buchung wird aktualisiert",
        "Done. Your appointment was moved to Monday 11:00.": "Fertig. Dein Termin wurde auf Montag 11:00 verschoben.",
        "Provider booking updated successfully.": "Provider-Buchung erfolgreich aktualisiert.",
        "The provider-side booking is updated and the CRM gets a matching update event.": "Die Provider-Buchung wird aktualisiert und das CRM bekommt ein passendes Update-Event.",
        "Cancellation": "Absage",
        "The customer cancels an appointment and the provider booking is cancelled too.": "Der Kunde sagt einen Termin ab und die Provider-Buchung wird ebenfalls abgesagt.",
        "This scenario shows that cancellation is a real workflow with provider and CRM consequences.": "Dieses Szenario zeigt, dass eine Absage ein echter Workflow mit Provider- und CRM-Folgen ist.",
        "The customer asks to cancel and the system handles the cancellation end to end.": "Der Kunde bittet um Absage und das System bearbeitet die Absage von Anfang bis Ende.",
        "The Orchestrator requests a provider cancellation, the Google Adapter confirms it, and CRM gets a cancel event.": "Der Orchestrator fordert die Provider-Absage an, der Google Adapter bestaetigt sie und das CRM bekommt ein Absage-Event.",
        "Customer wants to cancel": "Kunde moechte absagen",
        "Please cancel my appointment.": "Bitte sage meinen Termin ab.",
        "Okay. I am cancelling it now.": "Okay. Ich sage ihn jetzt ab.",
        "Cancellation requested by customer.": "Absage wurde vom Kunden angefordert.",
        "The cancellation starts in messaging, but it has to finish cleanly in the backend too.": "Die Absage startet im Messaging, muss aber auch im Backend sauber abgeschlossen werden.",
        "Booking is cancelled": "Buchung wird abgesagt",
        "Your appointment is cancelled.": "Dein Termin ist abgesagt.",
        "Journey cancelled and provider cancellation confirmed.": "Journey abgesagt und Provider-Absage bestaetigt.",
        "The booking is cancelled in the provider and a CRM cancel request is emitted.": "Die Buchung wird beim Provider abgesagt und eine CRM-Absageanforderung wird erzeugt.",
        "No Slot and Escalation": "Kein Slot und Eskalation",
        "No free slot is found, the system offers options, and a human handover is shown.": "Es wird kein freier Slot gefunden, das System bietet Optionen an und zeigt eine menschliche Uebergabe.",
        "This is important because good automation must know when it cannot solve the problem alone.": "Das ist wichtig, weil gute Automatisierung wissen muss, wann sie ein Problem nicht allein loesen kann.",
        "When there is no free slot, the system does not get stuck. It offers alternatives or human help.": "Wenn kein freier Slot vorhanden ist, bleibt das System nicht stecken. Es bietet Alternativen oder menschliche Hilfe an.",
        "The Orchestrator detects the no-slot outcome, writes audit data, and triggers escalation or callback logic.": "Der Orchestrator erkennt das No-Slot-Ergebnis, schreibt Audit-Daten und startet Eskalations- oder Rueckruflogik.",
        "No slot is found": "Kein Slot wird gefunden",
        "I need an appointment next week.": "Ich brauche naechste Woche einen Termin.",
        "I could not find a free slot. Would you like next month or human help?": "Ich konnte keinen freien Slot finden. Moechtest du naechsten Monat oder menschliche Hilfe?",
        "Next month": "Naechster Monat",
        "Need human help": "Ich brauche menschliche Hilfe",
        "Call me back": "Ruf mich zurueck",
        "No valid slots available; human handover requested.": "Keine gueltigen Slots verfuegbar; menschliche Uebergabe angefordert.",
        "The system does not fail silently.": "Das System scheitert nicht still.",
        "It offers next month, human help, or callback options.": "Es bietet naechsten Monat, menschliche Hilfe oder Rueckrufoptionen an.",
        "Provider Failure": "Provider-Fehler",
        "A provider-side failure is shown clearly, together with the audit and escalation path.": "Ein Provider-Fehler wird klar gezeigt, zusammen mit Audit- und Eskalationsweg.",
        "This scenario is useful for technical and management demos because it shows controlled failure handling.": "Dieses Szenario ist fuer Technik- und Management-Demos nuetzlich, weil es kontrollierte Fehlerbehandlung zeigt.",
        "Even when the provider fails, the system still reacts in a clear and safe way.": "Selbst wenn der Provider scheitert, reagiert das System klar und sicher.",
        "Provider errors become audit records, escalation events, and a clear handover path.": "Provider-Fehler werden zu Audit-Eintraegen, Eskalations-Events und einem klaren Uebergabeweg.",
        "Provider update fails": "Provider-Update scheitert",
        "Please move my appointment.": "Bitte verschiebe meinen Termin.",
        "I ran into a problem and I am asking a human to help.": "Ich habe ein Problem erkannt und bitte einen Menschen zu helfen.",
        "Provider reference was missing or stale during update.": "Die Provider-Referenz fehlte oder war beim Update veraltet.",
        "A provider failure should not confuse the customer or hide technical details.": "Ein Provider-Fehler darf den Kunden nicht verwirren oder technische Details verstecken.",
        "The platform keeps a clear error and escalation path.": "Die Plattform behaelt einen klaren Fehler- und Eskalationsweg bei.",
        "sent": "gesendet",
        "received": "empfangen",
        "delivered": "zugestellt",
        "inbound-captured": "eingehend-erfasst",
        "20 users": "20 Nutzer",
        "100 users": "100 Nutzer",
        "1000 users": "1000 Nutzer",
        "4 workers": "4 Worker",
        "12 workers": "12 Worker",
        "48 workers": "48 Worker",
    }
}


def _translate(value, lang: str):
    if lang != "de":
        return deepcopy(value)
    if isinstance(value, str):
        return TRANSLATIONS["de"].get(value, value)
    if isinstance(value, list):
        return [_translate(item, lang) for item in value]
    if isinstance(value, dict):
        return {key: _translate(item, lang) for key, item in value.items()}
    return deepcopy(value)


def _simulate_message_metadata(scenario_id: str, step_index: int, step: dict) -> dict:
    enriched = deepcopy(step)
    seed = f"{scenario_id}-{step_index}-{step.get('active_component', 'system')}"
    digest = sha1(seed.encode("utf-8")).hexdigest()[:8]
    has_message = bool(step.get("customer_message") or step.get("platform_message") or step.get("active_component") == "LEKAB")
    if not has_message:
        return enriched

    message_channel = step.get("message_channel")
    if not message_channel:
        message_channel = "SMS" if "fallback" in " ".join(step.get("event_stream", [])).lower() else "RCS"

    enriched.setdefault("lekab_job_id", f"lekab-job-{digest}")
    enriched.setdefault("message_id", f"msg-{digest}")
    enriched.setdefault("message_channel", message_channel)
    enriched.setdefault("message_status", "sent" if step.get("platform_message") else "received")
    enriched.setdefault(
        "delivery_status",
        "delivered" if step.get("platform_message") else "inbound-captured",
    )
    return enriched


def _build_event_records(
    scenario_id: str,
    step_index: int,
    step: dict,
    journey_id: str,
    correlation_id: str,
    trace_id: str,
) -> list[dict]:
    base_time = datetime(2026, 3, 28, 9, 0, tzinfo=timezone.utc) + timedelta(minutes=step_index * 3)
    records: list[dict] = []
    for event_index, event_type in enumerate(step.get("event_stream", []), start=1):
        records.append(
            {
                "timestamp": (base_time + timedelta(seconds=event_index * 7)).isoformat().replace("+00:00", "Z"),
                "event_type": event_type,
                "journey_id": journey_id,
                "correlation_id": correlation_id,
                "trace_id": trace_id,
                "payload": {
                    "scenario_id": scenario_id,
                    "step_label": step.get("label"),
                    "active_component": step.get("active_component"),
                    "journey_state": step.get("journey_state"),
                },
            }
        )
    return records


def _performance_snapshot(step: dict, event_count: int) -> dict:
    base = 180 if step.get("active_component") == "LEKAB" else 240
    modifier = 35 * max(event_count, 1)
    if step.get("escalated"):
        modifier += 90
    return {
        "avg_response_ms": base + modifier,
        "max_response_ms": base + modifier + 120,
        "events_per_second": round(max(event_count, 1) / 2.0, 1),
    }


def _technical_payload(step: dict, journey_id: str, correlation_id: str, trace_id: str) -> dict:
    return {
        "journey_id": journey_id,
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "journey_state": step.get("journey_state"),
        "active_component": step.get("active_component"),
        "flow_steps": step.get("flow_steps", {}),
        "booking_reference": step.get("booking_reference"),
        "provider_reference": step.get("provider_reference"),
        "message_id": step.get("message_id"),
        "lekab_job_id": step.get("lekab_job_id"),
    }


def _with_technical_monitoring(scenarios: list[dict]) -> list[dict]:
    enriched_scenarios = deepcopy(scenarios)
    for scenario in enriched_scenarios:
        journey_id = f"journey-{scenario['id']}"
        correlation_id = f"corr-{scenario['id']}"
        trace_id = f"trace-{scenario['id']}"
        original_steps = deepcopy(scenario.get("steps", []))
        scenario["journey_id"] = journey_id
        scenario["correlation_id"] = correlation_id
        scenario["trace_id"] = trace_id
        scenario["steps"] = []
        all_events: list[dict] = []
        for index, original_step in enumerate(original_steps, start=1):
            step = _simulate_message_metadata(scenario["id"], index, original_step)
            step_trace_id = f"{trace_id}-{index}"
            step["journey_id"] = journey_id
            step["correlation_id"] = correlation_id
            step["trace_id"] = step_trace_id
            step["events"] = _build_event_records(scenario["id"], index, step, journey_id, correlation_id, step_trace_id)
            all_events.extend(step["events"])
            step["performance"] = _performance_snapshot(step, len(step["events"]))
            step["raw_payload"] = _technical_payload(step, journey_id, correlation_id, step_trace_id)
            step["command_structure"] = {
                "command_type": f"{step.get('active_component', 'system').lower().replace(' ', '_')}.step.process",
                "tenant_id": "demo",
                "journey_id": journey_id,
                "correlation_id": correlation_id,
                "trace_id": step_trace_id,
            }
            scenario["steps"].append(step)
        scenario["all_events"] = list(reversed(all_events))
    return enriched_scenarios


def _load_profiles() -> list[dict]:
    return [
        {"id": "20", "label": "20 users", "active_journeys": 20, "avg_processing_ms": 220, "max_processing_ms": 420, "events_per_second": 12.5, "parallel_execution": "4 workers"},
        {"id": "100", "label": "100 users", "active_journeys": 100, "avg_processing_ms": 310, "max_processing_ms": 690, "events_per_second": 55.0, "parallel_execution": "12 workers"},
        {"id": "1000", "label": "1000 users", "active_journeys": 1000, "avg_processing_ms": 540, "max_processing_ms": 1200, "events_per_second": 340.0, "parallel_execution": "48 workers"},
    ]


def build_simulation_payload(lang: str = "en") -> dict:
    payload = {
        "modes": [
            {"id": "demo", "label": "Demo"},
            {"id": "monitoring", "label": "Monitoring"},
            {"id": "combined", "label": "Combined"},
        ],
        "statuses": ["pending", "active", "done", "failed", "escalated"],
        "scenarios": _with_technical_monitoring(SCENARIOS),
        "load_profiles": _load_profiles(),
    }
    return _translate(payload, "de" if lang == "de" else "en")
