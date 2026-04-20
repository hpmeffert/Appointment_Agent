# Release Notes v1.3.5

Version: v1.3.5
Language: DE

## Was neu ist

- Das Reminder-Cockpit zeigt jetzt Delivery-Kanaele auf einfache Weise.
- Das Cockpit zeigt Validation-Ergebnisse in klaren Worten.
- Das Cockpit zeigt Delivery-Ergebnisse in einer Result-Timeline.
- Die Health-Sicht zeigt jetzt Runtime-Status, letzte Aktivitaet und den naechsten faelligen Schritt.
- Die Doku ist jetzt so geschrieben, dass ein motivierter 16-Jaehriger sie verstehen kann.
- Der Demo-Guide hat jetzt drei kurze Delivery-Stories.

## Wichtige Routen

- `GET /ui/reminder-scheduler/v1.3.5`
- `GET /api/reminder-ui/v1.3.5/payload`
- `GET /api/reminder-ui/v1.3.5/help`
- `GET /api/reminder-ui/v1.3.5/config`
- `GET /api/reminder-ui/v1.3.5/config/preview`
- `GET /api/reminder-ui/v1.3.5/results`
- `GET /api/reminder-ui/v1.3.5/health`

## Pruefung

- Die UI rendert mit der neuen Delivery-Sprache.
- Das Payload liefert mindestens drei Demo-Stories.
- Die Hilfe zeigt die wichtigen Parameter.
- Die Tests decken UI, Payload, Help, Config, Preview, Results und Health ab.
