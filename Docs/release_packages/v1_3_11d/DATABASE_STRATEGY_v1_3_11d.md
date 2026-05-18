# Database Strategy v1.3.11d

## Main idea

The hosted demo runtime uses SQLite inside Docker because it is simple, portable, and good enough for a controlled sales demo system.

## Current database location

- container path: `/app/data/appointment_agent.db`
- configured by: `APPOINTMENT_AGENT_DB_URL`

## Why SQLite is used here

- very easy to package in Docker
- no extra database server is needed
- good for a single hosted demo runtime
- easy to reset by removing the Docker volume

## Persistence model

The hosted demo runtime uses a named Docker volume:

- `appointment-agent-demo-data-v1311d`

This means:

- data survives container restart
- data disappears only when the volume is removed

## What the database currently stores in demo mode

- demo appointments
- address records
- reminder state
- message monitor history
- scenario context and related demo state

## Important parameter

- `APPOINTMENT_AGENT_DB_URL`
  This points the runtime at the database file. For the hosted demo package, it should stay on the Docker-managed data path unless you intentionally move it.
