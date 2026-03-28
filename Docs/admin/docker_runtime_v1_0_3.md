# Appointment Agent Docker Admin Guide v1.0.3

Version: v1.0.4 Patch 1
Status: current Docker-backed demo patch
Language: English

This guide explains the Docker runtime in a simple and practical way.

## What Is Running

For `v1.0.3`, Docker starts one combined app container.

Inside that container you get:

- API routes
- Demo UI routes
- Monitoring routes
- documentation routes
- local SQLite persistence
- appointment reminder demo flows

This is enough for local demos and development without pretending we already have a big production cluster.

## Main Docker Files

- `Dockerfile`
  This tells Docker how to build the application image.
- `docker-compose.yml`
  This tells Docker Compose how to start the app in a repeatable way.
- `.dockerignore`
  This keeps junk, local DB files, and test artifacts out of the image build context.
- `.env.example`
  This shows which parameters can be changed safely for local runtime.

## Important Parameters

- `APPOINTMENT_AGENT_APP_HOST`
  Keep this as `0.0.0.0` in Docker so the container listens correctly.
- `APPOINTMENT_AGENT_APP_PORT`
  This is the external port you open in the browser. Default: `8080`.
- `APPOINTMENT_AGENT_DB_URL`
  This is the SQLite path used by the app. In Docker it points to `/app/data/appointment_agent.db`.
- `APPOINTMENT_AGENT_LOG_LEVEL`
  This decides how detailed the logs are.
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  `true` means use the prototype Google path, not a real Google account.
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`
  `true` means use the current LEKAB mock behavior.
- `APPOINTMENT_AGENT_DEMO_BASE_PATH`
  This tells the app which demo route should be treated as the main demo entry path.

## Start Procedure

1. Copy the sample file:
   `cp .env.example .env`
2. Start the stack:
   `docker compose up --build`
3. Check health:
   `http://localhost:8080/health`
4. Open the demo:
   `http://localhost:8080/ui/demo-monitoring/v1.0.2`

## What Should Work

After startup, these should respond:

- `/health`
- `/help`
- `/ui/demo-monitoring/v1.0.2`
- `/api/demo-monitoring/v1.0.2/scenarios`
- `/docs/demo`

The scenario payload should now also include reminder cases:

- `appointment-reminder-keep`
- `appointment-reminder-reschedule`
- `appointment-reminder-cancel`
- `appointment-reminder-call-me`

## Reminder Flow Parameters

- `appointment_date`
  The date shown in the reminder.
- `appointment_time`
  The time shown in the reminder.
- `booking_reference`
  The internal booking id used by the platform.
- `provider_reference`
  The external provider id, for example from Google.
- `selected_action`
  The action chosen from the reminder flow.
- `current_state`
  The resulting state after the action, such as `BOOKED`, `WAITING_FOR_SELECTION`, `CLOSED`, or `ESCALATED`.

## Reset Behavior

- `docker compose down`
  Stops the app, but keeps the named Docker volume.
- `docker compose down -v`
  Stops the app and removes the Docker volume. This is the clean reset path.

## Troubleshooting

- If the UI does not load, check `docker compose logs`.
- If the docs route fails in Linux, look for a `Docs/` path issue.
- If the DB cannot be opened, remove the volume with `docker compose down -v` and start again.
- If reminder actions do not appear in the demo, check that the scenario payload includes the new reminder scenario ids.
