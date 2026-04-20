# Appointment Agent

This project is a versioned prototype platform for the LEKAB Appointment Agent.

In simple words:

- a customer sends a message
- the system understands the request
- it searches for free appointment slots
- it books, changes, or cancels appointments
- it shows both customer flow and technical flow in a live demo UI

## Current Versions

- Core public release line: `v1.4.0`
- Demo UI stable line: `v1.0.0`
- Demo UI release preparation line: `v1.0.2`
- Demo UI current release line: `v1.3.9-patch9`
- Docker runtime release line: `v1.4.0`

## Main Modules

- `apps/lekab_adapter/v1_0_0`
- `apps/appointment_orchestrator/v1_0_0`
- `apps/appointment_orchestrator/v1_0_1`
- `apps/google_adapter/v1_0_0`
- `apps/google_adapter/v1_0_1`
- `apps/google_adapter/v1_1_0_patch1`
- `apps/demo_monitoring_ui/v1_0_0`
- `apps/demo_monitoring_ui/v1_0_2`
- `apps/demo_monitoring_ui/v1_0_4_patch1`
- `apps/demo_monitoring_ui/v1_0_4_patch2`
- `apps/demo_monitoring_ui/v1_0_5`
- `apps/demo_monitoring_ui/v1_0_6`
- `apps/demo_monitoring_ui/v1_0_6_patch1`
- `apps/demo_monitoring_ui/v1_1_0_patch1`
- `apps/demo_monitoring_ui/v1_3_0`
- `apps/demo_monitoring_ui/v1_3_1`
- `apps/demo_monitoring_ui/v1_3_2`
- `apps/demo_monitoring_ui/v1_3_3`
- `apps/reminder_scheduler/v1_3_0`
- `apps/reminder_scheduler/v1_3_1`
- `apps/reminder_scheduler/v1_3_2`
- `apps/reminder_scheduler/v1_3_3`
- `apps/shared/v1_0_0`
- `Docs/`

## Current Product State

- LEKAB is still a mocked prototype adapter for internal flow simulation.
- Google booking flows are available in the prototype, but the real upstream Google API integration is planned for a later release step.
- Microsoft is prepared as a future adapter line and is not yet a full production integration.

## Architecture

```text
Customer / Messaging
        |
        v
LEKAB Adapter
        |
        v
Appointment Orchestrator
        |
        v
Google Adapter
        |
        v
Booking Result / Audit / CRM Events
```

## How To Run With Docker

```bash
cp .env.example .env
docker compose up --build
```

Docker is used here so you can start the full local prototype in one repeatable way.

The container starts the API, demo UI routes, monitoring routes, docs routes, and local SQLite prototype storage.

The default port is `8080`.

Current release focus in `v1.4.0`:

- real LEKAB RCS messaging now supports end-to-end multi-step appointment flows
- real Google Calendar availability and booking writes are active in the tested runtime
- selected address linkage is reflected in titles, descriptions, and metadata
- per-address timezone handling is applied in the booking path for region-correct scheduling

## How To Stop Or Reset Docker

Stop the running stack:

```bash
docker compose down
```

Reset the local Docker runtime state, including the named data volume:

```bash
docker compose down -v
```

## How To Open The Demo

Open:

- Demo UI: `http://localhost:8080/ui/demo-monitoring/v1.0.0`
- Demo UI Release Candidate: `http://localhost:8080/ui/demo-monitoring/v1.0.2`
- Demo Cockpit Current Release: `http://localhost:8080/ui/demo-monitoring/v1.3.9`
- Demo Cockpit Current Patch: `http://localhost:8080/ui/demo-monitoring/v1.3.9-patch9`
- Address Database UI: `http://localhost:8080/ui/address-database/v1.3.9`
- Embedded Reminder Scheduler Release: `http://localhost:8080/ui/reminder-scheduler/v1.3.6`
- Demo Cockpit v1.0.5: `http://localhost:8080/ui/demo-monitoring/v1.0.5`
- Demo Cockpit v1.0.6: `http://localhost:8080/ui/demo-monitoring/v1.0.6`
- Demo Cockpit v1.0.6 Patch 1: `http://localhost:8080/ui/demo-monitoring/v1.0.6-patch1`
- Demo scenarios API: `http://localhost:8080/api/demo-monitoring/v1.0.0/scenarios`
- Demo scenarios API Release Candidate: `http://localhost:8080/api/demo-monitoring/v1.0.2/scenarios`
- Reminder scheduler UI payload: `http://localhost:8080/api/reminder-ui/v1.3.6/payload`
- Reminder scheduler UI help: `http://localhost:8080/api/reminder-ui/v1.3.6/help`
- Reminder scheduler config API: `http://localhost:8080/api/reminders/v1.3.6/config`
- Reminder scheduler preview API: `http://localhost:8080/api/reminders/v1.3.6/config/preview`
- Reminder scheduler jobs API: `http://localhost:8080/api/reminders/v1.3.6/jobs`
- Reminder scheduler rebuild API: `http://localhost:8080/api/reminders/v1.3.6/rebuild`
- Reminder scheduler health API: `http://localhost:8080/api/reminders/v1.3.6/health`
- Reminder linkage demo API: `http://localhost:8080/api/reminders/v1.3.6/linkage/demo`
- Combined demo payload API: `http://localhost:8080/api/demo-monitoring/v1.3.9/payload`
- Combined demo help API: `http://localhost:8080/api/demo-monitoring/v1.3.9/help`
- Address database help API: `http://localhost:8080/api/addresses/v1.3.9/help`
- Address database list API: `http://localhost:8080/api/addresses/v1.3.9`
- LEKAB RCS settings API: `http://localhost:8080/api/lekab/v1.2.1-patch4/settings/rcs`
- LEKAB RCS validation API: `http://localhost:8080/api/lekab/v1.2.1-patch4/settings/rcs/validate`
- Demo cockpit payload v1.0.5: `http://localhost:8080/api/demo-monitoring/v1.0.5/payload`
- Demo cockpit payload v1.0.6: `http://localhost:8080/api/demo-monitoring/v1.0.6/payload`
- Demo cockpit payload v1.0.6 Patch 1: `http://localhost:8080/api/demo-monitoring/v1.0.6-patch1/payload`
- Google test mode status API: `http://localhost:8080/api/google/v1.3.6/mode`
- Google live sync status API: `http://localhost:8080/api/google/v1.3.6/live-sync/status`
- Google conflict check API: `http://localhost:8080/api/google/v1.3.6/live-sync/conflict-check`
- Google availability slots API: `http://localhost:8080/api/google/v1.3.6/availability/slots`
- Google slot hold create API: `http://localhost:8080/api/google/v1.3.6/slot-hold/create`
- Google slot hold release API: `http://localhost:8080/api/google/v1.3.6/slot-hold/release`
- Google booking create API: `http://localhost:8080/api/google/v1.3.6/booking/create`
- Google linkage demo API: `http://localhost:8080/api/google/v1.3.6/linkage/demo`
- Help overview: `http://localhost:8080/help`
- Health check: `http://localhost:8080/health`
- Demo Guide: `http://localhost:8080/docs/demo`
- User Guide: `http://localhost:8080/docs/user`
- Admin Guide: `http://localhost:8080/docs/admin`

## How To Run Tests

```bash
./scripts/run_tests.sh
```

Test summaries and JUnit output are written to `test-results/`.

For a quick Docker smoke test after startup:

```bash
./scripts/docker_smoke_test.sh
```

## Repository Structure

- `apps/` application code
- `Docs/` documentation sources
- `tests/` automated tests
- `scripts/` helper scripts
- `docker/` docker runtime notes
- `data/` local runtime database files

## Security Basics

- Do not commit real credentials.
- Use `.env.example` as your sample configuration.
- Runtime database files stay local in `data/`.
- Use `Simulation` mode until your Google test calendar is intentionally configured for live demo writes.

## Common Docker Problems

- If Docker says the port is already in use, stop the other app that already uses port `8080`, or change `APPOINTMENT_AGENT_APP_PORT` in `.env`.
- If the app cannot start, check `docker compose logs` and look for module import or path errors.
- If the UI opens but looks empty, test the API route `/api/demo-monitoring/v1.3.9/payload`.
- If `Test` mode says it is unavailable, check `.env` for `GOOGLE_REAL_INTEGRATION_ENABLED`, `GOOGLE_REFRESH_TOKEN`, and `GOOGLE_CALENDAR_ID`.
- If the database cannot be written, reset with `docker compose down -v` and start again.
