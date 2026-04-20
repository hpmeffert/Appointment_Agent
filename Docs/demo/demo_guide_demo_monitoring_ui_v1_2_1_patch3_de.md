# Demo Guide Demo Monitoring UI v1.2.1-patch3

Version: v1.2.1-patch3
Audience: Demo
Language: DE

## Was in Patch 3 neu ist

Patch 3 behaelt die Doku-Qualitaet aus Patch 2 und ergaenzt:
- Plattform-Erklaerungs-Panels direkt im Cockpit
- Demo-Storyboard-Karten direkt im Cockpit
- klarere Presenter-Hinweise fuer den Business Value

## Wofuer diese Demo da ist

Diese Demo zeigt, dass der Appointment Agent nicht nur ein Chatfenster ist.

Es ist eine modulare Terminplattform:
- Messaging-Kanaele auf der einen Seite
- Scheduling-Adapter auf der anderen Seite
- ein Service Bus und ein gemeinsames Operator-Cockpit in der Mitte

Guter Satz fuer die Praesentation:

- "Der Kunde sieht nur eine einfache Konversation. Das Unternehmen sieht eine Plattform, die den ganzen Terminprozess steuern und ueberwachen kann."

## So arbeitet die Plattform

- `LEKAB Adapter`
  Sendet und empfaengt RCS- und SMS-aehnliche Nachrichten.
- `Appointment Orchestrator`
  Entscheidet, was die Journey als Naechstes tun soll.
- `Google Adapter`
  Sucht Slots, haelt Slots, bucht Termine und behandelt Konflikte.
- `Zukuenftige Adapter`
  Microsoft, CRM oder andere Provider koennen spaeter dazu kommen.
- `Service Bus`
  Interne Verbindungsschicht zwischen Adaptern, Orchestrierung, Monitoring und Audit.

![Annotierte Cockpit-Uebersicht](/docs/assets/screenshots/v1_2_1_patch3/cockpit-overview.svg)
![Plattform-Flow-Uebersicht](/docs/assets/screenshots/v1_2_1_patch3/platform-flow.svg)

## Empfohlene Bildschirm-Reihenfolge

1. Cockpit Dashboard oeffnen.
2. `Message Monitor` zeigen.
3. `Google Demo Control` zeigen.
4. `Settings -> RCS` zeigen.
5. Danach die fuenf Stories spielen.

## Story 1: Buchung

1. Auf `Dashboard` starten.
2. Erklaeren, dass der Kunde einen Termin moechte.
3. Die Booking-Story und die Slot-Buttons zeigen.
4. Einen Slot klicken.
5. `Confirm` klicken.

Systemreaktion:
- freie Slots werden aus dem Booking-Backend geladen
- ein kurzer Hold wird erzeugt
- vor dem finalen Booking wird noch einmal geprueft

UI-Aenderung:
- Transcript aktualisiert sich
- Operator Summary zeigt Slot und Hold
- Monitoring zeigt die Booking-Events

Wow-Effekt:
- der Klick ist nicht nur Deko, sondern treibt echte Terminlogik

## Story 2: Verschiebung

1. Eine Story mit vorhandenem Termin oeffnen.
2. `Reschedule` klicken.
3. Einen neuen Slot waehlen.
4. `Confirm` klicken.

Systemreaktion:
- der alte Termin wird nicht blind ueberschrieben
- neue freie Slots werden neu geladen
- der neue Slot wird vor dem Update kurz reserviert

UI-Aenderung:
- der gewaehlte Slot aendert sich
- Monitoring zeigt Reschedule- und Hold-Events

## Story 3: Storno

1. Die Storno-Story oeffnen.
2. `Cancel` klicken.
3. Den resultierenden Pfad erklaeren.

Systemreaktion:
- die Kundenentscheidung wird in eine interne Aktion uebersetzt
- die Journey wird aktualisiert

UI-Aenderung:
- Transcript und Monitoring aktualisieren sich sofort

## Story 4: Rueckruf

1. Die Callback-Story oeffnen.
2. `Call Me` klicken.
3. Operator Summary und Monitoring zeigen.

Systemreaktion:
- das System markiert einen Human-Follow-up-Pfad

UI-Aenderung:
- die Story wechselt von Automation zu menschlicher Nachbearbeitung

## Story 5: Slot Hold

1. Eine Story mit mehreren Slots oeffnen.
2. Einen Slot klicken.
3. Kurz auf den Hold-Hinweis zeigen, bevor bestaetigt wird.

Systemreaktion:
- der Slot wird fuer kurze Zeit reserviert
- ein zweiter Nutzer soll ihn in dieser Zeit nicht bekommen
- vor dem Commit wird live erneut geprueft

UI-Aenderung:
- Hold-Status wird sichtbar
- Hold-Minuten sind in Settings und Summary sichtbar

Guter Satz dazu:
- "Das ist der Wow-Moment. Wir zeigen nicht nur Auswahl, wir schuetzen sie auch."

![Annotierte RCS-Settings-Seite](/docs/assets/screenshots/v1_2_1_patch3/rcs-settings.svg)

## Neuer Cockpit-Walkthrough in Patch 3

Im Dashboard auf diese zwei Bereiche zeigen:
- `How the Platform Works`
- `Demo Storyboard`

Erklaeren:
- "Der Presenter muss nicht sofort in die Docs springen."
- "Die Plattform-Schichten sind direkt im Produkt sichtbar."
- "Auch die fuenf Demo-Stories und ihre Wow-Effekte sind direkt im Produkt sichtbar."

## Wichtige Demo-Parameter

- `GOOGLE_TEST_MODE_DEFAULT`
  `simulation` schreibt nicht in Google.
  `test` schreibt in den konfigurierten Testkalender.
- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Legt fest, wie lange ein Slot reserviert bleibt.
- `APPOINTMENT_AGENT_MAX_SLOTS_PER_OFFER`
  Legt fest, wie viele Optionen gleichzeitig angeboten werden.
- `channel_priority`
  Legt fest, ob zuerst RCS oder SMS versucht wird.

## Was nicht in diesen Guide gehoert

Release Notes gehoeren nicht in den Demo Guide.

Sie liegen separat in:
- `Docs/releases/release_notes_v1_2_1_patch3_de.md`
