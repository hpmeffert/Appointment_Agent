# User Guide Demo Monitoring UI v1.1.0 Patch 8a

Version: v1.1.0-patch8a
Audience: User
Language: DE

## Was neu ist

Patch 8a bringt der Demo bei, einen Slot fuer kurze Zeit zu reservieren, bevor die finale Buchung passiert.

Das bedeutet:

- wenn du einen Slot waehlst, wird er kurzzeitig geschuetzt
- ein anderer Nutzer soll denselben Slot nicht parallel buchen koennen
- wenn du zu lange wartest, laeuft der Hold ab und der Slot wird wieder frei

## Der wichtigste Parameter einfach erklaert

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Dieser Wert sagt, wie viele Minuten das System einen gewaehlten Slot reserviert halten soll.

Beispiel:

- Wert `2`
- der Slot bleibt 2 Minuten reserviert
- danach kann der Slot wieder angeboten werden

## Was du im Cockpit sehen kannst

- eine Hold-Meldung nach der Slot-Auswahl
- Hold-Status im Monitoring
- Hold-Dauer in den Einstellungen

## Warum das hilft

Damit wirkt die Demo viel naeher an einer echten Buchungsplattform, weil reale Systeme Doppelbuchungen verhindern muessen.
