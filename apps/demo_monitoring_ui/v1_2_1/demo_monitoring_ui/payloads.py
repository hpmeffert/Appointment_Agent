from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_2_0.demo_monitoring_ui.payloads import build_v120_payload


def build_v121_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_v120_payload(lang=lang))
    payload["version"] = "v1.2.1"
    payload["ui_meta"]["tagline"] = (
        "Messaging conversation platform demonstrator with appointment flow, message monitor, and incident-style reporting."
        if lang == "en"
        else "Messaging-Conversation-Plattform-Demonstrator mit Terminfluss, Message Monitor und incident-artigem Reporting."
    )
    payload["pages"] = [
        {"id": "dashboard", "label": "Dashboard" if lang == "en" else "Dashboard"},
        {"id": "message-monitor", "label": "Message Monitor" if lang == "en" else "Message Monitor"},
        {"id": "communications-reports", "label": "Reports" if lang == "en" else "Berichte"},
        {"id": "monitoring", "label": "Monitoring" if lang == "en" else "Monitoring"},
        {"id": "settings", "label": "Settings" if lang == "en" else "Einstellungen"},
        {"id": "google-demo-control", "label": "Google Demo Control" if lang == "en" else "Google Demo Control"},
        {"id": "help", "label": "Help" if lang == "en" else "Hilfe"},
    ]
    payload["communication_model"]["booking_backend"] = "google_adapter_v1_2_0"
    payload["communication_model"]["messaging_backend"] = "lekab_adapter_v1_2_1"
    payload["message_monitor"] = {
        "title": "Message Monitor" if lang == "en" else "Message Monitor",
        "subtitle": (
            "Incoming and outgoing message traffic in one operator view."
            if lang == "en"
            else "Eingehender und ausgehender Nachrichtenverkehr in einer Operator-Ansicht."
        ),
    }
    payload["communications_reports"] = {
        "title": "Communications Reports" if lang == "en" else "Kommunikationsberichte",
        "subtitle": (
            "Customer-style and admin-style report cards for messaging traffic."
            if lang == "en"
            else "Kundenartige und adminartige Berichtskarten fuer den Nachrichtenverkehr."
        ),
    }
    payload["settings_snapshot"] = [
        *payload["settings_snapshot"],
        {
            "label": "Messaging Adapter" if lang == "en" else "Messaging Adapter",
            "value": (
                "LEKAB v1.2.1 normalizes RCS, SMS, inbound, and status traffic into one internal model."
                if lang == "en"
                else "LEKAB v1.2.1 normalisiert RCS-, SMS-, Inbound- und Statusverkehr in ein gemeinsames internes Modell."
            ),
        },
    ]
    return payload
