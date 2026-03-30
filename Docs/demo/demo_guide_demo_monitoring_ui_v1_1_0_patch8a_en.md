# Demo Guide Demo Monitoring UI v1.1.0 Patch 8a

Version: v1.1.0-patch8a
Audience: Demo
Language: EN

## Best Patch 8a story

Show that the system now protects the slot between selection and final booking.

## Demo flow

1. Open the cockpit route `v1.1.0-patch8a`.
2. Go to `Settings` and point to `Slot Hold Minutes`.
3. Explain that the default demo value is `2`.
4. Go back to `Dashboard` and click a slot button.
5. Show that the slot is now temporarily reserved.
6. Open `Monitoring` and point to:
   - `slot.hold.created`
   - `slot.hold.active`
7. Explain that final booking only works while the hold is active.

## What to say

- The hold is not only in Google. It lives in our platform state.
- This is how we stop parallel booking races.
- Google is still checked again before final booking.

## Why the system temporarily reserves a slot

Two users can look at the same free slot at the same time.

The temporary hold gives one journey a short protected window.

That makes the platform safer and more realistic.
