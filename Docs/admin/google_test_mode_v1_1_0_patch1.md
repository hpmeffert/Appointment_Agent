# Google Test Mode and Demo Prep v1.1.0 Patch 1

Version: v1.1.0 Patch 1
Audience: Admin
Language: EN

## What this patch adds

This patch gives the operator a safe switch between two Google behaviors:

- `Simulation`
- `Test`

`Simulation` means the system uses fake calendar data. Nothing is written to Google.

`Test` means the system uses the real Google calendar from your local `.env`. This is meant for controlled demos only.

## Main endpoints

- `GET /api/google/v1.1.0-patch1/mode`
- `POST /api/google/v1.1.0-patch1/demo-calendar/prepare`
- `GET /api/google/v1.1.0-patch1/contact-linking`

## Important parameters

- `mode`
  This tells the system which behavior you want.
  Use `simulation` for safe fake behavior.
  Use `test` for real Google Calendar writes.

- `timeframe`
  This tells the system which time window to prepare.
  Allowed values:
  - `day`
  - `week`
  - `month`

- `action`
  This tells the system what to do with the chosen timeframe.
  Allowed values:
  - `generate`
  - `delete`
  - `reset`

- `count`
  This is the number of demo appointments to create.
  Allowed range in this patch: `1` to `30`.

- `include_customer_name`
  If `true`, the generated appointment title and details include a demo customer name.

- `include_description`
  If `true`, the event description includes the demo marker and the short reason for the appointment.

- `include_location`
  If `true`, the event gets a useful demo location like `Remote Call` or `Customer Property`.

## Safety rules

- Demo-generated events are marked with `[Appointment Agent Demo]`.
- Cleanup only removes events that have this demo marker.
- Manual real appointments must not be deleted by the reset logic.
- Test mode should point only to a dedicated demo/test calendar.

## Environment variables

- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  If this is `true`, the platform stays in fake Google mode.

- `GOOGLE_REAL_INTEGRATION_ENABLED`
  If this is `true`, the real Google Calendar client may be used.

- `GOOGLE_TEST_MODE_DEFAULT`
  This chooses which Google mode the UI starts with.
  Allowed values:
  - `simulation`
  - `test`

- `GOOGLE_CALENDAR_ID`
  The exact Google Calendar that test mode should use.

- `GOOGLE_REFRESH_TOKEN`
  The refresh token used to request Google access tokens.

- `GOOGLE_CONTACTS_ENABLED`
  This does not fully enable People API syncing yet.
  In this patch it only marks that contact-aware behavior is being prepared.

## Manual entry strategy

Manual appointments are different from generated demo appointments.

Generated appointments:
- already know the demo customer
- can show whether a mobile number exists
- can show whether SMS/RCS would be possible

Manual appointments:
- may only contain a title or attendee email
- may need later lookup through Google People API
- may end in a safe fallback like `not linked` or `linked without mobile`

## Future direction

Right now the test calendar may still belong to a personal workspace.
Later this should move into a LEKAB-controlled workspace so calendar ownership and contact ownership stay in a business environment.
