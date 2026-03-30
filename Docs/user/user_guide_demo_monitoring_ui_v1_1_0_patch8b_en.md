# User Guide Demo Monitoring UI v1.1.0 Patch 8b

Version: v1.1.0-patch8b
Audience: User
Language: EN

## What happens when you click a button

Patch 8b makes the demo more real.

When you click `Reschedule`, the system does not only change the screen.
It really loads the next appointment slots from the booking backend.

## What happens when you click a slot

When you choose a slot:

1. the slot is normalized
2. a temporary hold is created
3. the UI shows that the slot is reserved for a short time
4. the system waits for your confirmation

## Why the slot is only reserved temporarily

This prevents double booking.

The system gives one journey a short protected window, but it does not block the slot forever.

## Why a slot may become unavailable

A slot can disappear because:

- another user took it
- the hold expired
- a real Google calendar event blocks it

When that happens, the system shows a clear message and offers other times.
