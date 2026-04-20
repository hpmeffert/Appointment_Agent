# User Guide Reminder Scheduler v1.3.2

Version: v1.3.2
Audience: User
Language: EN

## What this cockpit is for

This cockpit helps an operator do three things:
- set reminder rules
- preview reminder times
- understand what jobs the system would create
- check timezone and DST notes

## Main pages

- `Dashboard`
  Shows the main reminder overview and the demo stories.
- `Setup`
  Lets the operator change the reminder policy.
- `Preview`
  Shows calculated reminder times before anything is sent.
- `Jobs`
  Shows the reminder jobs that would be created.
- `Lifecycle`
  Shows the important reminder job states like planned, dispatching, sent, failed, skipped, and cancelled.
- `Time`
  Shows the appointment timezone, DST awareness, and the near-term reminder window.
- `Help`
  Shows short explanations and document links.

## The most important parameters

- `enabled`
  Turns reminders on or off.
- `mode`
  `manual` means you choose the times yourself.
  `auto_distributed` means the system calculates the times for you.
- `reminder_count`
  How many reminders are created for one appointment.
- `first_reminder_hours_before`
  The farthest reminder in manual mode.
- `second_reminder_hours_before`
  The second reminder in manual mode.
- `third_reminder_hours_before`
  The third reminder in manual mode.
- `last_reminder_gap_before_appointment_hours`
  How close the last reminder should be to the appointment.
- `preload_window_hours`
  How far ahead the scheduler should look for appointments.
- `channel_email_enabled`
  Allows email reminders.
- `channel_voice_enabled`
  Allows voice reminders.
- `channel_rcs_sms_enabled`
  Allows RCS or SMS reminders.

## Timezone and DST in simple words

The appointment has a timezone. That tells the system which local clock to use.

That matters because:
- the same appointment time means something different in another country
- daylight saving time can change the local clock
- near-term reminders can become more important when the appointment is close

The `Time` page shows:
- the appointment timezone
- if DST safety is enabled
- how many hours count as near-term

## Reminder lifecycle states

- `planned`
  The job exists and is waiting for its send time.
- `dispatching`
  The system is sending the reminder right now.
- `sent`
  The reminder was delivered successfully.
- `failed`
  The send attempt did not work.
- `skipped`
  The job was intentionally not sent.
- `cancelled`
  The job was stopped because the appointment changed or the plan was rebuilt.

## Near-term reminders

If a reminder is close to the current time, the cockpit should make that visible.

This helps the operator:
- double-check the last reminder first
- avoid surprises during timezone changes
- understand which reminder needs attention now

## How to use the setup page

1. Start with the default policy.
2. Choose `manual` or `auto_distributed`.
3. Set how many reminders you want.
4. Check the preview.
5. Read the validation box before you save anything.

On the `Time` page, also check:
- the timezone
- the DST note
- the near-term reminder window

## Simple rule of thumb

- one reminder is easiest to explain
- three reminders show the full power of the scheduler
- auto distributed mode is useful when you want the system to do the math
