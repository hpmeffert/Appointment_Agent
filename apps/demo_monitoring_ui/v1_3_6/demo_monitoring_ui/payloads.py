from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone


def _text(en: str, de: str, lang: str) -> str:
    return de if lang == "de" else en


def _berlin_time(year: int, month: int, day: int, hour: int, minute: int) -> str:
    return datetime(year, month, day, hour, minute, tzinfo=timezone(timedelta(hours=2))).isoformat()


def _appointment_source(lang: str) -> dict:
    return {
        "title": _text("Appointment Source", "Appointment Source", lang),
        "subtitle": _text(
            "The cockpit shows where the appointment came from and what system delivered it.",
            "Das Cockpit zeigt, woher der Termin kommt und welches System ihn geliefert hat.",
            lang,
        ),
        "metrics": [
            {"label": _text("Source system", "Source system", lang), "value": "Google Calendar"},
            {"label": _text("Source type", "Source type", lang), "value": _text("Linked booking", "Verknuepfter Termin", lang)},
            {"label": _text("External id", "External id", lang), "value": "gcal-87421"},
            {"label": _text("Import state", "Import state", lang), "value": _text("Linked", "Verknuepft", lang)},
        ],
        "cards": [
            {
                "title": _text("Why this matters", "Warum das wichtig ist", lang),
                "body": _text(
                    "The operator can see that the reminder starts from a real appointment source, not from a fake demo record.",
                    "Der Operator sieht, dass die Erinnerung von einer echten Terminquelle kommt und nicht von einem Schein-Datensatz.",
                    lang,
                ),
                "state": "ok",
            },
            {
                "title": _text("What the source contains", "Was die Quelle enthaelt", lang),
                "body": _text(
                    "The source carries the customer name, the appointment time, and the link to the Google calendar entry.",
                    "Die Quelle enthaelt den Kundennamen, die Terminzeit und den Bezug zum Google-Kalendereintrag.",
                    lang,
                ),
                "state": "neutral",
            },
        ],
    }


def _google_linkage(lang: str) -> dict:
    return {
        "title": _text("Google Linkage", "Google Linkage", lang),
        "subtitle": _text(
            "This shows how the appointment is tied to the Google test calendar.",
            "Hier sieht man, wie der Termin mit dem Google-Testkalender verbunden ist.",
            lang,
        ),
        "metrics": [
            {"label": _text("Calendar name", "Calendar name", lang), "value": "Appointment Agent Test"},
            {"label": _text("Calendar id", "Calendar id", lang), "value": "appointment-agent-test-calendar"},
            {"label": _text("Link status", "Link status", lang), "value": _text("Connected", "Verbunden", lang)},
            {"label": _text("Last sync", "Last sync", lang), "value": "2026-04-08T08:15:00+02:00"},
        ],
        "cards": [
            {
                "title": _text("Connection check", "Verbindungspruefung", lang),
                "body": _text(
                    "The cockpit tells the operator if the calendar link is ready, waiting, or broken.",
                    "Das Cockpit sagt dem Operator, ob die Kalenderverbindung bereit, wartend oder kaputt ist.",
                    lang,
                ),
                "state": "ok",
            },
            {
                "title": _text("Safe handling", "Sichere Behandlung", lang),
                "body": _text(
                    "This demo only shows the link; the actual Google write actions stay behind the controlled demo actions.",
                    "Diese Demo zeigt nur die Verbindung; die echten Google-Schreibaktionen bleiben hinter den gesteuerten Demo-Aktionen.",
                    lang,
                ),
                "state": "neutral",
            },
        ],
    }


def _appointment_details(lang: str) -> dict:
    return {
        "title": _text("Appointment Details", "Appointment Details", lang),
        "subtitle": _text(
            "This is the appointment that later gets reminders.",
            "Das ist der Termin, fuer den spaeter Erinnerungen geplant werden.",
            lang,
        ),
        "metrics": [
            {"label": _text("Customer", "Customer", lang), "value": "Anna Berger"},
            {"label": _text("Appointment type", "Appointment type", lang), "value": _text("Dentist check-up", "Zahnarztkontrolle", lang)},
            {"label": _text("Start", "Start", lang), "value": "2026-04-20 10:00"},
            {"label": _text("Timezone", "Timezone", lang), "value": "Europe/Berlin"},
        ],
        "cards": [
            {
                "title": _text("Location", "Ort", lang),
                "body": _text("Musterstrasse 12, Berlin", "Musterstrasse 12, Berlin", lang),
                "state": "neutral",
            },
            {
                "title": _text("Duration", "Dauer", lang),
                "body": _text("30 minutes", "30 Minuten", lang),
                "state": "neutral",
            },
            {
                "title": _text("Important note", "Wichtiger Hinweis", lang),
                "body": _text(
                    "The operator can quickly see who the appointment belongs to, when it starts, and where it happens.",
                    "Der Operator sieht schnell, wem der Termin gehoert, wann er startet und wo er stattfindet.",
                    lang,
                ),
                "state": "ok",
            },
        ],
    }


def _reminder_policy(lang: str) -> dict:
    return {
        "title": _text("Reminder Policy", "Reminder Policy", lang),
        "subtitle": _text(
            "The policy decides when reminders are sent and which channel is tried first.",
            "Die Policy entscheidet, wann Erinnerungen gesendet werden und welcher Kanal zuerst versucht wird.",
            lang,
        ),
        "metrics": [
            {"label": _text("Enabled", "Enabled", lang), "value": "true"},
            {"label": _text("Silence threshold", "Silence threshold", lang), "value": "1300 ms"},
            {"label": _text("Reminder offsets", "Reminder offsets", lang), "value": "1440 / 120 / 30 min"},
            {"label": _text("Primary channel", "Primary channel", lang), "value": "rcs_sms"},
            {"label": _text("Fallback channels", "Fallback channels", lang), "value": "email"},
            {"label": _text("Quiet hours", "Quiet hours", lang), "value": "20:00 - 08:00"},
        ],
        "rules": [
            _text("The silence threshold is 1300 ms by default.", "Die Silence Threshold liegt standardmaessig bei 1300 ms.", lang),
            _text("The first reminder goes out one day before the appointment.", "Die erste Erinnerung geht einen Tag vor dem Termin raus.", lang),
            _text("A second reminder is planned two hours before the appointment.", "Eine zweite Erinnerung ist zwei Stunden vor dem Termin geplant.", lang),
            _text("A final reminder is planned 30 minutes before the appointment.", "Eine letzte Erinnerung ist 30 Minuten vor dem Termin geplant.", lang),
            _text("Quiet hours stop reminders from being sent at the wrong time.", "Quiet Hours verhindern, dass Erinnerungen zur falschen Zeit gesendet werden.", lang),
        ],
        "cards": [
            {
                "title": _text("Why this matters", "Warum das wichtig ist", lang),
                "body": _text(
                    "The operator can explain the reminder plan in one short sentence.",
                    "Der Operator kann den Erinnerungsplan in einem kurzen Satz erklaeren.",
                    lang,
                ),
                "state": "ok",
            },
            {
                "title": _text("Fallback logic", "Fallback-Logik", lang),
                "body": _text(
                    "If the first channel is not ready, the cockpit shows the backup channel clearly.",
                    "Wenn der erste Kanal nicht bereit ist, zeigt das Cockpit den Ersatzkanal klar an.",
                    lang,
                ),
                "state": "warn",
            },
        ],
    }


def _reminder_preview(lang: str) -> dict:
    appointment_start = datetime(2026, 4, 20, 10, 0, tzinfo=timezone(timedelta(hours=2)))
    return {
        "title": _text("Reminder Preview", "Reminder Preview", lang),
        "subtitle": _text(
            "This preview shows what the reminder scheduler will create from the appointment.",
            "Diese Vorschau zeigt, was der Reminder Scheduler aus dem Termin erzeugt.",
            lang,
        ),
        "metrics": [
            {"label": _text("Next due", "Next due", lang), "value": _berlin_time(2026, 4, 19, 10, 0)},
            {"label": _text("Preview count", "Preview count", lang), "value": "3"},
            {"label": _text("Appointment date", "Appointment date", lang), "value": appointment_start.date().isoformat()},
            {"label": _text("Preview state", "Preview state", lang), "value": _text("Ready", "Bereit", lang)},
        ],
        "timeline": [
            {
                "step": _text("24 hours before", "24 Stunden vorher", lang),
                "when": "2026-04-19 10:00",
                "channel": "rcs_sms",
                "body": _text("First reminder: the appointment is tomorrow.", "Erste Erinnerung: Der Termin ist morgen.", lang),
            },
            {
                "step": _text("2 hours before", "2 Stunden vorher", lang),
                "when": "2026-04-20 08:00",
                "channel": "rcs_sms",
                "body": _text("Second reminder: please get ready for the appointment.", "Zweite Erinnerung: Bitte auf den Termin vorbereiten.", lang),
            },
            {
                "step": _text("30 minutes before", "30 Minuten vorher", lang),
                "when": "2026-04-20 09:30",
                "channel": "email",
                "body": _text("Final reminder: the appointment starts soon.", "Letzte Erinnerung: Der Termin startet gleich.", lang),
            },
        ],
        "cards": [
            {
                "title": _text("Preview result", "Preview-Ergebnis", lang),
                "body": _text(
                    "The operator sees the reminder order before anything is sent.",
                    "Der Operator sieht die Reihenfolge der Erinnerungen, bevor etwas gesendet wird.",
                    lang,
                ),
                "state": "ok",
            },
            {
                "title": _text("Silence threshold", "Silence Threshold", lang),
                "body": _text(
                    "The system waits 1300 ms before it decides that the user stopped speaking.",
                    "Das System wartet 1300 ms, bevor es entscheidet, dass der Nutzer aufgehört hat zu sprechen.",
                    lang,
                ),
                "state": "neutral",
            },
        ],
    }


def _reminder_jobs(lang: str) -> dict:
    return {
        "title": _text("Reminder Jobs", "Reminder Jobs", lang),
        "subtitle": _text(
            "This page shows planned, updated, cancelled, and sent reminder jobs.",
            "Diese Seite zeigt geplante, aktualisierte, abgebrochene und gesendete Reminder Jobs.",
            lang,
        ),
        "status_overview": {
            "planned": 3,
            "updated": 1,
            "cancelled": 1,
            "sent": 1,
            "skipped": 0,
            "failed": 0,
        },
        "jobs": [
            {
                "job_id": "job-1001",
                "kind": _text("24h reminder", "24h Erinnerung", lang),
                "due_at": "2026-04-19T10:00:00+02:00",
                "status": "planned",
                "channel": "rcs_sms",
                "note": _text("First reminder in the queue.", "Erste Erinnerung in der Warteschlange.", lang),
            },
            {
                "job_id": "job-1002",
                "kind": _text("2h reminder", "2h Erinnerung", lang),
                "due_at": "2026-04-20T08:00:00+02:00",
                "status": "updated",
                "channel": "rcs_sms",
                "note": _text("This job was updated after a reschedule.", "Dieser Job wurde nach einer Verschiebung aktualisiert.", lang),
            },
            {
                "job_id": "job-1003",
                "kind": _text("30m reminder", "30m Erinnerung", lang),
                "due_at": "2026-04-20T09:30:00+02:00",
                "status": "planned",
                "channel": "email",
                "note": _text("The last reminder is ready for the fallback channel.", "Die letzte Erinnerung ist fuer den Ersatzkanal bereit.", lang),
            },
            {
                "job_id": "job-1004",
                "kind": _text("Cancelled reminder", "Abgebrochene Erinnerung", lang),
                "due_at": "2026-04-18T10:00:00+02:00",
                "status": "cancelled",
                "channel": "rcs_sms",
                "note": _text("This job was cancelled when the appointment was cancelled.", "Dieser Job wurde bei der Terminabsage ebenfalls abgebrochen.", lang),
            },
        ],
        "cards": [
            {
                "title": _text("What the operator sees", "Was der Operator sieht", lang),
                "body": _text(
                    "Each reminder job shows a status, a due time, and the channel that will be used.",
                    "Jeder Reminder Job zeigt einen Status, eine Faelligkeitszeit und den verwendeten Kanal.",
                    lang,
                ),
                "state": "ok",
            },
            {
                "title": _text("Why status matters", "Warum der Status wichtig ist", lang),
                "body": _text(
                    "The cockpit can show whether a job is still planned, already updated, cancelled, or sent.",
                    "Das Cockpit kann zeigen, ob ein Job noch geplant, bereits aktualisiert, abgebrochen oder gesendet ist.",
                    lang,
                ),
                "state": "neutral",
            },
        ],
    }


def _runtime_health(lang: str) -> dict:
    return {
        "title": _text("Health", "Health", lang),
        "subtitle": _text(
            "This tells the operator if the runtime is ready for the next reminder.",
            "Das zeigt dem Operator, ob die Laufzeit fuer die naechste Erinnerung bereit ist.",
            lang,
        ),
        "metrics": [
            {"label": _text("Database", "Database", lang), "value": "ok"},
            {"label": _text("Worker", "Worker", lang), "value": "ready"},
            {"label": _text("Queue depth", "Queue depth", lang), "value": "3"},
            {"label": _text("Next due", "Next due", lang), "value": "2026-04-19T10:00:00+02:00"},
            {"label": _text("Last source sync", "Last source sync", lang), "value": "2026-04-08T08:15:00+02:00"},
        ],
        "notes": [
            _text("No stale locks are waiting.", "Es warten keine alten Locks.", lang),
            _text("The Google link is healthy and the reminder plan is visible.", "Die Google-Verbindung ist gesund und der Erinnerungsplan ist sichtbar.", lang),
            _text("The next job can be explained in one sentence.", "Der naechste Job kann in einem Satz erklaert werden.", lang),
        ],
        "checks": [
            {"label": _text("DB status", "DB status", lang), "value": "ok"},
            {"label": _text("Worker status", "Worker status", lang), "value": "ready"},
            {"label": _text("Google linkage", "Google linkage", lang), "value": _text("connected", "verbunden", lang)},
            {"label": _text("Reminder policy", "Reminder policy", lang), "value": _text("loaded", "geladen", lang)},
        ],
    }


def _demo_stories(lang: str) -> list[dict]:
    return [
        {
            "id": "new-appointment",
            "title": _text("Story 1: New appointment from Google", "Story 1: Neuer Termin aus Google", lang),
            "summary": _text(
                "The appointment arrives from Google Calendar and the reminder plan is created immediately.",
                "Der Termin kommt aus Google Calendar und der Erinnerungsplan wird sofort erstellt.",
                lang,
            ),
            "what_to_say": _text(
                "This is the normal path: a linked appointment enters the system and becomes reminder jobs.",
                "Das ist der Normalfall: Ein verknuepfter Termin kommt ins System und wird zu Reminder Jobs.",
                lang,
            ),
            "why_it_matters": _text(
                "The operator can see the source, the link, and the reminder plan in one screen.",
                "Der Operator sieht Quelle, Verknuepfung und Erinnerungsplan in einem einzigen Bildschirm.",
                lang,
            ),
        },
        {
            "id": "reschedule",
            "title": _text("Story 2: Appointment rescheduled", "Story 2: Termin verschoben", lang),
            "summary": _text(
                "The appointment time changes and the reminder jobs are updated.",
                "Die Terminzeit aendert sich und die Reminder Jobs werden angepasst.",
                lang,
            ),
            "what_to_say": _text(
                "The system does not forget the appointment; it updates the plan.",
                "Das System vergisst den Termin nicht, sondern passt den Plan an.",
                lang,
            ),
            "why_it_matters": _text(
                "This keeps the reminders correct when the customer reschedules.",
                "So bleiben die Erinnerungen korrekt, wenn der Kunde verschiebt.",
                lang,
            ),
        },
        {
            "id": "cancelled",
            "title": _text("Story 3: Appointment cancelled", "Story 3: Termin abgesagt", lang),
            "summary": _text(
                "The appointment is cancelled and the reminder jobs are cancelled too.",
                "Der Termin wird abgesagt und die Reminder Jobs werden ebenfalls abgebrochen.",
                lang,
            ),
            "what_to_say": _text(
                "The cockpit shows that the reminder work is stopped safely.",
                "Das Cockpit zeigt, dass die Erinnerungsarbeit sicher gestoppt wurde.",
                lang,
            ),
            "why_it_matters": _text(
                "Nobody wants a reminder after an appointment is already gone.",
                "Niemand will eine Erinnerung bekommen, wenn der Termin schon weg ist.",
                lang,
            ),
        },
    ]


def _operator_summary(lang: str) -> dict:
    return {
        "title": _text("What the operator should notice", "Was der Operator beachten sollte", lang),
        "subtitle": _text(
            "The cockpit explains the flow from appointment source to reminder jobs in simple words.",
            "Das Cockpit erklaert den Weg von der Terminquelle bis zu den Reminder Jobs in einfachen Worten.",
            lang,
        ),
        "bullets": [
            _text("Source comes first, then the Google link, then the appointment details.", "Zuerst kommt die Quelle, dann die Google-Verbindung und dann die Termindetails.", lang),
            _text("The policy decides when the reminders are sent.", "Die Policy entscheidet, wann die Erinnerungen gesendet werden.", lang),
            _text("Preview and jobs show what will happen next.", "Vorschau und Jobs zeigen, was als Nächstes passiert.", lang),
        ],
        "flow_steps": [
            _text("Open the source page and check the Google linkage.", "Die Quellseite oeffnen und die Google-Verbindung pruefen.", lang),
            _text("Open the details page and read the appointment data.", "Die Detailseite oeffnen und die Termindaten lesen.", lang),
            _text("Open the policy and preview pages to see the reminder plan.", "Die Policy- und Vorschauseiten oeffnen, um den Erinnerungsplan zu sehen.", lang),
            _text("Open jobs and health to confirm the runtime is ready.", "Jobs und Health oeffnen, um die Laufzeit zu pruefen.", lang),
        ],
    }


def build_v136_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    payload = {
        "version": "v1.3.6",
        "ui_meta": {
            "tagline": _text(
                "Combined appointment source, Google linkage, reminder policy, reminder preview, jobs, and health in one cockpit.",
                "Kombinierte Terminquelle, Google-Verknuepfung, Reminder-Policy, Vorschau, Jobs und Health in einem Cockpit.",
                language,
            ),
            "accent": "amber",
            "role": "admin-console",
        },
        "pages": [
            {"id": "dashboard", "label": _text("Dashboard", "Dashboard", language)},
            {"id": "source", "label": _text("Source", "Quelle", language)},
            {"id": "details", "label": _text("Details", "Details", language)},
            {"id": "policy", "label": _text("Policy", "Policy", language)},
            {"id": "preview", "label": _text("Preview", "Vorschau", language)},
            {"id": "jobs", "label": _text("Jobs", "Jobs", language)},
            {"id": "health", "label": _text("Health", "Health", language)},
            {"id": "help", "label": _text("Help", "Hilfe", language)},
        ],
        "dashboard_summary": {
            "title": _text("Combined reminder cockpit", "Kombiniertes Reminder-Cockpit", language),
            "subtitle": _text(
                "The operator can see the source, the Google link, the appointment, the policy, the preview, the jobs, and the health in one place.",
                "Der Operator sieht Quelle, Google-Verbindung, Termin, Policy, Vorschau, Jobs und Health an einem Ort.",
                language,
            ),
            "metrics": [
                {"label": _text("Appointment source", "Terminquelle", language), "value": "Google Calendar"},
                {"label": _text("Google linkage", "Google-Verknuepfung", language), "value": _text("connected", "verbunden", language)},
                {"label": _text("Reminder offsets", "Reminder-Abstaende", language), "value": "24h / 2h / 30m"},
                {"label": _text("Silence threshold", "Silence Threshold", language), "value": "1300 ms"},
                {"label": _text("Reminder jobs", "Reminder Jobs", language), "value": "4"},
                {"label": _text("Runtime", "Laufzeit", language), "value": _text("healthy", "gesund", language)},
            ],
        },
        "appointment_source": _appointment_source(language),
        "google_linkage": _google_linkage(language),
        "appointment_details": _appointment_details(language),
        "reminder_policy": _reminder_policy(language),
        "reminder_preview": _reminder_preview(language),
        "reminder_jobs": _reminder_jobs(language),
        "runtime_health": _runtime_health(language),
        "current_story": _demo_stories(language)[0],
        "demo_stories": _demo_stories(language),
        "operator_summary": _operator_summary(language),
        "help_links": [
            {"label": _text("User Guide", "User Guide", language), "href": f"/docs/user?lang={language}"},
            {"label": _text("Demo Guide", "Demo Guide", language), "href": f"/docs/demo?lang={language}"},
            {"label": _text("Admin Guide", "Admin Guide", language), "href": f"/docs/admin?lang={language}"},
        ],
        "ui_api_links": [
            "/api/reminder-ui/v1.3.6/payload",
            "/api/reminder-ui/v1.3.6/help",
            "/api/reminder-ui/v1.3.6/config",
            "/api/reminder-ui/v1.3.6/config/preview",
            "/api/reminder-ui/v1.3.6/jobs",
            "/api/reminder-ui/v1.3.6/health",
        ],
        "api_links": [
            "/api/reminder-ui/v1.3.6/payload",
            "/api/reminder-ui/v1.3.6/help",
            "/api/reminder-ui/v1.3.6/config",
            "/api/reminder-ui/v1.3.6/config/preview",
            "/api/reminder-ui/v1.3.6/jobs",
            "/api/reminder-ui/v1.3.6/health",
        ],
        "docs_highlights": [
            _text(
                "The docs explain the source, the Google link, the reminder rules, and the job list in simple language.",
                "Die Doku erklaert Quelle, Google-Verknuepfung, Reminder-Regeln und Job-Liste in einfacher Sprache.",
                language,
            ),
            _text(
                "The demo guide gives three short stories that are easy to present.",
                "Der Demo-Guide liefert drei kurze Storys, die man leicht praesentieren kann.",
                language,
            ),
            _text(
                "The admin guide lists the parameters and explains each one in plain words.",
                "Der Admin-Guide listet die Parameter auf und erklaert jeden Punkt in einfachen Worten.",
                language,
            ),
            _text(
                "Silence Threshold defaults to 1300 ms and is visible in the cockpit.",
                "Silence Threshold hat standardmaessig 1300 ms und ist im Cockpit sichtbar.",
                language,
            ),
        ],
        "parameter_explanations": [
            {
                "name": "silence_threshold_ms",
                "value": "1300",
                "description": _text(
                    "How long the system waits before it decides that the user stopped speaking.",
                    "Wie lange das System wartet, bevor es entscheidet, dass der Nutzer nicht mehr spricht.",
                    language,
                ),
            },
            {
                "name": "reminder_offsets_minutes",
                "value": "1440, 120, 30",
                "description": _text(
                    "The minutes before the appointment when reminders are planned.",
                    "Die Minuten vor dem Termin, zu denen Erinnerungen geplant werden.",
                    language,
                ),
            },
            {
                "name": "google_calendar_id",
                "value": "appointment-agent-test-calendar",
                "description": _text(
                    "The calendar that receives the linked appointment in the demo.",
                    "Der Kalender, der im Demo-Fall den verknuepften Termin bekommt.",
                    language,
                ),
            },
            {
                "name": "appointment_type",
                "value": "dentist",
                "description": _text(
                    "The type of appointment, for example dentist, wallbox, gas meter, or water meter.",
                    "Die Terminart, zum Beispiel Zahnarzt, Wallbox, Gaszaehler oder Wasserzaehler.",
                    language,
                ),
            },
            {
                "name": "job_status",
                "value": "planned / updated / cancelled / sent",
                "description": _text(
                    "The current state of each reminder job.",
                    "Der aktuelle Zustand jedes Reminder Jobs.",
                    language,
                ),
            },
        ],
        "status_overview": {
            "planned": 3,
            "updated": 1,
            "cancelled": 1,
            "sent": 1,
            "skipped": 0,
            "failed": 0,
        },
    }
    return deepcopy(payload)
