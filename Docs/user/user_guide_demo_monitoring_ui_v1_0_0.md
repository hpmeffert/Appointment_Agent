# Demo Monitoring UI User Guide v1.0.0

## Wofuer ist diese Seite da?

Diese Seite hilft dir, den Appointment Agent zu erklaeren.

Links sieht man:

- was der Kunde schreibt
- welche Auswahl er sieht
- welche Antwort das System gibt

Rechts sieht man:

- welcher Teil des Systems gerade arbeitet
- welche Events entstehen
- welcher Status gerade aktiv ist
- welche Audit-Eintraege geschrieben werden

## Adresse der UI

Die Seite ist unter dieser Route erreichbar:

`/ui/demo-monitoring/v1.0.0`

## Die wichtigsten Steuerelemente

- `Mode`
  Hier wechselst du zwischen `Demo`, `Monitoring` und `Combined`.

- `Scenario`
  Hier waehlst du den Ablauf aus, den du zeigen willst.
  Beispiele:
  - Standard Booking
  - Reschedule
  - Cancellation
  - No Slot and Escalation
  - Provider Failure

- `Restart`
  Setzt das aktuelle Szenario wieder auf den ersten Schritt.

- `Next Step`
  Springt zum naechsten Schritt im Ablauf.

- `Autoplay`
  Spielt den Ablauf automatisch ab.

- `Show IDs`
  Blendet technische IDs wie `booking_reference` und `provider_reference` ein oder aus.

- `Show Audit Details`
  Blendet die Audit-Eintraege ein oder aus.

## Wichtige Anzeigefelder rechts

- `Journey State`
  Der aktuelle Zustand des Ablaufs.

- `Active Component`
  Welcher Teil des Systems gerade arbeitet.

- `Flow Steps`
  Zeigt, welche Bereiche schon fertig sind, noch laufen oder fehlgeschlagen sind.

- `Event Timeline`
  Zeigt die wichtigsten System-Ereignisse in Reihenfolge.

- `Booking Details`
  Zeigt interne und externe Termin-Referenzen.

- `CRM Events`
  Zeigt, welche Ereignisse spaeter an ein CRM weitergegeben werden koennten.

- `Key Parameters`
  Dieser Bereich erklaert die wichtigsten technischen IDs direkt in einfachen Worten.

## Gute Nutzung fuer eine Demo

Wenn du die Seite praesentierst:

1. starte mit `Combined`
2. nutze zuerst `Standard Booking`
3. gehe Schritt fuer Schritt mit `Next Step`
4. erklaere danach `Reschedule`
5. zeige zum Schluss `No Slot and Escalation` oder `Provider Failure`
