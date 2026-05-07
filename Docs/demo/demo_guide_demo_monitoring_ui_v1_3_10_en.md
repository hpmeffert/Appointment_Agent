# Appointment Agent Demo Guide v1.3.10 (EN)

## Demo Focus
Use this release line to demonstrate:
- safe appointment identification
- explicit multi-appointment selection
- future-only slot search

## Story 1 — One appointment, direct reschedule
### Goal
Show that a unique appointment can be identified and rescheduled safely.

### Steps
1. Open the `Real` or `Simulation` flow with a known customer.
2. Trigger a reminder.
3. Choose `Reschedule`.
4. Show that the system proceeds directly because only one future appointment matches.
5. Select a future slot.
6. Confirm the booking update.

### What to call out
- no ambiguity dialog
- only future-valid slots
- final slot is rechecked before mutation

## Story 2 — Multiple appointments, explicit selection required
### Goal
Show that the system does not guess when the customer has more than one relevant future appointment.

### Steps
1. Prepare a customer with at least two future appointments.
2. Trigger `Reschedule` or `Cancel`.
3. Show that the system presents a selection step instead of mutating immediately.
4. Pick one appointment explicitly.
5. Continue the intended action only for the selected appointment.

### What to call out
- safe ambiguity handling
- one-vs-many boundary
- auditability of the selected target

## Story 3 — Future-only slot safety
### Goal
Show that the system does not offer stale or already elapsed slots.

### Steps
1. Trigger a slot search close to the current time.
2. Show that same-day past slots are filtered out.
3. Select a valid future slot.
4. Explain that the slot is checked again before mutation.

### What to call out
- minimum lead time of `30 minutes`
- same-day future filtering
- protected no-match / stale-slot behavior

## Operator Notes
- Keep the dashboard open to show message flow and state transitions.
- Use the customer journey output to explain whether the system resolved one appointment, several candidates, or no safe match.
- Mention that `v1.3.10` is non-breaking and additive.
