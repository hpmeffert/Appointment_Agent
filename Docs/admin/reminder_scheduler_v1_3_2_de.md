# Reminder Scheduler v1.3.2

Version: v1.3.2
Audience: Admin
Language: DE

## Ziel dieses Releases

`v1.3.2` haelt die Reminder-Scheduler-Linie bei und macht zusaetzlich Zeitzone, Sommerzeit und nahe Termine leichter sichtbar.

Das Ziel ist einfach:
- Termine lesen
- Reminder-Zeiten berechnen
- Regelwerk speichern
- das Ganze in einem leicht verstaendlichen Cockpit zeigen
- Zeitzone und Sommerzeit sichtbar machen
- nahe Erinnerungen leicht erkennbar machen

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
- Zeit-Bewusstsein
  Zeigt die Zeitzone, die DST-Info und den Bereich fuer nahe Erinnerungen an.

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

## Zeitzone und Sommerzeit

Das Cockpit zeigt jetzt die Zeitzone des Termins.

Das ist wichtig, weil:
- 08:00 Uhr in einer Zeitzone nicht immer 08:00 Uhr in einer anderen Zeitzone ist
- Sommerzeit den lokalen Kalender verschieben kann
- nahe Erinnerungen schwerer zu lesen sind, wenn die Zeit kurz vor dem Jetzt liegt

Der Block `time_awareness` erklaert:
- `timezone`
  Die lokale Zeitzone des Termins, zum Beispiel `Europe/Berlin`.
- `dst_guard`
  Sagt, ob das Cockpit auf Sommerzeit achten soll.
- `near_term_window_hours`
  Zeigt, wie viele Stunden als nahe Erinnerung gelten und extra sichtbar sein sollen.

## Job-Lifecycle-Zustaende

Das Cockpit zeigt die wichtigsten Reminder-Job-Zustaende klarer:
- `planned`
- `dispatching`
- `sent`
- `failed`
- `skipped`
- `cancelled`

So kann ein Admin schneller sehen, was der Scheduler gerade macht.

## Verhalten fuer nahe Erinnerungen

Wenn eine Erinnerung sehr nah am aktuellen Zeitpunkt liegt, soll das Cockpit sie klar zeigen.

Das hilft bei:
- Erinnerungen, die bald faellig sind
- Zeitverschiebungen durch Sommerzeit
- der Kontrolle der letzten Erinnerung vor dem Termin

## Pruefregeln

- Reminder-Anzahl muss zwischen `0` und `3` liegen
- Stunden duerfen nicht negativ sein
- manuelle Zeiten muessen in der richtigen Reihenfolge sein
- doppelte Zeiten sollten vermieden werden
- die maximale Spanne muss eingehalten werden, wenn sie aktiv ist

## API fuer die erste Linie

Das Modul ist auf diese Routen ausgelegt:
- `GET /api/reminders/v1.3.2/config`
- `GET /api/reminders/v1.3.2/config/preview`
- `GET /api/reminders/v1.3.2/jobs`
- `GET /api/reminders/v1.3.2/rebuild`
- `GET /api/reminders/v1.3.2/health`

## Was Admins pruefen sollten

1. Die Setup-Seite laedt.
2. Die Vorschau aendert sich bei Parameteraenderungen.
3. Die Job-Liste zeigt die geplanten Erinnerungen.
4. Der Pruefbereich erklaert Fehler in einfacher Sprache.
5. Die Versionsnummer ist im Header und im Help-Text sichtbar.
