# Appointment Agent Admin Guide v1.4.0

## Release Position

`v1.4.0` is the first functional production-ready core release.

The stable live demonstrator route remains:

- `/ui/demo-monitoring/v1.3.9`

The current live patch shell remains:

- `/ui/demo-monitoring/v1.3.9-patch9`

## Operational Scope

- Real LEKAB RCS messaging is active
- Real callback processing is active
- Dynamic Google availability is active
- Google Calendar booking writes are active
- Address linkage is active
- Address timezone can now be persisted and used in the booking path

## Admin Checks

- Verify LEKAB RCS settings in the cockpit
- Verify callback URLs and webhook fetch settings
- Verify Google mode status and calendar target
- Verify selected address linkage before real runs
- Verify address timezone for region-sensitive tests

## Release Notes for Operators

- Top-level app version is visible as `v1.4.0`
- Silence Threshold default remains `1300ms`
- The release is functionally production-capable
- UX improvements remain planned for `v1.5.0`
