# Demo Monitoring UI v1.2.0

Version: v1.2.0
Audience: Admin
Language: EN

## What v1.2.0 represents

`v1.2.0` is the first consolidated integrated demonstrator release.

It combines:

- interactive communication actions
- interactive slot buttons
- live booking checks
- slot holds
- conflict handling
- monitoring updates across the full flow

## Important parameters

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Temporary reservation length.
  Demo recommendation: `2`
  Realistic operation: `3-10`

- `APPOINTMENT_AGENT_BOOKING_WINDOW_DAYS`
  Search horizon for appointment slots.

- `APPOINTMENT_AGENT_MAX_SLOTS_PER_OFFER`
  How many slot options the operator flow should return.

- `APPOINTMENT_AGENT_DEFAULT_DURATION_MINUTES`
  Standard appointment length.

- `APPOINTMENT_AGENT_RESCHEDULE_CUTOFF_HOURS`
  Minimum lead time before an appointment can still be moved.

- `APPOINTMENT_AGENT_QUIET_HOURS`
  Messaging quiet period.

- `GOOGLE_TEST_MODE_DEFAULT`
  Default runtime mode.
  `simulation`: no real Google writes
  `test`: writes to the configured Google test calendar

## Parallel booking explanation

1. A slot is offered.
2. A user clicks it.
3. The platform creates a temporary hold.
4. Another user should no longer get the same slot.
5. Before booking, Google is checked live again.
6. If Google changed, the booking is blocked and alternatives are shown.
