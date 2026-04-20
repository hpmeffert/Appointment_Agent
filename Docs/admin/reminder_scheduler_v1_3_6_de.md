# Reminder Scheduler v1.3.6

Version: v1.3.6
Audience: Admin
Language: DE

## Ziel dieses Patches

`v1.3.6` ist ein kombiniertes Demonstrator-Cockpit und eine Bruecken-Release-Linie.

Es zeigt den ganzen Weg in einer Ansicht:
- woher der Termin kommt
- wie der Termin mit Google Calendar verbunden ist
- welche Termindaten gespeichert sind
- welche Reminder-Policy aktiv ist
- wie die Reminder-Vorschau aussieht
- welche Reminder Jobs existieren
- ob die Laufzeit gesund ist

Das Cockpit behält den bekannten Incident-Stil und bleibt einfach lesbar.
Zusaetzlich gibt es sichere Demo-APIs, die Google-Quelle, normalisierten Termin und reminder-faehige Sicht getrennt zeigen.

## Seiten im Cockpit

- `Dashboard`
  Zeigt die Kurzuebersicht und die drei Storys.
- `Source`
  Zeigt die Terminquelle und die Google-Verknuepfung.
- `Details`
  Zeigt die Termindaten.
- `Policy`
  Zeigt die Reminder-Policy und die wichtigsten Regeln.
- `Preview`
  Zeigt die Vorschau und die Reminder-Reihenfolge.
- `Jobs`
  Zeigt die Reminder Jobs und ihren Status.
- `Health`
  Zeigt die Laufzeit und die Diagnose.
- `Help`
  Zeigt Links und Parameter-Erklaerungen.

## Wichtige Parameter

- `appointment_source_system`
  Das System, aus dem der Termin kommt.
- `google_calendar_id`
  Der Google-Kalender fuer den verknuepften Termin.
- `google_link_status`
  Zeigt, ob die Google-Verbindung aktiv ist.
- `appointment_type`
  Die Art des Termins, zum Beispiel Zahnarzt oder Wallbox.
- `appointment_start`
  Der Startzeitpunkt des Termins.
- `timezone`
  Die Zeitzone des Termins.
- `reminder_offsets_minutes`
  Wann die Erinnerungen vor dem Termin geplant werden.
- `silence_threshold_ms`
  Wie lange das System wartet, bis es denkt, dass der Nutzer aufgehört hat zu sprechen.
  Der Standard ist `1300 ms`.
- `quiet_hours`
  Der Zeitbereich, in dem keine Erinnerung gesendet werden soll.
- `reminder_channels`
  Die Kanaele fuer die Erinnerungen.
- `max_retries`
  Wie oft ein erneuter Versuch erlaubt ist.
- `job_status`
  Der Zustand eines Reminder Jobs, zum Beispiel geplant, aktualisiert, abgebrochen oder gesendet.
- `next_due_at`
  Der naechste Zeitpunkt, an dem ein Job faellig ist.
- `db_status`
  Zeigt, ob die Datenbank gesund ist.
- `worker_status`
  Zeigt, ob der Worker bereit ist.

## Demo-Storys

Das Cockpit enthaelt drei kurze Demo-Storys:
- ein neuer Termin kommt aus Google
- der Termin wird verschoben
- der Termin wird abgesagt

## API-Routen fuer diese Linie

- `GET /ui/reminder-scheduler/v1.3.6`
- `GET /api/reminder-ui/v1.3.6/payload`
- `GET /api/reminder-ui/v1.3.6/help`
- `GET /api/reminder-ui/v1.3.6/config`
- `GET /api/reminder-ui/v1.3.6/config/preview`
- `GET /api/reminder-ui/v1.3.6/jobs`
- `GET /api/reminder-ui/v1.3.6/health`
- `GET /api/reminders/v1.3.6/linkage/demo`
- `GET /api/reminders/v1.3.6/linkage/reminder-preview`
- `GET /api/google/v1.3.6/linkage/demo`
- `GET /api/google/v1.3.6/linkage/stories`

## Was der Admin pruefen soll

1. Der Header zeigt `v1.3.6`.
2. Die Seiten zeigen Source, Google-Link, Details, Policy, Preview, Jobs und Health.
3. Die Help-Seite erklaert die Parameter in einfachen Worten.
4. Die drei Storys sind sichtbar und kurz genug fuer eine schnelle Demo.
