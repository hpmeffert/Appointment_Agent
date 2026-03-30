# Demo Monitoring UI v1.1.0 Patch 8

Version: v1.1.0-patch8
Audience: Admin
Language: EN

## What Patch 8 adds

Patch 8 keeps the same Incident-style UI, but the Google backend becomes more realistic.

New Google endpoints now support:

- live slot retrieval
- availability checks before booking
- conflict detection
- alternative slot suggestions
- create, cancel, and reschedule flows

## Important endpoints

- `/api/google/v1.1.0-patch8/availability/slots`
  Returns normalized free slots.

- `/api/google/v1.1.0-patch8/availability/check`
  Checks whether one selected slot is still available.

- `/api/google/v1.1.0-patch8/booking/create`
  Creates a booking if the slot is still free.

- `/api/google/v1.1.0-patch8/booking/cancel`
  Cancels an existing booking.

- `/api/google/v1.1.0-patch8/booking/reschedule`
  Rechecks the new slot and then moves the booking.

## Provider-neutral slot model

Each slot is normalized as:

- `slot_id`
- `start`
- `end`
- `label`
- `available`
- `calendar_provider`

This matters because the UI should not need a redesign when the backend changes from simulation to Google or later to Microsoft.

## Conflict handling

Before a booking is created or rescheduled, the adapter checks for overlaps.

If there is a conflict:

- the booking is blocked
- `slot.conflict_detected` is emitted
- alternative slots are returned

## Main monitoring labels

- `slot.checked`
- `slot.conflict_detected`
- `booking.created`
- `booking.failed`
- `booking.rescheduled`
- `booking.cancelled`
