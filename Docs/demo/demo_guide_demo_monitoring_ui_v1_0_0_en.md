# Demo Guide Demo Monitoring UI v1.0.0 EN

Version: v1.0.4 Patch 2
Status: active demo patch
Language: English
Release shown in UI header: `v1.0.4 Patch 2`
Note: This filename stays stable for route compatibility. The content is updated for `v1.0.4 Patch 2`.

## Why this appointment agent exists

This system exists to remove the back-and-forth of manual appointment booking.

In simple words, it helps because:

- customers can book or change appointments faster
- teams do not need to manually answer every small booking request
- reminders reduce missed appointments
- communication and backend booking logic stay connected automatically

## What parts work together

You can explain the system like this:

- `Customer / RCS / SMS`
  This is the communication side where the person sends or receives messages.
- `LEKAB`
  LEKAB handles the communication and workflow side. It sends messages and tracks message-related jobs.
- `Service Bus`
  Think of the bus like a central highway. Each part sends messages there, but the parts do not need hard direct links to every other part.
- `Appointment Orchestrator`
  This is the brain. It decides what should happen next.
- `Google Adapter`
  This part checks free time slots and writes booking changes to Google-side systems.
- `CRM Event Layer`
  This prepares business follow-up information.
- `Audit / Monitoring`
  This shows what happened and helps with debugging and trust.

## What "orchestrated" means

Orchestrated means the work is split into clear roles:

- one part sends the message
- one part decides the next step
- one part checks and books appointment times
- one part records business follow-up and technical history

That separation is important because it makes the system easier to understand, scale, and improve later.

## Practical architecture diagram

```text
Customer
  ↓
RCS / SMS
  ↓
LEKAB Messaging / Workflow Layer
  ↓
Service Bus
  ↓
Appointment Orchestrator
  ↓
Google Adapter
  ↓
Google Calendar
  ↓
Booking Result
  ↘
   CRM Event / Audit / Monitoring
```

How to explain this diagram:

- the customer starts on the communication side
- LEKAB handles message delivery and workflow jobs
- the Service Bus carries messages between parts
- the Orchestrator decides what to do next
- the Google Adapter talks to the calendar side
- the result is shown as booking state, CRM events, and audit information

## Opening line for the demo

Best opening sentence:

"On the left you see the customer. On the right you see what the system is doing."

Good follow-up sentence:

"The version in the header shows exactly which release we are demonstrating."

## Story 1 - Standard Booking

Use scenario `Standard Booking`.

What you can say:

1. The customer asks for an appointment.
2. LEKAB receives the communication-side message.
3. The Orchestrator asks for real availability.
4. The Google Adapter returns real slots.
5. The customer picks one slot.
6. The platform creates a real booking.

Important line:

"This is not a chatbot. This is process automation."

## Story 2 - Reschedule

Use scenario `Reschedule`.

What you can say:

1. This is not a new booking.
2. This is a change to an existing booking.
3. The `provider_reference` is the external booking id on the provider side.
4. The `message_id` tracks the communication side, while `booking_reference` tracks the appointment side.
5. The Orchestrator keeps the journey logic, while the Google Adapter updates the provider booking.

## Story 3 - Cancellation

Use scenario `Cancellation`.

What you can say:

1. The cancellation starts in messaging.
2. The cancellation must also finish cleanly in the backend.
3. The CRM layer gets a matching cancel event.

## Story 4 - No Slot and Escalation

Use scenario `No Slot and Escalation`.

What you can say:

1. Good automation must know when it cannot solve a problem alone.
2. If there is no free slot, the system does not freeze.
3. It offers alternatives, callback, or human handover.

## Story 5 - Provider Failure

Use scenario `Provider Failure`.

What you can say:

1. Even when the provider fails, the platform still reacts in a clear way.
2. The customer gets a safe answer.
3. The audit trail and escalation path stay visible.

## Preparing a Google Calendar Demo

### Goal

Make the calendar look realistic before a live demo:

- some slots are already booked
- some slots are still free
- the calendar looks like a real working day, week, or month

### Step 1 - Switch to Test Mode

In the UI:

- go to `Google Demo Control`
- choose `Test`

What this means:

- `Simulation` keeps everything fake and safe
- `Test` uses the real Google test calendar from your local setup

Important presenter sentence:

"Now I switch from safe simulation to the real test calendar."

### Step 2 - Prepare the Calendar

In the UI:

- click `Prepare Demo Calendar` or `Generate Demo Appointments`
- choose `Today`, `This Week`, or `This Month`
- choose how many appointments you want

Useful rule:

- `Today` is good for a short focused demo
- `This Week` is good when you want to show both free and busy days
- `This Month` is good when you want the calendar to look full and realistic

### What the system creates

The system creates realistic demo entries, for example:

- `Dentist Appointment - Dr. Zahn (Check-up)`
- `Heating Maintenance - Annual Inspection`
- `Wallbox Inspection - Check Wall Box Installation`

Why this matters:

- vague titles look fake
- real titles make the Google Calendar easier to understand live

### Step 3 - Verify the Calendar

Open:

- `https://calendar.google.com`

Check:

- which slots are booked
- which slots are free
- whether the live demo titles are visible

Good presenter sentence:

"This is a real calendar. The system understands availability."

### Step 4 - Reset After the Demo

In the UI:

- click `Delete Demo Appointments`

What this does:

- it removes only demo-generated entries
- it should not remove normal manual real appointments

This is safe because demo events are marked clearly before cleanup is allowed.

### Technical view

- `events.insert`
  Used to create the demo calendar entries.

- `freeBusy`
  Used to understand which time windows are still available.

### Simple parameter explanation

- `mode`
  Decides whether the system stays in fake behavior or writes to the real test calendar.

- `timeframe`
  Decides whether demo preparation happens for one day, one week, or one month.

- `count`
  Decides how many demo appointments should be created.

- `action`
  Decides whether the system should generate, delete, or reset the demo entries.

## How the Service Bus works

Simple explanation:

The Service Bus is like a central highway for system messages.

That means:

- LEKAB does not need a hard direct connection to every other module
- the Orchestrator can react to events in one stable place
- adapters can be changed later without rebuilding the whole platform
- debugging is easier because events can be followed step by step

Presenter line:

"This system is built on a service bus. That means communication is separated from logic and external systems."

## How the system scales

- `20 users`
  Many journeys can already run in parallel. Each journey has its own ids, so one flow does not overwrite another one.
- `100 users`
  Stateless services can scale horizontally. More containers can share the work.
- `1000 users`
  The main scaling knobs are more containers, more CPU, more memory, future queueing, and database optimization.

Key line:

"This system scales by separating responsibilities and running them independently."

## Important parameters in simple language

- `journey_id`
  One id for one full appointment journey from start to finish.

- `correlation_id`
  A shared id that helps connect messages and events that belong together.

- `trace_id`
  A deeper technical id for debugging and tracking.

- `booking_reference`
  Our internal booking id for the appointment side.

- `provider_reference`
  The external booking id on the provider side.

- `message_id`
  The id for the communication-side message. It helps track which outbound or inbound message belongs to the flow.

- `lekab_job_id`
  The LEKAB-side workflow job id. This is not the same as `message_id`.

- `appointment_date`
  The date shown in reminder flows.

- `appointment_time`
  The time shown in reminder flows.

- `selected_action`
  The option selected in a reminder flow, for example `keep`, `reschedule`, `cancel`, or `call_me`.

## New technical monitoring view

The monitoring area now has deeper technical tabs:

- `Timeline`
  Shows events in time order, with timestamp, `event_type`, `journey_id`, `correlation_id`, and `trace_id`.
- `Trace`
  Helps you follow one request chain through the system.
- `Performance`
  Shows simulated metrics like average response time, max response time, and events per second.

Good presenter lines:

- "This view shows what is happening inside the system."
- "You can follow a single request using correlation_id."
- "This proves the system is not just messaging, but real process orchestration."

## Recommended demo order

1. Start with `Standard Booking`.
2. Continue with `Reschedule`.
3. Show `Cancellation`.
4. End with `No Slot and Escalation` or `Provider Failure`.
