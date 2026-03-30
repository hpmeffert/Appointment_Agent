from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_1_0_patch8b.demo_monitoring_ui.payloads import build_patch8b_payload


def build_v120_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_patch8b_payload(lang=lang))
    payload["version"] = "v1.2.0"
    payload["ui_meta"]["tagline"] = (
        "Integrated appointment demonstrator with interactive booking, slot hold protection, and live conflict handling."
        if lang == "en"
        else "Integrierter Termin-Demonstrator mit interaktiver Buchung, Slot-Hold-Schutz und Live-Konfliktbehandlung."
    )
    payload["communication_model"]["booking_backend"] = "google_adapter_v1_2_0"
    return payload
