# Demo Monitoring UI v1.1.0 Patch 5

Version: v1.1.0-patch5
Audience: Admin
Language: DE

## Was sich geaendert hat

Dieser Release macht das Incident-Demo-Cockpit zum dauerhaften UI-Standard.

Die wichtigste sichtbare Aenderung ist, dass `Google Demo Control` jetzt ein eigener Menuepunkt im Kopfbereich ist.

Dadurch sind Google Demo Aktionen nicht mehr mit dem Dashboard vermischt.

## Warum das wichtig ist

Ein Presenter kann das Cockpit jetzt einfach erklaeren:

- Dashboard = Business- und Story-Ueberblick
- Monitoring = technische Event-Sicht
- Einstellungen = Operator-Parameter
- Google Demo Control = Kalender-Test- und Simulationsaktionen
- Hilfe = Dokumentation

## Seite Google Demo Control

Diese Seite enthaelt:

- aktuellen Modus: `Simulation` oder `Test`
- Informationen zum Zielkalender
- Zeitraum-Auswahl
- Vertical-Auswahl
- `Prepare Demo Calendar`
- `Generate Demo Appointments`
- `Delete Demo Appointments`
- `Reset Demo Calendar`
- sichtbares Erfolgs- und Fehlerfeedback
- einen klaren Warnhinweis, dass `Test` in den real konfigurierten Google Testkalender schreibt

## Wichtige Parameter einfach erklaert

- `mode`
  Dieser Wert entscheidet, ob Google Aktionen nur sicher simuliert werden oder echt schreiben.
  `simulation` bedeutet: es werden keine echten Google Kalendereintraege erzeugt.
  `test` bedeutet: der konfigurierte Google Testkalender kann veraendert werden.

- `timeframe`
  Dieser Wert entscheidet, fuer welchen Zeitraum die Demo-Hilfe arbeitet.
  `day` bedeutet heute.
  `week` bedeutet die aktuelle Woche.
  `month` bedeutet der aktuelle Monat.

- `count`
  Dieser Wert bestimmt, wie viele Demo-Termine erzeugt werden sollen.

- `vertical`
  Dieser Wert bestimmt, welches Business-Beispiel fuer Titel und Beschreibungen genutzt wird.
  Beispiele sind Zahnarzt, Wallbox und Nahwaerme.

## Dauerhafte Shell-Regel

Zukuenftige UI-Arbeit soll diese Shell weiterverwenden.

Es soll kein zweiter Cockpit-Stil entstehen, ausser es gibt eine ausdrueckliche Freigabe fuer ein groesseres Redesign.
