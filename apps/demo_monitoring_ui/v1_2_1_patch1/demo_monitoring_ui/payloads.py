from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_2_1.demo_monitoring_ui.payloads import build_v121_payload


def build_v121_patch1_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_v121_payload(lang=lang))
    payload["version"] = "v1.2.1-patch1"
    payload["ui_meta"]["tagline"] = (
        "Messaging cockpit with dedicated RCS settings, message monitor, and incident-style reporting."
        if lang == "en"
        else "Messaging-Cockpit mit eigener RCS-Einstellungsseite, Message Monitor und incident-artigem Reporting."
    )
    payload["pages"] = [
        {"id": "dashboard", "label": "Dashboard" if lang == "en" else "Dashboard"},
        {"id": "message-monitor", "label": "Message Monitor" if lang == "en" else "Message Monitor"},
        {"id": "communications-reports", "label": "Reports" if lang == "en" else "Berichte"},
        {"id": "monitoring", "label": "Monitoring" if lang == "en" else "Monitoring"},
        {"id": "settings-general", "label": "Settings" if lang == "en" else "Einstellungen"},
        {"id": "settings-rcs", "label": "Settings -> RCS" if lang == "en" else "Einstellungen -> RCS"},
        {"id": "google-demo-control", "label": "Google Demo Control" if lang == "en" else "Google Demo Control"},
        {"id": "help", "label": "Help" if lang == "en" else "Hilfe"},
    ]
    payload["settings_navigation"] = {
        "items": [
            {"id": "settings-general", "label": "General" if lang == "en" else "Allgemein"},
            {"id": "settings-rcs", "label": "RCS" if lang == "en" else "RCS"},
        ]
    }
    payload["rcs_settings"] = {
        "title": "RCS Settings" if lang == "en" else "RCS Einstellungen",
        "subtitle": (
            "Operator-facing LEKAB RCS/SMS configuration with save, reload, and readiness validation."
            if lang == "en"
            else "Operator-orientierte LEKAB RCS/SMS Konfiguration mit Speichern, Neuladen und Readiness-Pruefung."
        ),
    }
    return payload
