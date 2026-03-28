# Demo Guide v1.0.1

## Scenario 1
Start a journey with `RETRY_WITH_BROADER_WINDOW` and show that the no-slot path retries before offering escalation.

## Scenario 2
Create a booking, trigger `/journeys/reschedule`, then confirm the replacement slot and show the CRM update preparation event.

## Scenario 3
Trigger explicit help escalation and review the persisted audit trail via `/journeys/{journey_id}/audit`.
