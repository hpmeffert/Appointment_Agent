# Demo Guide Reminder Scheduler v1.3.3

Version: v1.3.3
Audience: Demo
Language: EN

## What this demo should show

This demo should show that reminder planning is simple, safe, explainable, and easy to operate even when lifecycle states change.
It should also show that sync, change detection, and duplicate protection stay visible without adding extra complexity.

Use this line:

- "The customer only sees a reminder. The operator sees the plan behind it."

## Suggested screen order

1. Open `Dashboard`.
2. Show the `Setup` page.
3. Switch between `manual` and `auto_distributed`.
4. Open `Preview`.
5. Open `Jobs`.
6. Open `Lifecycle`.
7. Open `Sync`.
8. End with `Help`.

## Story 1: New appointment sync

1. Open the `Sync` page.
2. Point at the sync window and hash detection notes.
3. Show how a new appointment becomes one reminder plan.
4. Explain that duplicate jobs are blocked on repeated sync runs.

Why this matters:
- repeated sync runs must not create duplicates
- the operator should understand when a new appointment becomes a reminder plan

## Story 2: Update sync

1. Open the `Sync` page again.
2. Explain that updated appointments move reminders in a predictable way.
3. Show the lifecycle list and the reminder plan together.
4. Point at the duplicate protection note.

What to say:
- "The cockpit shows why the plan changed and keeps the list free of duplicates."

Why this matters:
- teams trust the adapter behavior
- the reminder plan stays easy to explain

## Story 3: Cancel sync

1. Open the `Sync` page again.
2. Explain that cancelled appointments stop the reminder plan cleanly.
3. Show that the reminder jobs disappear in a predictable way.
4. Keep the lifecycle list visible so the operator sees the state change.

What to say:
- "The system reacts to the appointment state instead of keeping stale jobs around."

Why this matters:
- teams can explain the change without backend jargon
- the operator sees what happened in plain language

## Important parameters to explain

- `enabled`
  Turns the scheduler on or off.
- `mode`
  Chooses manual or automatic reminder planning.
- `reminder_count`
  Defines how many reminders are created.
- `last_reminder_gap_before_appointment_hours`
  Defines the last reminder point before the appointment.
- `max_span_between_first_and_last_reminder_hours`
  Prevents a plan that is too spread out.
- `channel_rcs_sms_enabled`
  Shows that the platform can send reminders through messaging channels.
- `sync_window_days`
  Shows how many days ahead the adapter checks.
- `polling_interval_minutes`
  Shows how often the adapter checks again.
- `hash_detection_enabled`
  Shows if the adapter compares hashes to spot changes.
- `idempotency_guard`
  Shows if duplicate jobs are blocked on repeated runs.
- `lifecycle_states`
  Shows the job states the operator can expect in the cockpit.

## Closing line

- "This cockpit turns reminder planning into a clear operator task instead of a hidden background process."
