# User Guide v1.0.1

## Was ist das?

Der Appointment Orchestrator ist das "Gehirn" des Systems.
Er entscheidet, was als Naechstes passieren soll:

- freie Termine suchen
- einen Termin bestaetigen
- einen Termin verschieben
- einen Termin absagen
- einen Menschen einschalten, wenn die Automatik nicht reicht

Alle neuen Endpunkte dieser Version starten mit:

`/api/orchestrator/v1.0.1`

## Wichtige Grundbegriffe

- `journey_id`
  Das ist die eindeutige ID fuer einen kompletten Termin-Ablauf.
  Beispiel: von der ersten Nachricht bis zur fertigen Buchung.

- `correlation_id`
  Das ist eine Verfolgungs-ID.
  Mit ihr kann man spaeter in Logs, Audit-Daten und Events sehen, was zusammengehoert.

- `booking_reference`
  Das ist unsere eigene Termin-ID im System.

- `provider_reference`
  Das ist die ID beim externen System.
  In diesem Projekt ist das zum Beispiel die ID im Google-Kalender.

## Die wichtigsten Endpunkte

### `/journeys/start`

Startet einen neuen Termin-Ablauf.

Wichtige Parameter:

- `journey_id`
  Bedeutung: Eigene ID fuer diesen Ablauf.
  Typ: `string`
  Pflicht: Ja
  Beispiel: `"journey-1234abcd"`

- `tenant_id`
  Bedeutung: Zu welchem Kunden oder Systembereich die Daten gehoeren.
  Typ: `string`
  Pflicht: Ja
  Beispiel: `"demo"`

- `correlation_id`
  Bedeutung: Technische Nachverfolgungs-ID fuer Events und Audit.
  Typ: `string`
  Pflicht: Ja
  Beispiel: `"corr-77aa11bb"`

- `customer_id`
  Bedeutung: Die interne ID des Kunden.
  Typ: `string`
  Pflicht: Ja
  Beispiel: `"C-100"`

- `service_type`
  Bedeutung: Welche Art von Termin gesucht wird.
  Typ: `string`
  Pflicht: Ja
  Beispiel: `"consultation"`

- `timezone`
  Bedeutung: In welcher Zeitzone Uhrzeiten gelesen und angezeigt werden.
  Typ: `string`
  Pflicht: Ja
  Beispiel: `"Europe/Berlin"`

### `/journeys/select`

Speichert, welchen freien Termin der Nutzer ausgewaehlt hat.

Wichtige Parameter:

- `journey_id`
  Bedeutung: Auf welchen Ablauf sich die Auswahl bezieht.

- `slot_id`
  Bedeutung: Die ID des ausgewaehlten freien Termins.
  Beispiel: `"gslot-1"`

- `actor`
  Bedeutung: Wer die Auswahl gemacht hat.
  Meistens ist das `"customer"`.

### `/journeys/confirm`

Bestaetigt eine Buchung.
Ab hier wird der Termin wirklich ueber den Google Adapter verarbeitet.

Wichtige Parameter:

- `booking`
  Bedeutung: Das ist das eigentliche Buchungsobjekt.
  Es enthaelt z. B. `journey_id`, `slot_id`, `calendar_target`, `title` und `timezone`.

- `dispatch`
  Bedeutung: Das ist der Auftrag fuer die Benachrichtigung.
  Darin steht zum Beispiel, welche Nachricht an welche Telefonnummer gesendet werden soll.

Wichtige Felder in `booking`:

- `slot_id`
  Welcher freie Termin gebucht werden soll.

- `calendar_target`
  In welchem Kalender der Termin landen soll.

- `title`
  Der Titel des Termineintrags.

- `timezone`
  Welche Zeitzone fuer den Termin gilt.

### `/journeys/reschedule`

Startet den Verschiebe-Ablauf fuer einen schon bestehenden Termin.

Das System:

1. prueft, ob Verschieben erlaubt ist
2. sucht neue freie Termine
3. laesst den Nutzer einen neuen Termin waehlen
4. aktualisiert danach den Termin im Google Adapter

### `/journeys/cancel`

Sagt einen Termin ab.

Wichtige Parameter:

- `reason`
  Bedeutung: Warum abgesagt wird.
  Beispiel: `"customer_request"`

- `requested_by`
  Bedeutung: Wer die Absage ausgeloest hat.
  Beispiel: `"customer"`

### `/journeys/escalate`

Schaltet einen Menschen ein.
Das ist wichtig, wenn die Automatik nicht weiterkommt.

Beispiele:

- es gibt keine freien Termine
- ein Fehler im Provider ist passiert
- der Nutzer will Hilfe

### `/journeys/{journey_id}/audit`

Zeigt wichtige Entscheidungen des Systems.

Das ist besonders hilfreich, wenn man wissen will:

- warum ein Termin angeboten wurde
- warum eine Eskalation passiert ist
- warum ein Termin verschoben oder abgesagt wurde

## Was ist in v1.0.1 neu?

- Reschedule ist jetzt ein echter Ablauf
- Booking, Reschedule und Cancel nutzen Google Adapter `v1.0.1`
- Audit-Daten werden gespeichert
- CRM-Vorbereitungs-Events bleiben erhalten
