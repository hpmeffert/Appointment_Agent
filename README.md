# Appointment Agent

The Appointment Agent is a versioned, event-driven demo platform for appointment booking, rescheduling, cancellation, reminder planning, address correlation, and communication monitoring.

In simple words:

- a customer sends a message
- the system interprets the request
- it searches for available times
- it books, changes, or cancels appointments
- it plans reminders
- it keeps address, message, and appointment context together
- it shows the full business and technical flow in a live demo cockpit

## Current release picture

This repository currently contains a versioned demo platform with multiple stable module lines.

The important current lines are:

- Hosted demo release package target: `v1.3.11d`
- Core runtime line: `v1.4.0`
- Main combined demo cockpit: `v1.3.10`
- Address database cockpit line: `v1.3.9`
- Reminder cockpit line: `v1.3.6`
- LEKAB monitoring/settings line: `v1.3.8`
- Docker runtime baseline: `v1.4.0`

`v1.3.11d` is intentionally documented as a hosted demo package release. It bundles the currently proven demo lines into one Azure-ready Docker setup for sales usage.

## What the platform can already demonstrate

### Appointment and orchestration flows

- guided confirm / reschedule / cancel demo journeys
- slot lookup and slot selection
- slot-hold handling and parallel booking protection
- reply-to-action interpretation for inbound responses
- operator-visible scenario context across modules

### Google demo and calendar flows

- Google demo control for prepare / generate / delete / reset
- live and simulation mode split
- generated appointment linkage into the demo story
- calendar-aware demo slot and booking flows

### Reminder flows

- reminder policy and preview
- reminder job visibility
- linkage from appointment source to reminder plan
- reminder-focused cockpit and bridge views

### Communication and monitoring

- LEKAB-related settings and demo controls
- communication history with inbound and outbound messages
- message monitor and report cards
- callback fetching and monitoring support
- reply interpretation preview

### Address and cross-module context

- address database UI
- address-to-appointment linkage
- cross-module address anchor for messages and reminders
- shared correlation context for demo scenarios

### Demo operations

- Docker-based local runtime
- health checks and smoke tests
- docs routes for user, demo, and admin guides
- structured demo scenario testing and local artifacts

## Main modules

- `apps/shared/v1_0_0`
- `apps/appointment_orchestrator/v1_0_1`
- `apps/google_adapter/v1_3_6`
- `apps/lekab_adapter/v1_3_8`
- `apps/address_database/v1_3_9`
- `apps/demo_monitoring_ui/v1_3_9`
- `apps/reminder_scheduler/v1_3_6`
- `Docs/`
- `deploy/azure-demo/`

## Runtime architecture

```text
Customer / Messaging
        |
        v
LEKAB Adapter / Message Monitor
        |
        v
Appointment Orchestrator
        |
        v
Google Adapter / Calendar Demo
        |
        v
Reminder Scheduler
        |
        v
Address Context / Monitoring / Demo Cockpit
```

## Quick start with Docker

### Standard local start

```bash
cp .env.example .env
docker compose up --build -d
```

### Hosted demo package start

Use the Azure demo package files:

```bash
cp deploy/azure-demo/.env.azure.demo.example deploy/azure-demo/.env.azure.demo
docker compose \
  -f deploy/azure-demo/docker-compose.azure.demo.yml \
  --env-file deploy/azure-demo/.env.azure.demo \
  up --build -d
```

## Main URLs

### Main demo pages

- Combined demo cockpit: `http://localhost:8080/ui/demo-monitoring/v1.3.10`
- Compatibility cockpit route: `http://localhost:8080/ui/demo-monitoring/v1.3.9`
- Address database: `http://localhost:8080/ui/address-database/v1.3.9`
- Reminder cockpit: `http://localhost:8080/ui/reminder-scheduler/v1.3.6`

### Core APIs

- Combined cockpit payload: `http://localhost:8080/api/demo-monitoring/v1.3.9/payload`
- Combined cockpit help: `http://localhost:8080/api/demo-monitoring/v1.3.9/help`
- Reminder config: `http://localhost:8080/api/reminders/v1.3.6/config`
- Reminder jobs: `http://localhost:8080/api/reminders/v1.3.6/jobs`
- Google demo linkage: `http://localhost:8080/api/google/v1.3.6/linkage/demo`
- LEKAB RCS settings: `http://localhost:8080/api/lekab/v1.3.8/settings/rcs`
- Address database help: `http://localhost:8080/api/addresses/v1.3.9/help`

### Service pages

- Root: `http://localhost:8080/`
- Health: `http://localhost:8080/health`
- Demo guide: `http://localhost:8080/docs/demo`
- User guide: `http://localhost:8080/docs/user`
- Admin guide: `http://localhost:8080/docs/admin`

## Docker and database behavior

- The runtime uses SQLite inside the container runtime path `/app/data/appointment_agent.db`
- The default Docker Compose stack persists that database in the named volume `appointment-agent-data`
- The Azure demo package uses its own named volume to keep demo data separate
- Demo reset is done by stopping the stack and removing the named volume

## Testing

Run the full suite:

```bash
./scripts/run_tests.sh
```

Run the Docker smoke test:

```bash
./scripts/docker_smoke_test.sh
```

## Hosted demo release package docs

The `v1.3.11d` hosted demo package is documented here:

- [Release package index](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/README.md)
- [Installation guide](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/INSTALLATION_GUIDE_v1_3_11d.md)
- [Docker topology](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/DOCKER_TOPOLOGY_v1_3_11d.md)
- [Database strategy](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/DATABASE_STRATEGY_v1_3_11d.md)
- [Seed and reset strategy](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/SEED_AND_RESET_STRATEGY_v1_3_11d.md)
- [Azure environment parameters](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/AZURE_ENVIRONMENT_PARAMETERS_v1_3_11d.md)
- [Demo operations and startup](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/DEMO_OPERATIONS_AND_STARTUP_v1_3_11d.md)
- [Release manifest](/Users/jpm/Documents/GitHub/Appointment_Agent/Docs/release_packages/v1_3_11d/RELEASE_MANIFEST_v1_3_11d.md)

## Repository structure

- `apps/` application code
- `Docs/` documentation
- `deploy/azure-demo/` hosted demo deployment package
- `tests/` automated tests
- `scripts/` helper scripts
- `docker/` Docker runtime notes
- `data/` local runtime DB files

## Security basics

- Do not commit real credentials.
- Use the example env files as templates only.
- Keep Google, LEKAB, and callback secrets in local or hosted secret storage.
- Treat the hosted demo release as a controlled sales runtime, not as a production tenant platform.

## Common Docker problems

- If port `8080` is already used, change `APPOINTMENT_AGENT_APP_PORT`.
- If the UI opens but looks incomplete, test `/api/demo-monitoring/v1.3.9/payload`.
- If Google real mode is unavailable, check the related Google env values.
- If database writes fail, recreate the Docker volume and start again.
