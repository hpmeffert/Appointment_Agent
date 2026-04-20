from __future__ import annotations

from copy import deepcopy


def _button(label_en: str, label_de: str, value: str, *, canonical_action: str, selection_kind: str, journey_target: str | None = None) -> dict:
    return {
        "action_id": value,
        "label_en": label_en,
        "label_de": label_de,
        "value": value,
        "action_type": "reply",
        "canonical_action": canonical_action,
        "selection_kind": selection_kind,
        "journey_target": journey_target,
    }


INITIAL_BUTTONS = [
    _button("Confirm", "Bestaetigen", "confirm", canonical_action="appointment.confirm_requested", selection_kind="initial"),
    _button("Reschedule", "Verschieben", "reschedule", canonical_action="appointment.reschedule_requested", selection_kind="initial", journey_target="relative_choice"),
    _button("Cancel", "Absagen", "cancel", canonical_action="appointment.cancel_requested", selection_kind="initial"),
]

RELATIVE_BUTTONS = [
    _button("This week", "Diese Woche", "this_week", canonical_action="appointment.find_slot_this_week_requested", selection_kind="relative", journey_target="date_choice"),
    _button("Next week", "Naechste Woche", "next_week", canonical_action="appointment.find_slot_next_week_requested", selection_kind="relative", journey_target="date_choice"),
    _button("This month", "Diesen Monat", "this_month", canonical_action="appointment.find_slot_this_month_requested", selection_kind="relative", journey_target="date_choice"),
    _button("Next month", "Naechsten Monat", "next_month", canonical_action="appointment.find_slot_next_month_requested", selection_kind="relative", journey_target="date_choice"),
    _button("Next free slot", "Naechster freier Slot", "next_free_slot", canonical_action="appointment.find_next_free_slot_requested", selection_kind="relative", journey_target="date_choice"),
]

DATE_BUTTONS = [
    _button("05 May", "05. Mai", "date_05_may", canonical_action="appointment.slot_selected", selection_kind="date", journey_target="time_choice"),
    _button("06 May", "06. Mai", "date_06_may", canonical_action="appointment.slot_selected", selection_kind="date", journey_target="time_choice"),
    _button("08 May", "08. Mai", "date_08_may", canonical_action="appointment.slot_selected", selection_kind="date", journey_target="time_choice"),
    _button("12 May", "12. Mai", "date_12_may", canonical_action="appointment.slot_selected", selection_kind="date", journey_target="time_choice"),
]

TIME_BUTTONS = [
    _button("09:00", "09:00", "time_0900", canonical_action="appointment.slot_selected", selection_kind="time"),
    _button("11:30", "11:30", "time_1130", canonical_action="appointment.slot_selected", selection_kind="time"),
    _button("16:00", "16:00", "time_1600", canonical_action="appointment.slot_selected", selection_kind="time"),
    _button("18:30", "18:30", "time_1830", canonical_action="appointment.slot_selected", selection_kind="time"),
]


def _localized_buttons(buttons: list[dict], language: str) -> list[dict]:
    localized: list[dict] = []
    for item in buttons:
        localized.append(
            {
                "action_id": item["action_id"],
                "label": item["label_de"] if language == "de" else item["label_en"],
                "value": item["value"],
                "action_type": item["action_type"],
                "canonical_action": item["canonical_action"],
                "selection_kind": item["selection_kind"],
                "journey_target": item.get("journey_target"),
            }
        )
    return localized


def _localized_payload(language: str, text_en: str, text_de: str, buttons: list[dict], next_step_map: dict[str, str]) -> dict:
    return {
        "channel": "RCS",
        "message_type": "suggestion_buttons",
        "text": text_de if language == "de" else text_en,
        "suggestions": _localized_buttons(buttons, language),
        "next_step_map": deepcopy(next_step_map),
    }


SCENARIO_MATRIX = [
    {
        "id": "confirm-appointment",
        "title_en": "Confirm appointment",
        "title_de": "Termin bestaetigen",
        "summary_en": "The customer confirms that the existing appointment should stay as it is.",
        "summary_de": "Der Kunde bestaetigt, dass der bestehende Termin so bleiben soll.",
        "input_text": "confirm",
        "expected_action": "appointment.confirm_requested",
        "expected_intent": "confirm",
        "expected_state": "safe",
        "outbound_text_en": "Reminder: You have an appointment on 20 April at 10:00. Reply confirm, cancel, or reschedule.",
        "outbound_text_de": "Erinnerung: Sie haben am 20. April um 10:00 einen Termin. Antworten Sie mit bestaetigen, absagen oder verschieben.",
        "journey_step_type": "initial_choice",
        "button_group": "initial_choice",
        "button_source": INITIAL_BUTTONS,
        "next_step_map": {"confirm": "confirmation_complete", "reschedule": "relative_choice", "cancel": "cancellation_complete"},
    },
    {
        "id": "cancel-appointment",
        "title_en": "Cancel appointment",
        "title_de": "Termin absagen",
        "summary_en": "The customer cancels the linked appointment from the reminder flow.",
        "summary_de": "Der Kunde sagt den verknuepften Termin aus dem Reminder-Ablauf heraus ab.",
        "input_text": "cancel",
        "expected_action": "appointment.cancel_requested",
        "expected_intent": "cancel",
        "expected_state": "safe",
        "outbound_text_en": "Reminder: Reply cancel if you cannot attend the appointment.",
        "outbound_text_de": "Erinnerung: Antworten Sie mit absagen, wenn Sie den Termin nicht wahrnehmen koennen.",
        "journey_step_type": "initial_choice",
        "button_group": "initial_choice",
        "button_source": INITIAL_BUTTONS,
        "next_step_map": {"confirm": "confirmation_complete", "reschedule": "relative_choice", "cancel": "cancellation_complete"},
    },
    {
        "id": "reschedule-appointment",
        "title_en": "Reschedule appointment",
        "title_de": "Termin verschieben",
        "summary_en": "The customer asks for a different slot instead of keeping the current one.",
        "summary_de": "Der Kunde moechte statt des aktuellen Termins einen anderen Slot.",
        "input_text": "reschedule",
        "expected_action": "appointment.reschedule_requested",
        "expected_intent": "reschedule",
        "expected_state": "safe",
        "outbound_text_en": "Reminder: Reply reschedule if you need a different time.",
        "outbound_text_de": "Erinnerung: Antworten Sie mit verschieben, wenn Sie eine andere Zeit brauchen.",
        "journey_step_type": "initial_choice",
        "button_group": "initial_choice",
        "button_source": INITIAL_BUTTONS,
        "next_step_map": {"confirm": "confirmation_complete", "reschedule": "relative_choice", "cancel": "cancellation_complete"},
    },
    {
        "id": "new-appointment-search",
        "title_en": "Search new appointment",
        "title_de": "Neuen Termin suchen",
        "summary_en": "The customer asks the system to find a new appointment or the next free slot.",
        "summary_de": "Der Kunde bittet das System, einen neuen Termin oder den naechsten freien Slot zu finden.",
        "input_text": "new appointment",
        "expected_action": "appointment.find_next_free_slot_requested",
        "expected_intent": "appointment_next_free_slot",
        "expected_state": "safe",
        "outbound_text_en": "Reply new appointment if you want us to search a fresh slot.",
        "outbound_text_de": "Antworten Sie mit neuer Termin, wenn wir einen frischen Slot suchen sollen.",
        "journey_step_type": "relative_choice",
        "button_group": "relative_choice",
        "button_source": RELATIVE_BUTTONS,
        "next_step_map": {
            "this_week": "date_choice",
            "next_week": "date_choice",
            "this_month": "date_choice",
            "next_month": "date_choice",
            "next_free_slot": "date_choice",
        },
    },
    {
        "id": "this-week",
        "title_en": "This week",
        "title_de": "Diese Woche",
        "summary_en": "The customer wants an appointment window inside the current week.",
        "summary_de": "Der Kunde moechte ein Terminfenster innerhalb der aktuellen Woche.",
        "input_text": "this week",
        "expected_action": "appointment.find_slot_this_week_requested",
        "expected_intent": "appointment_this_week",
        "expected_state": "safe",
        "outbound_text_en": "You can also answer with this week, next week, this month, or next month.",
        "outbound_text_de": "Sie koennen auch mit diese Woche, naechste Woche, dieser Monat oder naechster Monat antworten.",
        "journey_step_type": "relative_choice",
        "button_group": "relative_choice",
        "button_source": RELATIVE_BUTTONS,
        "next_step_map": {
            "this_week": "date_choice",
            "next_week": "date_choice",
            "this_month": "date_choice",
            "next_month": "date_choice",
            "next_free_slot": "date_choice",
        },
    },
    {
        "id": "next-week",
        "title_en": "Next week",
        "title_de": "Naechste Woche",
        "summary_en": "The customer asks for a slot next week.",
        "summary_de": "Der Kunde moechte einen Slot in der naechsten Woche.",
        "input_text": "next week",
        "expected_action": "appointment.find_slot_next_week_requested",
        "expected_intent": "appointment_next_week",
        "expected_state": "safe",
        "outbound_text_en": "Reply next week if the customer wants a slot in the next week window.",
        "outbound_text_de": "Antworten Sie mit naechste Woche, wenn der Kunde einen Slot im naechsten Wochenfenster moechte.",
        "journey_step_type": "relative_choice",
        "button_group": "relative_choice",
        "button_source": RELATIVE_BUTTONS,
        "next_step_map": {
            "this_week": "date_choice",
            "next_week": "date_choice",
            "this_month": "date_choice",
            "next_month": "date_choice",
            "next_free_slot": "date_choice",
        },
    },
    {
        "id": "this-month",
        "title_en": "This month",
        "title_de": "Diesen Monat",
        "summary_en": "The customer wants an appointment window inside the current month.",
        "summary_de": "Der Kunde moechte ein Terminfenster innerhalb des aktuellen Monats.",
        "input_text": "this month",
        "expected_action": "appointment.find_slot_this_month_requested",
        "expected_intent": "appointment_this_month",
        "expected_state": "safe",
        "outbound_text_en": "Reply this month if the customer wants any slot in the current month.",
        "outbound_text_de": "Antworten Sie mit diesen Monat, wenn der Kunde irgendeinen Slot im aktuellen Monat moechte.",
        "journey_step_type": "relative_choice",
        "button_group": "relative_choice",
        "button_source": RELATIVE_BUTTONS,
        "next_step_map": {
            "this_week": "date_choice",
            "next_week": "date_choice",
            "this_month": "date_choice",
            "next_month": "date_choice",
            "next_free_slot": "date_choice",
        },
    },
    {
        "id": "next-month",
        "title_en": "Next month",
        "title_de": "Naechsten Monat",
        "summary_en": "The customer wants an appointment in the next month window.",
        "summary_de": "Der Kunde moechte einen Termin im naechsten Monatsfenster.",
        "input_text": "next month",
        "expected_action": "appointment.find_slot_next_month_requested",
        "expected_intent": "appointment_next_month",
        "expected_state": "safe",
        "outbound_text_en": "Reply next month if the customer wants a wider window next month.",
        "outbound_text_de": "Antworten Sie mit naechsten Monat, wenn der Kunde ein groesseres Fenster im naechsten Monat moechte.",
        "journey_step_type": "relative_choice",
        "button_group": "relative_choice",
        "button_source": RELATIVE_BUTTONS,
        "next_step_map": {
            "this_week": "date_choice",
            "next_week": "date_choice",
            "this_month": "date_choice",
            "next_month": "date_choice",
            "next_free_slot": "date_choice",
        },
    },
    {
        "id": "explicit-date-selection",
        "title_en": "Explicit date selection",
        "title_de": "Explizite Datumsauswahl",
        "summary_en": "The customer chooses one date from proposed options.",
        "summary_de": "Der Kunde waehlt ein Datum aus den vorgeschlagenen Optionen.",
        "input_text": "05 May",
        "expected_action": "appointment.slot_selected",
        "expected_intent": "slot_selection",
        "expected_state": "ambiguous",
        "outbound_text_en": "Please choose one of these dates: 05 May, 07 May, or 09 May.",
        "outbound_text_de": "Bitte waehlen Sie eines dieser Daten: 05. Mai, 07. Mai oder 09. Mai.",
        "journey_step_type": "date_choice",
        "button_group": "date_choice",
        "button_source": DATE_BUTTONS,
        "next_step_map": {
            "date_05_may": "time_choice",
            "date_06_may": "time_choice",
            "date_08_may": "time_choice",
            "date_12_may": "time_choice",
        },
    },
    {
        "id": "explicit-time-selection",
        "title_en": "Explicit time selection",
        "title_de": "Explizite Zeitauswahl",
        "summary_en": "The customer chooses one time from proposed free slots.",
        "summary_de": "Der Kunde waehlt eine Uhrzeit aus vorgeschlagenen freien Slots.",
        "input_text": "16:00",
        "expected_action": "appointment.slot_selected",
        "expected_intent": "slot_selection",
        "expected_state": "ambiguous",
        "outbound_text_en": "Please choose one of these times: 14:00, 16:00, or 17:30.",
        "outbound_text_de": "Bitte waehlen Sie eine dieser Uhrzeiten: 14:00, 16:00 oder 17:30.",
        "journey_step_type": "time_choice",
        "button_group": "time_choice",
        "button_source": TIME_BUTTONS,
        "next_step_map": {
            "time_0900": "slot_selected",
            "time_1130": "slot_selected",
            "time_1600": "slot_selected",
            "time_1830": "slot_selected",
        },
    },
    {
        "id": "combined-date-time-selection",
        "title_en": "Combined date and time",
        "title_de": "Kombiniertes Datum und Uhrzeit",
        "summary_en": "The customer replies with both a date and a time in one message.",
        "summary_de": "Der Kunde antwortet mit Datum und Uhrzeit in einer Nachricht.",
        "input_text": "05 May, 16:00",
        "expected_action": "appointment.slot_selected",
        "expected_intent": "slot_selection",
        "expected_state": "safe",
        "outbound_text_en": "You can reply with a full slot such as 05 May, 16:00.",
        "outbound_text_de": "Sie koennen mit einem kompletten Slot wie 05. Mai, 16:00 antworten.",
        "journey_step_type": "time_choice",
        "button_group": "time_choice",
        "button_source": TIME_BUTTONS,
        "next_step_map": {
            "time_0900": "slot_selected",
            "time_1130": "slot_selected",
            "time_1600": "slot_selected",
            "time_1830": "slot_selected",
        },
    },
]


def scenario_catalog(lang: str = "en") -> list[dict]:
    language = "de" if lang == "de" else "en"
    catalog: list[dict] = []
    for entry in SCENARIO_MATRIX:
        scenario = deepcopy(entry)
        scenario["title"] = entry["title_de"] if language == "de" else entry["title_en"]
        scenario["summary"] = entry["summary_de"] if language == "de" else entry["summary_en"]
        scenario["outbound_text"] = entry["outbound_text_de"] if language == "de" else entry["outbound_text_en"]
        scenario["available_actions"] = [item["value"] for item in entry.get("button_source", [])]
        scenario["suggestion_buttons"] = _localized_buttons(entry.get("button_source", []), language)
        scenario["real_channel_payload"] = _localized_payload(
            language,
            entry["outbound_text_en"],
            entry["outbound_text_de"],
            entry.get("button_source", []),
            entry.get("next_step_map", {}),
        )
        catalog.append(scenario)
    return catalog


def build_phase5_scenarios(lang: str = "en") -> list[dict]:
    language = "de" if lang == "de" else "en"
    scenarios: list[dict] = []
    for scenario in scenario_catalog(language):
        reply_label = "Customer reply" if language == "en" else "Kundenantwort"
        action_label = "Interpreted action" if language == "en" else "Interpretierte Aktion"
        scenario_summary = (
            f"The expected action is {scenario['expected_action']} and the expected interpretation state is {scenario['expected_state']}."
            if language == "en"
            else f"Die erwartete Aktion ist {scenario['expected_action']} und der erwartete Interpretationsstatus ist {scenario['expected_state']}."
        )
        scenarios.append(
            {
                "id": scenario["id"],
                "title": scenario["title"],
                "summary": scenario["summary"],
                "presenter_intro": scenario["summary"],
                "simple_explanation": scenario["summary"],
                "technical_explanation": scenario_summary,
                "starting_mode": "combined",
                "phase5_matrix": {
                    "input": scenario["input_text"],
                    "expected_action": scenario["expected_action"],
                    "expected_intent": scenario["expected_intent"],
                    "expected_state": scenario["expected_state"],
                },
                "steps": [
                    {
                        "label": "Outbound reminder" if language == "en" else "Ausgehender Reminder",
                        "journey_state": "REMINDER_PENDING",
                        "customer_message": "",
                        "platform_message": scenario["outbound_text"],
                        "speaker_notes": scenario["summary"],
                        "communication_message": {
                            "text": scenario["outbound_text"],
                            "actions": deepcopy(scenario["suggestion_buttons"]),
                            "slot_options": [],
                            "calendar_provider": "google",
                            "journey_step_type": scenario.get("journey_step_type"),
                            "available_actions": deepcopy(scenario.get("available_actions", [])),
                            "suggestion_buttons": deepcopy(scenario.get("suggestion_buttons", [])),
                            "next_step_map": deepcopy(scenario.get("next_step_map", {})),
                            "real_channel_payload": deepcopy(scenario.get("real_channel_payload", {})),
                        },
                        "trace_id": f"trace-{scenario['id']}",
                        "correlation_id": f"corr-{scenario['id']}",
                        "journey_id": f"journey-{scenario['id']}",
                        "booking_reference": "booking-gdemo-dentist-001",
                    },
                    {
                        "label": reply_label,
                        "journey_state": "REPLY_RECEIVED",
                        "customer_message": scenario["input_text"],
                        "platform_message": "",
                        "speaker_notes": scenario["summary"],
                        "communication_message": {
                            "text": scenario["outbound_text"],
                            "actions": [],
                            "slot_options": [],
                            "calendar_provider": "google",
                            "journey_step_type": scenario.get("journey_step_type"),
                            "selected_button": scenario["input_text"],
                        },
                        "trace_id": f"trace-{scenario['id']}",
                        "correlation_id": f"corr-{scenario['id']}",
                        "journey_id": f"journey-{scenario['id']}",
                        "booking_reference": "booking-gdemo-dentist-001",
                    },
                    {
                        "label": action_label,
                        "journey_state": "ACTION_PREPARED",
                        "customer_message": "",
                        "platform_message": scenario_summary,
                        "speaker_notes": scenario_summary,
                        "communication_message": {
                            "text": scenario_summary,
                            "actions": [],
                            "slot_options": [],
                            "calendar_provider": "google",
                            "selected_button": scenario["input_text"],
                        },
                        "trace_id": f"trace-{scenario['id']}",
                        "correlation_id": f"corr-{scenario['id']}",
                        "journey_id": f"journey-{scenario['id']}",
                        "booking_reference": "booking-gdemo-dentist-001",
                    },
                ],
            }
        )
    return scenarios
