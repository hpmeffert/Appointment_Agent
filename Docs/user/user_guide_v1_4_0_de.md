# User Guide v1.4.0

## Was v1.4.0 bietet

`v1.4.0` ist die erste funktional produktionsreife Freigabe des Appointment Agent.

Es kann jetzt eine komplette Termin-Journey mit echtem Messaging, echter Callback-Verarbeitung, dynamischer Verfuegbarkeit und Google-Calendar-Booking ausgefuehrt werden.

## Zentrale Nutzerfluesse

- Reminder auf dem Mobilgeraet erhalten
- `Reschedule` auswaehlen
- Ein Zeitfenster wie `This week` oder `Next week` auswaehlen
- Eines der angebotenen Daten auswaehlen
- Eine der angebotenen Uhrzeiten auswaehlen
- Den Termin bestaetigen
- Die finale Bestaetigung erhalten

## Erwartetes Verhalten

- Buttons erscheinen auf dem Mobilgeraet als interaktive Reply-Buttons
- Vorgeschlagene Daten und Uhrzeiten kommen aus der echten Google-Verfuegbarkeitslogik
- Bestaetigte Buchungen werden in Google Calendar geschrieben
- Event-Titel verwenden den Kundennamen
- Event-Beschreibungen enthalten Adresse und Kontext
- Lokale Zeitzonenbehandlung wird fuer unterstuetzte Address-Datensaetze angewendet

## Wichtige Einstiegspunkte

- Demo-Cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.9`
- Aktuelles Patch-Cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.9-patch9`
- Help: `http://localhost:8080/help`
- Health: `http://localhost:8080/health`

## Hinweise

- Die sichtbare App-Release-Version ist `v1.4.0`
- Die Cockpit-Route bleibt auf dem stabilen Pfad `v1.3.9`
- UX-Verbesserungen sind fuer `v1.5.0` geplant
