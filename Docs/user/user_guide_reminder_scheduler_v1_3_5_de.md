# User Guide Reminder Scheduler v1.3.5

Version: v1.3.5
Audience: User
Language: DE

## Wofuer dieses Cockpit da ist

Das Cockpit hilft dem Operator bei drei Dingen:
- einen Delivery-Kanal waehlen
- pruefen, ob Delivery erlaubt ist
- das Delivery-Ergebnis sehen
- verstehen, was das System als Naechstes machen wird

## Die wichtigsten Seiten

- `Dashboard`
  Zeigt die Uebersicht und die Demo-Stories.
- `Delivery`
  Hier kann der Operator die Delivery-Einstellungen aendern.
- `Validation`
  Zeigt, warum Delivery bereit, gewarnt oder blockiert ist.
- `Results`
  Zeigt die Delivery-Ergebnisse in einer einfachen Liste.
- `Channels`
  Zeigt, welche Kanaele bereit sind.
- `Operator`
  Zeigt den einfachen Ablauf fuer den Operator.
- `Help`
  Zeigt kurze Erklaerungen und Dokument-Links.

## Die wichtigsten Parameter

- `enabled`
  Schaltet Delivery an oder aus.
- `delivery_mode`
  `priority_order` bedeutet: der erste Kanal gewinnt.
  `fallback_chain` bedeutet: das System darf einen Backup-Kanal probieren.
- `primary_channel`
  Der erste Kanal, den das System versucht.
- `allow_fallback_channels`
  Erlaubt einen anderen Kanal, wenn der erste nicht bereit ist.
- `validate_recipient`
  Prueft, ob das Ziel gueltig aussieht.
- `validate_channel`
  Prueft, ob der Kanal erlaubt ist.
- `max_retry_count`
  Wie oft das System es noch einmal versuchen darf.
- `delivery_window_minutes`
  Wie lange das Delivery-Fenster offen bleibt.
- `message_length_limit`
  Wie gross die Nachricht sein darf.
- `result_retention_days`
  Wie lange das Ergebnis sichtbar bleibt.
- `db_status`
  Zeigt, ob die Datenbankverbindung in Ordnung ist.
- `worker_status`
  Zeigt, ob der Reminder-Worker bereit oder deaktiviert ist.
- `channel_email_enabled`
  Erlaubt E-Mail-Delivery.
- `channel_voice_enabled`
  Erlaubt Voice-Delivery.
- `channel_rcs_sms_enabled`
  Erlaubt RCS/SMS-Delivery.

## Validation-Ergebnisse in einfachen Worten

- `passed`
  Delivery kann starten.
- `warning`
  Der Operator sollte die Einstellungen noch einmal ansehen.
- `blocked`
  Delivery darf noch nicht starten.

## Delivery-Ergebnisse in einfachen Worten

- `sent`
  Die Nachricht wurde geschickt.
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

## So benutzt man das Cockpit

1. `Dashboard` oeffnen.
2. `Delivery` oeffnen.
3. Einen Kanal oder eine Pruefung aendern.
4. `Validation` oeffnen.
5. `Results` oeffnen.
6. Bei Bedarf `Help` oeffnen.

## Einfache Faustregel

- ein aktiver Kanal ist die einfachste Einstellung
- Fallback-Kanaele helfen, wenn der Hauptkanal beschaeftigt ist
- Validation zeigt Probleme frueh
