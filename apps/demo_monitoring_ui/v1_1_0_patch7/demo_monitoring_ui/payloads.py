from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import re

from demo_monitoring_ui.v1_1_0_patch6.demo_monitoring_ui.payloads import build_patch6_payload


ACTION_ALIASES = {
    "keep": {"keep", "keep_appointment", "termin_behalten", "behalten"},
    "reschedule": {"reschedule", "verschieben", "verschiebung"},
    "cancel": {"cancel", "absagen", "absage"},
    "call_me": {"call_me", "callme", "ruf_mich_an", "ruckruf", "rueckruf", "zuruckrufen_lassen", "zurueckrufen_lassen"},
    "confirm": {"confirm", "bestaetigen", "bestatigen"},
}


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _normalize(value: str) -> str:
    normalized = (
        value.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("-", " ")
    )
    return _slugify(normalized)


def _canonical_action_value(label: str) -> str | None:
    normalized = _normalize(label)
    for action_value, aliases in ACTION_ALIASES.items():
        if normalized in aliases:
            return action_value
    return None


def _looks_like_slot(label: str) -> bool:
    return any(token in label for token in (":", "Tomorrow", "Friday", "Monday", "Tuesday", "Wednesday", "Thursday", "Tue", "Wed", "Thu", "Mon", "Morgen", "Freitag", "Montag", "Dienstag", "Mittwoch", "Donnerstag"))


def _build_structured_message(step: dict, index: int) -> dict:
    # This normalized message shape keeps the UI provider-neutral and close to
    # how LEKAB/RCS/SMS style reply buttons could be represented later.
    message = {
        "text": step.get("platform_message") or "",
        "channel": step.get("message_channel") or "RCS",
        "message_id": step.get("message_id"),
        "lekab_job_id": step.get("lekab_job_id"),
        "calendar_provider": step.get("calendar_provider") or "simulated",
        "actions": [],
        "slot_options": [],
    }
    for option_index, label in enumerate(step.get("slot_options") or [], start=1):
        action_value = _canonical_action_value(str(label))
        if action_value is not None:
            message["actions"].append(
                {
                    "type": "reply",
                    "label": label,
                    "value": action_value,
                }
            )
            continue
        if _looks_like_slot(str(label)):
            message["slot_options"].append(
                {
                    "slot_id": f"{step.get('journey_id', 'journey')}-step-{index}-slot-{option_index}",
                    "label": label,
                    "start": None,
                    "end": None,
                    "duration_minutes": step.get("duration_minutes"),
                    "calendar_provider": step.get("calendar_provider") or "simulated",
                }
            )
            continue
        message["actions"].append(
            {
                "type": "reply",
                "label": label,
                "value": _slugify(str(label)),
            }
        )
    return message


def build_patch7_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_patch6_payload(lang=lang))
    payload["version"] = "v1.1.0-patch7"
    payload["ui_meta"]["tagline"] = (
        "Incident-style cockpit shell with interactive communication buttons and slot selection."
        if lang == "en"
        else "Incident-artige Cockpit-Shell mit interaktiven Kommunikationsbuttons und Slot-Auswahl."
    )
    payload["communication_model"] = {
        "provider_neutral": True,
        "reply_action_types": ["keep", "reschedule", "cancel", "call_me", "confirm"],
        "calendar_provider_values": ["simulated", "google", "microsoft"],
        "demo_purpose": (
            "Structured message envelopes prepare the demo for future LEKAB and RCS reply actions."
            if lang == "en"
            else "Strukturierte Nachrichtenhuellen bereiten die Demo fuer spaetere LEKAB- und RCS-Antwortaktionen vor."
        ),
    }
    for scenario in payload["scenarios"]:
        for index, step in enumerate(scenario.get("steps", []), start=1):
            step["calendar_provider"] = step.get("calendar_provider") or "simulated"
            step["communication_message"] = _build_structured_message(step, index)
    payload["google_demo_control"]["default_from_date"] = date.today().isoformat()
    payload["google_demo_control"]["default_to_date"] = (date.today() + timedelta(days=6)).isoformat()
    return payload
