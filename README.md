# Appointment Agent

This project is a versioned prototype platform for the LEKAB Appointment Agent.

In simple words:

- a customer sends a message
- the system understands the request
- it searches for free appointment slots
- it books, changes, or cancels appointments
- it shows both customer flow and technical flow in a live demo UI

## Current Versions

- Core internal integration line: `v1.0.1`
- Demo UI stable line: `v1.0.0`
- Demo UI release preparation line: `v1.0.2`

## Main Modules

- `apps/lekab_adapter/v1_0_0`
- `apps/appointment_orchestrator/v1_0_0`
- `apps/appointment_orchestrator/v1_0_1`
- `apps/google_adapter/v1_0_0`
- `apps/google_adapter/v1_0_1`
- `apps/demo_monitoring_ui/v1_0_0`
- `apps/demo_monitoring_ui/v1_0_2`
- `apps/shared/v1_0_0`

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

## How To Run The Backend

```bash
docker compose up --build
```

The backend starts on port `8080`.

## How To Open The Demo

Open:

- Demo UI: `http://localhost:8080/ui/demo-monitoring/v1.0.0`
- Demo UI Release Candidate: `http://localhost:8080/ui/demo-monitoring/v1.0.2`
- Demo scenarios API: `http://localhost:8080/api/demo-monitoring/v1.0.0/scenarios`
- Demo scenarios API Release Candidate: `http://localhost:8080/api/demo-monitoring/v1.0.2/scenarios`
- Help overview: `http://localhost:8080/help`
- Demo Guide: `http://localhost:8080/docs/demo`
- User Guide: `http://localhost:8080/docs/user`
- Admin Guide: `http://localhost:8080/docs/admin`

## How To Run Tests

```bash
./scripts/run_tests.sh
```

Test summaries and JUnit output are written to `test-results/`.

## Repository Structure

- `apps/` application code
- `docs/` documentation
- `tests/` automated tests
- `scripts/` helper scripts
- `docker/` future docker-specific assets
- `data/` local runtime database files

## Security Basics

- Do not commit real credentials.
- Use `.env.example` as your sample configuration.
- Runtime database files stay local in `data/`.
