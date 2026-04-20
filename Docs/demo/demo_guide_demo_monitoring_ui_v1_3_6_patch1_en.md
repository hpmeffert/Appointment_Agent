# Demo Guide Demo Monitoring UI v1.3.6-patch1

Version: v1.3.6-patch1
Audience: Demo
Language: EN

## What this demo should show

This demo should show one combined story:
- the stable incident-style cockpit from `v1.2.1-patch4`
- the reminder and Google story from `v1.3.6`

The new menu item makes it possible to move from the patch-4 cockpit into the reminder demo in one release line.

Use this line:

- "This cockpit shows the customer message, the operator flow, and the reminder plan in one place."

## Best screen order

1. Open `Dashboard`.
2. Show the patch-4 cockpit areas.
3. Open `Reminder / Google Demo`.
4. Show the Google-linked appointment.
5. Show the reminder plan.
6. Show `Message Monitor`.
7. Show `Monitoring`.
8. End with `Help`.

## Story 1: New appointment from Google

1. Open `Reminder / Google Demo`.
2. Show that the appointment comes from Google Calendar.
3. Open the reminder plan.
4. Point at the planned reminder times.
5. Open `Dashboard` again and show the combined cockpit flow.

What to say:
- "A Google-linked appointment becomes a reminder plan."

Why this matters:
- the audience sees source, link, and reminder in one flow
- the story is short and easy to understand

## Story 2: Appointment rescheduled

1. Open the reminder story.
2. Say that the appointment time changed.
3. Show that the reminder plan changed too.
4. Open `Monitoring` if you want to show that the platform stays in control.

What to say:
- "The system keeps the appointment and updates the reminder plan."

Why this matters:
- the team can explain a reschedule without technical words
- the reminder times stay correct

## Story 3: Appointment cancelled

1. Open the reminder story.
2. Say that the appointment was cancelled.
3. Show that the reminder work stops too.
4. Open `Help` and point at the version text.

What to say:
- "When the appointment is gone, the reminders stop safely."

Why this matters:
- nobody gets a reminder for an appointment that no longer exists
- the operator can trust the job status

## Important parameters to explain

- `silence_threshold_ms`
  The short pause before the system assumes the user stopped speaking.
  The default is `1300 ms`.
- `reminder_offsets_minutes`
  How many minutes before the appointment reminders are planned.
- `google_calendar_id`
  Which Google calendar is linked.
- `appointment_type`
  What kind of appointment it is.
- `job_status`
  The state of a reminder job.
- `next_due_at`
  When the next job is due.
- `guidedMode`
  `free` means manual control.
  `guided` means the prepared story is active.
- `guidedStepIndex`
  The current step in the story.

## Closing line

- "This release keeps the cockpit simple, visible, and safe."
- "The same screen line can present the operator cockpit and the reminder story."

