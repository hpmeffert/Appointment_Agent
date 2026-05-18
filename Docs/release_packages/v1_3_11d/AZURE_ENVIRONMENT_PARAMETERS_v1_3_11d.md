# Azure Environment Parameters v1.3.11d

## Goal

This document explains the environment values that matter most when you host the Docker demo package on Azure.

## Core runtime values

- `APPOINTMENT_AGENT_APP_HOST`
  Usually `0.0.0.0` so the container can accept external traffic.
- `APPOINTMENT_AGENT_APP_PORT`
  The web port inside and outside the container mapping.
- `APPOINTMENT_AGENT_LOG_LEVEL`
  Logging verbosity, usually `info` for hosted demo use.
- `APPOINTMENT_AGENT_DB_URL`
  SQLite database path inside the container.

## Demo behavior values

- `APPOINTMENT_AGENT_DEMO_BASE_PATH`
  Current hosted demo entry path: `/ui/demo-monitoring/v1.3.10`
- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  Keep `true` for the safest demo setup.
- `APPOINTMENT_AGENT_LEKAB_MOCK_MODE`
  Keep `true` for the safest demo setup.
- `APPOINTMENT_AGENT_DEFAULT_LANGUAGE`
  Demo default language.

## Public URL values

- `APPOINTMENT_AGENT_PUBLIC_BASE_URL`
  The public Azure URL where the demo is reachable.
- `APPOINTMENT_AGENT_PUBLIC_SCHEME`
  Normally `https`.
- `APPOINTMENT_AGENT_TRUST_PROXY_HEADERS`
  Should stay `true` if Azure or a reverse proxy sits in front of the container.

## Google-related values

- `GOOGLE_REAL_INTEGRATION_ENABLED`
- `GOOGLE_TEST_MODE_DEFAULT`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_CALENDAR_ID`
- `GOOGLE_DEFAULT_TIMEZONE`

For the easiest hosted demo, keep:

- `GOOGLE_REAL_INTEGRATION_ENABLED=false`
- `GOOGLE_TEST_MODE_DEFAULT=simulation`

## Communication-related values

- `LEKAB_CALLBACK_URL`
- `LEKAB_WEBHOOK_FETCH_URL`
- `LEKAB_WEBHOOK_API_KEY`
- `LEKAB_RIME_API_KEY`

These should only be filled if you intentionally want the hosted demo to talk to a real callback or communication test path.

## Rule of thumb

For the first Azure-hosted sales demo:

- prefer simulation defaults
- only add real secrets on purpose
- keep public URL values correct from day one
