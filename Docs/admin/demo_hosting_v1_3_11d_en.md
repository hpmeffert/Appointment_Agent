# Demo Hosting v1.3.11d

## Purpose

This admin guide explains how the Appointment Agent is packaged as a hosted Docker demo release for Azure-oriented sales usage.

## What v1.3.11d is

`v1.3.11d` is a hosted demo package release.

It does not introduce a new full application line of its own. Instead, it bundles the currently proven runtime and cockpit lines into one documented Docker deployment package for sales demos.

## Version map

- package release: `v1.3.11d`
- runtime line: `v1.4.0`
- combined cockpit: `v1.3.10`
- address database: `v1.3.9`
- reminder line: `v1.3.6`
- LEKAB settings and monitor: `v1.3.8`

## Core admin topics

### Docker topology

The hosted demo runs with:

- one application container
- one named Docker volume for database persistence

### Database strategy

- SQLite stays inside the Docker runtime
- the DB file lives at `/app/data/appointment_agent.db`
- the volume keeps the demo state stable across restarts

### Seed and reset strategy

The hosted demo is designed for simple reset by Docker volume removal.

### Azure-oriented parameters

The most important Azure-relevant values are:

- `APPOINTMENT_AGENT_PUBLIC_BASE_URL`
- `APPOINTMENT_AGENT_PUBLIC_SCHEME`
- `APPOINTMENT_AGENT_TRUST_PROXY_HEADERS`
- `APPOINTMENT_AGENT_APP_PORT`
- `APPOINTMENT_AGENT_DB_URL`

### Demo operations

The main operator goal is:

- easy startup
- predictable demo state
- easy reset
- safe simulation defaults

## Important setup files

- `deploy/azure-demo/.env.azure.demo.example`
- `deploy/azure-demo/docker-compose.azure.demo.yml`
- `deploy/azure-demo/README.md`

## Related release package documents

- `Docs/release_packages/v1_3_11d/INSTALLATION_GUIDE_v1_3_11d.md`
- `Docs/release_packages/v1_3_11d/DOCKER_TOPOLOGY_v1_3_11d.md`
- `Docs/release_packages/v1_3_11d/DATABASE_STRATEGY_v1_3_11d.md`
- `Docs/release_packages/v1_3_11d/SEED_AND_RESET_STRATEGY_v1_3_11d.md`
- `Docs/release_packages/v1_3_11d/AZURE_ENVIRONMENT_PARAMETERS_v1_3_11d.md`
- `Docs/release_packages/v1_3_11d/DEMO_OPERATIONS_AND_STARTUP_v1_3_11d.md`
- `Docs/release_packages/v1_3_11d/RELEASE_MANIFEST_v1_3_11d.md`
