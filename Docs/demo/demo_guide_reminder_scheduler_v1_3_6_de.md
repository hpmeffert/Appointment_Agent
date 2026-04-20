# Demo Guide Reminder Scheduler v1.3.6

Version: v1.3.6
Audience: Demo
Language: DE

## Was diese Demo zeigen soll

Diese Demo soll den ganzen Reminder-Weg in einem Cockpit zeigen:
- die Terminquelle
- die Google-Verknuepfung
- die Termindaten
- die Reminder-Policy
- die Reminder-Vorschau
- die Reminder Jobs
- die Laufzeit- und Diagnose-Sicht
- die Bruecke von Google-Quelldaten zu reminder-faehigen Daten

Nutze diesen Satz:

- "Der Operator sieht Terminquelle, Google-Link, Reminder-Plan und Health in einer einzigen Ansicht."

## Empfohlene Reihenfolge auf dem Bildschirm

1. `Dashboard` oeffnen.
2. `Source` zeigen.
3. `Details` zeigen.
4. `Policy` zeigen.
5. `Preview` oeffnen.
6. `Jobs` oeffnen.
7. `Health` oeffnen.
8. Mit `Help` enden.

## Story 1: Neuer Termin aus Google

1. `Source` oeffnen.
2. Zeigen, dass der Termin aus Google Calendar kommt.
3. `Details` oeffnen.
4. Kundendaten, Zeit und Terminart zeigen.
5. `Preview` oeffnen.
6. Auf die Reminder-Reihenfolge zeigen.

Was man sagen kann:
- "Das ist der Normalfall. Ein verknuepfter Google-Termin wird zu einem Reminder-Plan."

Warum das wichtig ist:
- der Operator sieht Quelle, Verknuepfung und Plan in einem Ablauf
- die Demo bleibt kurz und leicht erklaerbar
- das Team kann `/api/google/v1.3.6/linkage/demo` oeffnen, wenn jemand das Rohobjekt sehen will

## Story 2: Termin verschoben

1. `Details` oeffnen.
2. Sagen, dass sich die Zeit des Termins geaendert hat.
3. `Jobs` oeffnen.
4. Zeigen, dass die Reminder Jobs angepasst wurden.
5. `Preview` oeffnen.
6. Die neuen Zeiten mit dem neuen Termin abgleichen.

Was man sagen kann:
- "Das System behaelt den Termin und passt den Reminder-Plan an."

Warum das wichtig ist:
- das Team kann eine Verschiebung ohne Fachchinesisch erklaeren
- der Plan bleibt korrekt

## Story 3: Termin abgesagt

1. `Details` oeffnen.
2. Sagen, dass der Termin abgesagt wurde.
3. `Jobs` oeffnen.
4. Zeigen, dass die Reminder Jobs ebenfalls abgebrochen wurden.
5. `Health` oeffnen.
6. Zeigen, dass die Laufzeit gesund bleibt.

Was man sagen kann:
- "Die Erinnerungsarbeit stoppt sicher, wenn der Termin weg ist."

Warum das wichtig ist:
- niemand bekommt eine Erinnerung fuer einen Termin, den es nicht mehr gibt
- der Operator kann dem Job-Status vertrauen

## Wichtige Parameter zum Erklaeren

- `appointment_source_system`
  Woher der Termin kommt.
- `google_calendar_id`
  Welcher Google-Kalender verbunden ist.
- `appointment_type`
  Welche Art von Termin es ist.
- `appointment_start`
  Wann der Termin startet.
- `timezone`
  Die lokale Zeit des Termins.
- `reminder_offsets_minutes`
  Wann vor dem Termin Erinnerungen geplant werden.
- `silence_threshold_ms`
  Die kurze Pause, bevor das System denkt, dass der Nutzer aufgehört hat zu sprechen.
- `quiet_hours`
  Die Zeit, in der keine Erinnerung gesendet werden soll.
- `job_status`
  Der Zustand des Reminder Jobs.
- `next_due_at`
  Wann der naechste Job faellig ist.

## Schlusssatz

- "Dieses Cockpit macht den ganzen Reminder-Weg einfach, sichtbar und sicher."
- "Ein neuer Kollege kann die Story verstehen, ohne zuerst den Code zu lesen."
