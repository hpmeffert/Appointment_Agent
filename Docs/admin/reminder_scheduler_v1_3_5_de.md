# Reminder Scheduler v1.3.5

Version: v1.3.5
Audience: Admin
Language: DE

## Patch-Ziel

`v1.3.5` zeigt die Delivery-Schicht in einem einfachen Cockpit und macht den Runtime-Zustand leichter verstaendlich.

Das Cockpit erklaert drei Dinge:
- welcher Delivery-Kanal gewaehlt wird
- warum die Validation erlaubt oder blockiert
- welches Delivery-Ergebnis entstanden ist
- was als Naechstes geplant ist und wann das System zuletzt aktiv war

## Seiten im Cockpit

- `Dashboard`
  Zeigt die Uebersicht und die Demo-Stories.
- `Delivery`
  Hier kann der Operator die Delivery-Parameter aendern.
- `Validation`
  Zeigt, warum Delivery bereit, gewarnt oder blockiert ist.
- `Results`
  Zeigt sent, fallback_sent, blocked, retrying, failed und skipped.
- `Channels`
  Zeigt, welche Kanaele bereit sind.
- `Operator`
  Zeigt den einfachen Schritt-fuer-Schritt-Ablauf.
- `Help`
  Zeigt Links und kurze Erklaerungen.

## Wichtige Parameter

- `enabled`
  Schaltet Delivery an oder aus.
- `delivery_mode`
  `priority_order` nutzt zuerst einen Kanal.
  `fallback_chain` erlaubt einen Backup-Weg.
- `primary_channel`
  Der erste Kanal, den das System versucht.
- `allow_fallback_channels`
  Erlaubt einen anderen Kanal, wenn der erste nicht bereit ist.
- `validate_recipient`
  Prueft das Ziel vor dem Start.
- `validate_channel`
  Prueft, ob der gewaehlte Kanal erlaubt ist.
- `max_retry_count`
  Wie viele Versuche erlaubt sind.
- `delivery_window_minutes`
  Wie lange das Delivery-Fenster offen bleibt.
- `message_length_limit`
  Wie lang die Nachricht sein darf, bevor das Cockpit blockiert.
- `result_retention_days`
  Wie lange Ergebnisse sichtbar bleiben.
- `channel_email_enabled`
  Erlaubt E-Mail-Delivery.
- `channel_voice_enabled`
  Erlaubt Voice-Delivery.
- `channel_rcs_sms_enabled`
  Erlaubt RCS/SMS-Delivery.

## Validation-Ergebnisse

- `passed`
  Delivery ist bereit.
- `warning`
  Der Operator sollte die Einstellung noch einmal pruefen.
- `blocked`
  Delivery darf noch nicht starten.

## Delivery-Ergebnisse

- `sent`
  Die Nachricht wurde auf dem gewaehlten Kanal geschickt.
- `fallback_sent`
  Die Nachricht nutzte einen Backup-Kanal.
- `blocked`
  Delivery wurde vor dem Senden gestoppt.
- `retrying`
  Das System versucht es noch einmal.
- `failed`
  Delivery hat nicht geklappt.
- `skipped`
  Delivery wurde nicht gestartet.

## API-Routen fuer diese Release-Linie

- `GET /api/reminder-ui/v1.3.5/payload`
- `GET /api/reminder-ui/v1.3.5/help`
- `GET /api/reminder-ui/v1.3.5/config`
- `GET /api/reminder-ui/v1.3.5/config/preview`
- `GET /api/reminder-ui/v1.3.5/results`
- `GET /api/reminder-ui/v1.3.5/health`
- `GET /api/reminders/v1.3.5/health`

## Was der Admin pruefen sollte

1. Der Header zeigt `v1.3.5`.
2. Das Cockpit zeigt Kanaele, Validation und Ergebnisse.
3. Die Hilfe erklaert die Parameter in einfacher Sprache.
4. Die Demo-Stories sind kurz genug, um sie schnell zu praesentieren.
