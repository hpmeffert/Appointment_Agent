# User Guide Demo Monitoring UI v1.2.1-patch3

Version: v1.2.1-patch3
Audience: User
Language: EN

## What this screen does

The cockpit is the operator view of the Appointment Agent platform.

It helps you:
- follow the customer conversation
- understand what the system is doing in the background
- test calendar actions safely
- inspect messaging settings without looking into code

## Main pages

- `Dashboard`
  Shows the current story, the current mode, the operator summary, and the active customer flow.
- `Message Monitor`
  Shows incoming and outgoing messages in one normalized list.
- `Reports`
  Shows higher-level communication summary cards.
- `Monitoring`
  Shows technical events, traces, and performance records.
- `Settings`
  Shows general runtime values like hold minutes and other operator-facing runtime information.
- `Settings -> RCS`
  Shows LEKAB messaging parameters and readiness.
- `Google Demo Control`
  Lets you prepare or manage demo appointments in simulation or test mode.
- `Help`
  Opens the current demo, user, and admin documents.

![Annotated cockpit overview](/docs/assets/screenshots/v1_2_1_patch3/cockpit-overview.svg)

## New in patch 3

The dashboard now also shows:
- `How the Platform Works`
- `Demo Storyboard`

This helps an operator or presenter explain the product without leaving the cockpit.

## Why the buttons look different in this patch

In day mode, action buttons now use:
- a grey background
- white text
- a stronger border
- a more obvious clickable style

This makes the following buttons easier to see:
- demo buttons
- operator panel buttons
- slot buttons
- story buttons
- communication action buttons

## What the main buttons do

- `Demo`
  Shows the customer story flow.
- `Monitoring`
  Switches the dashboard panel to the technical monitoring view.
- `Restart Story`
  Resets the current interactive story to the beginning.
- `Confirm`
  Confirms the chosen slot and continues the booking or reschedule path.
- `Reschedule`
  Loads new appointment options for an existing booking.
- `Cancel`
  Stops the current booking path or cancels an existing appointment.
- `Call Me`
  Requests a callback or human follow-up.

## What happens when you click a slot

1. The system stores the selected slot in the current journey.
2. It asks the backend to create a short hold.
3. The hold becomes visible in the operator summary.
4. Monitoring records the hold event.
5. When you confirm, the system checks again if the slot is still free.

This protects the flow against parallel booking problems.

## Google Demo Control parameters

- `Mode`
  `simulation` means no real Google calendar changes.
  `test` means the configured test calendar can really change.
- `From Date`
  First day that the demo generator should use.
- `To Date`
  Last day that the demo generator should use.
- `Appointment Type`
  Defines what kind of example appointments should be created.
- `Prepare`
  Shows what would be created without writing to Google.
- `Generate`
  Creates demo appointments.
- `Delete`
  Removes demo appointments again.
- `Reset`
  Deletes existing demo appointments and creates a fresh demo state.

## RCS Settings page

The `Settings -> RCS` page explains the LEKAB setup in plain language.

It shows:
- which values are already saved
- which secrets are masked
- whether the adapter is ready
- which required fields are still missing

![Annotated RCS settings page](/docs/assets/screenshots/v1_2_1_patch3/rcs-settings.svg)

## Important words

- `ready`
  The adapter has enough required values for a usable test messaging setup.
- `missing fields`
  These values still block the setup.
- `warnings`
  These do not always block the setup, but they matter for operators.
- `SMS fallback`
  If RCS is not possible, the platform can continue with SMS.
- `channel_priority`
  Defines which channel should be tried first.
