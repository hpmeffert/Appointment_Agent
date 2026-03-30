from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_1_0_patch7.demo_monitoring_ui.payloads import build_patch7_payload


def build_patch8_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_patch7_payload(lang=lang))
    payload["version"] = "v1.1.0-patch8"
    payload["ui_meta"]["tagline"] = (
        "Incident-style cockpit shell with interactive communication and Google live slot handling."
        if lang == "en"
        else "Incident-artige Cockpit-Shell mit interaktiver Kommunikation und Google Live-Slot-Handling."
    )
    payload["communication_model"]["booking_backend"] = "google_adapter_v1.1.0_patch8"
    return payload
