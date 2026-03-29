# Demo Guide Demo Monitoring UI v1.1.0 Patch 5

Version: v1.1.0-patch5
Audience: Demo
Language: DE

## Demo-Botschaft in einem Satz

Dieses Cockpit trennt Story, technisches Monitoring, Konfiguration und Google Kalender-Demo-Steuerung in klare Bereiche im Kopfmenue.

## Story-Szenario 1

- Oeffne `Dashboard`
- Waehle ein Standard-Booking-Szenario
- Erklaere, dass die Kundenstory einfach bleibt, waehrend das System trotzdem Trace- und Correlation-IDs fuehrt

## Story-Szenario 2

- Oeffne `Google Demo Control`
- Bleibe in `Simulation`
- Nutze `Prepare Demo Calendar`
- Erklaere, dass das sicher ist, weil keine echten Google Eintraege geschrieben werden

## Story-Szenario 3

- Bleibe auf `Google Demo Control`
- Wechsle zu `Test`
- Erklaere den Warnhinweis
- Nutze `Generate Demo Appointments`
- Erklaere, dass nur der eigene Google Testkalender geaendert wird

## Gute Presenter-Formulierung

- Dashboard ist fuer die Business-Story.
- Monitoring ist fuer den technischen Nachweis.
- Einstellungen sind fuer die Operator-Parameter.
- Google Demo Control ist fuer simulierte oder echte Testkalender-Aktionen.

## Wichtige Parameter

- `mode`
  Simulation oder Test.

- `timeframe`
  Das Datumsfenster fuer Vorbereitung und Erzeugung.

- `count`
  Wie viele Termine erzeugt oder bearbeitet werden sollen.

- `vertical`
  Welches Business-Beispiel Titel und Beschreibungen praegt.
