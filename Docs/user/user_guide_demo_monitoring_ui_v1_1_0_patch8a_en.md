# User Guide Demo Monitoring UI v1.1.0 Patch 8a

Version: v1.1.0-patch8a
Audience: User
Language: EN

## What is new

Patch 8a teaches the demo how to reserve a slot for a short time before final booking.

That means:

- if you pick a slot, it is temporarily protected
- another user should not book the same slot in parallel
- if you wait too long, the hold expires and the slot becomes free again

## The main parameter in simple words

- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  This says how many minutes the system should keep one selected slot reserved.

Example:

- value `2`
- the slot stays reserved for 2 minutes
- after that, the slot can be offered again

## What you can see in the cockpit

- a hold message after slot selection
- hold status in Monitoring
- hold duration in Settings

## Why this helps

This makes the demo feel much closer to a real booking platform because real systems must prevent double booking.
