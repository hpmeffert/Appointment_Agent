# Demo Guide v1.4.0

## Ueberblick

`v1.4.0` ist die erste Freigabe, in der der Appointment Agent als durchgaengiges End-to-End-System demonstriert werden kann.

## Demo-Einstieg

- Cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.9`
- Aktuelle Patch-Linie: `http://localhost:8080/ui/demo-monitoring/v1.3.9-patch9`

## Story-Szenario 1 — Reminder bestaetigen

1. Im Real-Mode starten
2. Einen Reminder senden
3. `Confirm` auswaehlen
4. Den finalen Bestaetigungsstatus im Dashboard pruefen

## Story-Szenario 2 — Vollstaendiger Reschedule-Flow

1. Einen Reminder senden
2. `Reschedule` auswaehlen
3. Ein Scheduling-Fenster auswaehlen
4. Ein dynamisches Datum auswaehlen
5. Eine dynamische Uhrzeit auswaehlen
6. `Confirm` auswaehlen
7. Das Google-Calendar-Event pruefen

## Story-Szenario 3 — Address- und Kalenderqualitaet

1. Einen echten Reschedule-Flow fuer eine verknuepfte Adresse durchfuehren
2. Das Google-Calendar-Titelformat pruefen
3. Die Adresszeilen in der Beschreibung pruefen
4. Die Linkage-Metadaten pruefen

## Story-Szenario 4 — Zeitzonenvalidierung

1. Eine Adresse mit `Europe/Berlin` verwenden
2. Einen lokalen Slot wie `14:00` auswaehlen
3. Den Termin bestaetigen
4. Pruefen, dass das Google-Calendar-Event bei `14:00` bleibt

## Demo-Hinweise

- Fuer den produktionsnahen Flow den Real-Mode verwenden
- Der Scenario-Mode bleibt fuer gefuehrte Simulation verfuegbar
- UX-Verbesserungen werden bewusst auf `v1.5.0` verschoben
