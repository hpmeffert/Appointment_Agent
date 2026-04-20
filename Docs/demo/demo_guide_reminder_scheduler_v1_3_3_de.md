# Demo Guide Reminder Scheduler v1.3.3

Version: v1.3.3
Audience: Demo
Language: DE

## Was diese Demo zeigen soll

Die Demo soll zeigen, dass Reminder-Planung einfach, sicher, erklaerbar und auch bei Lifecycle-Zustaenden gut lesbar ist.
Sie soll auch zeigen, dass Sync, Change Detection und Duplikatschutz sichtbar bleiben, ohne das Layout komplizierter zu machen.

Nutze diesen Satz:

- "Der Kunde sieht nur eine Erinnerung. Der Operator sieht den Plan dahinter."

## Empfohlene Reihenfolge

1. `Dashboard` oeffnen
2. Die Seite `Setup` zeigen
3. Zwischen `manual` und `auto_distributed` wechseln
4. `Preview` oeffnen
5. `Jobs` oeffnen
6. `Lifecycle` oeffnen
7. `Sync` oeffnen
8. Zum Schluss `Help` zeigen

## Story 1: Neue Termin-Synchronisation

1. Die Seite `Sync` oeffnen
2. Auf das Sync-Fenster und die Hash-Pruefung zeigen
3. Erklaeren, wie aus einem neuen Termin genau ein Reminder-Plan wird
4. Erklaeren, dass doppelte Jobs bei wiederholten Sync-Laufen blockiert werden

Warum das wichtig ist:
- wiederholte Sync-Laufe duerfen keine Duplikate erzeugen
- der Operator soll verstehen, wann ein neuer Termin zu einem Reminder-Plan wird

## Story 2: Update-Sync

1. Die Seite `Sync` wieder oeffnen
2. Erklaeren, dass geaenderte Termine den Reminder-Plan vorhersehbar bewegen
3. Die Lifecycle-Liste und den Reminder-Plan zusammen zeigen
4. Auf den Duplikatschutz hinweisen

Was du sagen kannst:
- "Das Cockpit zeigt, warum sich der Plan geaendert hat, und haelt die Liste frei von Duplikaten."

Warum das wichtig ist:
- Teams vertrauen dem Adapter-Verhalten
- der Reminder-Plan bleibt leicht erklaerbar

## Story 3: Cancel-Sync

1. Die Seite `Sync` wieder oeffnen
2. Erklaeren, dass stornierte Termine den Reminder-Plan sauber stoppen
3. Zeigen, dass die Reminder-Jobs auf vorhersehbare Weise verschwinden
4. Die Lifecycle-Liste sichtbar halten

Was du sagen kannst:
- "Das System reagiert auf den Terminstatus statt alte Jobs stehenzulassen."

Warum das wichtig ist:
- Teams koennen die Aenderung ohne Backend-Jargon erklaeren
- der Operator sieht in einfacher Sprache, was passiert ist

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
- `sync_window_days`
  Zeigt, wie viele Tage voraus der Adapter schaut.
- `polling_interval_minutes`
  Zeigt, wie oft der Adapter erneut prueft.
- `hash_detection_enabled`
  Zeigt, ob der Adapter Hashes vergleicht, um Aenderungen zu erkennen.
- `idempotency_guard`
  Zeigt, ob doppelte Jobs bei wiederholten Laufen blockiert werden.
- `lifecycle_states`
  Zeigt die Job-Zustaende, die der Operator im Cockpit erwarten kann.

## Schlusssatz

- "Dieses Cockpit macht aus Reminder-Planung eine klare Operator-Aufgabe statt eines versteckten Hintergrundprozesses."
