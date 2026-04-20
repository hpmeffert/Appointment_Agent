from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_2_1.demo_monitoring_ui.payloads import build_v121_payload


def build_v121_patch2_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_v121_payload(lang=lang))
    payload["version"] = "v1.2.1-patch2"
    payload["ui_meta"]["tagline"] = (
        "Messaging cockpit with dedicated RCS settings, clearer day-mode controls, and onboarding-friendly documentation."
        if lang == "en"
        else "Messaging-Cockpit mit eigener RCS-Einstellungsseite, klareren Day-Mode-Buttons und onboarding-freundlicher Dokumentation."
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
            "Operator-facing LEKAB RCS/SMS configuration with save, reload, readiness validation, and clearer helper text."
            if lang == "en"
            else "Operator-orientierte LEKAB RCS/SMS Konfiguration mit Speichern, Neuladen, Readiness-Pruefung und klareren Hilfetexten."
        ),
    }
    payload["documentation_highlights"] = [
        (
            "Five complete demo stories explain booking, rescheduling, cancellation, callback, and slot hold."
            if lang == "en"
            else "Fuenf komplette Demo-Stories erklaeren Buchung, Verschiebung, Storno, Rueckruf und Slot Hold."
        ),
        (
            "Platform explanation now shows adapters, channels, and the service bus in one onboarding view."
            if lang == "en"
            else "Die Plattform-Erklaerung zeigt jetzt Adapter, Kanaele und den Service Bus in einer gemeinsamen Onboarding-Sicht."
        ),
        (
            "Buttons in day mode now use a stronger visual treatment so operators can spot actions faster."
            if lang == "en"
            else "Buttons im Day Mode haben jetzt ein staerkeres visuelles Design, damit Operatoren Aktionen schneller erkennen."
        ),
    ]
    return payload
