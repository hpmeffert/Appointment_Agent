# Reminder Scheduler v1.3.3

Version: v1.3.3
Audience: Admin
Language: DE

## Ziel dieses Releases

`v1.3.3` haelt die Reminder-Scheduler-Linie bei und macht zusaetzlich Sync-Fenster, Change Detection und Idempotenz leichter sichtbar.

Das Ziel ist einfach:
- Termine lesen
- Reminder-Zeiten berechnen
- Regelwerk speichern
- das Ganze in einem leicht verstaendlichen Cockpit zeigen
- zeigen, wie das Sync-Fenster arbeitet
- zeigen, wann Aenderungen Updates oder Stornos ausloesen

## Architektur in einfachen Worten

Das Modul hat mehrere Teile:
- Setup-UI
  Ein Operator kann hier die Reminder-Regeln aendern.
- Vorschau-Engine
  Zeigt die geplanten Zeiten, bevor etwas gespeichert oder versendet wird.
- Job-Liste
  Zeigt, welche Reminder-Jobs entstehen wuerden.
- Scheduler-Logik
  Erzeugt und versendet spaeter die echten Jobs.
- Gemeinsamer Speicher
  Haelt Regeln und Job-Status im gemeinsamen Plattform-DB-Layer fest.
- Sync-Bewusstsein
  Zeigt das Sync-Fenster, die Hash-Pruefung und den Idempotenz-Schutz an.

## Wichtige Reminder-Parameter

- `enabled`
  Schaltet den Scheduler an oder aus.
- `mode`
  `manual` bedeutet: der Operator gibt die Zeiten direkt ein.
  `auto_distributed` bedeutet: das System berechnet die Zeiten automatisch.
- `reminder_count`
  Wie viele Erinnerungen es pro Termin gibt.
  Erlaubt sind `0` bis `3`.
- `first_reminder_hours_before`
  Die weiteste Erinnerung im manuellen Modus.
- `second_reminder_hours_before`
  Die zweite Erinnerung im manuellen Modus.
- `third_reminder_hours_before`
  Die dritte Erinnerung im manuellen Modus.
- `max_span_between_first_and_last_reminder_hours`
  Maximaler Abstand zwischen erster und letzter Erinnerung bei automatischer Verteilung.
- `last_reminder_gap_before_appointment_hours`
  Die letzte Erinnerung soll so viele Stunden vor dem Termin liegen.
- `enforce_max_span`
  Wenn `true`, warnt die Vorschau bei zu grosser Spanne.
- `preload_window_hours`
  Wie weit das System im Voraus nach Terminen schauen soll.
- `sync_window_days`
  Wie viele Tage voraus der Adapter nach Änderungen schaut.
- `polling_interval_minutes`
  Wie oft der Adapter erneut prueft.
- `hash_detection_enabled`
  Schaltet die Hash-basierte Change Detection an oder aus.
- `idempotency_guard`
  Verhindert doppelte Jobs, wenn derselbe Termin erneut auftaucht.
- `channel_email_enabled`
  Erlaubt E-Mail-Erinnerungen.
- `channel_voice_enabled`
  Erlaubt Voice-Erinnerungen.
- `channel_rcs_sms_enabled`
  Erlaubt RCS- oder SMS-Erinnerungen.

## Sync-Fenster und Change Detection

Das Cockpit zeigt jetzt eine kleine Sync-Box fuer den Kalender-Adapter.

Das ist wichtig, weil:
- wiederholte Sync-Laufe keine doppelten Termine erzeugen sollen
- geaenderte Termine den Reminder-Plan vorhersehbar bewegen sollen
- stornierte Termine den Reminder-Plan sauber stoppen sollen

Der Block `sync_awareness` erklaert:
- `adapter_name`
  Die erwartete Adapter-Art, zum Beispiel `calendar-adapter`.
- `sync_window_days`
  Wie viele Tage voraus der Adapter prueft.
- `polling_interval_minutes`
  Wie oft der Adapter nach Aenderungen schaut.
- `hash_detection_enabled`
  Ob der Sync Hashes vergleicht, um Aenderungen zu erkennen.
- `idempotency_guard`
  Ob Wiederholungen vor doppelten Jobs geschuetzt werden.

## Job-Lifecycle-Zustaende

Das Cockpit zeigt die wichtigsten Reminder-Job-Zustaende klarer:
- `planned`
- `dispatching`
- `sent`
- `failed`
- `skipped`
- `cancelled`

So kann ein Admin schneller sehen, was der Scheduler gerade macht.

## Reminder-Reconciliation

Wenn der Sync eine Aenderung sieht, soll das Cockpit die Wirkung leicht verstaendlich zeigen.

Das hilft bei:
- einem neuen Termin
- einer Zeitaenderung, die Erinnerungen verschiebt
- einer Stornierung, bei der die Jobs stoppen muessen

## Pruefregeln

- Reminder-Anzahl muss zwischen `0` und `3` liegen
- Stunden duerfen nicht negativ sein
- manuelle Zeiten muessen in der richtigen Reihenfolge sein
- doppelte Zeiten sollten vermieden werden
- die maximale Spanne muss eingehalten werden, wenn sie aktiv ist

## API fuer die erste Linie

Das Modul ist auf diese Routen ausgelegt:
- `GET /api/reminders/v1.3.3/config`
- `GET /api/reminders/v1.3.3/config/preview`
- `GET /api/reminders/v1.3.3/jobs`
- `GET /api/reminders/v1.3.3/rebuild`
- `GET /api/reminders/v1.3.3/health`

## Was Admins pruefen sollten

1. Die Setup-Seite laedt.
2. Die Vorschau aendert sich bei Parameteraenderungen.
3. Die Job-Liste zeigt die geplanten Erinnerungen.
4. Der Pruefbereich erklaert Fehler in einfacher Sprache.
5. Die Versionsnummer ist im Header und im Help-Text sichtbar.
