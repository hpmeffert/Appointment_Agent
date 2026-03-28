# Appointment Agent

This project is a versioned prototype platform for the LEKAB Appointment Agent.

In simple words:

- a customer sends a message
- the system understands the request
- it searches for free appointment slots
- it books, changes, or cancels appointments
- it shows both customer flow and technical flow in a live demo UI

## Current Versions

- Core internal integration line: `v1.0.4-patch2`
- Demo UI stable line: `v1.0.0`
- Demo UI release preparation line: `v1.0.2`
- Demo UI current patch line: `v1.0.4-patch2`
- Docker runtime release line: `v1.0.4-patch2`

## Main Modules

- `apps/lekab_adapter/v1_0_0`
- `apps/appointment_orchestrator/v1_0_0`
- `apps/appointment_orchestrator/v1_0_1`
- `apps/google_adapter/v1_0_0`
- `apps/google_adapter/v1_0_1`
- `apps/demo_monitoring_ui/v1_0_0`
- `apps/demo_monitoring_ui/v1_0_2`
- `apps/demo_monitoring_ui/v1_0_4_patch1`
- `apps/demo_monitoring_ui/v1_0_4_patch2`
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

Current patch focus in `v1.0.4-patch2`:

- event timeline view
- correlation and trace view
- load and concurrency simulation
- performance panel
- technical mode toggle

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
- Demo UI Current Patch: `http://localhost:8080/ui/demo-monitoring/v1.0.4-patch2`
- Demo scenarios API: `http://localhost:8080/api/demo-monitoring/v1.0.0/scenarios`
- Demo scenarios API Release Candidate: `http://localhost:8080/api/demo-monitoring/v1.0.2/scenarios`
- Demo scenarios API Current Patch: `http://localhost:8080/api/demo-monitoring/v1.0.4-patch2/scenarios`
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

## Common Docker Problems

- If Docker says the port is already in use, stop the other app that already uses port `8080`, or change `APPOINTMENT_AGENT_APP_PORT` in `.env`.
- If the app cannot start, check `docker compose logs` and look for module import or path errors.
- If the UI opens but looks empty, test the API route `/api/demo-monitoring/v1.0.4-patch2/scenarios`.
- If the database cannot be written, reset with `docker compose down -v` and start again.
