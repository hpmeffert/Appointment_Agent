from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_2_1_patch4.demo_monitoring_ui.payloads import build_v121_patch4_payload
from demo_monitoring_ui.v1_3_6.demo_monitoring_ui.payloads import build_v136_payload


def build_v136_patch1_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    payload = deepcopy(build_v121_patch4_payload(lang=language))
    reminder_payload = build_v136_payload(lang=language)

    payload["version"] = "v1.3.6-patch1"
    payload["ui_meta"]["tagline"] = (
        "Incident-style combined demo cockpit with the classic patch4 operator shell and the new v1.3.6 appointment-to-reminder journey."
        if language == "en"
        else "Incident-artiges kombiniertes Demo-Cockpit mit der bekannten patch4-Operator-Shell und der neuen v1.3.6 Termin-zu-Reminder-Journey."
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
        {"id": "help", "label": "Help" if language == "en" else "Hilfe"},
    ]
    payload["documentation_highlights"] = list(payload.get("documentation_highlights", [])) + [
        (
            "A new menu point now connects the classic operator shell with the v1.3.6 Google-to-reminder demonstrator."
            if language == "en"
            else "Ein neuer Menuepunkt verbindet jetzt die klassische Operator-Shell mit dem v1.3.6 Google-zu-Reminder-Demonstrator."
        ),
    ]
    payload["platform_overview"]["items"].append(
        {
            "title": "Reminder Scheduler" if language == "en" else "Reminder Scheduler",
            "body": (
                "The new menu point shows how a Google-linked appointment becomes a reminder plan, a reminder preview, and visible jobs."
                if language == "en"
                else "Der neue Menuepunkt zeigt, wie aus einem Google-verknuepften Termin ein Reminder-Plan, eine Vorschau und sichtbare Jobs werden."
            ),
        }
    )
    payload["business_value_points"] = list(payload.get("business_value_points", [])) + [
        (
            "One demo surface can now explain both messaging operations and the full appointment-to-reminder chain."
            if language == "en"
            else "Eine Demo-Oberflaeche kann jetzt sowohl Messaging-Operationen als auch die komplette Termin-zu-Reminder-Kette erklaeren."
        ),
    ]
    payload["reminder_scheduler_bridge"] = {
        "title": "Appointment Source to Reminder Jobs" if language == "en" else "Terminquelle bis Reminder Jobs",
        "subtitle": (
            "This menu page keeps the patch4 cockpit shell, but adds the v1.3.6 reminder story as one integrated operator page."
            if language == "en"
            else "Diese Menue-Seite behaelt die patch4-Cockpit-Shell, fuegt aber die v1.3.6 Reminder-Story als integrierte Operator-Seite hinzu."
        ),
        "overview_metrics": reminder_payload["dashboard_summary"]["metrics"],
        "source_metrics": reminder_payload["appointment_source"]["metrics"] + reminder_payload["google_linkage"]["metrics"],
        "detail_metrics": reminder_payload["appointment_details"]["metrics"] + reminder_payload["reminder_policy"]["metrics"][:3],
        "timeline": reminder_payload["reminder_preview"]["timeline"],
        "jobs": reminder_payload["reminder_jobs"]["jobs"],
        "health_metrics": reminder_payload["runtime_health"]["metrics"],
        "operator_summary": reminder_payload["operator_summary"],
        "embedded_ui_url": "/ui/reminder-scheduler/v1.3.6",
        "embedded_label": (
            "Open the standalone reminder cockpit"
            if language == "en"
            else "Eigenstaendiges Reminder-Cockpit oeffnen"
        ),
        "cards": [
            {
                "title": "Why this page exists" if language == "en" else "Warum diese Seite existiert",
                "body": (
                    "Operators can stay in the familiar patch4 shell and still show the new appointment-to-reminder flow."
                    if language == "en"
                    else "Operatoren koennen in der vertrauten patch4-Shell bleiben und trotzdem den neuen Termin-zu-Reminder-Ablauf zeigen."
                ),
            },
            {
                "title": "What it combines" if language == "en" else "Was sie verbindet",
                "body": (
                    "It combines Google appointment source visibility, reminder policy visibility, preview visibility, and runtime readiness."
                    if language == "en"
                    else "Sie verbindet Google-Terminquelle, Reminder-Policy, Vorschau und Runtime-Readiness in einer Sicht."
                ),
            },
        ],
        "quick_links": [
            {
                "label": "Reminder Cockpit" if language == "en" else "Reminder Cockpit",
                "href": "/ui/reminder-cockpit/v1.3.7",
            },
            {
                "label": "Full Reminder Scheduler UI" if language == "en" else "Vollstaendige Reminder Scheduler UI",
                "href": "/ui/reminder-scheduler/v1.3.6",
            },
            {
                "label": "Reminder Demo Guide" if language == "en" else "Reminder Demo Guide",
                "href": f"/docs/demo?lang={language}",
            },
            {
                "label": "Reminder User Guide" if language == "en" else "Reminder User Guide",
                "href": f"/docs/user?lang={language}",
            },
            {
                "label": "Reminder Admin Guide" if language == "en" else "Reminder Admin Guide",
                "href": f"/docs/admin?lang={language}",
            },
        ],
        "demo_story_scenarios": [
            (
                "New Google-linked appointment becomes reminder-ready"
                if language == "en"
                else "Neuer Google-verknuepfter Termin wird reminder-faehig"
            ),
            (
                "Reschedule keeps the story visible and rebuilds reminder times"
                if language == "en"
                else "Eine Verschiebung haelt die Story sichtbar und baut Reminder-Zeiten neu auf"
            ),
            (
                "Cancellation stops reminder work safely"
                if language == "en"
                else "Eine Absage stoppt die Reminder-Arbeit sicher"
            ),
        ],
    }
    return payload
