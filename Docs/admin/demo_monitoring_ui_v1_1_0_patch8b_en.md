# Demo Monitoring UI v1.1.0 Patch 8b

Version: v1.1.0-patch8b
Audience: Admin
Language: EN

## What Patch 8b changes

Patch 8b connects three earlier lines into one believable flow:

- Patch 7 interactive buttons
- Patch 8 live slot and booking logic
- Patch 8a slot holds and parallel booking protection

Now the cockpit can move from a button click to a real slot lookup, a real hold, and a real booking call.

## Full parameter explanations

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Temporary reservation duration.
  Lower value: slots return faster to the pool, but users have less time.
  Higher value: safer for slow users, but blocked slots stay unavailable longer.
  Demo recommendation: `2`
  Realistic operation: `3-10`, depending on channel and customer speed.

- `APPOINTMENT_AGENT_BOOKING_WINDOW_DAYS`
  How far into the future slot search can look.
  Lower value: faster and simpler, but less flexibility.
  Higher value: more choices, but more data and more complexity.
  Demo recommendation: `30`

- `APPOINTMENT_AGENT_MAX_SLOTS_PER_OFFER`
  How many slot suggestions the system should return.
  Lower value: simpler UI.
  Higher value: more choice, but more scanning work for the user.
  Demo recommendation: `3`

- `APPOINTMENT_AGENT_DEFAULT_DURATION_MINUTES`
  Standard appointment length when no other duration is specified.
  Lower value: more capacity, but less buffer.
  Higher value: safer timing, but fewer available slots.

- `APPOINTMENT_AGENT_RESCHEDULE_CUTOFF_HOURS`
  The minimum number of hours before an appointment when rescheduling is still allowed.

- `APPOINTMENT_AGENT_QUIET_HOURS`
  Time range when the system should avoid messaging customers.

- `GOOGLE_TEST_MODE_DEFAULT`
  Default operator mode.
  `simulation`: no real Google calendar writes
  `test`: writes to the configured Google test calendar

## How parallel booking protection works

1. A user chooses a slot.
2. The platform creates a temporary hold in its own state.
3. The same slot should disappear for other journeys.
4. Before final booking, Google Calendar is checked again live.
5. If Google changed, booking is blocked and alternatives are shown.

## Why Google still matters after a hold

The hold protects the slot inside our platform.

Google is still the live truth for occupancy.

That matters because:

- another process may create a calendar entry
- a human may add an event manually
- an external change may happen after the first slot search
