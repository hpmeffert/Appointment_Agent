# User Guide v1.4.0

## What v1.4.0 gives you

`v1.4.0` is the first functional production-ready release of the Appointment Agent.

You can now run a complete appointment journey with real messaging, real callback handling, dynamic availability, and Google Calendar booking.

## Main User Flows

- Receive a reminder on the mobile device
- Select `Reschedule`
- Select a scheduling window such as `This week` or `Next week`
- Select one of the offered dates
- Select one of the offered times
- Confirm the appointment
- Receive the final confirmation

## What you should expect

- Buttons appear on the mobile device as interactive reply buttons
- Suggested dates and times come from the real Google availability flow
- Confirmed bookings are written to Google Calendar
- Event titles use the customer name
- Event descriptions include address and context
- Local timezone handling is applied for supported address records

## Current Main Entry Points

- Demo cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.9`
- Current patch cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.9-patch9`
- Help: `http://localhost:8080/help`
- Health: `http://localhost:8080/health`

## Notes

- The visible app release is `v1.4.0`
- The cockpit route stays on the stable `v1.3.9` path
- UX improvements are planned for `v1.5.0`
