from __future__ import annotations

from copy import deepcopy

from appointment_agent_shared.config import settings
from demo_monitoring_ui.v1_0_0.demo_monitoring_ui.scenarios import build_simulation_payload


def _localize(lang: str, en: str, de: str) -> str:
    return de if lang == "de" else en


def _settings_snapshot(lang: str) -> list[dict[str, str]]:
    return [
        {"label": _localize(lang, "Booking window days", "Buchungsfenster Tage"), "value": str(settings.booking_window_days)},
        {"label": _localize(lang, "Max slots per offer", "Max Slots pro Angebot"), "value": str(settings.max_slots_per_offer)},
        {"label": _localize(lang, "Default duration", "Standarddauer"), "value": f"{settings.default_duration_minutes} min"},
        {"label": _localize(lang, "Slot hold minutes", "Slot Hold Minuten"), "value": str(settings.slot_hold_minutes)},
        {"label": _localize(lang, "Quiet hours", "Ruhezeiten"), "value": settings.quiet_hours},
        {"label": _localize(lang, "Reschedule cutoff", "Umbuchungsgrenze"), "value": f"{settings.reschedule_cutoff_hours} h"},
        {"label": _localize(lang, "Google mode", "Google Modus"), "value": "Simulation" if settings.google_mock_mode else "Test-ready"},
        {"label": _localize(lang, "LEKAB mock mode", "LEKAB Mock Modus"), "value": str(settings.lekab_mock_mode).lower()},
        {"label": _localize(lang, "Demo base path", "Demo Basis-Pfad"), "value": settings.demo_base_path},
    ]


def _help_links(lang: str) -> list[dict[str, str]]:
    return [
        {"id": "demo", "label": _localize(lang, "Demo Guide", "Demo Leitfaden"), "href": f"/docs/demo?lang={lang}"},
        {"id": "user", "label": _localize(lang, "User Guide", "Benutzerleitfaden"), "href": f"/docs/user?lang={lang}"},
        {"id": "admin", "label": _localize(lang, "Admin Guide", "Admin Leitfaden"), "href": f"/docs/admin?lang={lang}"},
    ]


def _vertical_profiles(lang: str) -> list[dict[str, object]]:
    return [
        {
            "id": "dentist",
            "label": _localize(lang, "Dentist", "Zahnarzt"),
            "description": _localize(lang, "Dental appointments and follow-ups", "Zahnarzttermine und Nachkontrollen"),
            "audience_fit": _localize(lang, "Best for healthcare and appointment-office demos", "Am besten fuer Healthcare- und Praxis-Demos"),
            "operator_explanation": _localize(
                lang,
                "This vertical feels personal and everyday. It is easy for almost every audience to understand.",
                "Dieses Vertical wirkt persoenlich und alltagsnah. Fast jedes Publikum versteht es sofort.",
            ),
            "customer_examples": ["Anna Becker", "Julia Hoffmann", "Markus Weber"],
            "sample_titles": [
                "Dental Check-up - Dr. Zahn",
                "Tooth Cleaning - Dr. Zahn",
                "Follow-up Appointment - Dr. Zahn",
            ],
            "sample_description": _localize(
                lang,
                "Routine dental check-up for an existing patient.",
                "Routinekontrolle fuer einen bestehenden Patienten.",
            ),
            "reminder_example": _localize(
                lang,
                "Reminder: You have a dental check-up tomorrow at 10:00 with Dr. Zahn.",
                "Erinnerung: Sie haben morgen um 10:00 eine Zahnkontrolle bei Dr. Zahn.",
            ),
            "follow_up_prompt": _localize(
                lang,
                "Would you like to keep, reschedule, or cancel your appointment?",
                "Moechten Sie Ihren Termin behalten, verschieben oder absagen?",
            ),
            "monitoring_labels": [
                "dentist.checkup.search.requested",
                "dentist.appointment.confirmed",
                "dentist.reminder.sent",
            ],
        },
        {
            "id": "wallbox",
            "label": _localize(lang, "Stadtwerke Wallbox", "Stadtwerke Wallbox"),
            "description": _localize(lang, "Inspection and technician home visits", "Pruefung und Technikereinsaetze beim Kunden"),
            "audience_fit": _localize(lang, "Best for utilities and field-service demos", "Am besten fuer Utilities und Field-Service-Demos"),
            "operator_explanation": _localize(
                lang,
                "This vertical works well for municipal utility demos because it combines scheduling with technician visits.",
                "Dieses Vertical passt gut fuer kommunale Utility-Demos, weil es Terminlogik mit Technikereinsaetzen verbindet.",
            ),
            "customer_examples": ["Familie Schneider", "Julia Hoffmann", "Markus Weber"],
            "sample_titles": [
                "Wallbox Inspection - Home Visit",
                "EV Charger Safety Check",
                "Wallbox Commissioning Review",
            ],
            "sample_description": _localize(
                lang,
                "Utility technician visit for a residential wallbox inspection.",
                "Technikertermin der Stadtwerke fuer eine Wallbox-Pruefung beim Kunden.",
            ),
            "reminder_example": _localize(
                lang,
                "Reminder: Your wallbox inspection is scheduled for tomorrow at 14:00.",
                "Erinnerung: Ihre Wallbox-Pruefung ist fuer morgen um 14:00 geplant.",
            ),
            "follow_up_prompt": _localize(
                lang,
                "Would you like to keep, reschedule, cancel, or request a call?",
                "Moechten Sie den Termin behalten, verschieben, absagen oder einen Rueckruf anfordern?",
            ),
            "monitoring_labels": [
                "wallbox.inspection.search.requested",
                "utility.technician.appointment.confirmed",
                "wallbox.reminder.sent",
            ],
        },
        {
            "id": "district_heating",
            "label": _localize(lang, "District Heating", "Nahwaerme"),
            "description": _localize(lang, "Transfer station checks and service visits", "Uebergabestationen und Serviceeinsaetze"),
            "audience_fit": _localize(lang, "Best for infrastructure and municipal utility demos", "Am besten fuer Infrastruktur- und kommunale Utility-Demos"),
            "operator_explanation": _localize(
                lang,
                "This vertical feels more technical and is useful when the audience expects infrastructure or municipal service language.",
                "Dieses Vertical wirkt technischer und ist gut, wenn das Publikum Infrastruktur- oder Stadtwerke-Sprache erwartet.",
            ),
            "customer_examples": ["Familie Schneider", "Hausverwaltung Nordblick", "Anna Becker"],
            "sample_titles": [
                "District Heating Transfer Station Inspection",
                "Nahwaerme Uebergabestation Check",
                "Heat Transfer Unit Service Visit",
            ],
            "sample_description": _localize(
                lang,
                "Inspection appointment for the district heating transfer station in the utility room.",
                "Prueftermin fuer die Nahwaerme-Uebergabestation im Technikraum.",
            ),
            "reminder_example": _localize(
                lang,
                "Reminder: Your district heating transfer station inspection is scheduled for tomorrow at 09:00.",
                "Erinnerung: Ihre Pruefung der Nahwaerme-Uebergabestation ist fuer morgen um 09:00 geplant.",
            ),
            "follow_up_prompt": _localize(
                lang,
                "Would you like to confirm, move, cancel, or speak to an agent?",
                "Moechten Sie bestaetigen, verschieben, absagen oder mit einem Mitarbeiter sprechen?",
            ),
            "monitoring_labels": [
                "district_heating.inspection.search.requested",
                "heat_transfer.appointment.confirmed",
                "district_heating.reminder.sent",
            ],
        },
    ]


def build_cockpit_payload(version: str, lang: str = "en", include_verticals: bool = False) -> dict:
    base_payload = build_simulation_payload(lang=lang)
    payload = deepcopy(base_payload)
    payload["version"] = version
    payload["pages"] = [
        {"id": "dashboard", "label": _localize(lang, "Dashboard", "Dashboard")},
        {"id": "monitoring", "label": _localize(lang, "Monitoring", "Monitoring")},
        {"id": "settings", "label": _localize(lang, "Settings", "Einstellungen")},
        {"id": "help", "label": _localize(lang, "Help", "Hilfe")},
    ]
    payload["dashboard_modes"] = [
        {"id": "demo", "label": _localize(lang, "Demo", "Demo")},
        {"id": "monitoring", "label": _localize(lang, "Monitoring", "Monitoring")},
        {"id": "combined", "label": _localize(lang, "Combined", "Kombiniert")},
    ]
    payload["settings_snapshot"] = _settings_snapshot(lang)
    payload["help_links"] = _help_links(lang)
    payload["ui_meta"] = {
        "product_name": _localize(lang, "Appointment Agent Cockpit", "Appointment Agent Cockpit"),
        "tagline": _localize(
            lang,
            "Incident-style demo cockpit for appointments, monitoring, and operator setup.",
            "Incident-aehnliches Demo-Cockpit fuer Termine, Monitoring und Operator-Setup.",
        ),
        "theme_default": "day",
    }
    if include_verticals:
        payload["verticals"] = _vertical_profiles(lang)
    return payload
