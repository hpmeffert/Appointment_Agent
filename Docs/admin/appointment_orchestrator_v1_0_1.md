# Appointment Orchestrator v1.0.1 Admin Notes

## Einfache Kurzbeschreibung

Der Orchestrator ist die zentrale Steuerung fuer Termin-Ablaufe.
Er entscheidet nicht nur "was", sondern auch "warum als Naechstes".

In `v1.0.1` kann er jetzt:

- freie Termine suchen
- keine freien Termine sinnvoll behandeln
- Buchungen bestaetigen
- Buchungen verschieben
- Buchungen absagen
- Menschen einschalten
- Audit-Daten speichern

## Was ist technisch neu?

- `audit_records`
  Das ist eine eigene Tabelle fuer wichtige Entscheidungen.
  Dort werden Dinge gespeichert wie:
  - warum eskaliert wurde
  - warum ein Reminder geschickt wurde
  - warum ein Reschedule erlaubt oder abgelehnt wurde

- No-Slot-Strategie
  Wenn keine freien Termine gefunden werden, macht das System nicht einfach Schluss.
  Es kann stattdessen:
  - einen groesseren Zeitraum versuchen
  - mehr Praeferenzen anfragen
  - einen Rueckruf anbieten
  - an einen Menschen uebergeben

- Google Adapter `v1.0.1`
  Der Orchestrator nutzt jetzt den Google Adapter wirklich fuer:
  - Slot-Suche
  - Booking-Create
  - Reschedule-Update
  - Cancellation

## Wichtige Parameter und Felder

- `journey_id`
  Die Haupt-ID fuer einen kompletten Termin-Ablauf.
  Alles, was zu diesem Ablauf gehoert, wird darueber zusammengefuehrt.

- `correlation_id`
  Technische Verfolgungs-ID fuer Logs, Audit und Events.
  Sehr wichtig fuer Fehlersuche.

- `booking_reference`
  Die interne Termin-ID unseres Systems.

- `provider_reference`
  Die externe ID beim Provider.
  Bei Google ist das die Referenz zum Kalendereintrag.

- `current_state`
  Der aktuelle Zustand des Ablaufs.
  Beispiele:
  - `WAITING_FOR_SELECTION`
  - `BOOKED`
  - `REMINDER_PENDING`
  - `ESCALATED`

- `reason_code`
  Kurzer technischer Grundcode im Audit.
  Beispiel:
  - `no_slots`
  - `reschedule_allowed`
  - `missing_provider_reference`

## Warum das wichtig ist

Spaeter soll man Antworten geben koennen auf Fragen wie:

- Warum wurde kein Termin angeboten?
- Warum wurde der Nutzer an einen Menschen weitergegeben?
- Warum ist die Buchung fehlgeschlagen?
- Welche externe Google-Referenz gehoert zu welcher internen Buchung?

Darum werden diese Informationen nicht nur geloggt, sondern gespeichert.
