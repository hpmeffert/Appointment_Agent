# Demo Guide v1.3.8

## Story 1: Cancel

Say:

- The customer replies with a clear cancel request.
- The platform sees `Reply Intent = cancel`.
- The platform prepares `appointment.cancel_requested`.

## Story 2: Next week

Say:

- The customer does not choose an exact slot yet.
- The platform sees `appointment_next_week`.
- The platform prepares `appointment.find_slot_next_week_requested`.

## Story 3: Slot choice

Say:

- The customer picks a concrete time or an ordered option like `the first one`.
- The platform extracts a slot candidate.
- The operator can see whether that choice is safe or still ambiguous.
