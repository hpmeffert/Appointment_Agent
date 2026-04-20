# User Guide Reminder Scheduler v1.3.6

Version: v1.3.6
Audience: User
Language: EN

## What this cockpit shows

This cockpit is a simple picture of the reminder flow.

It shows:
- where the appointment came from
- how Google Calendar is linked
- what the appointment details are
- which reminder rules are active
- what the reminder preview will create
- which reminder jobs are open
- whether the runtime is healthy
- which stable IDs connect the Google source to the reminder plan

## How to use the pages

- `Dashboard`
  Start here. You see the whole story in one short view.
- `Source`
  Check the appointment source and the Google link.
- `Details`
  Read the customer name, time, place, and appointment type.
- `Policy`
  See when reminders will be sent.
- `Preview`
  See the reminder order before anything is sent.
- `Jobs`
  See which reminder jobs are planned, updated, cancelled, or sent.
- `Health`
  Check if the system is ready.
- `Help`
  Read the parameter explanations and the docs links.

## Important parameters in simple words

- `silence_threshold_ms`
  How long the system waits before it decides that the user stopped speaking.
  In this release the default is `1300 ms`.
- `reminder_offsets_minutes`
  How many minutes before the appointment the reminders should go out.
- `google_calendar_id`
  The calendar that holds the linked appointment.
- `appointment_type`
  The kind of appointment, for example dentist, wallbox, gas meter, or water meter.
- `quiet_hours`
  The time when reminders should stay quiet.
- `job_status`
  Shows if a reminder job is planned, updated, cancelled, or sent.
- `next_due_at`
  The next time the system wants to do work.
- `worker_status`
  Shows if the worker is ready.

## What to say in a demo

- "This cockpit shows the full reminder path in one screen."
- "The appointment starts in Google Calendar and becomes reminder jobs."
- "If the appointment changes or is cancelled, the plan changes too."

## Language and theme

- Use `EN` or `DE` in the header to switch the language.
- Use `Theme` to switch between day and night mode.

## Safety note

This release is a UI and documentation release.
It keeps the same look and keeps the wording simple for new users.
