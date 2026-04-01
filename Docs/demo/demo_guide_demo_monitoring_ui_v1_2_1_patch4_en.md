# Demo Guide Demo Monitoring UI v1.2.1-patch4

Version: v1.2.1-patch4
Audience: Demo
Language: EN

## What changed in patch 4

Patch 4 keeps the Incident-style look and adds a stronger presenter flow:
- a new `Free` and `Guided` demo mode switch
- a guided story panel with the current step, next action, and UI focus
- an `Auto Demo` button for walkthrough mode
- a more messaging-first dashboard
- stronger platform visibility for channels, integrations, and AI building blocks

## What this demo should show

This demo should make one thing easy to understand:

- the customer sees a simple message flow
- the operator sees the full process
- the platform connects messaging, scheduling, monitoring, and settings

Use this line:

- "This is not just a chatbot screen. It is an appointment platform with one shared operator cockpit."

## Best screen order

1. Open `Dashboard`.
2. Show `Free` versus `Guided`.
3. Start `Guided`.
4. Use `Auto Demo` or `Next Step`.
5. Show `Message Monitor`.
6. Show `Monitoring`.
7. Show `Settings -> RCS`.
8. Show `Google Demo Control`.

![Annotated cockpit overview](/docs/assets/screenshots/v1_2_1_patch4/cockpit-overview.svg)
![Platform flow overview](/docs/assets/screenshots/v1_2_1_patch4/platform-flow.svg)

## Guided Demo Mode

`Guided Demo Mode` is the new presenter helper.

It shows:
- the current demo step
- what you should say next
- which UI area to point at
- how far you are in the story

### Important guided parameters

- `guidedMode`
  Decides whether the operator moves freely or follows the prepared story.
  `free` means manual exploration.
  `guided` means the story engine highlights the next step.
- `guidedStepIndex`
  Internal counter for the active story step.
  It starts at `0`.
  It changes when you click `Next Step` or when auto mode advances.
- `auto_run_interval_ms`
  Delay between automatic story steps.
  In this patch the default is `2200`.
  That means the UI advances roughly every 2.2 seconds.
- `ui_focus`
  Name of the screen area that the presenter should point to.
  Example values are `chatStream`, `slotList`, `guidedDemoPanel`, or `platformOverviewGrid`.

## Story 1: Messaging first

1. Open the dashboard.
2. Point at the customer message.
3. Explain that the conversation is the visible customer layer.

What the system shows:
- the transcript
- the current story
- the current mode
- the platform summary

Use this line:

- "We always start with the message because that is what the customer actually experiences."

## Story 2: Interactive action buttons

1. Click `Confirm`, `Reschedule`, `Cancel`, or `Call Me`.
2. Explain that the buttons are connected to real flow logic.

What changes:
- operator summary updates
- monitoring gets new events
- the journey path changes

Use this line:

- "These buttons do not just decorate the UI. They drive the actual appointment path."

## Story 3: Slot buttons and hold logic

1. Click `Reschedule` or open a story with slot options.
2. Click one slot.
3. Pause on the hold message.
4. Then click `Confirm`.

What happens:
- the platform creates a temporary hold
- the hold protects the slot against parallel booking
- the booking is revalidated before commit

Use this line:

- "The wow moment is not only that the platform shows slots. It also protects them."

## Story 4: Platform visibility

Point at `How the Platform Works` and explain:
- `Channels`
  RCS, SMS, and later more channels like voice or WhatsApp
- `Messaging Adapter`
  LEKAB turns provider-specific traffic into one internal format
- `Service Bus`
  Internal handover layer between modules
- `Integrations`
  Google is active today, other providers can follow later
- `AI Layer`
  Future place for agent logic and RAG context

Use this line:

- "The platform is built so one provider can change without rebuilding the whole product."

## Story 5: Message Monitor

Open `Message Monitor`.

Explain:
- inbound and outbound messages are shown together
- message status stays visible
- operators can inspect the full message path

Important parameters to mention:
- `message_id`
  Internal id of one message record.
  This helps operators find the exact message again.
- `provider_message_id`
  Id from the external provider.
  This helps with provider-side troubleshooting.
- `journey_id`
  Id of the customer journey.
  This links many messages to one appointment flow.
- `booking_reference`
  Internal booking id.
  This links the message to a booking record.

## Story 6: Google Demo Control

Open `Google Demo Control`.

Explain the fields:
- `Mode`
  `simulation` means no real Google changes.
  `test` means the configured test calendar can really change.
- `From Date`
  First day that the generator may use.
- `To Date`
  Last day that the generator may use.
- `Appointment Count`
  Number of demo appointments to create.
- `Appointment Type`
  Business type for the generated records, for example `dentist` or `wallbox`.

Explain the buttons:
- `Prepare Demo Calendar`
  Shows a preview only. It does not write to Google.
- `Generate Demo Appointments`
  Creates demo records in the target calendar when `Mode = test`.
- `Delete Demo Appointments`
  Removes previously created demo records.
- `Reset Demo Calendar`
  Deletes and recreates the demo state.

## Story 7: RCS settings

Open `Settings -> RCS`.

Explain:
- the page saves LEKAB settings in local SQLite storage
- secret fields stay masked
- readiness is calculated and shown to the operator
- `Test Connection` is a safe readiness check

![Annotated RCS settings page](/docs/assets/screenshots/v1_2_1_patch4/rcs-settings.svg)

## Presenter lines for the close

- "The customer sees a message. The business sees a controlled process."
- "The same cockpit covers messaging, booking, monitoring, and settings."
- "The architecture is modular enough to grow beyond Google or one messaging provider."

## Related release notes

- `Docs/releases/release_notes_v1_2_1_patch4_en.md`
