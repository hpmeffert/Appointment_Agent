# User Guide Demo Monitoring UI v1.3.6-patch1

Version: v1.3.6-patch1
Audience: User
Language: DE

## Wofuer dieses Cockpit da ist

Das Cockpit hilft einem Operator, drei Dinge gleichzeitig zu sehen:
- was der Kunde sieht
- was die Plattform macht
- was die Reminder-Story im Hintergrund tut

Dieser Patch verbindet das stabile Patch-4-Cockpit mit der Reminder- und Google-Demo aus `v1.3.6`.

## Hauptseiten

- `Dashboard`
  Hauptseite mit dem kombinierten Demo-Ablauf.
- `Message Monitor`
  Zeigt eingehende und ausgehende Nachrichten.
- `Monitoring`
  Zeigt technische Events, Traces und Performance-Daten.
- `Settings`
  Zeigt allgemeine Operator-Parameter.
- `Settings -> RCS`
  Zeigt LEKAB RCS- und SMS-Settings.
- `Google Demo Control`
  Sicherer Bereich fuer Google-Demo-Daten.
- `Reminder / Google Demo`
  Neuer Menuepunkt fuer die kombinierte Reminder-Story.
- `Help`
  Oeffnet die aktuellen Leitfaeden.

## Was in Patch 1 neu ist

- das Patch-4-Cockpit bleibt erhalten
- ein neuer Menuepunkt oeffnet die Reminder- und Google-Demo aus `v1.3.6`
- die Doku erklaert den neuen kombinierten Weg in einfachen Worten
- die Version steht im Header und in der Help

## Dashboard kurz erklaert

Das Dashboard bleibt die wichtigste Seite.

Es zeigt:
- `Current Story`
  Welche Business-Story gerade aktiv ist.
- `Current Mode`
  Ob das Cockpit in freiem oder gefuehrtem Modus laeuft.
- `Messages and Customer Journey`
  Transcript, Antwortbuttons, Slot-Buttons und Status.
- `Guided Demo Mode`
  Den aktuellen Presenter-Schritt und den naechsten Fokus.
- `Operator Summary`
  Trace-IDs, gewaehlte Aktion, Slot, Hold-Status und Result-Pfad.
- `Reminder Story`
  Den Google-verknuepften Termin und den Reminder-Plan.

## Wichtige Parameter

- `guidedMode`
  `free` bedeutet manuelle Steuerung.
  `guided` bedeutet die vorbereitete Story laeuft.
- `guidedStepIndex`
  Die aktuelle Schritt-Nummer in der Story.
- `autoDemoRunning`
  `true` bedeutet, dass die Story automatisch weiterlaeuft.
- `silence_threshold_ms`
  Die kurze Pause, bevor das System denkt, dass der Nutzer aufgehört hat zu sprechen.
  Der Standard ist `1300 ms`.
- `reminder_offsets_minutes`
  Wie viele Minuten vor dem Termin Erinnerungen geplant werden.
- `slot_hold_minutes`
  Wie lange ein Slot kurzzeitig reserviert bleibt.
- `google_calendar_id`
  Der Google-Kalender fuer den verknuepften Termin.
- `appointment_type`
  Der Geschaeftstyp fuer die Demo-Daten.
- `message_id`
  Die interne ID einer Nachricht.
- `trace_id`
  Die technische ID fuer zusammenhaengende Events.

## Die wichtigsten Buttons

- `Restart Story`
  Startet die aktuelle Story neu.
- `Next Step`
  Geht zum naechsten Schritt.
- `Auto Demo`
  Startet oder stoppt die automatische Story.
- Antwortbuttons wie `Confirm`, `Reschedule`, `Cancel` und `Call Me`
  Fuehren die Customer Journey weiter.
- Slot-Buttons
  Waehl einen Termin-Slot aus und pruefe einen kurzen Hold.

## Was der neue Reminder-Menuepunkt zeigt

Der neue Menuepunkt `Reminder / Google Demo` oeffnet die kombinierte Story.
Dort sieht man:
- wie der Termin aus Google kommt
- wie Erinnerungen geplant werden
- wie eine Aenderung den Reminder-Plan anpasst
- wie eine Absage die Reminder-Arbeit sicher stoppt

## Gute Regel fuer Nutzer

Wenn du die Kunden-Story erklaeren willst, bleib auf `Dashboard`.

Wenn du technische Belege zeigen willst, wechsle zu:
- `Message Monitor`
- `Monitoring`
- `Settings -> RCS`
- `Reminder / Google Demo`

