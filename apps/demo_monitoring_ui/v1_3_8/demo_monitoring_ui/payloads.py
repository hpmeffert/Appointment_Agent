from __future__ import annotations

from copy import deepcopy

from demo_monitoring_ui.v1_3_6_patch1.demo_monitoring_ui.payloads import build_v136_patch1_payload


def build_v138_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    payload = deepcopy(build_v136_patch1_payload(lang=language))
    payload["version"] = "v1.3.8"
    payload["ui_meta"]["tagline"] = (
        "Combined demo cockpit with reply-to-action visibility, communication history, Google linkage, and reminder flow in one shell."
        if language == "en"
        else "Kombiniertes Demo-Cockpit mit Reply-to-Action-Sicht, Communication History, Google-Verknuepfung und Reminder-Ablauf in einer Shell."
    )
    payload["documentation_highlights"] = list(payload.get("documentation_highlights", [])) + [
        (
            "Reply-to-action shows which internal appointment action the platform would request after an inbound RCS reply."
            if language == "en"
            else "Reply-to-Action zeigt, welche interne Termin-Aktion die Plattform nach einer eingehenden RCS-Antwort anfordern wuerde."
        ),
        (
            "The message monitor now separates safe, ambiguous, and review-needed interpretations."
            if language == "en"
            else "Der Message Monitor trennt jetzt sichere, mehrdeutige und pruefpflichtige Interpretationen."
        ),
    ]
    payload["business_value_points"] = list(payload.get("business_value_points", [])) + [
        (
            "Stakeholders can now see not just that a reply arrived, but what business action the platform would trigger next."
            if language == "en"
            else "Stakeholder sehen jetzt nicht nur, dass eine Antwort angekommen ist, sondern auch, welche fachliche Aktion die Plattform als Naechstes ausloesen wuerde."
        ),
    ]
    bridge = payload.get("reminder_scheduler_bridge") or {}
    if bridge:
        bridge["title"] = "Appointment Source, Replies, and Reminders" if language == "en" else "Terminquelle, Antworten und Reminder"
        bridge["subtitle"] = (
            "The combined shell now explains the full path from outbound message to inbound reply and prepared appointment action."
            if language == "en"
            else "Die kombinierte Shell erklaert jetzt den kompletten Weg von der ausgehenden Nachricht ueber die eingehende Antwort bis zur vorbereiteten Termin-Aktion."
        )
        bridge["quick_links"] = [
            {
                "label": "Reminder Cockpit" if language == "en" else "Reminder Cockpit",
                "href": "/ui/reminder-cockpit/v1.3.8",
            },
            {
                "label": "Full Reminder Scheduler UI" if language == "en" else "Vollstaendige Reminder Scheduler UI",
                "href": "/ui/reminder-scheduler/v1.3.6",
            },
            {
                "label": "Reply-to-Action Demo Guide" if language == "en" else "Reply-to-Action Demo Guide",
                "href": f"/docs/demo?lang={language}",
            },
            {
                "label": "Reply-to-Action User Guide" if language == "en" else "Reply-to-Action User Guide",
                "href": f"/docs/user?lang={language}",
            },
            {
                "label": "Reply-to-Action Admin Guide" if language == "en" else "Reply-to-Action Admin Guide",
                "href": f"/docs/admin?lang={language}",
            },
        ]
    return payload
