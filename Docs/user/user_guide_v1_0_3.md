# User Guide v1.0.3

Version: v1.0.4 Patch 2
Status: current Docker-backed demo patch
Language: English

This guide explains how to start the Appointment Agent prototype with Docker.

## Why Docker Is Used

Docker helps you run the project in one ready-made box.

That means:

- fewer manual setup steps
- easier local demos
- fewer "it works on my machine" problems

## Start In 2 Steps

1. Create your local config file:

```bash
cp .env.example .env
```

2. Start the project:

```bash
docker compose up --build
```

## What To Open

Open this in your browser:

- `http://localhost:8080/ui/demo-monitoring/v1.0.4-patch2`

If everything is working, you should see:

- a big demo page
- mode buttons like Demo, Monitoring, Combined
- scenario controls
- a help button with `?`
- reminder scenarios like keep, reschedule, cancel, and call me
- a header that shows `v1.0.4 Patch 2`
- a messaging card with `message_id` and `lekab_job_id`

## Useful Links

- Health check: `http://localhost:8080/health`
- Demo Guide: `http://localhost:8080/docs/demo`
- User Guide: `http://localhost:8080/docs/user`
- Admin Guide: `http://localhost:8080/docs/admin`

## New Reminder Flow

The project now includes a reminder flow for existing appointments.

That means the system can show a message like:

- "Reminder: You have an appointment tomorrow at 10:00."

And then offer these actions:

- Keep appointment
- Reschedule
- Cancel
- Call me

This is useful because many real customers do not want to start from zero. They just want to react to the reminder quickly.

## Important Reminder Parameters

- `appointment_date`
  This is the calendar date shown in the reminder message.
- `appointment_time`
  This is the appointment time shown in the reminder message.
- `appointment_type`
  This is the short label for the appointment, for example `consultation`.
- `booking_reference`
  This is the internal appointment id that helps the system track the booking.
- `provider_reference`
  This is the provider-side id, for example the Google event id.
- `selected_action`
  This shows what the customer chose in the reminder flow: `keep`, `reschedule`, `cancel`, or `call_me`.
- `journey_id`
  This is the id for the full appointment process from start to finish.
- `correlation_id`
  This helps connect matching events and log entries.

## Important Parameters

- `APPOINTMENT_AGENT_APP_PORT`
  This decides which browser port you open.
- `APPOINTMENT_AGENT_DEFAULT_LANGUAGE`
  This sets the default language direction for the app.
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  This keeps the Google side safe for demos.
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`
  This keeps the LEKAB side safe for demos.

## Stop Or Reset

Stop:

```bash
docker compose down
```

Reset everything:

```bash
docker compose down -v
```

Use reset if the app gets stuck because of old local runtime state.
