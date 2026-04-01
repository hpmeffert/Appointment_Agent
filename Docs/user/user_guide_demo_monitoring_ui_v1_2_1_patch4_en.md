# User Guide Demo Monitoring UI v1.2.1-patch4

Version: v1.2.1-patch4
Audience: User
Language: EN

## What this cockpit is for

This cockpit helps an operator understand three things at the same time:
- what the customer sees
- what the platform is doing
- what settings or integrations matter right now

## Main pages

- `Dashboard`
  Main story page with transcript, actions, slots, guided story panel, and operator summary.
- `Message Monitor`
  Shows inbound and outbound messages in one place.
- `Reports`
  Turns raw message traffic into simple summary cards.
- `Monitoring`
  Shows technical events, traces, and performance records.
- `Settings`
  Shows general operator parameters.
- `Settings -> RCS`
  Shows LEKAB RCS and SMS configuration.
- `Google Demo Control`
  Safe workspace for Google demo data.
- `Help`
  Opens the current guides.

## New in patch 4

- `Guided` and `Free` mode on the dashboard
- a guided story panel
- an auto-demo button
- stronger platform visibility
- a more messaging-first dashboard

## Dashboard basics

The dashboard is the most important page.

It has these areas:
- `Current Story`
  Shows which business story you are presenting.
- `Current Mode`
  Shows dashboard mode, guided mode, and Google mode.
- `Google Workspace`
  Shows provider and date-range context.
- `Messages and Customer Journey`
  Shows transcript, reply buttons, slot buttons, and current interaction status.
- `Guided Demo Mode`
  Shows the active presenter step and where to focus.
- `Operator Summary`
  Shows trace ids, selected action, selected slot, hold status, and result path.

## Guided mode parameters

- `guidedMode`
  `free` means you control the demo manually.
  `guided` means the prepared story is active.
- `guidedStepIndex`
  Current story step inside the guided flow.
  It increases as the demo moves forward.
- `autoDemoRunning`
  `true` means the story advances automatically.
  `false` means it only changes when the operator clicks.
- `ui_focus`
  Tells you which panel to look at next.

Why this matters:
- presenters stay on track
- new colleagues can learn the demo faster
- the UI itself explains what should happen next

## Buttons you will use most

- `Restart Story`
  Resets the current scenario.
- `Next Step`
  Moves to the next manual or guided step.
- `Auto Demo`
  Starts or stops automatic story progression.
- reply buttons such as `Confirm`, `Reschedule`, `Cancel`, `Call Me`
  Trigger the next journey path.
- slot buttons
  Pick a time slot and try to create a temporary hold.

## Message Monitor parameters

- `message_id`
  Internal id for one message.
- `provider_message_id`
  External provider id for the same message.
- `direction`
  `inbound` means from customer to platform.
  `outbound` means from platform to customer.
- `status`
  Delivery or processing state.
- `journey_id`
  Connects a message to one customer process.
- `booking_reference`
  Connects a message to one booking.

## Monitoring parameters

- `trace_id`
  Connects technical events that belong to one processing path.
- `correlation_id`
  Connects related calls across modules.
- `event_type`
  Name of the technical event, for example `slot.hold.created`.
- `latency_ms`
  Time in milliseconds for one action or service step.

## Slot hold basics

When you click a slot:
1. the platform remembers the slot
2. it asks for a temporary hold
3. the hold becomes visible in the UI
4. the final booking still rechecks availability

Important parameter:
- `slot_hold_minutes`
  How long the slot stays protected before it becomes free again.

## Google Demo Control parameters

- `Mode`
  `simulation` = preview only, no real calendar changes.
  `test` = real changes in the configured Google test calendar.
- `From Date`
  Start of the date range.
- `To Date`
  End of the date range.
- `Appointment Count`
  How many demo appointments to create.
- `Appointment Type`
  Business category such as `dentist`, `wallbox`, `gas_meter`, or `water_meter`.

## RCS settings parameters

- `workspace_id`
  Technical LEKAB workspace.
- `auth_client_id`
  App id used for authentication.
- `auth_client_secret`
  Secret for that app id.
- `channel_priority`
  Which channel should be tried first.
- `sms_fallback_enabled`
  Allows SMS if RCS is not available.
- `callback_url`
  URL where the provider can send status updates or replies.

## Good rule for operators

If you want to explain business value, stay on `Dashboard`.

If you want to explain technical proof, switch to:
- `Message Monitor`
- `Monitoring`
- `Settings -> RCS`
