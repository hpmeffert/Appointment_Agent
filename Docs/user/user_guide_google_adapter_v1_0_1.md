# Google Adapter User Guide v1.0.1

## Was macht der Google Adapter?

Der Google Adapter ist die Schicht zwischen unserem System und dem Google-Kalender.

Wichtig:

- Der Orchestrator entscheidet die Logik.
- Der Google Adapter fuehrt die Kalender-Aktion aus.

Das heisst:

- freie Termine suchen
- Termin anlegen
- Termin aendern
- Termin absagen

Alle Endpunkte dieser Version starten mit:

`/api/google/v1.0.1`

## Wichtige Begriffe

- `booking_reference`
  Unsere eigene Buchungs-ID im System.

- `provider_reference`
  Die externe ID beim Provider.
  Hier ist das die Referenz zum Google-Kalendereintrag.

- `calendar_target`
  Der Kalender, in den geschrieben wird.
  Beispiel: `"advisor@example.com"`

## Endpunkt `/slots`

Sucht freie Termine.

Wichtige Parameter:

- `tenant_id`
  Bedeutung: Zu welchem Mandanten oder Kunden die Anfrage gehoert.

- `journey_id`
  Bedeutung: Zu welchem Ablauf diese Suche gehoert.

- `service_type`
  Bedeutung: Welche Art Termin gesucht wird.

- `duration_minutes`
  Bedeutung: Wie lange der Termin dauern soll.
  Typ: `integer`
  Beispiel: `30`

- `date_window_start`
  Bedeutung: Ab wann gesucht werden soll.
  Typ: `datetime`
  Beispiel: `"2026-03-28T00:00:00+01:00"`

- `date_window_end`
  Bedeutung: Bis wann gesucht werden soll.

- `timezone`
  Bedeutung: In welcher Zeitzone die Uhrzeiten gelten.

- `resource_candidates`
  Bedeutung: Liste von Kalendern oder Ressourcen, die geprueft werden sollen.
  Beispiel: `["advisor@example.com"]`

Rueckgabe:

- `slot_id`
  Unsere ID fuer einen freien Termin.

- `provider`
  Welcher Provider die Daten liefert.
  Hier: `"google"`

- `provider_reference`
  Externe Referenz fuer den Slot oder die Provider-Seite.

## Endpunkt `/bookings` mit `POST`

Legt einen Termin an.

Wichtige Parameter:

- `journey_id`
  Zu welchem Ablauf die Buchung gehoert.

- `booking_reference`
  Eigene Buchungs-ID.
  Wenn keine gesetzt wird, erzeugt das System eine.

- `slot_id`
  Welcher freie Termin gebucht werden soll.

- `calendar_target`
  In welchen Kalender geschrieben werden soll.

- `title`
  Titel des Kalendereintrags.

- `description`
  Zusatztext fuer den Termin.

- `timezone`
  Zeitzone des Termins.

Rueckgabe:

- `booking_reference`
  Unsere interne ID.

- `provider_reference`
  Die externe Google-Referenz.

- `status`
  Zum Beispiel `"CONFIRMED"`.

## Endpunkt `/bookings` mit `PATCH`

Aendert einen bestehenden Termin.

Wichtige Parameter:

- `booking_reference`
  Unsere interne Buchungs-ID.

- `provider_reference`
  Die externe Google-Referenz.
  Ohne diese Referenz weiss das System nicht sicher, welcher Kalendereintrag geaendert werden soll.

- `new_start`
  Neue Startzeit.

- `new_end`
  Neue Endzeit.

- `new_title`
  Neuer Titel, falls noetig.

Wenn `provider_reference` fehlt oder falsch ist, liefert der Adapter einen klaren Fehler statt still etwas Falsches zu tun.

## Endpunkt `/bookings/cancel`

Sagt einen Termin ab.

Wichtige Parameter:

- `booking_reference`
  Unsere interne ID.

- `provider_reference`
  Externe Google-Referenz.

- `reason`
  Grund fuer die Absage.

- `requested_by`
  Wer die Absage ausgeloest hat.

## Endpunkt `/bookings/{booking_reference}`

Liest die gespeicherte, normalisierte Buchung.

Das ist hilfreich, wenn man pruefen will:

- welche interne ID der Termin hat
- welche externe Provider-Referenz dazu gehoert
- welchen Status der Termin gerade hat
