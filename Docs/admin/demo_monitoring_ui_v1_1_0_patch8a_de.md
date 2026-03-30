# Demo Monitoring UI v1.1.0 Patch 8a

Version: v1.1.0-patch8a
Audience: Admin
Language: DE

## Was Patch 8a ergaenzt

Patch 8a behaelt das akzeptierte Incident-artige Cockpit, fuegt aber eine wichtige Sicherheitsschicht fuer die Terminlogik hinzu:

- temporaere Slot-Holds
- Schutz gegen parallele Buchungen
- Ablauf von Holds
- einstellbare Hold-Dauer

## Warum Slot-Holds wichtig sind

Ohne Slot-Hold koennten zwei Nutzer denselben freien Slot sehen und fast gleichzeitig buchen wollen.

Patch 8a verhindert genau das:

- Nutzer A waehlt einen Slot
- die Plattform erstellt eine temporaere Reservierung
- Nutzer B soll denselben Slot nicht mehr als frei sehen
- die finale Buchung funktioniert nur, solange der Hold noch aktiv ist

## Wichtige Parameter

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Das ist die Zeit fuer die temporaere Reservierung in Minuten.
  Standardwert in diesem Demo-Release: `2`

- `slot_id`
  Die interne Kennung eines Slots.

- `journey_id`
  Die eindeutige Kennung eines Terminablaufs.

- `hold_id`
  Die eindeutige Kennung einer temporaeren Reservierung.

- `expires_at_utc`
  Der Zeitpunkt, an dem der Hold nicht mehr gueltig ist.

## Wichtige Endpunkte

- `/api/google/v1.1.0-patch8a/slot-hold/create`
  Erstellt eine temporaere Reservierung.

- `/api/google/v1.1.0-patch8a/slot-hold/release`
  Gibt eine temporaere Reservierung frei.

- `/api/google/v1.1.0-patch8a/availability/slots`
  Liefert Slots, die nach Google-Konflikten und aktiven Holds noch frei sind.

- `/api/google/v1.1.0-patch8a/booking/create`
  Erstellt eine Buchung nur dann, wenn der Hold noch aktiv ist und der Provider-Check weiterhin positiv ist.

## Wichtige Monitoring-Labels

- `slot.hold.created`
- `slot.hold.active`
- `slot.hold.expired`
- `slot.hold.released`
- `slot.hold.consumed`
- `booking.blocked.by_parallel_request`
