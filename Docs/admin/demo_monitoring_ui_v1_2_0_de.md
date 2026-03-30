# Demo Monitoring UI v1.2.0

Version: v1.2.0
Audience: Admin
Language: DE

## Was v1.2.0 darstellt

`v1.2.0` ist der erste konsolidierte integrierte Demonstrator-Release.

Er verbindet:

- interaktive Kommunikationsaktionen
- interaktive Slot-Buttons
- Live-Booking-Pruefungen
- Slot-Holds
- Konfliktbehandlung
- Monitoring-Updates ueber den ganzen Ablauf

## Wichtige Parameter

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Laenge der temporaeren Reservierung.
  Demo-Empfehlung: `2`
  Realistische Nutzung: `3-10`

- `APPOINTMENT_AGENT_BOOKING_WINDOW_DAYS`
  Suchhorizont fuer Termin-Slots.

- `APPOINTMENT_AGENT_MAX_SLOTS_PER_OFFER`
  Wie viele Slot-Optionen zurueckgegeben werden.

- `APPOINTMENT_AGENT_DEFAULT_DURATION_MINUTES`
  Standard-Laenge eines Termins.

- `APPOINTMENT_AGENT_RESCHEDULE_CUTOFF_HOURS`
  Mindestvorlauf fuer Verschiebungen.

- `APPOINTMENT_AGENT_QUIET_HOURS`
  Ruhezeit fuer Messaging.

- `GOOGLE_TEST_MODE_DEFAULT`
  Standard-Laufzeitmodus.
  `simulation`: keine echten Google-Schreibzugriffe
  `test`: schreibt in den konfigurierten Google-Testkalender
