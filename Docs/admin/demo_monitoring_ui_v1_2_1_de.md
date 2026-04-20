# Admin Guide Demo Monitoring UI v1.2.1

Version: v1.2.1
Sprache: DE

## Was neu ist

`v1.2.1` macht aus dem oeffentlichen Demonstrator ein messaging-faehiges Cockpit.

Neue Teile:
- `Message Monitor`
- `Communications Reports`
- `LEKAB Adapter v1.2.1` fuer normalisierten RCS/SMS-Verkehr

## Architektur einfach erklaert

Die UI liest keine rohen LEKAB-Antworten direkt.

Der Ablauf ist:
1. LEKAB-artiger Provider-Verkehr kommt im Adapter an
2. der Adapter normalisiert ihn in ein internes Nachrichtenmodell
3. der Message Monitor liest dieses gemeinsame Modell
4. die Berichtsseite zeigt dieselben Daten in einer praesentationsfreundlichen Form

## Wichtige Parameter

- `message_id`: interne stabile Plattform-ID
- `provider_message_id`: externe Provider-Nachrichten-ID
- `provider_job_id`: externer Workflow- oder Batch-Bezug
- `channel`: zum Beispiel `RCS` oder `SMS`
- `direction`: `outbound` oder `inbound`
- `status`: zum Beispiel `accepted`, `delivered`, `received` oder `failed`
- `customer_id`: interne Kunden-ID
- `contact_reference`: Kontakt- oder Addressbook-Bezug
- `phone_number`: zugehoerige Telefonnummer
- `journey_id`: Flow- oder Journey-Bezug
- `booking_reference`: Terminbezug
- `message_type`: zum Beispiel `text`, `card` oder `reply`
- `body`: eigentlicher Nachrichteninhalt
- `actions`: optionale Buttons oder Antwortaktionen

## Message Monitor

Die Seite zeigt:
- Summenkarten
- Filter fuer `channel`, `direction` und `status`
- Nachrichtenliste
- Detailkarte

## Berichtssicht

Die Berichtsseite uebernimmt das Incident-artige Reporting-Gefuehl fuer:
- Demo-Erklaerung
- Admin-Sicht
- Kunden-/Journey-Kontext
