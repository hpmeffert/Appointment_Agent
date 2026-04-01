from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_2_1.demo_monitoring_ui.payloads import build_v121_payload


def build_v121_patch4_payload(lang: str = "en") -> dict:
    payload = deepcopy(build_v121_payload(lang=lang))
    payload["version"] = "v1.2.1-patch4"
    payload["ui_meta"]["tagline"] = (
        "Messaging-first guided demo cockpit with stronger storytelling, platform visibility, and wow-demo flow."
        if lang == "en"
        else "Messaging-first Demo-Cockpit mit staerkerer Story-Fuehrung, Plattform-Sichtbarkeit und Wow-Demo-Ablauf."
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
            "One platform combines channels, adapters, orchestration, AI support, and monitoring."
            if lang == "en"
            else "Eine Plattform verbindet Kanaele, Adapter, Orchestrierung, AI-Unterstuetzung und Monitoring."
        ),
        "items": [
            {
                "title": "Channels" if lang == "en" else "Kanaele",
                "body": (
                    "RCS, SMS, WhatsApp (planned), chat, and later voice are customer-facing entry points."
                    if lang == "en"
                    else "RCS, SMS, WhatsApp (geplant), Chat und spaeter Voice sind die kundennahe Einstiegsschicht."
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
                "title": "Integrations" if lang == "en" else "Integrationen",
                "body": (
                    "Google is active today, while Microsoft and CRM integrations stay visible as the next extensibility path."
                    if lang == "en"
                    else "Google ist heute aktiv, waehrend Microsoft- und CRM-Integrationen als naechster Erweiterungspfad sichtbar bleiben."
                ),
            },
            {
                "title": "AI Layer" if lang == "en" else "AI-Schicht",
                "body": (
                    "The agent layer can later combine orchestration with RAG-based business context."
                    if lang == "en"
                    else "Die Agent-Schicht kann spaeter Orchestrierung mit RAG-basiertem Business-Kontext verbinden."
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
    payload["guided_demo"] = {
        "title": "Guided Demo Mode" if lang == "en" else "Gefuehrter Demo-Modus",
        "subtitle": (
            "Switch between a free operator view and a presenter-guided story mode."
            if lang == "en"
            else "Wechsle zwischen freier Operator-Sicht und presenter-gefuehrtem Story-Modus."
        ),
        "modes": [
            {"id": "free", "label": "Free" if lang == "en" else "Frei"},
            {"id": "guided", "label": "Guided" if lang == "en" else "Gefuehrt"},
        ],
        "auto_run_interval_ms": 2200,
        "steps": [
            {
                "step_id": "intro",
                "title": "Start with messaging" if lang == "en" else "Mit Messaging starten",
                "description": (
                    "Show the customer message first. This keeps the demo human and messaging-first."
                    if lang == "en"
                    else "Zeige zuerst die Kundennachricht. So bleibt die Demo menschlich und messaging-first."
                ),
                "ui_focus": "chatStream",
                "action": "present_intro",
            },
            {
                "step_id": "pick_action",
                "title": "Use interactive reply buttons" if lang == "en" else "Interaktive Antwortbuttons nutzen",
                "description": (
                    "Click confirm, reschedule, cancel, or callback to show that the buttons really drive the flow."
                    if lang == "en"
                    else "Klicke auf bestaetigen, verschieben, absagen oder rueckruf, um zu zeigen, dass die Buttons den Ablauf wirklich steuern."
                ),
                "ui_focus": "slotList",
                "action": "click_reply",
            },
            {
                "step_id": "follow_status",
                "title": "Watch live status" if lang == "en" else "Live-Status beobachten",
                "description": (
                    "The guided panel, operator summary, and monitor now show the same journey state."
                    if lang == "en"
                    else "Guided Panel, Operator Summary und Monitor zeigen jetzt denselben Journey-Zustand."
                ),
                "ui_focus": "guidedDemoPanel",
                "action": "watch_status",
            },
            {
                "step_id": "show_platform",
                "title": "Explain the platform" if lang == "en" else "Die Plattform erklaeren",
                "description": (
                    "Point at channels, integrations, and the AI layer to explain that this is a platform, not a single chatbot."
                    if lang == "en"
                    else "Zeige auf Kanaele, Integrationen und die AI-Schicht, um zu erklaeren, dass das eine Plattform und kein einzelner Chatbot ist."
                ),
                "ui_focus": "platformOverviewGrid",
                "action": "explain_platform",
            },
            {
                "step_id": "close_wow",
                "title": "Close with the wow effect" if lang == "en" else "Mit dem Wow-Effekt schliessen",
                "description": (
                    "Use slot hold, message monitor, and business value together as the final wow moment."
                    if lang == "en"
                    else "Nutze Slot Hold, Message Monitor und Business Value gemeinsam als finalen Wow-Moment."
                ),
                "ui_focus": "demoStoryboardGrid",
                "action": "close_wow",
            },
        ],
    }
    payload["platform_visibility"] = {
        "title": "Platform Visibility" if lang == "en" else "Plattform-Sichtbarkeit",
        "channels": ["RCS", "SMS", "WhatsApp (planned)" if lang == "en" else "WhatsApp (geplant)", "Voice" if lang == "en" else "Voice"],
        "integrations": ["Google", "Microsoft", "CRM"],
        "ai": ["Agent", "RAG"],
    }
    return payload
