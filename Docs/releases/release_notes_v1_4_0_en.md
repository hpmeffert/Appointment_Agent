# Release Notes v1.4.0

## Summary

Version `1.4.0` marks the first production-ready functional core release of the Appointment Agent.

The system now supports a verified end-to-end appointment flow with real messaging, real callback processing, dynamic Google-backed availability, confirmed Google Calendar writes, and timezone-correct scheduling behavior.

## Highlights

- Real LEKAB RCS outbound messaging with interactive reply buttons
- Stable callback roundtrip for multi-step mobile-device flows
- Guided live flow:
  `Reminder -> Reschedule -> timeframe -> date -> time -> Confirm`
- Dynamic Google Calendar availability for date and time suggestions
- Real Google Calendar booking and reschedule writes
- Correct calendar event title format:
  `<Appointment Type> – <Customer Name>`
- Structured event descriptions with address and context
- Stable linkage metadata for `correlation_id`, `booking_reference`, `appointment_id`, and `address_id`
- Address-driven timezone handling for region-correct booking behavior

## Verified Scope

- Real device testing completed
- Real callback roundtrip completed
- Dynamic date suggestions verified
- Dynamic time suggestions verified
- Confirm flow verified
- Google Calendar event creation verified
- Address/title/description formatting verified
- Timezone fix verified for the active Germany test flow

## Functional Modules Included

- LEKAB RCS messaging
- Callback-driven orchestration
- Multi-step appointment scheduling
- Google availability engine
- Google booking write path
- Dashboard demonstrator
- Address linkage and timezone support

## Known Acceptable Limitations

- UX is functional but not final
- Dashboard design polish is planned for `v1.5`
- Advanced retry logic is not yet implemented
- Full monitoring and alerting are not yet implemented

## Runtime Notes

- Top-level app release is visible as `v1.4.0`
- Current demo cockpit route remains stable at `/ui/demo-monitoring/v1.3.9`
- Current live cockpit patch line remains `v1.3.9-patch9`
- Silence Threshold default remains `1300ms`

## Next Release

Planned focus for `v1.5.0`:

- UX improvements
- Demo dashboard redesign
- Usability enhancements
