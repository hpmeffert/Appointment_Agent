from __future__ import annotations

from copy import deepcopy

from appointment_agent_shared.config import settings
from demo_monitoring_ui.v1_1_0_patch8a.demo_monitoring_ui.payloads import build_patch8a_payload


def build_patch8b_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_patch8a_payload(lang=lang))
    payload["version"] = "v1.1.0-patch8b"
    payload["ui_meta"]["tagline"] = (
        "Incident-style cockpit shell with connected reply actions, live slot booking, and slot hold protection."
        if lang == "en"
        else "Incident-artige Cockpit-Shell mit verbundenen Antwortaktionen, Live-Slot-Buchung und Slot-Hold-Schutz."
    )
    payload["communication_model"]["booking_backend"] = "google_adapter_v1.1.0_patch8b"
    payload["hold_settings"] = {
        "slot_hold_minutes": settings.slot_hold_minutes,
        "default_for_demo": 2,
        "recommended_values": [2, 5, 10],
        "explanation": (
            "This is the temporary reservation time. When a user picks a slot, the platform keeps it blocked for this many minutes."
            if lang == "en"
            else "Das ist die Zeit fuer die temporaere Reservierung. Wenn ein Nutzer einen Slot waehlt, blockiert die Plattform ihn fuer diese Anzahl Minuten."
        ),
    }
    payload["interactive_demo_flow"] = {
        "booking_confirmation_actions": [
            {"type": "reply", "label": "Confirm" if lang == "en" else "Bestaetigen", "value": "confirm"},
            {"type": "reply", "label": "Reschedule" if lang == "en" else "Verschieben", "value": "reschedule"},
            {"type": "reply", "label": "Cancel" if lang == "en" else "Absagen", "value": "cancel"},
            {"type": "reply", "label": "Call Me" if lang == "en" else "Zurueckrufen", "value": "call_me"},
        ],
        "slot_lookup_message": "Here are the next available appointment times."
        if lang == "en"
        else "Hier sind die naechsten verfuegbaren Terminvorschlaege.",
        "hold_message_template": "This slot is reserved for you for {minutes} minutes. Please confirm before the hold expires."
        if lang == "en"
        else "Dieser Slot ist fuer {minutes} Minuten fuer dich reserviert. Bitte bestaetige vor Ablauf des Holds.",
        "conflict_message": "This slot is no longer available. Here are the next available times."
        if lang == "en"
        else "Dieser Slot ist nicht mehr verfuegbar. Hier sind die naechsten freien Zeiten.",
    }
    payload["settings_snapshot"] = [
        *payload["settings_snapshot"],
        {
            "label": "Slot Hold Behavior" if lang == "en" else "Slot Hold Verhalten",
            "value": "Temporary reservation in platform state before final Google booking."
            if lang == "en"
            else "Temporäre Reservierung im Plattform-Status vor der finalen Google-Buchung.",
        },
    ]
    return payload
