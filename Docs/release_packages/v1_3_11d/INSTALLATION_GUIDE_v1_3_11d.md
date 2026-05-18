# Installation Guide v1.3.11d

## What this guide does

This guide explains how to install and start the hosted demo package of the Appointment Agent with Docker.

The goal is a simple setup for an Azure-hosted demo environment that sales colleagues can later use.

## What you need

- Docker and Docker Compose
- access to this repository
- one copied demo env file
- optional real Google or LEKAB secrets, only if you want more than pure simulation

## The easiest setup path

### 1. Copy the Azure demo env file

```bash
cp deploy/azure-demo/.env.azure.demo.example deploy/azure-demo/.env.azure.demo
```

### 2. Review the important values

At minimum, check these:

- `APPOINTMENT_AGENT_APP_PORT`
- `APPOINTMENT_AGENT_DEMO_BASE_PATH`
- `APPOINTMENT_AGENT_PUBLIC_BASE_URL`
- `GOOGLE_REAL_INTEGRATION_ENABLED`
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`

## 3. Start the hosted demo stack

```bash
docker compose \
  -f deploy/azure-demo/docker-compose.azure.demo.yml \
  --env-file deploy/azure-demo/.env.azure.demo \
  up --build -d
```

## 4. Check the health endpoint

Open:

- `http://localhost:8080/health`

You should see a healthy response.

## 5. Open the main demo cockpit

Open:

- `http://localhost:8080/ui/demo-monitoring/v1.3.10`

## Important parameters explained

- `APPOINTMENT_AGENT_APP_PORT`
  This is the external port for the web application.
- `APPOINTMENT_AGENT_DB_URL`
  This tells the runtime where the SQLite database file lives.
- `APPOINTMENT_AGENT_DEMO_BASE_PATH`
  This is the main cockpit route the hosted demo should consider as its base entry point.
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  `true` means Google stays in safe simulation mode.
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`
  `true` means communication stays in safe demo mode.
- `GOOGLE_REAL_INTEGRATION_ENABLED`
  `false` means no real upstream Google integration is required for the standard hosted demo.
- `APPOINTMENT_AGENT_PUBLIC_BASE_URL`
  This is the public Azure URL that later points to the hosted demo.

## When you want the safest sales setup

Use these defaults:

- Google mock mode on
- LEKAB mock mode on
- no real secrets
- persistent Docker volume enabled

That gives the most stable demo environment with the least risk.
