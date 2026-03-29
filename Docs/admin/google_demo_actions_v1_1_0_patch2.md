# Google Demo Actions v1.1.0 Patch 2 Admin Guide

Version: v1.1.0-patch2
Audience: Admin
Language: EN

## What was fixed

The root cause was simple:

- the `Prepare` button called the same backend logic as `Generate`
- frontend errors were not shown clearly
- the operator could not easily tell if anything actually happened

## New routes

- `GET /api/google/v1.1.0-patch2/mode`
- `POST /api/google/v1.1.0-patch2/demo-calendar/prepare-preview`
- `POST /api/google/v1.1.0-patch2/demo-calendar/generate`
- `POST /api/google/v1.1.0-patch2/demo-calendar/delete`
- `POST /api/google/v1.1.0-patch2/demo-calendar/reset`
- `GET /api/google/v1.1.0-patch2/contact-linking`

## Button behavior

### `Prepare Demo Calendar`

Creates a preview only.

Important:

- no Google event is written
- no local demo event is persisted
- the UI shows sample appointments and a preview message

### `Generate Demo Appointments`

Creates real demo appointments for the selected mode.

- in `simulation` mode it creates simulated results only
- in `test` mode it writes to the configured Google test calendar

### `Delete Demo Appointments`

Deletes only demo-generated appointments.

Safety rule:

- deletion targets demo markers only
- manual calendar entries must stay untouched

### `Reset Demo Calendar`

Deletes old demo-generated appointments and then creates a fresh demo set.

## Important parameters

### `mode`

- `simulation`
- `test`

### `timeframe`

- `day`
- `week`
- `month`

### `count`

How many appointments should be prepared or generated.

Allowed range:

- `1` to `30`

### `vertical`

- `general`
- `dentist`
- `wallbox`
- `district_heating`

### `action`

- `prepare`
- `generate`
- `delete`
- `reset`

## Manual verification

1. Open the UI route `/ui/demo-monitoring/v1.1.0-patch2`.
2. Click `Prepare Demo Calendar` and check that only preview feedback appears.
3. Click `Generate Demo Appointments`.
4. If `test` mode is active, open Google Calendar and verify the test calendar entries.
5. Click `Delete Demo Appointments`.
6. Verify that demo-generated entries are gone and manual entries remain.
