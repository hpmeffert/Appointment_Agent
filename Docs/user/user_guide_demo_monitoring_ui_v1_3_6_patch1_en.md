# User Guide Demo Monitoring UI v1.3.6-patch1

Version: v1.3.6-patch1
Audience: User
Language: EN

## What this cockpit is for

This cockpit helps an operator see three things at the same time:
- what the customer sees
- what the platform is doing
- what the reminder story is doing behind the scenes

This patch combines the stable patch-4 cockpit with the `v1.3.6` reminder and Google demo.

## Main pages

- `Dashboard`
  Main story page with the combined demo flow.
- `Message Monitor`
  Shows inbound and outbound messages in one place.
- `Monitoring`
  Shows technical events, traces, and performance data.
- `Settings`
  Shows general operator settings.
- `Settings -> RCS`
  Shows LEKAB RCS and SMS settings.
- `Google Demo Control`
  Safe workspace for Google demo data.
- `Reminder / Google Demo`
  New menu item for the combined reminder story.
- `Help`
  Opens the current guides.

## What is new in patch 1

- the patch-4 cockpit stays in place
- a new menu item opens the `v1.3.6` reminder and Google demo
- the docs explain the new combined path in simple words
- the version is shown in the header and in help

## Dashboard basics

The dashboard is still the main page.

It shows:
- `Current Story`
  Which business story is active.
- `Current Mode`
  Whether the cockpit is in free mode or guided mode.
- `Messages and Customer Journey`
  The transcript, reply buttons, slot buttons, and status.
- `Guided Demo Mode`
  The current presenter step and the next focus area.
- `Operator Summary`
  Trace ids, selected action, selected slot, hold status, and result path.
- `Reminder Story`
  The Google-linked appointment and the reminder plan.

## Important parameters

- `guidedMode`
  `free` means manual control.
  `guided` means the prepared story runs.
- `guidedStepIndex`
  The current step number in the story.
- `autoDemoRunning`
  `true` means the story moves forward automatically.
- `silence_threshold_ms`
  The short pause before the system assumes the user stopped speaking.
  The default is `1300 ms`.
- `reminder_offsets_minutes`
  How many minutes before the appointment reminders are planned.
- `slot_hold_minutes`
  How long a slot stays reserved for a short time.
- `google_calendar_id`
  The Google calendar used for the linked appointment.
- `appointment_type`
  The business type for the demo data.
- `message_id`
  The internal id of one message.
- `trace_id`
  The technical id that links related events.

## Buttons you will use most

- `Restart Story`
  Starts the current story again.
- `Next Step`
  Moves to the next step.
- `Auto Demo`
  Starts or stops the automatic story.
- reply buttons such as `Confirm`, `Reschedule`, `Cancel`, and `Call Me`
  Move the customer journey forward.
- slot buttons
  Pick a time slot and try a temporary hold.

## What the new reminder menu item shows

The new `Reminder / Google Demo` menu item opens the combined story.
There you can see:
- how the appointment comes from Google
- how reminders are planned
- how a changed appointment updates the reminder plan
- how a cancelled appointment stops the reminder work safely

## Good rule for users

If you want to explain the customer story, stay on `Dashboard`.

If you want to show technical proof, switch to:
- `Message Monitor`
- `Monitoring`
- `Settings -> RCS`
- `Reminder / Google Demo`

