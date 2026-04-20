# Demo Guide Demo Monitoring UI v1.2.1-patch3

Version: v1.2.1-patch3
Audience: Demo
Language: EN

## What changed in patch 3

Patch 3 keeps the Patch 2 documentation quality and adds:
- platform explanation panels directly inside the cockpit
- demo storyboard cards directly inside the cockpit
- stronger presenter guidance for business value

## What this demo is for

This demo shows that the Appointment Agent is not just one chatbot screen.

It is a modular appointment platform:
- messaging channels on one side
- scheduling adapters on the other side
- one service bus and one operator cockpit in the middle

Use this line when you present it:

- "The customer only sees a simple conversation. The company sees a platform that can route, monitor, and control the full appointment process."

## How the platform works

The platform has five main parts:

- `LEKAB Adapter`
  Sends and receives RCS and SMS style messages.
- `Appointment Orchestrator`
  Decides what the journey should do next.
- `Google Adapter`
  Checks slots, holds slots, books appointments, and handles conflicts.
- `Future Adapters`
  Microsoft, CRM, or other providers can be added later without rebuilding the whole system.
- `Service Bus`
  The internal handover layer between adapters, orchestration, monitoring, and audit.

Use this line:

- "Adapters let us change providers without rewriting the complete product."

## Suggested screen sequence

1. Open the cockpit dashboard.
2. Show `Message Monitor`.
3. Show `Google Demo Control`.
4. Show `Settings -> RCS`.
5. Run the five stories below.

![Annotated cockpit overview](/docs/assets/screenshots/v1_2_1_patch3/cockpit-overview.svg)
![Platform flow overview](/docs/assets/screenshots/v1_2_1_patch3/platform-flow.svg)

## Story 1: Booking

1. Start on `Dashboard`.
2. Explain that the customer asked for an appointment.
3. Click the booking story and show the slot buttons.
4. Click one slot.
5. Click `Confirm`.

System reaction:
- the platform loads slots from the booking backend
- it creates a temporary hold
- it checks availability again before the final booking

UI change:
- the transcript updates
- operator summary shows the selected slot and hold status
- monitoring records the booking flow events

Wow effect:
- the click is not cosmetic; it drives real appointment logic

## Story 2: Rescheduling

1. Open a story with an existing appointment.
2. Click `Reschedule`.
3. Pick a new slot.
4. Click `Confirm`.

System reaction:
- the system does not blindly overwrite the old booking
- it asks the provider for fresh slots
- it holds the new slot before the update is finalized

UI change:
- the selected slot changes
- monitoring shows reschedule and hold events
- operator summary shows the new resulting path

Wow effect:
- the same cockpit handles first booking and later journey changes without switching tools

## Story 3: Cancellation

1. Open the cancellation story.
2. Click `Cancel`.
3. Explain the resulting system status.

System reaction:
- the customer decision is normalized into an internal action
- the journey is updated
- the operator can see the resulting cancellation path

UI change:
- transcript shows the cancellation answer
- summary and monitoring update immediately

Wow effect:
- the cancellation is visible as both customer communication and system event

## Story 4: Callback request

1. Open the callback story.
2. Click `Call Me`.
3. Show the operator summary and monitoring.

System reaction:
- the system marks that a human follow-up is needed
- the callback path becomes visible in the journey

UI change:
- transcript changes from automation to assisted handling
- monitoring highlights the callback request

Wow effect:
- automation can stop gracefully and hand over to people when needed

## Story 5: Slot Hold

1. Open a story with multiple slots.
2. Click one slot.
3. Pause on the hold message before you confirm.

System reaction:
- the selected slot is reserved for a short time
- another user should not get that same slot in parallel
- before commit, the system still rechecks live availability

UI change:
- hold status becomes visible
- hold minutes are visible in settings and summary
- monitoring records `slot.hold.created` and later confirmation or release events

UI line to say:
- "This is the wow moment. We do not just show choices. We protect them."

![Annotated RCS settings page](/docs/assets/screenshots/v1_2_1_patch3/rcs-settings.svg)

## New cockpit walkthrough in patch 3

Open the dashboard and point at:
- `How the Platform Works`
- `Demo Storyboard`

Explain:
- "Now the presenter does not have to jump into docs immediately."
- "The platform layers are visible right in the product."
- "The five demo stories and their wow effects are also visible in the product."

## Settings story for operators

Open:
- `Settings`
- then `Settings -> RCS`

Explain:
- "This is where the operator understands if the messaging setup is really usable."
- "Secrets stay masked, but readiness still becomes visible."
- "The page explains each parameter in plain language."

## Business value lines

- "One cockpit for communication, scheduling, and operator visibility."
- "One architecture that can grow with more adapters and channels."
- "Safer than a plain chat demo because slot holds and conflict checks are built in."

## Important parameters to explain during a demo

- `GOOGLE_TEST_MODE_DEFAULT`
  `simulation` means no real Google writes.
  `test` means the demo can write to the configured test calendar.
- `APPOINTMENT_AGENT_SLOT_HOLD_MINUTES`
  Defines how long a chosen slot stays reserved.
- `APPOINTMENT_AGENT_MAX_SLOTS_PER_OFFER`
  Defines how many options the customer gets at one time.
- `channel_priority`
  Defines whether RCS or SMS is attempted first.

## What not to mix into this guide

Do not read release notes during the demo.

Release notes belong in:
- `Docs/releases/release_notes_v1_2_1_patch3_en.md`
