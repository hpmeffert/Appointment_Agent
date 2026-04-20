# Demo Guide Reminder Scheduler v1.3.1

Version: v1.3.1
Audience: Demo
Language: DE

## Was diese Demo zeigen soll

Die Demo soll zeigen, dass Reminder-Planung einfach, sicher, erklaerbar und auch bei Lifecycle-Zustaenden gut lesbar ist.

Nutze diesen Satz:

- "Der Kunde sieht nur eine Erinnerung. Der Operator sieht den Plan dahinter."

## Empfohlene Reihenfolge

1. `Dashboard` oeffnen
2. Die Seite `Setup` zeigen
3. Zwischen `manual` und `auto_distributed` wechseln
4. `Preview` oeffnen
5. `Jobs` oeffnen
6. `Lifecycle` oeffnen
7. Zum Schluss `Help` zeigen

## Story 1: Eine Erinnerung

1. Mit den Standardwerten starten
2. Zeigen, dass nur eine Erinnerung aktiv ist
3. Die Vorschau auf den 24-Stunden-Abstand zeigen
4. Den Lifecycle-Tab zeigen und auf die Job-Zustaende hinweisen

Warum das wichtig ist:
- das ist die einfachste Reminder-Einstellung
- sie ist leicht fuer Kunden und Kollegen zu erklaeren

## Story 2: Manuelle Dreierserie

1. Auf `manual` wechseln
2. `72`, `48` und `24` Stunden vor dem Termin setzen
3. Die Vorschau oeffnen
4. Den Lifecycle-Tab oeffnen und die Statusuebersicht zeigen

Was du sagen kannst:
- "Im manuellen Modus entscheidet der Operator die Zeiten direkt."

Warum das wichtig ist:
- Teams koennen ihre eigenen Regeln nutzen
- die Vorschau macht die Reihenfolge vorab sichtbar

## Story 3: Automatisch verteilte Erinnerungen

1. Auf `auto_distributed` wechseln
2. `reminder_count = 3` setzen
3. Letzten Abstand und maximale Spanne definieren
4. Die Vorschau erneut zeigen
5. Den Lifecycle-Tab zeigen und die Job-Zustaende erlaeutern

Was du sagen kannst:
- "Das System kann die Rechnung fuer uns uebernehmen."

Warum das wichtig ist:
- der Operator muss nicht jedes Mal selbst rechnen
- die Regel bleibt trotzdem sichtbar und kontrollierbar

## Wichtige Parameter einfach erklaert

- `enabled`
  Schaltet den Scheduler an oder aus.
- `mode`
  Waehlt manuelle oder automatische Planung.
- `reminder_count`
  Wie viele Erinnerungen erzeugt werden.
- `last_reminder_gap_before_appointment_hours`
  Der letzte Punkt vor dem Termin.
- `max_span_between_first_and_last_reminder_hours`
  Verhindert eine zu grosse Spanne.
- `channel_rcs_sms_enabled`
  Zeigt, dass die Plattform Erinnerungen ueber Messaging senden kann.
- `lifecycle_states`
  Zeigt die Job-Zustaende, die der Operator im Cockpit erwarten kann.

## Schlusssatz

- "Dieses Cockpit macht aus Reminder-Planung eine klare Operator-Aufgabe statt eines versteckten Hintergrundprozesses."
