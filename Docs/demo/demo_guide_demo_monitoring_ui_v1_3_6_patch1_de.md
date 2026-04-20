# Demo Guide Demo Monitoring UI v1.3.6-patch1

Version: v1.3.6-patch1
Audience: Demo
Language: DE

## Was diese Demo zeigen soll

Diese Demo soll eine kombinierte Story zeigen:
- das stabile Incident-artige Cockpit aus `v1.2.1-patch4`
- die Reminder- und Google-Story aus `v1.3.6`

Der neue Menuepunkt macht es moeglich, in einer Release-Linie vom Patch-4-Cockpit direkt in die Reminder-Demo zu wechseln.

Nutze diesen Satz:

- "Dieses Cockpit zeigt die Kundennachricht, den Operator-Ablauf und den Reminder-Plan an einem Ort."

## Beste Reihenfolge auf dem Bildschirm

1. `Dashboard` oeffnen.
2. Die Patch-4-Cockpit-Bereiche zeigen.
3. `Reminder / Google Demo` oeffnen.
4. Den Google-verknuepften Termin zeigen.
5. Den Reminder-Plan zeigen.
6. `Message Monitor` zeigen.
7. `Monitoring` zeigen.
8. Mit `Help` enden.

## Story 1: Neuer Termin aus Google

1. Die Reminder-Story oeffnen.
2. Zeigen, dass der Termin aus Google Calendar kommt.
3. Den Reminder-Plan oeffnen.
4. Auf die geplanten Reminder-Zeiten zeigen.
5. Wieder `Dashboard` oeffnen und den kombinierten Cockpit-Ablauf zeigen.

Was man sagen kann:
- "Ein verknuepfter Google-Termin wird zu einem Reminder-Plan."

Warum das wichtig ist:
- das Publikum sieht Quelle, Link und Reminder in einem Ablauf
- die Story bleibt kurz und leicht zu verstehen

## Story 2: Termin verschoben

1. Die Reminder-Story oeffnen.
2. Sagen, dass sich die Zeit des Termins geaendert hat.
3. Zeigen, dass sich auch der Reminder-Plan geaendert hat.
4. `Monitoring` oeffnen, wenn du zeigen willst, dass die Plattform die Kontrolle behält.

Was man sagen kann:
- "Das System behaelt den Termin und passt den Reminder-Plan an."

Warum das wichtig ist:
- das Team kann eine Verschiebung ohne Fachchinesisch erklaeren
- die Reminder-Zeiten bleiben korrekt

## Story 3: Termin abgesagt

1. Die Reminder-Story oeffnen.
2. Sagen, dass der Termin abgesagt wurde.
3. Zeigen, dass auch die Reminder-Arbeit stoppt.
4. `Help` oeffnen und auf den Versions-Text zeigen.

Was man sagen kann:
- "Wenn der Termin weg ist, stoppen die Erinnerungen sicher."

Warum das wichtig ist:
- niemand bekommt eine Erinnerung fuer einen Termin, den es nicht mehr gibt
- der Operator kann dem Job-Status vertrauen

## Wichtige Parameter zum Erklaeren

- `silence_threshold_ms`
  Die kurze Pause, bevor das System denkt, dass der Nutzer aufgehört hat zu sprechen.
  Der Standard ist `1300 ms`.
- `reminder_offsets_minutes`
  Wie viele Minuten vor dem Termin Erinnerungen geplant werden.
- `google_calendar_id`
  Welcher Google-Kalender verknuepft ist.
- `appointment_type`
  Welche Art von Termin es ist.
- `job_status`
  Der Zustand eines Reminder Jobs.
- `next_due_at`
  Wann der naechste Job faellig ist.
- `guidedMode`
  `free` bedeutet manuelle Bedienung.
  `guided` bedeutet gefuehrte Story.
- `guidedStepIndex`
  Die aktuelle Schritt-Nummer in der Story.

## Schlusssatz

- "Dieses Release macht das Cockpit einfach, sichtbar und sicher."
- "Die gleiche Ansicht kann das Operator-Cockpit und die Reminder-Story zeigen."

