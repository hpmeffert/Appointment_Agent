# Docker Topology v1.3.11d

## Topology summary

`v1.3.11d` uses one main application container and one persistent named Docker volume for demo data.

## Topology diagram

```text
Public Browser
      |
      v
Azure Host / VM / Container Runtime
      |
      v
Docker Compose
      |
      v
appointment-agent container
      |
      +--> FastAPI / UI / Docs / APIs
      |
      +--> SQLite database at /app/data/appointment_agent.db
      |
      +--> named volume appointment-agent-demo-data-v1311d
```

## Why this topology is used

- simple to explain
- easy to deploy
- easy to reset
- enough for a hosted sales demo
- does not require a separate database server for the first hosted demo phase

## Main container responsibilities

The `appointment-agent` container provides:

- main web application
- demo cockpit
- address database UI
- reminder APIs
- Google demo APIs
- LEKAB settings and monitoring APIs
- docs routes
- health endpoint

## Main volume responsibility

The named volume stores:

- SQLite database file
- demo runtime state that should survive container restarts

## What is intentionally not part of this first topology

- separate production database server
- container orchestration cluster logic
- customer-grade HA topology

This release is for a controlled hosted demo runtime.
