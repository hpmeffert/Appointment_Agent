# Release Notes v1.3.10 (DE)

## Zusammenfassung
Version `v1.3.10` fuehrt `Dashboard+` ein: ein vereinfachtes Real-Modus-Demo-Dashboard fuer Vertriebsnutzer. Die bestehende Cockpit- und Journey-Logik bleibt erhalten, waehrend die Detailbedienung aus der primaeren Presenter-Ansicht entfernt wird.

## Highlights
- Neuer Top-Menuepunkt `Dashboard+` vor dem bestehenden `Dashboard`.
- Die zentrale Cockpit-Route oeffnet `Dashboard+` als erste Ansicht.
- Das bestehende `Dashboard` bleibt unveraendert fuer tiefergehende Operator- und Diagnoseansichten.
- Das Dashboard+ Operator Panel ist reduziert auf:
  - Scenario
  - festes Scenario Mode `Real`
  - Selected Address
  - manuelle Telefonnummer
  - Appointment Type
- Radio-Umschaltung zwischen Adress-Telefonnummer und manueller Mobilnummer.
- Validierung blockiert Real-Versand, wenn Telefonnummer ausgewaehlt ist und keine Mobilnummer eingetragen wurde.
- Die manuelle Mobilnummer wird bis zum Scenario Runner durchgereicht, damit Real-Mode Outbound Sends das gewaehlte Ziel verwenden.
- `Messages and Customer Journey` bleibt verhaltensgleich zum bestehenden Cockpit.

## Sicherheit
- Kein Real-Versand, wenn Telefonnummernmodus ohne Mobilnummer aktiv ist.
- Manuelles Telefonnummernfeld ist auf `40` Zeichen begrenzt.
- Das bestehende adressbasierte Sendeverhalten bleibt erhalten.
- Silence Threshold Default bleibt `1300 ms`.

## Dokumentation
- Benutzerleitfaden in DE und EN aktualisiert.
- Demo Leitfaden in DE und EN mit mindestens 3 vertriebsfertigen Story-Szenarien aktualisiert.
- Admin Leitfaden in DE und EN aktualisiert.
- Release Notes in DE und EN aktualisiert.
