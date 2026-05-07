# Release Notes v1.3.10 (DE)

## Zusammenfassung
Version `v1.3.10` führt eine sicherere Terminidentifikation und ausschließlich zukunftsgültige Slot-Vorschläge für den Appointment-Agent-Demonstrator und die Orchestrierungs-Pfade ein.

## Highlights
- Stärkere Eingaben für die Terminidentifikation:
  - Reservierungsähnliche Referenz
  - Appointment- oder Kalenderreferenz
  - Correlation-Referenz
  - Kundennummer
  - normalisierte Telefonnummer
- Explizite Termin-Auswahl bei mehreren passenden Terminen vor `Bestaetigen`, `Absagen` oder `Verschieben`.
- Zukunftsfilter für Slot-Vorschläge mit einer Default-Mindestvorlaufzeit von `30 Minuten`.
- Erneute Validierung des ausgewählten Slots vor der Mutation.
- Geschützte `v1.x`-Single-Match-Flows bleiben erhalten.

## Sicherheit
- Keine Mutation bei mehrdeutigem Zieltermin
- Keine Mutation bei `no match`
- Keine veralteten oder bereits abgelaufenen Same-Day-Slots
- Silence Threshold Default bleibt `1300 ms`

## Dokumentation
- Benutzerleitfaden aktualisiert
- Demo Leitfaden mit 3 Stories ergänzt
- Admin Leitfaden aktualisiert
- Release Notes in DE und EN ergänzt
