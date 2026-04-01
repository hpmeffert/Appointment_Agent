# Demo Guide Demo Monitoring UI v1.2.1-patch4

Version: v1.2.1-patch4
Audience: Demo
Language: DE

## Was in Patch 4 neu ist

Patch 4 behaelt das Incident-artige Layout und verbessert die Fuehrung fuer Praesentationen:
- neuer Schalter fuer `Free` und `Guided`
- Guided Panel mit aktuellem Schritt, naechster Aktion und UI-Fokus
- `Auto Demo` fuer eine automatische Vorfuehrung
- staerker messaging-first aufgebautes Dashboard
- klarere Sicht auf Kanaele, Integrationen und AI-Bausteine

## Was diese Demo zeigen soll

Diese Demo soll eine Sache leicht erklaeren:

- der Kunde sieht nur eine einfache Nachricht
- der Operator sieht den ganzen Prozess
- die Plattform verbindet Messaging, Scheduling, Monitoring und Settings

## Empfohlene Reihenfolge

1. `Dashboard` oeffnen
2. `Free` gegen `Guided` zeigen
3. `Guided` aktivieren
4. `Auto Demo` oder `Next Step` nutzen
5. `Message Monitor` zeigen
6. `Monitoring` zeigen
7. `Settings -> RCS` zeigen
8. `Google Demo Control` zeigen

![Annotated cockpit overview](/docs/assets/screenshots/v1_2_1_patch4/cockpit-overview.svg)
![Platform flow overview](/docs/assets/screenshots/v1_2_1_patch4/platform-flow.svg)

## Guided Demo Mode

Der Guided Mode hilft dem Presenter direkt in der UI.

Er zeigt:
- den aktuellen Story-Schritt
- was als Naechstes gezeigt werden soll
- auf welchen Bereich der UI man zeigen soll
- wie weit die Demo schon ist

### Wichtige Guided-Parameter

- `guidedMode`
  `free` bedeutet freie Bedienung.
  `guided` bedeutet gefuehrte Story.
- `guidedStepIndex`
  Zaehler fuer den aktuellen Story-Schritt.
- `auto_run_interval_ms`
  Zeit zwischen zwei automatischen Story-Schritten.
  In diesem Patch ist der Standard `2200`.
- `ui_focus`
  Name des Bereichs, auf den man zeigen soll, zum Beispiel `chatStream` oder `platformOverviewGrid`.

## Gute Demo-Linien

- "Das ist nicht nur ein Chatbot. Das ist eine Termin-Plattform."
- "Der Kunde sieht eine Nachricht. Das Unternehmen sieht einen kontrollierten Prozess."
- "Die Plattform zeigt Slots nicht nur an. Sie schuetzt sie auch."

## Wichtige Demo-Bereiche

- `Messages and Customer Journey`
  Zeigt Transcript, Antwortbuttons, Slot-Buttons und Status.
- `Guided Demo Mode`
  Zeigt den aktiven Presenter-Schritt.
- `Operator Summary`
  Zeigt Trace IDs, Aktion, Slot, Hold-Status und Result-Pfad.
- `How the Platform Works`
  Erklaert Kanaele, Adapter, Service Bus und AI.
- `Message Monitor`
  Zeigt eingehende und ausgehende Nachrichten zusammen.

## Google Demo Control kurz erklaert

- `Mode`
  `simulation` schreibt nichts in Google.
  `test` schreibt in den konfigurierten Google-Testkalender.
- `From Date`
  Startdatum fuer den Demo-Zeitraum.
- `To Date`
  Enddatum fuer den Demo-Zeitraum.
- `Appointment Count`
  Anzahl der Demo-Termine.
- `Appointment Type`
  Geschaeftlicher Typ wie `dentist` oder `wallbox`.

## RCS Settings kurz erklaert

`Settings -> RCS` zeigt:
- gespeicherte Werte
- maskierte Secrets
- Readiness
- Validierung und Test Connection

![Annotated RCS settings page](/docs/assets/screenshots/v1_2_1_patch4/rcs-settings.svg)
