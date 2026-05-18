# User Guide v1.3.11d

## What this release is for

`v1.3.11d` is meant to make the Appointment Agent easier to use as a hosted demo system.

That means the system is prepared so sales can later open one hosted URL and work with a stable Docker-based demo runtime.

## What you can use in the demo

- the combined appointment cockpit
- the reminder cockpit
- the address database
- the Google demo control
- the message monitor

## What is important for a safe demo

For the easiest setup, the hosted demo should usually stay in simulation-friendly mode.

Important values:

- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE=true`
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE=true`
- `GOOGLE_REAL_INTEGRATION_ENABLED=false`

## Main entry point

Open:

- `/ui/demo-monitoring/v1.3.10`

## Important parameters

- `APPOINTMENT_AGENT_APP_PORT`
  The port where the demo is reachable.
- `APPOINTMENT_AGENT_DEMO_BASE_PATH`
  The main demo route path.
- `APPOINTMENT_AGENT_PUBLIC_BASE_URL`
  The public Azure URL for the hosted demo.
- `APPOINTMENT_AGENT_DB_URL`
  The demo database path in the runtime.

## When something looks wrong

Check:

- `/health`
- the Docker container status
- the Docker volume reset path if old demo data causes confusion
