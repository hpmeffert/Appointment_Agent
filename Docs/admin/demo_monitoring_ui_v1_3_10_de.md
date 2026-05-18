# Appointment Agent Admin Leitfaden v1.3.10 (DE)

## Release-Ziel
`v1.3.10` fuegt `Dashboard+` hinzu: eine vereinfachte Real-Modus-Demo-Oberflaeche fuer den Vertrieb im Appointment Agent Cockpit.

Die Version ist additiv. Die bestehenden Menuepunkte `Dashboard`, `Message Monitor`, `Reports`, `Monitoring`, `Settings`, `Settings -> RCS`, `Google Demo Control`, `Reminder`, `Addresses` und `Help` bleiben verfuegbar.

## Admin-relevante Aenderungen
- Neuer Top-Menuepunkt: `Dashboard+`, platziert vor `Dashboard`.
- Die Hauptroute `/ui/demo-monitoring/v1.3.10` oeffnet zuerst `Dashboard+`.
- Das Dashboard+ Operator Panel enthaelt:
  - `Scenario`
  - festes `Scenario Mode = Real`
  - Radio-Ziel `Ausgewaehlte Adresse` plus Adressauswahl
  - Radio-Ziel `Telefonnummer` plus manuelles Telefonnummernfeld
  - `Appointment Type`
  - eine einzelne Startaktion fuer die Real-Demo
- Der Telefonnummernmodus verlangt eine nicht leere Mobilnummer.
- Das manuelle Telefonnummernfeld ist auf `40` Zeichen begrenzt.
- Der Scenario Runner akzeptiert `contact_target_mode` und `manual_phone_number` fuer Dashboard+ Real-Sends.

## Runtime Contract
Dashboard+ speichert den Zielmodus in den Scenario-Context-Metadaten:

```json
{
  "dashboard_plus": {
    "contact_target_mode": "address",
    "manual_phone_number": ""
  }
}
```

Unterstuetzte `contact_target_mode` Werte:
- `address`: Telefonnummer der ausgewaehlten Adresse verwenden
- `phone`: `manual_phone_number` verwenden

## Verifikations-Checkliste
1. `/ui/demo-monitoring/v1.3.10` oeffnen und pruefen, dass `Dashboard+` zuerst aktiv ist.
2. Pruefen, dass die Menuefolge `Dashboard+`, `Dashboard`, danach die bestehenden Eintraege ist.
3. Real-Szenario mit Kontaktziel `Ausgewaehlte Adresse` starten.
4. Real-Szenario mit Kontaktziel `Telefonnummer` und gueltiger Mobilnummer starten.
5. `Telefonnummer` auswaehlen, Feld leer lassen und pruefen, dass der Fehler den Versand blockiert.
6. Pruefen, dass `Messages and Customer Journey` unveraendert rendert.
7. Pruefen, dass `/api/demo-monitoring/v1.3.9/help` und `/api/demo-monitoring/v1.3.10/help` Version `v1.3.10` liefern.

## Betriebs-Defaults
- `silence_threshold_ms = 1300`
- Dashboard+ Scenario Mode: `Real`
- Manuelles Telefonnummernlimit: `40` Zeichen
- Die bestehende v1.3.9 API-Basis bleibt Kompatibilitaetsroute; sichtbare Anzeigeversion ist `v1.3.10`.

## Risikohinweise
- Dashboard+ darf das alte Dashboard nicht ersetzen oder entfernen. Es ist eine zusaetzliche vereinfachte Ansicht.
- Reply Buttons im Journey-Bereich bleiben im Real-Modus read-only, da Provider Callbacks die Source of Truth sind.
- Generierte Szenario-Artefakte nicht committen; lokale Runtime-Artefakte bleiben ausserhalb des Release-Commits.
