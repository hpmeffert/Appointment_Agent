# Demo Guide v1.0.3

Version: v1.0.4 Patch 1
Status: current Docker-backed demo patch
Language: English

This guide helps you run the Docker-based demo in a simple way.

## Start Before The Demo

```bash
cp .env.example .env
docker compose up --build
```

Open:

- `http://localhost:8080/ui/demo-monitoring/v1.0.2`

## Story Scenario 1: Standard Booking

What to show:

- customer message
- slot suggestions
- booking confirmation
- monitoring view on the right

What to say:

- "On the left you see the customer story."
- "On the right you see what the system is doing."
- "This is process automation, not just a chat answer."

## Story Scenario 2: No Slot To Escalation

What to show:

- no available slot
- escalation step
- audit and event flow

What to say:

- "If no slot is available, the system does not freeze."
- "It follows a defined fallback path."
- "That makes the process safer for real operations."

## Story Scenario 3: Reschedule

What to show:

- changed request
- new slot selection
- updated booking state

What to say:

- "The same journey can continue instead of starting from zero."
- "That keeps context, audit history, and booking references together."

## Story Scenario 4: Appointment Reminder

What to show:

- a reminder message with date and time
- action choices: keep, reschedule, cancel, call me
- booking reference and provider reference on the monitoring side
- audit and CRM event updates

What to say:

- "This is one of the most realistic appointment use cases."
- "The reminder is useful because the customer can react immediately."
- "The same reminder can lead into confirmation, reschedule, cancellation, or human handover."

## Reminder Parameters To Explain

- `appointment_date`
  This is the date shown in the reminder text.
- `appointment_time`
  This is the time shown in the reminder text.
- `booking_reference`
  This is our internal booking id.
- `provider_reference`
  This is the external provider booking id.
- `selected_action`
  This shows which reminder action the customer picked.
- `current_state`
  This shows whether the journey is still booked, in reschedule flow, escalated, or closed.

## Important Parameters

- `APPOINTMENT_AGENT_APP_PORT`
  This decides which browser URL you open.
- `APPOINTMENT_AGENT_DEMO_BASE_PATH`
  This points to the main demo route for the release.
- `APPOINTMENT_AGENT_DEFAULT_LANGUAGE`
  This decides the default language direction when the app starts.

## Quick Check Before Presenting

- `/health` returns `ok`
- demo page loads
- scenario API loads
- help menu opens docs pages
- reminder scenarios are visible in the scenario list
