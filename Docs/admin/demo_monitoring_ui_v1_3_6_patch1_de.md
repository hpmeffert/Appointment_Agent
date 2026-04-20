# Admin Guide Demo Monitoring UI v1.3.6-patch1

Version: v1.3.6-patch1
Audience: Admin
Language: DE

## Ziel dieses Patches

`v1.3.6-patch1` verbindet das Incident-artige Cockpit aus `v1.2.1-patch4` mit der Reminder- und Google-Demo aus `v1.3.6`.

Das Cockpit hat jetzt einen zusaetzlichen Menuepunkt fuer die kombinierte Reminder-Demo.
So kann man in einer Release-Linie zwei Dinge gut zeigen:
- das stabile Operator-Cockpit aus Patch 4
- die Reminder- und Google-Story aus `v1.3.6`

Das Ziel bleibt einfach:
- das Cockpit stabil halten
- die Demo leicht erklaeren
- den ganzen Weg von Nachricht bis Reminder an einem Ort zeigen

## Grundidee des Cockpits

Die bekannte Incident-Shell bleibt gleich.
Der neue kombinierte Menuepunkt oeffnet den Reminder- und Google-Ablauf, damit der Operator ohne Umweg vom Patch-4-Cockpit in die `v1.3.6` Reminder-Story wechseln kann.

Die wichtigen Bereiche sind:
- `Dashboard`
  Hauptseite mit dem kombinierten Demo-Ablauf.
- `Message Monitor`
  Zeigt eingehende und ausgehende Nachrichten.
- `Monitoring`
  Zeigt Traces, Events und Performance-Daten.
- `Settings -> RCS`
  Zeigt LEKAB-Settings und Readiness.
- `Google Demo Control`
  Sicherer Bereich fuer Google-Demo-Daten.
- `Reminder / Google Demo`
  Neuer Menuepunkt fuer die kombinierte `v1.3.6` Reminder-Story.
- `Help`
  Zeigt die Guides und den Versions-Text.

## Warum es dieses kombinierte Release gibt

Dieses Release verbindet zwei gute Demo-Sichten:
- das Patch-4-Cockpit fuer die Bedienung im Live-Betrieb
- die Reminder-Scheduler-Story fuer Google-verknuepfte Termine und Erinnerungen

So kann man zeigen:
- wie eine Nachricht in das System kommt
- wie der Termin mit Google verbunden wird
- wie Erinnerungen geplant werden
- wie der Operator im selben Cockpit die Kontrolle behält

## Wichtige Parameter

- `silence_threshold_ms`
  Wie lange das System wartet, bis es annimmt, dass der Nutzer aufgehört hat zu sprechen.
  Der Standard ist `1300 ms`.
- `reminder_offsets_minutes`
  Wie viele Minuten vor dem Termin Erinnerungen geplant werden.
- `google_calendar_id`
  Der Google-Kalender fuer den verknuepften Termin.
- `appointment_type`
  Der Geschaeftstyp fuer die Demo-Daten.
- `job_status`
  Der Zustand eines Reminder Jobs, zum Beispiel geplant, aktualisiert, abgebrochen oder gesendet.
- `guidedMode`
  `free` bedeutet manuelle Bedienung.
  `guided` bedeutet gefuehrte Story.
- `guidedStepIndex`
  Die aktuelle Schritt-Nummer in der Story.
- `slot_hold_minutes`
  Wie lange ein temporärer Slot-Hold aktiv bleibt.
- `message_id`
  Interne ID einer Nachricht.
- `trace_id`
  Technische ID fuer zusammenhaengende Events.

## Sicherheit und Betrieb

- Secrets auf den Settings-Seiten immer maskiert lassen.
- `simulation` nur fuer Vorschauen benutzen.
- `test` nur fuer den konfigurierten Testkalender benutzen.
- Das Incident-artige Layout nicht aendern, damit niemand eine neue Shell lernen muss.
- Version in Header und Help sichtbar halten.

## Was geprueft werden soll

1. Der Header zeigt `v1.3.6-patch1`.
2. Die Help-Seite zeigt die Version und den kombinierten Zweck.
3. Das Cockpit hat den neuen Menuepunkt fuer Reminder / Google.
4. Die Texte erklaeren die wichtigsten Parameter in einfachen Worten.
5. Das Verhalten aus Patch 4 bleibt stabil.

