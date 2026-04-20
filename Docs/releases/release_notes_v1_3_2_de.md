# Release Notes v1.3.2

Version: v1.3.2
Language: DE

## Was sich geaendert hat

- Reminder-Scheduler-UI-Linie nah an `v1.3.1` beibehalten
- eine kleine `Time`-Seite hinzugefuegt, damit Zeitzone und Sommerzeit sichtbar sind
- nahe Erinnerungen im Cockpit sichtbar gemacht, ohne den Stil zu aendern
- Seite fuer Reminder-Regeln beibehalten
- Live-Vorschau fuer Reminder beibehalten
- Uebersicht fuer Reminder-Jobs beibehalten
- Lifecycle-Tab mit planned, dispatching, sent, failed, skipped und cancelled beibehalten
- Admin-Guide, User-Guide, Demo-Guide und Release Notes in einfacher Sprache erweitert
- Incident-Shell und einfache Operator-Sprache beibehalten

## Warum das wichtig ist

- Reminder-Planung ist jetzt leichter erklaerbar
- der Operator sieht Regel, Vorschau, Jobs und Lifecycle-Zustaende an einem Ort
- der Operator sieht auch Zeitzone und Sommerzeit an einem Ort
- die Plattform ist bereit fuer den naechsten Backend-Schritt

## Verifikation

- UI-Route: `/ui/reminder-scheduler/v1.3.2`
- UI-Payload-Route: `/api/reminder-ui/v1.3.2/payload`
- Config-Route: `/api/reminders/v1.3.2/config`
- Preview-Route: `/api/reminders/v1.3.2/config/preview`
- Jobs-Route: `/api/reminders/v1.3.2/jobs`
- Health-Route: `/api/reminders/v1.3.2/health`
