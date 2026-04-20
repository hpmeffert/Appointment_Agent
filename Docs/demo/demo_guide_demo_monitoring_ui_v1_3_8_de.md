# Demo Leitfaden v1.3.8

## Story 1: Absage

Sage:

- Der Kunde antwortet mit einem klaren Absagewunsch.
- Die Plattform erkennt `Reply Intent = cancel`.
- Die Plattform bereitet `appointment.cancel_requested` vor.

## Story 2: Naechste Woche

Sage:

- Der Kunde waehlt noch keinen exakten Slot.
- Die Plattform erkennt `appointment_next_week`.
- Die Plattform bereitet `appointment.find_slot_next_week_requested` vor.

## Story 3: Slot-Auswahl

Sage:

- Der Kunde waehlt eine konkrete Uhrzeit oder eine Reihenfolge wie `der erste`.
- Die Plattform extrahiert einen Slot-Kandidaten.
- Der Operator sieht, ob diese Wahl sicher oder noch mehrdeutig ist.
