from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_3_8.demo_monitoring_ui.payloads import build_v138_payload

from .scenario_catalog import build_phase5_scenarios, scenario_catalog


def build_v139_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    payload = deepcopy(build_v138_payload(lang=language))
    payload["version"] = "v1.3.9-patch9"
    payload["ui_contract"] = {
        "display_version": "v1.3.9-patch9",
        "demo_api_version": "v1.3.9",
        "patch_alias_version": "v1.3.9-patch9",
        "legacy_patch_aliases": ["v1.3.9-patch1", "v1.3.9-patch2", "v1.3.9-patch3", "v1.3.9-patch4", "v1.3.9-patch5", "v1.3.9-patch6", "v1.3.9-patch7", "v1.3.9-patch8"],
        "google_api_version": "v1.3.6",
        "lekab_api_version": "v1.3.8",
        "address_api_version": "v1.3.9",
        "required_hydration_sources": [
            "payload",
            "scenario_catalog",
            "address_database",
            "scenario_context",
        ],
        "diagnostics": {
            "payload_disconnect_message": (
                "Payload disconnected. Check the demo API route registration and version alias wiring."
                if language == "en"
                else "Payload getrennt. Bitte Demo-API-Routen und Version-Alias-Verdrahtung pruefen."
            ),
            "scenario_empty_message": (
                "Scenario catalog unavailable or empty."
                if language == "en"
                else "Szenario-Katalog ist nicht verfuegbar oder leer."
            ),
            "address_empty_message": (
                "Address source unavailable or empty."
                if language == "en"
                else "Adressquelle ist nicht verfuegbar oder leer."
            ),
        },
    }
    payload["ui_meta"]["tagline"] = (
        "Combined incident-style cockpit with address database navigation, address linkage visibility, reply-to-action visibility, and reminder operations in one shell."
        if language == "en"
        else "Kombinierte Incident-artige Shell mit Address Database Navigation, sichtbarer Address-Linkage, Reply-to-Action-Sicht und Reminder-Bedienung in einer Oberflaeche."
    )
    payload["pages"] = [
        {"id": "dashboard", "label": "Dashboard" if language == "en" else "Dashboard"},
        {"id": "message-monitor", "label": "Message Monitor" if language == "en" else "Message Monitor"},
        {"id": "communications-reports", "label": "Reports" if language == "en" else "Berichte"},
        {"id": "monitoring", "label": "Monitoring" if language == "en" else "Monitoring"},
        {"id": "settings-general", "label": "Settings" if language == "en" else "Einstellungen"},
        {"id": "settings-rcs", "label": "Settings -> RCS" if language == "en" else "Einstellungen -> RCS"},
        {"id": "google-demo-control", "label": "Google Demo Control" if language == "en" else "Google Demo Control"},
        {"id": "appointment-reminders", "label": "Reminder" if language == "en" else "Reminder"},
        {"id": "addresses", "label": "Addresses" if language == "en" else "Adressen"},
        {"id": "help", "label": "Help" if language == "en" else "Hilfe"},
    ]
    payload["documentation_highlights"] = list(payload.get("documentation_highlights", [])) + [
        (
            "The address database is now visible as its own menu entry and standalone operator page."
            if language == "en"
            else "Die Address Database ist jetzt als eigener Menuepunkt und als eigenstaendige Operator-Seite sichtbar."
        ),
        (
            "Addresses can be searched, edited, deactivated, and inspected for appointment linkage without leaving the cockpit shell."
            if language == "en"
            else "Adressen koennen jetzt gesucht, bearbeitet, deaktiviert und auf Termin-Linkage geprueft werden, ohne die Cockpit-Shell zu verlassen."
        ),
    ]
    payload["business_value_points"] = list(payload.get("business_value_points", [])) + [
        (
            "Operators can now explain who the customer is, which address record is linked, and how that record connects to appointments and reminders."
            if language == "en"
            else "Operatoren koennen jetzt erklaeren, wer der Kunde ist, welcher Address Record verknuepft ist und wie dieser Record mit Terminen und Remindern zusammenhaengt."
        ),
        (
            "Phase 5 adds reproducible scenario evidence with local protocol files and guided replay buttons directly in the cockpit."
            if language == "en"
            else "Phase 5 fuegt reproduzierbare Szenario-Evidenz mit lokalen Protokolldateien und gefuehrten Replay-Buttons direkt im Cockpit hinzu."
        ),
    ]
    payload["scenarios"] = build_phase5_scenarios(language)
    payload["scenario_testing"] = {
        "title": "Scenario Testing" if language == "en" else "Szenario-Tests",
        "subtitle": (
            "Run one business scenario in simulation or real demo mode and keep the protocol files in the local project directory."
            if language == "en"
            else "Fuehre ein Business-Szenario im Simulations- oder Real-Demo-Modus aus und halte die Protokolldateien im lokalen Projektverzeichnis fest."
        ),
        "artifact_directory": "runtime-artifacts/demo-scenarios/v1_3_9",
        "scenario_matrix": [
            {
                "id": item["id"],
                "title": item["title"],
                "expected_action": item["expected_action"],
                "expected_state": item["expected_state"],
            }
            for item in scenario_catalog(language)
        ],
        "notes": [
            (
                "Simulation mode keeps the run demo-safe but still writes the same protocol and summary files."
                if language == "en"
                else "Der Simulationsmodus bleibt demo-sicher, schreibt aber trotzdem dieselben Protokoll- und Summary-Dateien."
            ),
            (
                "Real mode uses the configured output channel path and still writes the protocol files for later inspection."
                if language == "en"
                else "Der Real-Modus verwendet den konfigurierten Output-Kanalpfad und schreibt trotzdem Protokolldateien zur spaeteren Pruefung."
            ),
            (
                "Patch 9 keeps the interactive journey and restores deterministic Google calendar formatting for confirmed reschedules."
                if language == "en"
                else "Patch 9 behaelt die interaktive Journey bei und stellt das deterministische Google-Kalenderformat fuer bestaetigte Verschiebungen wieder her."
            ),
        ],
    }
    payload["interactive_demo_flow"] = {
        "phase6_enabled": True,
        "initial_actions": next((item["steps"][0]["communication_message"]["actions"] for item in payload["scenarios"] if item["id"] == "confirm-appointment"), []),
        "relative_actions": next((item["steps"][0]["communication_message"]["actions"] for item in payload["scenarios"] if item["id"] == "this-week"), []),
        "date_actions": next((item["steps"][0]["communication_message"]["actions"] for item in payload["scenarios"] if item["id"] == "explicit-date-selection"), []),
        "time_actions": next((item["steps"][0]["communication_message"]["actions"] for item in payload["scenarios"] if item["id"] == "explicit-time-selection"), []),
        "relative_step_message": (
            "Choose the preferred scheduling window."
            if language == "en"
            else "Waehlen Sie das bevorzugte Terminfenster."
        ),
        "date_step_message": (
            "Choose one of the proposed dates."
            if language == "en"
            else "Waehlen Sie eines der vorgeschlagenen Daten."
        ),
        "time_step_message": (
            "Choose one of the proposed times."
            if language == "en"
            else "Waehlen Sie eine der vorgeschlagenen Uhrzeiten."
        ),
        "selected_source_simulation": "simulation_click",
        "selected_source_real": "real_callback_or_test_path",
        "booking_confirmation_actions": next((item["steps"][0]["communication_message"]["actions"] for item in payload["scenarios"] if item["id"] == "confirm-appointment"), []),
    }
    payload["address_database"] = {
        "title": "Address Database" if language == "en" else "Adressdatenbank",
        "subtitle": (
            "The address record becomes the human-readable anchor for appointments, reminders, and communications."
            if language == "en"
            else "Der Address Record wird zum gut lesbaren Anker fuer Termine, Reminder und Kommunikation."
        ),
        "quick_links": [
            {
                "label": "Standalone Address Database" if language == "en" else "Eigenstaendige Adressdatenbank",
                "href": "/ui/address-database/v1.3.9",
            },
            {
                "label": "Address API Help" if language == "en" else "Address API Hilfe",
                "href": "/api/addresses/v1.3.9/help",
            },
            {
                "label": "Admin Guide" if language == "en" else "Admin Leitfaden",
                "href": f"/docs/admin?lang={language}",
            },
        ],
        "empty_state": (
            "No addresses match the current filter yet."
            if language == "en"
            else "Zum aktuellen Filter gibt es noch keine passenden Adressen."
        ),
    }
    bridge = payload.get("reminder_scheduler_bridge") or {}
    if bridge:
        bridge["subtitle"] = (
            "This integrated page now shows the address anchor together with appointment source, reminder policy, jobs, and health."
            if language == "en"
            else "Diese integrierte Seite zeigt jetzt den Adress-Anker zusammen mit Terminquelle, Reminder-Policy, Jobs und Health."
        )
        bridge["source_metrics"] = list(bridge.get("source_metrics") or []) + [
            {
                "label": "Address record" if language == "en" else "Adressdatensatz",
                "value": "Anna Berger | Berlin",
            },
            {
                "label": "Address id" if language == "en" else "Address-ID",
                "value": "addr-demo-001",
            },
        ]
        bridge["detail_metrics"] = list(bridge.get("detail_metrics") or []) + [
            {
                "label": "Correlation ref" if language == "en" else "Korrelations-Ref",
                "value": "corr-addr-demo-001",
            },
            {
                "label": "Preferred channel" if language == "en" else "Bevorzugter Kanal",
                "value": "rcs_sms",
            },
        ]
        bridge["cards"] = list(bridge.get("cards") or []) + [
            {
                "title": "Address anchor" if language == "en" else "Adress-Anker",
                "body": (
                    "The same address id ties the appointment source, reminder jobs, and communication history together."
                    if language == "en"
                    else "Dieselbe Address-ID verbindet Terminquelle, Reminder-Jobs und Communication History."
                ),
            }
        ]
        bridge["jobs"] = [
            {
                **job,
                "address_id": "addr-demo-001",
                "correlation_ref": "corr-addr-demo-001",
            }
            for job in list(bridge.get("jobs") or [])
        ]
        bridge["assignment_context"] = {
            "appointment_external_id": "gcal-87421",
            "booking_reference": "booking-gdemo-dentist-001",
            "calendar_ref": "appointment-agent-test-calendar",
            "correlation_ref": "corr-addr-demo-001",
            "address_id": "addr-demo-001",
            "address_display_name": "Anna Berger",
            "address_city": "Berlin",
        }
        bridge["assignment_notes"] = [
            (
                "Pick an address and assign it explicitly to the appointment so reminders, replies, and the calendar demo all use the same anchor."
                if language == "en"
                else "Waehle eine Adresse und ordne sie dem Termin explizit zu, damit Reminder, Replies und die Kalender-Demo denselben Anker verwenden."
            ),
            (
                "Generated Google demo appointments can reuse the same selected address so the link survives the calendar generation step."
                if language == "en"
                else "Erzeugte Google-Demo-Termine koennen dieselbe ausgewaehlte Adresse uebernehmen, damit die Verknuepfung die Kalender-Generierung ueberlebt."
            ),
        ]
        bridge["demo_story_scenarios"] = [
            item["title"] for item in scenario_catalog(language)
        ]
    return payload
