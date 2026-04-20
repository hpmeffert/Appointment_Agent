# Release Notes v1.3.1

Version: v1.3.1
Language: DE

## Was sich geaendert hat

- Reminder-Scheduler-UI-Linie beibehalten und Lifecycle-Zustaende sichtbarer gemacht
- Seite fuer Reminder-Regeln hinzugefuegt
- Live-Vorschau fuer Reminder hinzugefuegt
- Uebersicht fuer Reminder-Jobs hinzugefuegt
- Lifecycle-Tab mit planned, dispatching, sent, failed, skipped und cancelled hinzugefuegt
- Admin-Guide, User-Guide, Demo-Guide und Release Notes neu angelegt
- Incident-Shell und einfache Operator-Sprache beibehalten

## Warum das wichtig ist

- Reminder-Planung ist jetzt leichter erklaerbar
- der Operator sieht Regel, Vorschau, Jobs und Lifecycle-Zustaende an einem Ort
- die Plattform ist bereit fuer den naechsten Backend-Schritt

## Verifikation

- UI-Route: `/ui/reminder-scheduler/v1.3.1`
- UI-Payload-Route: `/api/reminder-ui/v1.3.1/payload`
- Config-Route: `/api/reminders/v1.3.1/config`
- Preview-Route: `/api/reminders/v1.3.1/config/preview`
- Jobs-Route: `/api/reminders/v1.3.1/jobs`
- Health-Route: `/api/reminders/v1.3.1/health`
