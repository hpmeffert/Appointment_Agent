# Demo Monitoring UI v1.1.0 Patch 7

Version: v1.1.0-patch7
Audience: Admin
Language: EN

## What changed

Patch 7 turns the communication area into a real simulator.

The customer message can now show:

- reply action buttons
- slot buttons
- structured message data that is closer to future LEKAB, RCS, or SMS integration

## Communication model

Each visible platform message can now contain a structured object called `communication_message`.

Important fields:

- `text`
  The main sentence the customer sees.

- `actions`
  A list of reply buttons such as `keep`, `reschedule`, `cancel`, or `call_me`.

- `slot_options`
  A list of normalized slot objects.

- `calendar_provider`
  The source of the slot model. In the demo this can be `simulated`, and later it can also be `google` or `microsoft`.

- `message_id`
  The message identifier that helps monitoring and later provider mapping.

- `lekab_job_id`
  A simulated LEKAB-oriented job reference that shows where message execution tracking would connect later.

## Slot option model

Each slot button uses a provider-neutral structure.

Important fields:

- `slot_id`
  A unique technical id for the slot in the demo.

- `label`
  The human-friendly text shown on the button, for example `Tue, 08 Apr, 10:00`.

- `start`
  Planned start timestamp. In simulation mode this can still be empty.

- `end`
  Planned end timestamp. In simulation mode this can still be empty.

- `duration_minutes`
  Optional duration if the provider already knows it.

- `calendar_provider`
  Where the slot came from.

## What happens when a user clicks

When a reply button or slot button is clicked, the cockpit now updates:

- visible transcript
- current story summary
- operator summary
- monitoring timeline
- monitoring trace
- local interaction status

## Monitoring events

Patch 7 adds local demo events such as:

- `message.action.keep.selected`
- `message.action.reschedule.selected`
- `message.action.cancel.selected`
- `message.action.call_me.selected`
- `slot.option.selected`

These are demo-side monitoring events, but they are shaped to be understandable and future-ready.

## Simulation and Google relation

- The interactive communication buttons work in demo state inside the cockpit.
- Google Demo Control still manages calendar preparation and cleanup.
- Simulation mode does not write to Google Calendar.
- Test mode writes only through the configured Google test setup.

## Maintainability rule

New interaction code contains inline comments in English on purpose.

These comments explain:

- why state transitions exist
- how actions map to scenario steps
- how slot options are normalized
- how the UI stays provider-neutral
- how this design can later map to LEKAB-style reply actions
