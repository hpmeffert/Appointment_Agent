# Appointment Agent

This project is a versioned prototype platform for the LEKAB Appointment Agent.

In simple words:

- a customer sends a message
- the system understands the request
- it searches for free appointment slots
- it books, changes, or cancels appointments
- it shows both customer flow and technical flow in a live demo UI

## Current Versions

- Core public release line: `v1.2.1-patch4`
- Demo UI stable line: `v1.0.0`
- Demo UI release preparation line: `v1.0.2`
- Demo UI current release line: `v1.2.1-patch4`
- Docker runtime release line: `v1.2.1-patch4`

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

Current release focus in `v1.2.1-patch4`:

- guided demo mode now supports `Free` and `Guided`
- auto-demo can walk through the presenter story step by step
- the dashboard is more messaging-first and shows live guided status
- platform visibility is clearer for channels, integrations, and AI building blocks
- message monitor, story engine, and operator summary now support a stronger live-demo narrative
- docs now explain the new guided parameters and presenter flow more clearly

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
- Demo UI Current Release: `http://localhost:8080/ui/demo-monitoring/v1.2.1-patch4`
- Demo Cockpit v1.0.5: `http://localhost:8080/ui/demo-monitoring/v1.0.5`
- Demo Cockpit v1.0.6: `http://localhost:8080/ui/demo-monitoring/v1.0.6`
- Demo Cockpit v1.0.6 Patch 1: `http://localhost:8080/ui/demo-monitoring/v1.0.6-patch1`
- Demo scenarios API: `http://localhost:8080/api/demo-monitoring/v1.0.0/scenarios`
- Demo scenarios API Release Candidate: `http://localhost:8080/api/demo-monitoring/v1.0.2/scenarios`
- Demo cockpit payload Current Release: `http://localhost:8080/api/demo-monitoring/v1.2.1-patch4/payload`
- Demo help API Current Release: `http://localhost:8080/api/demo-monitoring/v1.2.1-patch4/help`
- LEKAB RCS settings API: `http://localhost:8080/api/lekab/v1.2.1-patch4/settings/rcs`
- LEKAB RCS validation API: `http://localhost:8080/api/lekab/v1.2.1-patch4/settings/rcs/validate`
- Demo cockpit payload v1.0.5: `http://localhost:8080/api/demo-monitoring/v1.0.5/payload`
- Demo cockpit payload v1.0.6: `http://localhost:8080/api/demo-monitoring/v1.0.6/payload`
- Demo cockpit payload v1.0.6 Patch 1: `http://localhost:8080/api/demo-monitoring/v1.0.6-patch1/payload`
- Google test mode status API: `http://localhost:8080/api/google/v1.2.0/mode`
- Google live sync status API: `http://localhost:8080/api/google/v1.2.0/live-sync/status`
- Google conflict check API: `http://localhost:8080/api/google/v1.2.0/live-sync/conflict-check`
- Google availability slots API: `http://localhost:8080/api/google/v1.2.0/availability/slots`
- Google slot hold create API: `http://localhost:8080/api/google/v1.2.0/slot-hold/create`
- Google slot hold release API: `http://localhost:8080/api/google/v1.2.0/slot-hold/release`
- Google booking create API: `http://localhost:8080/api/google/v1.2.0/booking/create`
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
- If the UI opens but looks empty, test the API route `/api/demo-monitoring/v1.2.1-patch4/payload`.
- If `Test` mode says it is unavailable, check `.env` for `GOOGLE_REAL_INTEGRATION_ENABLED`, `GOOGLE_REFRESH_TOKEN`, and `GOOGLE_CALENDAR_ID`.
- If the database cannot be written, reset with `docker compose down -v` and start again.
