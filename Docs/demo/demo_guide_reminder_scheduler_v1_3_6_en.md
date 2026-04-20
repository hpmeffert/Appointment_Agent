# Demo Guide Reminder Scheduler v1.3.6

Version: v1.3.6
Audience: Demo
Language: EN

## What this demo should show

This demo should show the full reminder journey in one cockpit:
- the appointment source
- the Google linkage
- the appointment details
- the reminder policy
- the reminder preview
- the reminder jobs
- the runtime health
- the bridge from Google source data to reminder-ready data

Use this line:

- "The operator can see the appointment source, the Google link, the reminder plan, and the health in one view."

## Suggested screen order

1. Open `Dashboard`.
2. Show `Source`.
3. Show `Details`.
4. Show `Policy`.
5. Open `Preview`.
6. Open `Jobs`.
7. Open `Health`.
8. End with `Help`.

## Story 1: New appointment from Google

1. Open `Source`.
2. Show that the appointment comes from Google Calendar.
3. Open `Details`.
4. Show the customer, time, and appointment type.
5. Open `Preview`.
6. Point at the reminder timeline.

What to say:
- "This is the normal path. A Google-linked appointment becomes a reminder plan."

Why this matters:
- the operator sees source, link, and plan in one flow
- the demo is easy to explain in a few sentences
- the team can open `/api/google/v1.3.6/linkage/demo` if someone wants the raw linkage object

## Story 2: Appointment rescheduled

1. Open `Details`.
2. Say that the appointment time changed.
3. Open `Jobs`.
4. Show that the reminder jobs were updated.
5. Open `Preview`.
6. Show that the new reminder times match the new appointment time.

What to say:
- "The system keeps the appointment and updates the reminder plan."

Why this matters:
- the team can explain a reschedule without technical words
- the reminder plan stays correct

## Story 3: Appointment cancelled

1. Open `Details`.
2. Say that the appointment was cancelled.
3. Open `Jobs`.
4. Show that the reminder jobs are cancelled too.
5. Open `Health`.
6. Point out that the runtime stays healthy.

What to say:
- "The reminder work stops safely when the appointment is gone."

Why this matters:
- nobody gets a reminder for an appointment that no longer exists
- the operator can trust the job status

## Important parameters to explain

- `appointment_source_system`
  Where the appointment came from.
- `google_calendar_id`
  Which Google calendar is linked.
- `appointment_type`
  What kind of appointment it is.
- `appointment_start`
  When the appointment starts.
- `timezone`
  The local time of the appointment.
- `reminder_offsets_minutes`
  When reminders are planned before the appointment.
- `silence_threshold_ms`
  The short pause before the system decides that the user stopped speaking.
- `quiet_hours`
  The time when no reminder should be sent.
- `job_status`
  The state of the reminder job.
- `next_due_at`
  When the next job is due.

## Closing line

- "This cockpit keeps the full reminder flow simple, visible, and safe."
- "A new colleague can understand the story without reading code first."
