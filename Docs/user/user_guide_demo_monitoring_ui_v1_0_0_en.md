# Demo Monitoring UI User Guide v1.0.0 EN

Version: v1.0.4 Patch 2
Status: active demo patch
Language: English
Release shown in UI header: `v1.0.4 Patch 2`
Note: This filename stays stable for route compatibility. The content is updated for `v1.0.4 Patch 2`.

## What this page does

This page helps you explain the Appointment Agent visually.

On the left side you see:

- what the customer writes
- which options the customer gets
- what the platform answers

On the right side you see:

- which module is active
- which events are emitted
- which booking details exist
- which messaging details exist
- which audit notes exist

## Main URL

Use this page in the browser:

`/ui/demo-monitoring/v1.0.0`

## Main controls

- `Mode`
  Switch between `Demo`, `Monitoring`, and `Combined`.

- `Scenario`
  Choose the flow you want to show.

- `Restart`
  Go back to the first step of the current scenario.

- `Next Step`
  Move to the next step manually.

- `Autoplay`
  Play the scenario automatically.

- `Show IDs`
  Show or hide technical ids like `booking_reference`, `provider_reference`, and message-related identifiers.

- `Show Audit Details`
  Show or hide audit entries.

- `EN` and `DE`
  Switch the full UI language.

## What the right-side panels mean

- `Journey State`
  The current state of the appointment flow.

- `Flow Steps`
  Shows which modules are pending, active, done, failed, or escalated.

- `Event Timeline`
  Shows the main events in time order.

- `Booking Details`
  Shows internal and external booking references.

- `Messaging Details`
  Shows message-tracking information from the LEKAB side.

- `Audit Log`
  Shows important decisions made by the platform.

- `Key Parameters`
  Explains important technical parameters in simple language.

- `CRM Events`
  Shows which events could be forwarded to a CRM layer.

## New monitoring tabs

- `Timeline`
  Shows detailed events with timestamp, event type, journey id, correlation id, and trace id.
- `Trace`
  Groups the flow by request-tracking ids so you can follow one request chain.
- `Performance`
  Shows simulated load and performance numbers for `20`, `100`, and `1000` users.

## What the messaging identifiers mean

- `message_id`
  This is the identifier for the communication-side message. It helps you track which inbound or outbound message belongs to the journey.

- `lekab_job_id`
  This is the LEKAB-side workflow job identifier. It tracks the workflow job, not the message itself.

- `message_channel`
  Shows if the simulated message uses `RCS` or `SMS`.

- `message_status`
  Shows the current message state like `sent` or `received`.

- `delivery_status`
  Shows the delivery-side result like `delivered`.

## What the service bus means

The service bus is the message path between modules.

Simple idea:

- one module sends an event
- another module reacts to it
- the platform stays modular because modules do not need too many hard direct links

## How the system scales

- `20 users`
  Many appointment journeys can already run in parallel.
- `100 users`
  More containers can share the load.
- `1000 users`
  More compute power, better database tuning, queue-based buffering, and clear separation between Orchestrator, messaging, and adapters become more important.

## Important parameters

- `journey_id`
  One id for one whole customer appointment journey.

- `correlation_id`
  Helps connect related events.

- `trace_id`
  Helps with deep debugging.

- `booking_reference`
  Internal platform booking id.

- `provider_reference`
  External provider booking id.

- `message_id`
  Communication-side message id.

- `lekab_job_id`
  LEKAB workflow job id.

- `appointment_date`
  The date shown in reminder flows.

- `appointment_time`
  The time shown in reminder flows.

- `selected_action`
  The action the customer selected in a reminder flow.
