# Admin Guide Demo Monitoring UI v1.2.1-patch4

Version: v1.2.1-patch4
Audience: Admin
Language: DE

## Ziel von Patch 4

`v1.2.1-patch4` behaelt die stabile Incident-Shell und verbessert die Demo-Steuerung.

Das Ziel ist:
- Live-Demos leichter fuehrbar zu machen
- Laufzeitverhalten stabil zu halten
- die Plattform direkt in der UI klarer zu erklaeren

## Wichtige neue Elemente

- `guided_demo`
  Payload-gesteuerte Story-Engine fuer Presenter.
- `guidedMode`
  UI-Zustand fuer `free` oder `guided`.
- `guidedStepIndex`
  Aktueller Schritt der gefuehrten Story.
- `autoDemoRunning`
  Zeigt, ob die Guided Story automatisch weiterlaeuft.
- `platform_visibility`
  Strukturierte Sicht auf Kanaele, Integrationen und AI.

## Warum payload-gesteuerte Guidance wichtig ist

Die Story-Fuehrung ist nicht fest an viele einzelne UI-Bedingungen gebunden.

Stattdessen definiert das Payload:
- `step_id`
- `title`
- `description`
- `ui_focus`
- `action`

Das hilft, weil:
- Doku und UI leichter zusammenpassen
- die Story-Reihenfolge spaeter leichter geaendert werden kann
- neue Releases die Story-Engine erweitern koennen, ohne die Shell zu zerbrechen

## Zentrale UI-States

- `page`
  Aktive Seite wie `dashboard` oder `monitoring`.
- `scenarioId`
  Aktive Business-Story.
- `stepIndex`
  Aktueller Schritt im Transcript.
- `guidedMode`
  Presenter-Modus.
- `guidedStepIndex`
  Aktueller Guided-Schritt.
- `autoDemoRunning`
  Auto-Walkthrough-Zustand.
- `selectedAction`
  Aktuell gewaehlte Antwortaktion.
- `selectedSlot`
  Aktuell gewaehlter Termin-Slot.
- `holdStatus`
  Status des Slot-Holds, zum Beispiel `idle`, `active` oder `consumed`.

## Wichtige Betriebsparameter

- `slot_hold_minutes`
  Dauer der temporaeren Reservierung.
- `auto_run_interval_ms`
  Geschwindigkeit der automatischen Demo.
- `googleMode`
  `simulation` vermeidet echte Writes.
  `test` erlaubt echte Aenderungen im Testkalender.
- `selectedAppointmentType`
  Geschaeftlicher Typ fuer Demo-Daten.

## LEKAB-Routen in Patch 4

- `/api/lekab/v1.2.1-patch4/settings/rcs`
- `/api/lekab/v1.2.1-patch4/settings/rcs/validate`
- `/api/lekab/v1.2.1-patch4/settings/rcs/test-connection`

Wichtig:
- Secrets bleiben maskiert
- leere Secret-Felder behalten den alten Wert
- Readiness bleibt sichtbar
- SQLite bleibt der lokale Konfigurationsspeicher fuer den Prototyp
