# Release Notes Reminder Scheduler v1.3.6

Version: v1.3.6
Language: DE

## Zusammenfassung

`v1.3.6` ist ein kombiniertes Demonstrator- und Bruecken-Release.

Sie macht das Reminder-Cockpit zu einem kombinierten Demonstrator fuer:
- Terminquelle
- Google-Verknuepfung
- Termindaten
- Reminder-Policy
- Reminder-Vorschau
- Reminder Jobs
- Health und Diagnose

## Was sich geaendert hat

- Das Cockpit zeigt jetzt den ganzen Weg von der Terminquelle bis zu den Jobs.
- Google-Linkage-Demo-Endpunkte und Reminder-Linkage-Demo-Endpunkte sind jetzt in derselben Release-Linie verfuegbar.
- Das bekannte visuelle Design bleibt erhalten.
- Header und Help zeigen die Version sichtbar an.
- Die Texte sind einfach und gut erklaert.
- Die Doku erklaert die Parameter in klaren Worten.
- Der Demo-Guide enthaelt drei kurze Storys.

## Wichtige Parameter

- `silence_threshold_ms`
  Standard ist `1300 ms`.
- `reminder_offsets_minutes`
  Die geplanten Zeiten vor dem Termin.
- `google_calendar_id`
  Der Kalender fuer den verknuepften Termin.
- `appointment_type`
  Die Art des Termins.
- `job_status`
  Der Zustand eines Reminder Jobs.

## Was in dieser Version enthalten ist

- UI-Route: `/ui/reminder-scheduler/v1.3.6`
- Payload-Route: `/api/reminder-ui/v1.3.6/payload`
- Help-Route: `/api/reminder-ui/v1.3.6/help`
- Config-Route: `/api/reminder-ui/v1.3.6/config`
- Preview-Route: `/api/reminder-ui/v1.3.6/config/preview`
- Jobs-Route: `/api/reminder-ui/v1.3.6/jobs`
- Health-Route: `/api/reminder-ui/v1.3.6/health`

## Hinweise fuer das Team

- Das Look and Feel soll stabil bleiben.
- Die Erklaerungen sollen kurz und klar bleiben.
- Die Version soll im Produkt und in der Help sichtbar sein.
