# Docker Runtime Guide v1.0.3

This folder explains the Docker runtime for the Appointment Agent prototype.

## What Docker Does Here

Docker puts the project into one repeatable box.

That means:

- you do not need to install Python packages by hand
- the API starts the same way on another machine
- the demo UI and docs routes are available in the same local runtime
- the local SQLite prototype database lives in a Docker volume

## Fast Start

1. Copy the sample environment file:

```bash
cp .env.example .env
```

2. Build and start:

```bash
docker compose up --build
```

3. Open the demo in your browser:

- `http://localhost:8080/ui/demo-monitoring/v1.0.2`

## Helpful URLs

- Root: `http://localhost:8080/`
- Health: `http://localhost:8080/health`
- Demo UI: `http://localhost:8080/ui/demo-monitoring/v1.0.2`
- Scenarios API: `http://localhost:8080/api/demo-monitoring/v1.0.2/scenarios`
- Help API: `http://localhost:8080/api/demo-monitoring/v1.0.2/help`
- Demo Guide: `http://localhost:8080/docs/demo`

## Important Parameters

- `APPOINTMENT_AGENT_APP_HOST`
  This is the network address the app listens on inside Docker. Keep `0.0.0.0`.
- `APPOINTMENT_AGENT_APP_PORT`
  This is the HTTP port for the app. Default is `8080`.
- `APPOINTMENT_AGENT_DB_URL`
  This tells the app where the SQLite database file lives. In Docker it should point to `/app/data/...`.
- `APPOINTMENT_AGENT_LOG_LEVEL`
  This controls how loud the logs are. `info` is a good default for demos.
- `APPOINTMENT_AGENT_DEFAULT_LANGUAGE`
  This sets the default UI language choice. Right now the default is English.
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  This keeps the Google side in prototype mode instead of real production credentials.
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`
  This keeps the LEKAB side in mock mode for safe local demos.

## Stop And Reset

Stop:

```bash
docker compose down
```

Reset all local Docker runtime state:

```bash
docker compose down -v
```

## Smoke Test

Run this after startup:

```bash
./scripts/docker_smoke_test.sh
```

If it finishes without an error, the important demo routes are alive.

## Common Errors

- `port is already allocated`
  Another app already uses port `8080`.
- `No such file or directory` for the DB path
  The container could not create or reach the SQLite path.
- `ModuleNotFoundError`
  The image build or package install did not complete correctly.
- docs route opens with an error
  The container may have a path mismatch for the `Docs/` folder.
