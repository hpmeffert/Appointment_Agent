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
        "sync_window_days": 7,
        "polling_interval_minutes": 30,
        "hash_detection_enabled": True,
        "idempotency_guard": True,
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
            "sync_window_days": "Sync window days" if lang == "en" else "Sync-Fenster Tage",
            "polling_interval_minutes": "Polling interval minutes" if lang == "en" else "Polling-Intervall Minuten",
            "hash_detection_enabled": "Hash detection" if lang == "en" else "Hash-Erkennung",
            "idempotency_guard": "Idempotency guard" if lang == "en" else "Idempotenz-Schutz",
            "channel_email": "Email channel" if lang == "en" else "E-Mail-Kanal",
            "channel_voice": "Voice channel" if lang == "en" else "Voice-Kanal",
            "channel_rcs_sms": "RCS/SMS channel" if lang == "en" else "RCS/SMS-Kanal",
        },
    }


def build_v133_payload(lang: str = "en") -> dict:
    language = "de" if lang == "de" else "en"
    payload = {
        "version": "v1.3.3",
        "ui_meta": {
            "tagline": (
                "Reminder Scheduler Setup UI with clear policies, lifecycle visibility, sync strategy, and change detection."
                if language == "en"
                else "Reminder Scheduler Setup UI mit klaren Regeln, Lifecycle-Sichtbarkeit, Sync-Strategie und Change Detection."
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
            {"id": "sync", "label": "Sync" if language == "en" else "Sync"},
            {"id": "help", "label": "Help" if language == "en" else "Hilfe"},
        ],
        "reminder_setup": _default_setup(language),
        "appointment_example": _sample_appointment(language),
        "scheduler_overview": {
            "title": "How Reminder Scheduler Works" if language == "en" else "So funktioniert der Reminder Scheduler",
            "subtitle": (
                "The system reads appointments, detects changes, keeps sync windows in view, creates jobs, shows lifecycle states, and dispatches them safely."
                if language == "en"
                else "Das System liest Termine, erkennt Aenderungen, behält Sync-Fenster im Blick, erzeugt Jobs, zeigt Lifecycle-Zustaende und versendet sie sicher."
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
                    "title": "Sync Strategy" if language == "en" else "Sync-Strategie",
                    "body": (
                        "The cockpit shows the sync window, hash detection, and idempotency guard so repeated runs stay safe."
                        if language == "en"
                        else "Das Cockpit zeigt Sync-Fenster, Hash-Erkennung und Idempotenz-Schutz, damit wiederholte Läufe sicher bleiben."
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
            "sync windows, hashes, and idempotency checks stay visible",
        ],
        "demo_stories": [
            {
                "id": "sync-new",
                "title": "Story 1: New appointment sync" if language == "en" else "Story 1: Neue Termin-Synchronisation",
                "business_value": (
                    "A new appointment comes in through the sync window, is normalized, and creates reminder jobs without duplicates."
                    if language == "en"
                    else "Ein neuer Termin kommt ueber das Sync-Fenster rein, wird normalisiert und erzeugt Reminder-Jobs ohne Duplikate."
                ),
                "wow_effect": (
                    "The operator sees the new appointment, the hash check, and the created reminder plan in one glance."
                    if language == "en"
                    else "Der Operator sieht den neuen Termin, die Hash-Pruefung und den erzeugten Reminder-Plan auf einen Blick."
                ),
            },
            {
                "id": "sync-update",
                "title": "Story 2: Update sync" if language == "en" else "Story 2: Update-Sync",
                "business_value": (
                    "A changed appointment updates the reminder plan in a predictable way and keeps old jobs out of the list."
                    if language == "en"
                    else "Ein geaenderter Termin aktualisiert den Reminder-Plan vorhersehbar und haelt alte Jobs aus der Liste heraus."
                ),
                "wow_effect": (
                    "The cockpit shows why the plan changed and keeps the list free of duplicates."
                    if language == "en"
                    else "Das Cockpit zeigt, warum sich der Plan geaendert hat, und haelt die Liste frei von Duplikaten."
                ),
            },
            {
                "id": "sync-cancel",
                "title": "Story 3: Cancel sync" if language == "en" else "Story 3: Cancel-Sync",
                "business_value": (
                    "A cancelled appointment stops the reminder plan cleanly and makes the change easy to understand."
                    if language == "en"
                    else "Ein stornierter Termin stoppt den Reminder-Plan sauber und macht die Aenderung leicht verstaendlich."
                ),
                "wow_effect": (
                    "The operator sees the cancel reason and the reminder jobs disappear in a predictable way."
                    if language == "en"
                    else "Der Operator sieht den Storno-Grund und die Reminder-Jobs verschwinden auf vorhersehbare Weise."
                ),
            },
        ],
        "sync_awareness": {
            "adapter_name": "calendar-adapter",
            "sync_window_days": 7,
            "polling_interval_minutes": 30,
            "hash_detection_enabled": True,
            "idempotency_guard": True,
            "notes": [
                (
                    "Repeated sync runs should not create duplicate appointments or duplicate reminder jobs."
                    if language == "en"
                    else "Wiederholte Sync-Läufe sollen keine doppelten Termine oder doppelten Reminder-Jobs erzeugen."
                ),
                (
                    "Hash comparison helps the platform notice new, changed, or cancelled appointments quickly."
                    if language == "en"
                    else "Der Hash-Vergleich hilft der Plattform, neue, geaenderte oder stornierte Termine schnell zu erkennen."
                ),
            ],
        },
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
            {"id": "sync", "label": "Sync" if language == "en" else "Sync"},
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
            "/api/reminder-ui/v1.3.3/payload",
            "/api/reminder-ui/v1.3.3/help",
            "/api/reminder-ui/v1.3.3/config",
            "/api/reminder-ui/v1.3.3/config/preview",
            "/api/reminder-ui/v1.3.3/jobs",
        ],
        "api_links": [
            "/api/reminders/v1.3.3/config",
            "/api/reminders/v1.3.3/config/preview",
            "/api/reminders/v1.3.3/jobs",
            "/api/reminders/v1.3.3/rebuild",
            "/api/reminders/v1.3.3/health",
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
