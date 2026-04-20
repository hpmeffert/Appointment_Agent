# Admin Guide Demo Monitoring UI v1.3.6-patch1

Version: v1.3.6-patch1
Audience: Admin
Language: EN

## Patch goal

`v1.3.6-patch1` combines the incident-style cockpit from `v1.2.1-patch4` with the reminder and Google demo from `v1.3.6`.

The cockpit now has one extra menu item for the combined reminder demo.
That makes it easier to show two things in one release line:
- the stable operator cockpit from patch 4
- the reminder and Google story from `v1.3.6`

The goal is still simple:
- keep the cockpit stable
- make the demo easy to explain
- show the full path from message to reminder in one place

## Main cockpit idea

The incident-style shell stays the same.
The new combined menu item opens the reminder and Google demo flow, so the operator can switch from the patch-4 cockpit into the `v1.3.6` reminder story without confusion.

The main areas are:
- `Dashboard`
  Main story page with the combined demo flow.
- `Message Monitor`
  Shows inbound and outbound messages in one place.
- `Monitoring`
  Shows traces, events, and performance data.
- `Settings -> RCS`
  Shows LEKAB settings and readiness.
- `Google Demo Control`
  Safe workspace for Google demo data.
- `Reminder / Google Demo`
  New menu item for the combined `v1.3.6` reminder story.
- `Help`
  Shows the guides and version text.

## Why this combined release exists

This release joins two useful demo views:
- the patch-4 cockpit for live operator handling
- the reminder scheduler story for Google-linked appointments and reminders

That helps when you want to show:
- how a message enters the system
- how the appointment is linked to Google
- how reminders are planned
- how the operator keeps control in the same cockpit

## Important parameters

- `silence_threshold_ms`
  How long the system waits before it assumes the user stopped speaking.
  The default is `1300 ms`.
- `reminder_offsets_minutes`
  How many minutes before the appointment reminders are planned.
- `google_calendar_id`
  The Google calendar used for the linked appointment.
- `appointment_type`
  The business type used for the demo data.
- `job_status`
  The state of a reminder job, such as planned, updated, cancelled, or sent.
- `guidedMode`
  `free` means manual control.
  `guided` means the prepared story is active.
- `guidedStepIndex`
  The current step number in the story.
- `slot_hold_minutes`
  How long a temporary slot hold stays active.
- `message_id`
  Internal id of one message.
- `trace_id`
  Technical id that links related events.

## Safety and operation notes

- Keep secrets masked on settings pages.
- Use simulation mode when you only want to preview Google changes.
- Use test mode only for the configured test calendar.
- Keep the incident-style layout unchanged so users do not have to learn a new shell.
- Keep the version visible in the header and the help page.

## What to verify

1. The header shows `v1.3.6-patch1`.
2. The help page shows the version and the combined purpose.
3. The cockpit contains the new reminder / Google menu item.
4. The page text explains the key parameters in simple words.
5. The patch-4 cockpit behavior stays stable.

