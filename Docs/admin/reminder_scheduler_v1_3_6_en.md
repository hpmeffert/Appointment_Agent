# Reminder Scheduler v1.3.6

Version: v1.3.6
Audience: Admin
Language: EN

## Patch goal

`v1.3.6` is a combined demonstrator cockpit and bridge release.

It shows the full path in one view:
- where the appointment came from
- how the appointment is linked to Google Calendar
- what appointment details are stored
- which reminder policy is active
- what the reminder preview looks like
- which reminder jobs exist
- whether the runtime is healthy

The cockpit keeps the same incident-style look and uses simple language.
It also adds safe demo APIs that show the Google-linked source object, the normalized appointment, and the reminder-ready view separately.

## Pages in the cockpit

- `Dashboard`
  Shows the short overview and the three demo stories.
- `Source`
  Shows the appointment source and the Google linkage.
- `Details`
  Shows the appointment details.
- `Policy`
  Shows the reminder policy and the important rules.
- `Preview`
  Shows the reminder preview and the reminder timeline.
- `Jobs`
  Shows the reminder jobs and their status.
- `Health`
  Shows the runtime health and diagnostics.
- `Help`
  Shows links and the parameter explanations.

## Important parameters

- `appointment_source_system`
  The system that provided the appointment.
- `google_calendar_id`
  The Google calendar used for the linked appointment.
- `google_link_status`
  Shows if the Google link is connected or not.
- `appointment_type`
  The kind of appointment, for example dentist or wallbox.
- `appointment_start`
  When the appointment starts.
- `timezone`
  The local time zone of the appointment.
- `reminder_offsets_minutes`
  When reminders are planned before the appointment.
- `silence_threshold_ms`
  How long the system waits before it assumes the user stopped speaking.
  The default is `1300 ms`.
- `quiet_hours`
  The time range when reminders should not be sent.
- `reminder_channels`
  The channels used for reminders.
- `max_retries`
  How many retry attempts are allowed.
- `job_status`
  The state of a reminder job, for example planned, updated, cancelled, or sent.
- `next_due_at`
  The next time a reminder job is due.
- `db_status`
  Shows if the database is healthy.
- `worker_status`
  Shows if the worker is ready.

## Demo story set

The cockpit contains three short demo stories:
- a new appointment comes from Google
- the appointment is rescheduled
- the appointment is cancelled

## API routes for this release line

- `GET /ui/reminder-scheduler/v1.3.6`
- `GET /api/reminder-ui/v1.3.6/payload`
- `GET /api/reminder-ui/v1.3.6/help`
- `GET /api/reminder-ui/v1.3.6/config`
- `GET /api/reminder-ui/v1.3.6/config/preview`
- `GET /api/reminder-ui/v1.3.6/jobs`
- `GET /api/reminder-ui/v1.3.6/health`
- `GET /api/reminders/v1.3.6/linkage/demo`
- `GET /api/reminders/v1.3.6/linkage/reminder-preview`
- `GET /api/google/v1.3.6/linkage/demo`
- `GET /api/google/v1.3.6/linkage/stories`

## What the admin should verify

1. The header shows `v1.3.6`.
2. The pages show source, Google linkage, details, policy, preview, jobs, and health.
3. The help page explains the parameters in simple words.
4. The three demo stories are visible and short enough to present quickly.
