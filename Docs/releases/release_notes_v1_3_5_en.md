# Release Notes v1.3.5

Version: v1.3.5
Language: EN

## What is new

- The reminder cockpit now shows delivery channels in a simple way.
- The cockpit now shows validation outcomes in plain language.
- The cockpit now shows delivery results in a result timeline.
- The health view now shows runtime status, last activity, and what is due next.
- The docs were rewritten so a motivated 16-year-old can understand them.
- The demo guide now contains three short delivery stories.

## Main routes

- `GET /ui/reminder-scheduler/v1.3.5`
- `GET /api/reminder-ui/v1.3.5/payload`
- `GET /api/reminder-ui/v1.3.5/help`
- `GET /api/reminder-ui/v1.3.5/config`
- `GET /api/reminder-ui/v1.3.5/config/preview`
- `GET /api/reminder-ui/v1.3.5/results`
- `GET /api/reminder-ui/v1.3.5/health`

## Verification

- The UI renders with the new delivery wording.
- The payload returns at least three demo stories.
- The help output shows the important parameters.
- The tests cover the UI, payload, help, config, preview, results, and health routes.
