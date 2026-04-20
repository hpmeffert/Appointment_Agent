# Reminder Scheduler v1.3.0

Version: v1.3.0
Audience: Admin
Language: EN

## Patch goal

`v1.3.0` introduces the first Reminder Scheduler setup line.

The goal is simple:
- read appointments
- calculate reminder times
- store the reminder policy
- show the setup in a cockpit that is easy to understand

## Architecture in simple words

The module is split into a few parts:
- Setup UI
  Lets an operator edit the reminder policy.
- Preview engine
  Shows when reminders will be sent before anything is saved or sent.
- Job list
  Shows which reminder jobs would be created.
- Scheduler logic
  Will later create and dispatch the real jobs.
- Shared storage
  Keeps the reminder policy and job state in the common platform database layer.

## Important reminder parameters

- `enabled`
  Turns the whole scheduler on or off.
- `mode`
  `manual` means the operator types reminder times directly.
  `auto_distributed` means the system calculates reminder times automatically.
- `reminder_count`
  How many reminders should be created for one appointment.
  The allowed range is `0` to `3`.
- `first_reminder_hours_before`
  The farthest reminder in manual mode.
  Example: `72` means 72 hours before the appointment.
- `second_reminder_hours_before`
  The second reminder in manual mode.
- `third_reminder_hours_before`
  The third reminder in manual mode.
- `max_span_between_first_and_last_reminder_hours`
  Maximum distance between the first and last reminder when the system distributes reminders automatically.
- `last_reminder_gap_before_appointment_hours`
  The final reminder should be this many hours before the appointment.
- `enforce_max_span`
  If true, the preview should warn when the plan is too wide.
- `preload_window_hours`
  How far ahead the scheduler should look for appointments.
- `channel_email_enabled`
  Allows email reminders.
- `channel_voice_enabled`
  Allows voice reminders.
- `channel_rcs_sms_enabled`
  Allows RCS or SMS reminders.

## Validation rules

- reminder count must stay between `0` and `3`
- reminder hours must not be negative
- manual reminder values must be in the correct order
- duplicate reminder values should be avoided
- the max span must be respected when it is enabled

## API shape for the first release line

The module is designed around these routes:
- `GET /api/reminders/v1.3.0/config`
- `GET /api/reminders/v1.3.0/config/preview`
- `GET /api/reminders/v1.3.0/jobs`
- `GET /api/reminders/v1.3.0/rebuild`
- `GET /api/reminders/v1.3.0/health`

## What the admin should verify

1. The setup page loads.
2. The preview changes when parameters change.
3. The job list shows the planned reminders.
4. The validation area explains errors in plain language.
5. The release version is visible in the header and help text.

