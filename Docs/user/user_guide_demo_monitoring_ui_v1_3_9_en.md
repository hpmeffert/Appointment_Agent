# User Guide v1.3.9 Patch 9

## What Patch 9 adds

Patch 9 keeps the interactive journey from Patch 7 and restores the known-good Google Calendar output for confirmed real and simulated reschedules.

It now also improves:

- LEKAB RCS test-connection diagnostics for auth failures
- Google Demo Control validation and post-action refresh reliability
- generated Google event naming, description formatting, and address/contact linkage

You can now use visible reply buttons for:

- `Confirm`
- `Reschedule`
- `Cancel`

If `Reschedule` is chosen, the same area continues with guided buttons for:

- `This week`
- `Next week`
- `This month`
- `Next month`
- `Next free slot`

After that, the journey continues with explicit date buttons and then explicit time buttons.

## How to use the guided journey

1. Open `Dashboard`.
2. Pick a `Scenario`.
3. Pick `Simulation` or `Real`.
4. Pick a `Selected Address`.
5. Click `Run Scenario (Simulation)` or `Run Scenario (Real)`.
6. Stay in `Messages and Customer Journey`.
7. Click the visible reply buttons to move the story forward.

## What Simulation does

`simulation` keeps the interaction inside the demonstrator.

Each button click:

- updates the visible journey
- records the selected button
- advances to the next guided step
- writes protocol, demo log, and summary files

## What Real does

`real` keeps the same operator view, but also prepares the outbound RCS suggestion payload.

That means the operator can still see:

- which buttons were sent
- which buttons are currently expected
- which button or reply was selected
- which journey step is active now

Patch 9 now also keeps the real mobile path and the Dashboard mirror aligned:

- outbound real reminders use the active LEKAB runtime settings
- the adapter configures `/rime/seturl` with the persisted incoming and receipt callback URLs
- incoming mobile-device reply callbacks update the stored journey state
- the visible button row in the cockpit stays read-only in `real` mode and mirrors the actual callback result
- callback follow-up messages can continue the journey with the next real button set

## Important fields

- `scenario_id`
  The currently selected appointment story.
- `mode`
  `simulation` or `real`.
- `current_step`
  The active guided interaction step such as `relative_choice`, `date_choice`, or `time_choice`.
- `available_actions`
  The canonical button values for the current step.
- `suggestion_buttons`
  The localized button labels shown in the UI and reused for RCS.
- `real_channel_payload`
  The outbound RCS-style payload with suggestion buttons.
- `customer_journey_message`
  The persisted current real/simulated message contract reused by the cockpit mirror.
- `selected_button`
  The last visible choice selected in the journey.
- `selected_source`
  Shows whether the step came from a simulation click or from the real/test interaction path.

## Typical operator path

1. Start with `Confirm appointment` or `Reschedule appointment`.
2. Click `Reschedule`.
3. Click a relative window such as `Next week`.
4. Click one date.
5. Click one time.
6. Confirm or cancel the resulting flow.

## Google source of truth

When a valid selected address exists, Patch 9 treats the Address Database as the source of truth for Google demo generation and confirmed calendar writes:

- the generated event title uses the format `<Appointment Type> – <Customer Name>`
- the generated description keeps the full selected address and the reschedule/confirm context
- the stored metadata keeps stable `correlation_id`, `booking_reference`, `appointment_id`, and `address_id`
- no generic fallback naming is used while valid selected address data is present

## Files written locally

Scenario runs continue to write evidence files into:

- `runtime-artifacts/demo-scenarios/v1_3_9`

Those files are local runtime output and should not be committed.
