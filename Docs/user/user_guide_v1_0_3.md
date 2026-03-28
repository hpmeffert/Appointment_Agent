# User Guide v1.0.3

This guide explains how to start the Appointment Agent prototype with Docker.

## Why Docker Is Used

Docker helps you run the project in one ready-made box.

That means:

- fewer manual setup steps
- easier local demos
- fewer "it works on my machine" problems

## Start In 2 Steps

1. Create your local config file:

```bash
cp .env.example .env
```

2. Start the project:

```bash
docker compose up --build
```

## What To Open

Open this in your browser:

- `http://localhost:8080/ui/demo-monitoring/v1.0.2`

If everything is working, you should see:

- a big demo page
- mode buttons like Demo, Monitoring, Combined
- scenario controls
- a help button with `?`

## Useful Links

- Health check: `http://localhost:8080/health`
- Demo Guide: `http://localhost:8080/docs/demo`
- User Guide: `http://localhost:8080/docs/user`
- Admin Guide: `http://localhost:8080/docs/admin`

## Important Parameters

- `APPOINTMENT_AGENT_APP_PORT`
  This decides which browser port you open.
- `APPOINTMENT_AGENT_DEFAULT_LANGUAGE`
  This sets the default language direction for the app.
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  This keeps the Google side safe for demos.
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`
  This keeps the LEKAB side safe for demos.

## Stop Or Reset

Stop:

```bash
docker compose down
```

Reset everything:

```bash
docker compose down -v
```

Use reset if the app gets stuck because of old local runtime state.
