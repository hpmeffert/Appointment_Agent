from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone


def _sample_appointment(lang: str) -> dict:
    appointment_start = datetime(2026, 4, 20, 10, 0, tzinfo=timezone(timedelta(hours=2)))
    return {
        "appointment_id": "appt-reminder-1001",
        "title": "Reminder Scheduler Pilot" if lang == "en" else "Reminder Scheduler Pilot",
        "customer_name": "Anna Demo" if lang == "en" else "Anna Demo",
        "timezone": "Europe/Berlin",
        "start_at": appointment_start.isoformat(),
        "display_date": "2026-04-20",
        "display_time": "10:00",
    }


def _default_setup(lang: str) -> dict:
    return {
        "enabled": True,
        "mode": "manual",
        "reminder_count": 1,
        "first_reminder_hours_before": 24,
        "second_reminder_hours_before": 48,
        "third_reminder_hours_before": 72,
        "max_span_between_first_and_last_reminder_hours": 24,
        "last_reminder_gap_before_appointment_hours": 24,
        "enforce_max_span": True,
        "preload_window_hours": 168,
        "channel_email_enabled": True,
        "channel_voice_enabled": False,
        "channel_rcs_sms_enabled": True,
        "labels": {
            "enabled": "Enabled" if lang == "en" else "Aktiviert",
            "mode": "Mode" if lang == "en" else "Modus",
            "reminder_count": "Reminder Count" if lang == "en" else "Anzahl Erinnerungen",
            "first": "First reminder hours before" if lang == "en" else "Erste Erinnerung Stunden vor Termin",
            "second": "Second reminder hours before" if lang == "en" else "Zweite Erinnerung Stunden vor Termin",
            "third": "Third reminder hours before" if lang == "en" else "Dritte Erinnerung Stunden vor Termin",
            "max_span": "Max span between first and last" if lang == "en" else "Maximale Spanne zwischen erster und letzter",
            "last_gap": "Last reminder gap before appointment" if lang == "en" else "Letzter Abstand vor dem Termin",
            "enforce_span": "Enforce max span" if lang == "en" else "Maximale Spanne erzwingen",
            "preload_window": "Preload window hours" if lang == "en" else "Vorladefenster Stunden",
            "channel_email": "Email channel" if lang == "en" else "E-Mail-Kanal",
            "channel_voice": "Voice channel" if lang == "en" else "Voice-Kanal",
            "channel_rcs_sms": "RCS/SMS channel" if lang == "en" else "RCS/SMS-Kanal",
        },
    }


def build_v130_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    payload = {
        "version": "v1.3.1",
        "ui_meta": {
            "tagline": (
                "Reminder Scheduler Setup UI with clear policies, lifecycle visibility, preview, and safe planning."
                if language == "en"
                else "Reminder Scheduler Setup UI mit klaren Regeln, Lifecycle-Sichtbarkeit, Vorschau und sicherer Planung."
            ),
            "accent": "amber",
            "role": "admin-console",
        },
        "pages": [
            {"id": "dashboard", "label": "Dashboard" if language == "en" else "Dashboard"},
            {"id": "setup", "label": "Setup" if language == "en" else "Setup"},
            {"id": "preview", "label": "Preview" if language == "en" else "Vorschau"},
            {"id": "jobs", "label": "Jobs" if language == "en" else "Jobs"},
            {"id": "lifecycle", "label": "Lifecycle" if language == "en" else "Lifecycle"},
            {"id": "help", "label": "Help" if language == "en" else "Hilfe"},
        ],
        "reminder_setup": _default_setup(language),
        "appointment_example": _sample_appointment(language),
        "scheduler_overview": {
            "title": "How Reminder Scheduler Works" if language == "en" else "So funktioniert der Reminder Scheduler",
            "subtitle": (
                "The system reads appointments, calculates reminder times, creates jobs, shows lifecycle states, and dispatches them safely."
                if language == "en"
                else "Das System liest Termine, berechnet Erinnerungszeiten, erzeugt Jobs, zeigt Lifecycle-Zustaende und versendet sie sicher."
            ),
            "cards": [
                {
                    "title": "Policy" if language == "en" else "Regelwerk",
                    "body": (
                        "The saved reminder policy says how many reminders to create and how far before the appointment they belong."
                        if language == "en"
                        else "Die gespeicherte Regel sagt, wie viele Erinnerungen es gibt und wie weit sie vor dem Termin liegen."
                    ),
                },
                {
                    "title": "Planner" if language == "en" else "Planer",
                    "body": (
                        "The planning loop checks appointments and creates reminder jobs in advance."
                        if language == "en"
                        else "Die Planungs-Schleife prueft Termine und erzeugt Erinnerungs-Jobs im Voraus."
                    ),
                },
                {
                    "title": "Dispatcher" if language == "en" else "Dispatcher",
                    "body": (
                        "The dispatch loop sends due reminders and records what happened."
                        if language == "en"
                        else "Die Versand-Schleife sendet faellige Erinnerungen und protokolliert das Ergebnis."
                    ),
                },
                {
                    "title": "Lifecycle" if language == "en" else "Lifecycle",
                    "body": (
                        "The operator can see planned, dispatching, sent, failed, skipped, and cancelled jobs at a glance."
                        if language == "en"
                        else "Der Operator sieht geplante, versendende, gesendete, fehlgeschlagene, uebersprungene und stornierte Jobs auf einen Blick."
                    ),
                },
            ],
        },
        "validation_rules": [
            "0 to 3 reminders only",
            "hours must be greater or equal to zero",
            "reminders must be ordered from farthest to nearest",
            "max span must be respected when enabled",
            "job lifecycle states stay visible in the cockpit",
        ],
        "demo_stories": [
            {
                "id": "single-reminder",
                "title": "Story 1: One reminder" if language == "en" else "Story 1: Eine Erinnerung",
                "business_value": (
                    "A simple policy sends one reminder 24 hours before the appointment."
                    if language == "en"
                    else "Eine einfache Regel sendet eine Erinnerung 24 Stunden vor dem Termin."
                ),
                "wow_effect": (
                    "The operator can explain the reminder in one sentence and still see the live preview."
                    if language == "en"
                    else "Der Operator kann die Erinnerung in einem Satz erklaeren und sieht trotzdem die Live-Vorschau."
                ),
            },
            {
                "id": "manual-sequence",
                "title": "Story 2: Manual three-step sequence" if language == "en" else "Story 2: Manuelle Dreierserie",
                "business_value": (
                    "A team can define 72h, 48h, and 24h reminders manually and still see the lifecycle state summary."
                    if language == "en"
                    else "Ein Team kann 72h, 48h und 24h Erinnerungen manuell festlegen und sieht trotzdem die Lifecycle-Zustandsuebersicht."
                ),
                "wow_effect": (
                    "The preview shows the exact reminder order and the final gap before the appointment."
                    if language == "en"
                    else "Die Vorschau zeigt die genaue Reihenfolge und den letzten Abstand vor dem Termin."
                ),
            },
            {
                "id": "auto-distributed",
                "title": "Story 3: Auto distributed reminders" if language == "en" else "Story 3: Automatisch verteilte Erinnerungen",
                "business_value": (
                    "The system can spread reminders automatically when the operator only defines the count and constraints, while the job states remain easy to read."
                    if language == "en"
                    else "Das System kann Erinnerungen automatisch verteilen, wenn nur Anzahl und Regeln definiert sind, waehrend die Job-Zustaende lesbar bleiben."
                ),
                "wow_effect": (
                    "The calculated schedule appears immediately, so the operator can see the whole plan before saving."
                    if language == "en"
                    else "Der berechnete Zeitplan erscheint sofort, damit der Operator alles vor dem Speichern sieht."
                ),
            },
        ],
        "lifecycle_states": [
            "planned",
            "dispatching",
            "sent",
            "failed",
            "skipped",
            "cancelled",
        ],
        "setup_tabs": [
            {"id": "general", "label": "General" if language == "en" else "Allgemein"},
            {"id": "channels", "label": "Channels" if language == "en" else "Kanaele"},
            {"id": "validation", "label": "Validation" if language == "en" else "Pruefung"},
            {"id": "lifecycle", "label": "Lifecycle" if language == "en" else "Lifecycle"},
        ],
        "help_links": [
            {"label": "User Guide", "href": "/docs/user?lang=en"},
            {"label": "Demo Guide", "href": "/docs/demo?lang=en"},
            {"label": "Admin Guide", "href": "/docs/admin?lang=en"},
        ],
        "ui_api_links": [
            "/api/reminder-ui/v1.3.1/payload",
            "/api/reminder-ui/v1.3.1/help",
            "/api/reminder-ui/v1.3.1/config",
            "/api/reminder-ui/v1.3.1/config/preview",
            "/api/reminder-ui/v1.3.1/jobs",
        ],
        "api_links": [
            "/api/reminders/v1.3.1/config",
            "/api/reminders/v1.3.1/config/preview",
            "/api/reminders/v1.3.1/jobs",
            "/api/reminders/v1.3.1/rebuild",
            "/api/reminders/v1.3.1/health",
        ],
        "docs_highlights": [
            (
                "The docs explain the reminder policy in plain language."
                if language == "en"
                else "Die Doku erklaert die Reminder-Regeln in einfacher Sprache."
            ),
            (
                "The demo guide includes three presenter stories."
                if language == "en"
                else "Der Demo-Guide enthaelt drei Presenter-Stories."
            ),
            (
                "The admin guide explains every parameter with examples."
                if language == "en"
                else "Der Admin-Guide erklaert jeden Parameter mit Beispielen."
            ),
        ],
        "sample_jobs": [
            {
                "job_id": "job-reminder-001",
                "sequence": 1,
                "scheduled_for": "2026-04-19T10:00:00+02:00",
                "status": "planned",
                "channel": "email",
            },
            {
                "job_id": "job-reminder-002",
                "sequence": 2,
                "scheduled_for": "2026-04-20T08:00:00+02:00",
                "status": "dispatching",
                "channel": "rcs_sms",
            },
            {
                "job_id": "job-reminder-003",
                "sequence": 3,
                "scheduled_for": "2026-04-20T09:30:00+02:00",
                "status": "sent",
                "channel": "voice",
            },
            {
                "job_id": "job-reminder-004",
                "sequence": 1,
                "scheduled_for": "2026-04-18T09:30:00+02:00",
                "status": "failed",
                "channel": "email",
            },
            {
                "job_id": "job-reminder-005",
                "sequence": 2,
                "scheduled_for": "2026-04-18T08:30:00+02:00",
                "status": "cancelled",
                "channel": "rcs_sms",
            },
        ],
    }
    return deepcopy(payload)
