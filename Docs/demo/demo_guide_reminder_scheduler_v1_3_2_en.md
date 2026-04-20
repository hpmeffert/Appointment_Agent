# Demo Guide Reminder Scheduler v1.3.2

Version: v1.3.2
Audience: Demo
Language: EN

## What this demo should show

This demo should show that reminder planning is simple, safe, explainable, and easy to operate even when lifecycle states change.
It should also show that timezone, DST, and near-term reminders stay visible without adding extra complexity.

Use this line:

- "The customer only sees a reminder. The operator sees the plan behind it."

## Suggested screen order

1. Open `Dashboard`.
2. Show the `Setup` page.
3. Switch between `manual` and `auto_distributed`.
4. Open `Preview`.
5. Open `Jobs`.
6. Open `Lifecycle`.
7. Open `Time`.
8. End with `Help`.

## Story 1: One reminder

1. Start with the default policy.
2. Show that only one reminder is active.
3. Point at the preview and explain the 24 hour gap.

Why this matters:
- it is the simplest possible reminder setup
- it is easy to explain to a customer or a colleague

## Story 2: Manual three-step sequence

1. Switch to `manual`.
2. Set `72`, `48`, and `24` hours before the appointment.
3. Open the preview.
4. Open the lifecycle tab and show the state list.

What to say:
- "In manual mode the operator decides the times directly."

Why this matters:
- teams can use their own business rules
- the preview makes the order visible before anything is sent

## Story 3: Auto distributed reminders

1. Switch to `auto_distributed`.
2. Set `reminder_count = 3`.
3. Set the last reminder gap and max span.
4. Show the preview again.
5. Open the lifecycle tab and point at the planned job states.

What to say:
- "The system can do the math for us."

Why this matters:
- the operator does not need to calculate every time manually
- the policy still stays visible and controlled

## Story 4: Timezone aware near-term reminder

1. Open the `Time` page.
2. Point at the timezone and DST notes.
3. Show the reminder that is close to the current time.
4. Explain that near-term reminders are easier to check when they are visible in plain language.

What to say:
- "The system keeps the local timezone in view, so the operator can trust the displayed time."

Why this matters:
- small time changes can create big confusion if they are hidden
- near-term reminders should be easy to spot

## Story 5: DST boundary reminder

1. Open the `Time` page again.
2. Explain that daylight saving time can move the local clock.
3. Show the reminder window and the lifecycle list together.
4. Explain that the cockpit keeps the timing readable even when the clock changes.

What to say:
- "The cockpit shows the reminder time in the same local frame the operator uses every day."

Why this matters:
- teams avoid mistakes around summer time changes
- the reminder plan stays easy to explain

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
- `timezone`
  Shows which local time zone the appointment uses.
- `dst_guard`
  Shows if daylight saving time should be treated carefully.
- `near_term_window_hours`
  Shows how far ahead the cockpit should treat reminders as near-term.
- `lifecycle_states`
  Shows the job states the operator can expect in the cockpit.

## Closing line

- "This cockpit turns reminder planning into a clear operator task instead of a hidden background process."
