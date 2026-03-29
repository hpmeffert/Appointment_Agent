from __future__ import annotations

from datetime import date, timedelta

from demo_monitoring_ui.v1_0_5.demo_monitoring_ui.payloads import build_cockpit_payload


def _localize(lang: str, en: str, de: str) -> str:
    return de if lang == "de" else en


def build_patch6_payload(lang: str = "en") -> dict:
    payload = build_cockpit_payload(version="v1.1.0-patch6", lang=lang, include_verticals=True)
    payload["pages"] = [
        {"id": "dashboard", "label": _localize(lang, "Dashboard", "Dashboard")},
        {"id": "monitoring", "label": _localize(lang, "Monitoring", "Monitoring")},
        {"id": "settings", "label": _localize(lang, "Settings", "Einstellungen")},
        {"id": "google-demo-control", "label": _localize(lang, "Google Demo Control", "Google Demo Control")},
        {"id": "help", "label": _localize(lang, "Help", "Hilfe")},
    ]
    payload["ui_meta"]["tagline"] = _localize(
        lang,
        "Incident-style cockpit shell with Google Demo Control date range and appointment type selection.",
        "Incident-artige Cockpit-Shell mit Datumsbereich und Termin-Typ in Google Demo Control.",
    )
    payload["google_demo_control"] = {
        "title": _localize(lang, "Google Demo Control", "Google Demo Control"),
        "subtitle": _localize(
            lang,
            "This is the safe operator workspace for simulated or real test-calendar preparation.",
            "Das ist der sichere Operator-Arbeitsbereich fuer simulierte oder echte Testkalender-Vorbereitung.",
        ),
        "warning_simulation": _localize(
            lang,
            "Simulation does not write to Google Calendar.",
            "Simulation schreibt nicht in den Google Kalender.",
        ),
        "warning_test": _localize(
            lang,
            "Test writes to the real configured Google test calendar.",
            "Test schreibt in den real konfigurierten Google Testkalender.",
        ),
        "default_from_date": date.today().isoformat(),
        "default_to_date": (date.today() + timedelta(days=6)).isoformat(),
        "appointment_types": [
            {
                "id": "dentist",
                "label": _localize(lang, "Dentist Appointment", "Zahnarzttermin"),
            },
            {
                "id": "wallbox",
                "label": _localize(lang, "Electricity - Wallbox Check", "Elektrizitaetswerk - Wallbox Kontrolle"),
            },
            {
                "id": "gas_meter",
                "label": _localize(lang, "Gas - Meter Check", "Stadtwerke Gas - Gaszaehler Kontrolle"),
            },
            {
                "id": "water_meter",
                "label": _localize(lang, "Water - Meter Reading", "Wasserwerke - Zaehler ablesen"),
            },
        ],
    }
    return payload
