# Demo Monitoring UI v1.1.0 Patch 8a

Version: v1.1.0-patch8a
Audience: Admin
Language: EN

## What Patch 8a adds

Patch 8a keeps the accepted Incident-style cockpit, but adds a safety layer for scheduling:

- temporary slot holds
- parallel booking protection
- hold expiration handling
- configurable hold duration

## Why slot holds matter

Without a slot hold, two users could see the same free slot and try to book it at the same time.

Patch 8a prevents that:

- user A selects a slot
- the platform creates a temporary hold
- user B should no longer get the same slot as free
- final booking only works while the hold is still active

## Main parameters

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  This is the temporary reservation time in minutes.
  Default for this demo release: `2`

- `slot_id`
  The internal identifier of one slot.

- `journey_id`
  The unique ID for one appointment flow.

- `hold_id`
  The unique ID for one temporary reservation.

- `expires_at_utc`
  The time when the hold stops being valid.

## Important endpoints

- `/api/google/v1.1.0-patch8a/slot-hold/create`
  Creates a temporary reservation.

- `/api/google/v1.1.0-patch8a/slot-hold/release`
  Releases a temporary reservation.

- `/api/google/v1.1.0-patch8a/availability/slots`
  Returns slots that are still free after Google conflicts and active holds are filtered out.

- `/api/google/v1.1.0-patch8a/booking/create`
  Creates a booking only if the hold is still active and the provider check still passes.

## Main monitoring labels

- `slot.hold.created`
- `slot.hold.active`
- `slot.hold.expired`
- `slot.hold.released`
- `slot.hold.consumed`
- `booking.blocked.by_parallel_request`
