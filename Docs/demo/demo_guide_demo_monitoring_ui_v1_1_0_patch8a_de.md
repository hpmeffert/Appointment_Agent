# Demo Guide Demo Monitoring UI v1.1.0 Patch 8a

Version: v1.1.0-patch8a
Audience: Demo
Language: DE

## Beste Patch-8a-Story

Zeige, dass das System den Slot jetzt zwischen Auswahl und finaler Buchung schuetzt.

## Demo-Ablauf

1. Oeffne die Cockpit-Route `v1.1.0-patch8a`.
2. Gehe zu `Einstellungen` und zeige `Slot Hold Minuten`.
3. Erklaere, dass der Demo-Standardwert `2` ist.
4. Gehe zurueck auf `Dashboard` und klicke einen Slot-Button.
5. Zeige, dass der Slot jetzt temporaer reserviert ist.
6. Oeffne `Monitoring` und zeige:
   - `slot.hold.created`
   - `slot.hold.active`
7. Erklaere, dass die finale Buchung nur funktioniert, solange der Hold aktiv ist.

## Was du sagen kannst

- Der Hold liegt nicht nur in Google. Er lebt im Plattform-Status.
- So stoppen wir parallele Buchungsrennen.
- Vor der finalen Buchung wird Google trotzdem noch einmal live geprueft.

## Warum das System einen Slot temporaer reserviert

Zwei Nutzer koennen denselben freien Slot gleichzeitig sehen.

Der temporaere Hold gibt einem Journey-Ablauf ein kurzes geschuetztes Zeitfenster.

Dadurch wird die Plattform sicherer und realistischer.
