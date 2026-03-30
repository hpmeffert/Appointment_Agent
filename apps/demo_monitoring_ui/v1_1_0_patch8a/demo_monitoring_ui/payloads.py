from __future__ import annotations

from copy import deepcopy

from appointment_agent_shared.config import settings
from demo_monitoring_ui.v1_1_0_patch8.demo_monitoring_ui.payloads import build_patch8_payload


def build_patch8a_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_patch8_payload(lang=lang))
    payload["version"] = "v1.1.0-patch8a"
    payload["ui_meta"]["tagline"] = (
        "Incident-style cockpit shell with slot holds, parallel booking protection, and Google live revalidation."
        if lang == "en"
        else "Incident-artige Cockpit-Shell mit Slot-Holds, Parallel-Schutz und Google-Live-Revalidierung."
    )
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
