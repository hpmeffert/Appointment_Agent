# Demo Guide Reminder Scheduler v1.3.5

Version: v1.3.5
Audience: Demo
Language: DE

## Was diese Demo zeigen soll

Diese Demo soll zeigen, dass die Delivery-Schicht einfach zu erklaeren ist:
- einen Kanal waehlen
- das Validation-Ergebnis pruefen
- das Delivery-Ergebnis lesen
- den Runtime-Zustand in einfachen Worten zeigen

Nutze diesen Satz:

- "Der Operator sieht den Delivery-Weg, die Pruefung und das Ergebnis in einer Ansicht."

## Empfohlene Bildschirm-Reihenfolge

1. `Dashboard` oeffnen.
2. `Delivery` zeigen.
3. Den Primary Channel wechseln.
4. `Validation` oeffnen.
5. `Results` oeffnen.
6. `Channels` oeffnen.
7. `Operator` oeffnen.
8. Mit `Help` enden.

## Story 1: Primary channel works

1. `Delivery` oeffnen.
2. Zeigen, dass `RCS/SMS` aktiv ist.
3. Erklaeren, dass Validation passt.
4. `Results` oeffnen und den `sent` Eintrag zeigen.

Was du sagen kannst:
- "Das ist der normale Weg. Der erste Kanal ist bereit, also geht die Nachricht sofort raus."

Warum das wichtig ist:
- der Operator sieht einen einfachen und schnellen Delivery-Weg
- das Ergebnis ist leicht zu erklaeren

## Story 2: Validation blockt ein schlechtes Ziel

1. `Delivery` oeffnen.
2. Alle Kanaele ausschalten oder die Message-Lenght-Grenze kleiner setzen.
3. `Validation` oeffnen.
4. Das `blocked` Ergebnis zeigen.

Was du sagen kannst:
- "Das Cockpit stoppt schlechte Delivery, bevor etwas gesendet wird."

Warum das wichtig ist:
- der Operator sieht das Problem frueh
- das Team kann den Block in einfachen Worten erklaeren

## Story 3: Fallback rettet die Delivery

1. `Delivery` oeffnen.
2. Den Primary Channel auslassen, aber Fallback erlauben.
3. `Results` oeffnen.
4. Den `fallback_sent` Eintrag zeigen.

Was du sagen kannst:
- "Wenn der erste Kanal nicht bereit ist, uebernimmt der Backup-Kanal."

Warum das wichtig ist:
- der Operator sieht, warum sich das Ergebnis aendert
- die Delivery bleibt auf sichere Weise erfolgreich

## Wichtige Parameter erklaeren

- `enabled`
  Schaltet Delivery an oder aus.
- `delivery_mode`
  Zeigt, ob das Cockpit einen Hauptweg oder eine Fallback-Kette nutzt.
- `primary_channel`
  Zeigt den ersten Kanal, den das System versucht.
- `allow_fallback_channels`
  Zeigt, ob das System einen anderen Kanal nutzen darf.
- `validate_recipient`
  Zeigt, ob das Ziel zuerst geprueft wird.
- `validate_channel`
  Zeigt, ob der gewaehlte Kanal zuerst geprueft wird.
- `max_retry_count`
  Zeigt, wie viele Wiederholungen erlaubt sind.
- `delivery_window_minutes`
  Zeigt, wie lange die Delivery offen bleibt.
- `message_length_limit`
  Zeigt, wie gross die Nachricht sein darf.
- `result_retention_days`
  Zeigt, wie lange das Ergebnis sichtbar bleibt.

## Schluss-Satz

- "Dieses Cockpit macht Delivery leicht erklaerbar, auch fuer einen neuen Operator."
- "Es zeigt auch, was als Naechstes passiert und ob der Runtime-Zustand gesund ist."
