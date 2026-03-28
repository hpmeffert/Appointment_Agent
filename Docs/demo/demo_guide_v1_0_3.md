# Demo Guide v1.0.3

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
