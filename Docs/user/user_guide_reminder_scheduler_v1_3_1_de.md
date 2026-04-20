# User Guide Reminder Scheduler v1.3.1

Version: v1.3.1
Audience: User
Language: DE

## Wofuer dieses Cockpit da ist

Das Cockpit hilft einem Operator bei drei Dingen:
- Reminder-Regeln setzen
- Reminder-Zeiten ansehen
- verstehen, welche Jobs das System erzeugen wuerde

## Hauptseiten

- `Dashboard`
  Zeigt den Reminder-Ueberblick und die Demo-Stories.
- `Setup`
  Hier aendert der Operator die Reminder-Regeln.
- `Preview`
  Zeigt die berechneten Reminder-Zeiten vor dem Versand.
- `Jobs`
  Zeigt die Jobs, die entstehen wuerden.
- `Lifecycle`
  Zeigt die wichtigen Job-Zustaende wie planned, dispatching, sent, failed, skipped und cancelled.
- `Help`
  Zeigt kurze Erklaerungen und Dokument-Links.

## Die wichtigsten Parameter

- `enabled`
  Schaltet Reminder an oder aus.
- `mode`
  `manual` bedeutet: die Zeiten werden manuell gesetzt.
  `auto_distributed` bedeutet: das System berechnet die Zeiten.
- `reminder_count`
  Wie viele Erinnerungen pro Termin entstehen.
- `first_reminder_hours_before`
  Die weiteste Erinnerung im manuellen Modus.
- `second_reminder_hours_before`
  Die zweite Erinnerung im manuellen Modus.
- `third_reminder_hours_before`
  Die dritte Erinnerung im manuellen Modus.
- `last_reminder_gap_before_appointment_hours`
  Wie nah die letzte Erinnerung am Termin liegen soll.
- `preload_window_hours`
  Wie weit im Voraus das System Termine ansieht.
- `channel_email_enabled`
  Erlaubt E-Mail-Erinnerungen.
- `channel_voice_enabled`
  Erlaubt Voice-Erinnerungen.
- `channel_rcs_sms_enabled`
  Erlaubt RCS- oder SMS-Erinnerungen.

## Reminder-Lifecycle

- `planned`
  Der Job ist angelegt und wartet auf seine Sendezeit.
- `dispatching`
  Das System versendet die Erinnerung gerade.
- `sent`
  Die Erinnerung wurde erfolgreich verschickt.
- `failed`
  Der Sendeversuch hat nicht funktioniert.
- `skipped`
  Der Job wurde bewusst nicht versendet.
- `cancelled`
  Der Job wurde gestoppt, weil sich der Termin geaendert hat oder die Planung neu gebaut wurde.

## So benutzt man die Setup-Seite

1. Mit den Standardwerten starten.
2. `manual` oder `auto_distributed` waehlen.
3. Die gewuenschte Anzahl an Erinnerungen setzen.
4. Die Vorschau kontrollieren.
5. Die Pruefung lesen, bevor man etwas speichert.

## Einfache Faustregel

- eine Erinnerung ist am einfachsten zu erklaeren
- drei Erinnerungen zeigen die volle Staerke des Schedulers
- auto distributed ist gut, wenn das System die Rechnung uebernehmen soll
