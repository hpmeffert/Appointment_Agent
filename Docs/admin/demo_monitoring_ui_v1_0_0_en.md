# Demo Monitoring UI Admin Guide v1.0.0 EN

Version: v1.0.4 Patch 1
Status: active demo patch
Language: English
Release shown in UI header: `v1.0.4 Patch 1`
Note: This filename stays stable for route compatibility. The content is updated for `v1.0.4 Patch 1`.

## What this module is

This UI is a demo and monitoring surface.

It is not a full production admin portal.

It has two main jobs:

1. show how the appointment flow feels for a customer
2. show what the platform does technically at the same time

## The 3 modes

- `Demo`
  Focus on the customer-facing story.

- `Monitoring`
  Focus on the technical system view.

- `Combined`
  Show both sides together. This is usually the best mode for presentations.

## Main routes

- `/ui/demo-monitoring/v1.0.0`
  Opens the UI.

- `/api/demo-monitoring/v1.0.0/scenarios`
  Returns the simulation payload as JSON.

- `/api/demo-monitoring/v1.0.0/help`
  Returns a small overview of modes and scenario ids.

- `/docs/demo?lang=en|de`
  Opens the localized demo guide.

- `/docs/user?lang=en|de`
  Opens the localized user guide.

- `/docs/admin?lang=en|de`
  Opens the localized admin guide.

## Release visibility

The UI header now shows the active demo patch line so presenters can point to the exact build being shown.

Current visible release string:

`v1.0.4 Patch 1`

## Messaging identifiers

- `message_id`
  Tracks the simulated inbound or outbound message on the communication side.

- `lekab_job_id`
  Tracks the workflow job on the LEKAB side.

- `message_channel`
  Shows the messaging channel like `RCS` or `SMS`.

- `message_status`
  Shows the message lifecycle state.

- `delivery_status`
  Shows the delivery-side result.

## Service bus explanation

Use a service bus so the modules stay loosely coupled.

That gives us:

- cleaner boundaries between LEKAB, Orchestrator, adapters, and CRM events
- easier future provider changes
- better scaling and safer extension points

## Scaling explanation

- `20 users`
  Multiple journeys already run in parallel.

- `100 users`
  Stateless services can be replicated across more containers.

- `1000 users`
  Queueing, more compute, better database tuning, and stronger observability become important.

## Important parameters

- `journey_id`
  Main id for one complete appointment journey.

- `correlation_id`
  Connects related events and audit entries.

- `trace_id`
  Technical tracking id for deeper debugging.

- `booking_reference`
  Internal appointment id.

- `provider_reference`
  External provider appointment id.

- `message_id`
  Communication-side message id.

- `lekab_job_id`
  LEKAB workflow job id.
