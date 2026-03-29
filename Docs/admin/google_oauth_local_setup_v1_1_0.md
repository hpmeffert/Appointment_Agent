# Google OAuth Local Setup v1.1.0

Version: v1.1.0 Prep
Status: local preparation
Language: English

## What this setup is for

This setup helps you prepare the project for the first real Google Calendar integration work.

The goal is simple:

- keep your Google OAuth file safe
- get a real refresh token locally
- fill your local `.env` correctly
- avoid committing secrets

## Where to place the downloaded OAuth JSON

Use this local path:

`local-secrets/google/credentials.json`

Important:

- this file contains a real client secret
- never commit it
- never move it into a tracked source folder

The repo now ignores:

- `local-secrets/`
- `secrets/`
- `apps/google_adapter/json/`

## How to get the first refresh token

1. Make sure the desktop OAuth JSON is in `local-secrets/google/credentials.json`
2. Install the optional Google helper packages if needed:

```bash
pip install -e '.[google]'
```

3. Run the helper:

```bash
python3 scripts/get_google_refresh_token.py
```

What happens:

- a browser login flow opens
- Google asks for consent
- the helper prints the important `.env` values
- the helper stores a sensitive local token file in `local-secrets/google/token.json`

## How to fill your local `.env`

Use these values in your local `.env`:

```env
APPOINTMENT_AGENT_GOOGLE_MOCK_MODE=false
APPOINTMENT_AGENT_LEKAB_MOCK_MODE=true
APPOINTMENT_AGENT_DEMO_BASE_PATH=/ui/demo-monitoring/v1.0.4-patch2

GOOGLE_CLIENT_ID=<from OAuth client JSON>
GOOGLE_CLIENT_SECRET=<from OAuth client JSON>
GOOGLE_REDIRECT_URI=http://localhost
GOOGLE_REFRESH_TOKEN=<from the helper output>
GOOGLE_CALENDAR_ID=<your test calendar id>
GOOGLE_DEFAULT_TIMEZONE=Europe/Berlin
GOOGLE_REAL_INTEGRATION_ENABLED=true
```

Important rule:

- do not keep `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE=true` together with `GOOGLE_REAL_INTEGRATION_ENABLED=true`

## What the important fields mean

- `GOOGLE_CLIENT_ID`
  This is the public identifier of your desktop OAuth app.

- `GOOGLE_CLIENT_SECRET`
  This is the secret part of the OAuth client. Treat it like a password.

- `GOOGLE_REDIRECT_URI`
  This is where the local browser flow returns after login. For this local helper it should be `http://localhost`.

- `GOOGLE_REFRESH_TOKEN`
  This is the long-lived token that lets the app ask Google for new access tokens later.

- `GOOGLE_CALENDAR_ID`
  This is the exact Google Calendar you want to read and write.

- `GOOGLE_DEFAULT_TIMEZONE`
  This tells the future real integration which timezone to use by default.

- `APPOINTMENT_AGENT_GOOGLE_MOCK_MODE`
  When this is `true`, the project stays on the fake Google flow.

- `GOOGLE_REAL_INTEGRATION_ENABLED`
  When this is `true`, the project is allowed to use the real Google integration path later.

## Optional local calendar sanity check

After you have a token file, you can test calendar access:

```bash
python3 scripts/check_google_calendar_access.py --calendar-id YOUR_CALENDAR_ID
```

This script:

- reads the ignored local token file
- builds a Google Calendar client
- checks if the configured calendar can be reached

## Safety reminders

- do not commit `credentials.json`
- do not commit `token.json`
- do not commit a real `.env`
- if you accidentally place secrets in a tracked folder, move them out before committing
