# Appointment Agent Admin Leitfaden v1.3.10 (DE)

## Release-Ziel
`v1.3.10` haertet die Terminidentifikation und die zukunftsgueltige Slot-Behandlung im Demonstrator und in den Orchestrierungs-Pfaden.

## Admin-relevante Änderungen
- Terminidentifikation unterstützt stärkere referenzbasierte Auflösung
- mehrere passende Termine erfordern vor jeder Mutation eine explizite Auswahl
- Slot-Vorschläge laufen durch einen Future-Only-Sicherheitsfilter
- Same-Day-Slots berücksichtigen jetzt eine Mindestvorlaufzeit

## Betriebs-Defaults
- `minimum_lead_time_minutes = 30`
- `booking_window_days` bleibt durch die Konfiguration begrenzt
- `silence_threshold_ms = 1300`
- Adapter bleiben Ausführungsschichten; die Orchestrierung besitzt Auflösung und Mutationssicherheit

## Verifikations-Checkliste
1. Prüfen, dass geschützte Single-Match-Flows weiter funktionieren.
2. Prüfen, dass Multi-Match-Flows eine Termin-Auswahl erzwingen.
3. Prüfen, dass vergangene oder veraltete Same-Day-Slots nicht angeboten werden.
4. Prüfen, dass ausgewählte Slots vor der Mutation erneut geprüft werden.
5. Prüfen, dass DE- und EN-Dokumentation inklusive Release Notes vorhanden ist.

## Risikohinweise
- Legacy-Static-Date-Buttons in älteren rein simulierten Pfaden dürfen nicht als Source of Truth für reales Scheduling behandelt werden.
- Bestehende geschützte Runtime-Pfade müssen in der `v1.x`-Linie non-breaking bleiben.
