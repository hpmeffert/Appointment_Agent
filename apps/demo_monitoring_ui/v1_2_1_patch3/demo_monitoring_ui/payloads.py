from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_2_1.demo_monitoring_ui.payloads import build_v121_payload


def build_v121_patch3_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_v121_payload(lang=lang))
    payload["version"] = "v1.2.1-patch3"
    payload["ui_meta"]["tagline"] = (
        "Messaging cockpit with clearer platform storytelling, stronger demo guidance, and onboarding-friendly documentation."
        if lang == "en"
        else "Messaging-Cockpit mit klarerer Plattform-Erzaehlung, staerkerer Demo-Fuehrung und onboarding-freundlicher Dokumentation."
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
    payload["platform_overview"] = {
        "title": "How the Platform Works" if lang == "en" else "So funktioniert die Plattform",
        "subtitle": (
            "One platform combines channels, adapters, orchestration, and monitoring."
            if lang == "en"
            else "Eine Plattform verbindet Kanaele, Adapter, Orchestrierung und Monitoring."
        ),
        "items": [
            {
                "title": "Channels" if lang == "en" else "Kanaele",
                "body": (
                    "RCS, SMS, chat, and later voice are customer-facing entry points."
                    if lang == "en"
                    else "RCS, SMS, Chat und spaeter Voice sind die kundennahe Einstiegsschicht."
                ),
            },
            {
                "title": "Messaging Adapter" if lang == "en" else "Messaging-Adapter",
                "body": (
                    "LEKAB normalizes outbound and inbound traffic into one internal model."
                    if lang == "en"
                    else "LEKAB normalisiert ausgehenden und eingehenden Verkehr in ein gemeinsames internes Modell."
                ),
            },
            {
                "title": "Service Bus" if lang == "en" else "Service Bus",
                "body": (
                    "The service bus keeps modules loosely coupled so providers can change without redesigning the cockpit."
                    if lang == "en"
                    else "Der Service Bus haelt Module lose gekoppelt, damit Provider gewechselt werden koennen, ohne das Cockpit neu zu bauen."
                ),
            },
            {
                "title": "Scheduling Adapter" if lang == "en" else "Scheduling-Adapter",
                "body": (
                    "Google handles live slots, slot hold, booking, and conflict checks in the current demo."
                    if lang == "en"
                    else "Google uebernimmt in der aktuellen Demo Live-Slots, Slot Hold, Booking und Konfliktpruefung."
                ),
            },
        ],
    }
    payload["demo_storyboard"] = {
        "title": "Demo Storyboard" if lang == "en" else "Demo-Storyboard",
        "subtitle": (
            "A presenter-friendly map of the five main demo stories and their wow moments."
            if lang == "en"
            else "Eine presenter-freundliche Karte der fuenf wichtigsten Demo-Stories und ihrer Wow-Momente."
        ),
        "stories": [
            {
                "title": "Booking" if lang == "en" else "Buchung",
                "business_value": (
                    "Fast first-time appointment creation."
                    if lang == "en"
                    else "Schnelle Erstbuchung eines Termins."
                ),
                "wow_effect": (
                    "A click on the slot button triggers real hold and booking logic."
                    if lang == "en"
                    else "Ein Klick auf den Slot-Button startet echte Hold- und Booking-Logik."
                ),
            },
            {
                "title": "Rescheduling" if lang == "en" else "Verschiebung",
                "business_value": (
                    "Existing appointments can be changed without starting from zero."
                    if lang == "en"
                    else "Bestehende Termine koennen geaendert werden, ohne bei null zu starten."
                ),
                "wow_effect": (
                    "The platform keeps the same cockpit and still reloads live availability."
                    if lang == "en"
                    else "Die Plattform behaelt dasselbe Cockpit und laedt trotzdem live neue Verfuegbarkeit."
                ),
            },
            {
                "title": "Cancellation" if lang == "en" else "Storno",
                "business_value": (
                    "The business sees both customer intent and resulting system state."
                    if lang == "en"
                    else "Das Unternehmen sieht sowohl die Kundenabsicht als auch den resultierenden Systemstatus."
                ),
                "wow_effect": (
                    "Communication and technical state stay aligned in one shell."
                    if lang == "en"
                    else "Kommunikation und technischer Zustand bleiben in einer gemeinsamen Shell synchron."
                ),
            },
            {
                "title": "Callback" if lang == "en" else "Rueckruf",
                "business_value": (
                    "Automation can hand over cleanly when humans need to step in."
                    if lang == "en"
                    else "Automation kann sauber uebergeben, wenn Menschen uebernehmen muessen."
                ),
                "wow_effect": (
                    "The journey changes from automated to assisted without losing context."
                    if lang == "en"
                    else "Die Journey wechselt von automatisiert zu begleitet, ohne Kontext zu verlieren."
                ),
            },
            {
                "title": "Slot Hold" if lang == "en" else "Slot Hold",
                "business_value": (
                    "Protects scarce appointment capacity against parallel booking races."
                    if lang == "en"
                    else "Schuetzt knappe Termin-Kapazitaet vor parallelen Buchungsrennen."
                ),
                "wow_effect": (
                    "The system does not just show choices. It protects them."
                    if lang == "en"
                    else "Das System zeigt Auswahl nicht nur an. Es schuetzt sie auch."
                ),
            },
        ],
    }
    payload["business_value_points"] = [
        (
            "One cockpit for communication, scheduling, settings, and monitoring."
            if lang == "en"
            else "Ein Cockpit fuer Kommunikation, Scheduling, Settings und Monitoring."
        ),
        (
            "One architecture that can grow with more adapters and channels."
            if lang == "en"
            else "Eine Architektur, die mit weiteren Adaptern und Kanaelen wachsen kann."
        ),
        (
            "Safer than a plain demo because slot hold and conflict checks are built in."
            if lang == "en"
            else "Sicherer als eine reine Demo, weil Slot Hold und Konfliktpruefung eingebaut sind."
        ),
    ]
    return payload
