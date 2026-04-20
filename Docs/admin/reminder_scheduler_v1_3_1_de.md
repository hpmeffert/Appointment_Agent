# Reminder Scheduler v1.3.1

Version: v1.3.1
Audience: Admin
Language: DE

## Ziel dieses Releases

`v1.3.1` haelt die Reminder-Scheduler-Linie bei und macht den Job-Lifecycle leichter sichtbar.

Das Ziel ist einfach:
- Termine lesen
- Reminder-Zeiten berechnen
- Regelwerk speichern
- das Ganze in einem leicht verstaendlichen Cockpit zeigen

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
- `channel_email_enabled`
  Erlaubt E-Mail-Erinnerungen.
- `channel_voice_enabled`
  Erlaubt Voice-Erinnerungen.
- `channel_rcs_sms_enabled`
  Erlaubt RCS- oder SMS-Erinnerungen.

## Job-Lifecycle-Zustaende

Das Cockpit zeigt die wichtigsten Reminder-Job-Zustaende klarer:
- `planned`
- `dispatching`
- `sent`
- `failed`
- `skipped`
- `cancelled`

So kann ein Admin schneller sehen, was der Scheduler gerade macht.

## Pruefregeln

- Reminder-Anzahl muss zwischen `0` und `3` liegen
- Stunden duerfen nicht negativ sein
- manuelle Zeiten muessen in der richtigen Reihenfolge sein
- doppelte Zeiten sollten vermieden werden
- die maximale Spanne muss eingehalten werden, wenn sie aktiv ist

## API fuer die erste Linie

Das Modul ist auf diese Routen ausgelegt:
- `GET /api/reminders/v1.3.1/config`
- `GET /api/reminders/v1.3.1/config/preview`
- `GET /api/reminders/v1.3.1/jobs`
- `GET /api/reminders/v1.3.1/rebuild`
- `GET /api/reminders/v1.3.1/health`

## Was Admins pruefen sollten

1. Die Setup-Seite laedt.
2. Die Vorschau aendert sich bei Parameteraenderungen.
3. Die Job-Liste zeigt die geplanten Erinnerungen.
4. Der Pruefbereich erklaert Fehler in einfacher Sprache.
5. Die Versionsnummer ist im Header und im Help-Text sichtbar.
