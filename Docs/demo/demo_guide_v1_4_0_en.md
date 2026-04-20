# Demo Guide v1.4.0

## Overview

`v1.4.0` is the first release where the Appointment Agent can be demonstrated as one coherent end-to-end system.

## Demo Entry

- Cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.9`
- Current patch line: `http://localhost:8080/ui/demo-monitoring/v1.3.9-patch9`

## Story Scenario 1 — Reminder Confirmation

1. Start in real mode
2. Send a reminder
3. Select `Confirm`
4. Verify the final confirmation state in the dashboard

## Story Scenario 2 — Full Reschedule Flow

1. Send a reminder
2. Select `Reschedule`
3. Select a scheduling window
4. Select a dynamic date
5. Select a dynamic time
6. Select `Confirm`
7. Verify the Google Calendar event

## Story Scenario 3 — Address and Calendar Quality

1. Run a real reschedule flow for a linked address
2. Confirm the Google Calendar title format
3. Confirm the address lines in the description
4. Confirm metadata linkage is present

## Story Scenario 4 — Timezone Validation

1. Use an address configured with `Europe/Berlin`
2. Select a local slot such as `14:00`
3. Confirm the event
4. Verify that the Google Calendar event keeps `14:00`

## Demo Notes

- Use real mode for the production-capable flow
- Scenario mode remains available for guided simulation
- UX refinements are intentionally deferred to `v1.5.0`
