# User Guide Demo Monitoring UI v1.1.0 Patch 8

Version: v1.1.0-patch8
Audience: User
Language: EN

## What is new

Patch 8 makes Google-backed booking behavior more realistic.

If you choose a slot, the backend can now:

- check if it is still free
- stop the booking if another event blocks it
- suggest other slots

## What happens if a slot is no longer available

The system now returns a friendly message:

- the selected slot is no longer available
- please choose one of the alternatives

This means the demo behaves more like a real calendar system.

## What create, cancel, and reschedule do

- `Create`
  Books the slot if it is still free.

- `Cancel`
  Removes the booking.

- `Reschedule`
  Checks the new slot again before moving the booking.
