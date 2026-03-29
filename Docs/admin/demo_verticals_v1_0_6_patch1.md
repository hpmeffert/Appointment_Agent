# Demo Verticals v1.0.6 Patch 1 Admin Guide

Version: v1.0.6-patch1
Audience: Admin
Language: EN

## Goal of this patch

This patch improves content quality for the vertical demo line.

It is mainly about believable wording, not about a new UI layout.

## Main route

- `http://localhost:8080/ui/demo-monitoring/v1.0.6-patch1`

## APIs

- `http://localhost:8080/api/demo-monitoring/v1.0.6-patch1/help`
- `http://localhost:8080/api/demo-monitoring/v1.0.6-patch1/payload`

## What changed technically

- added a separate `v1.0.6-patch1` cockpit route
- kept the existing `v1.0.6` route stable
- enriched Google demo appointment generation with vertical-specific:
  - titles
  - descriptions
  - customer prompts
  - reminder texts
  - follow-up actions
  - monitoring labels
  - customer contexts
- enriched cockpit payload data with:
  - audience fit
  - operator explanation
  - sample titles
  - reminder examples
  - follow-up prompts

## Important parameters

### `vertical`

Business scenario switch for the whole demo package.

Supported values:

- `dentist`
- `wallbox`
- `district_heating`

### `mode`

Controls whether demo generation stays local or writes to the Google test calendar.

Supported values:

- `simulation`
- `test`

### `timeframe`

Controls the generated appointment window.

Supported values:

- `day`
- `week`
- `month`

### `count`

Controls the number of generated appointments.

Allowed range:

- `1` to `30`

### `action`

Controls the demo calendar operation.

Supported values:

- `generate`
- `delete`
- `reset`

## Validation points

Check these things after startup:

1. The route `/ui/demo-monitoring/v1.0.6-patch1` loads.
2. The selected vertical changes the visible content story.
3. The Google demo generation uses the selected vertical.
4. Reminder wording matches the vertical.
5. Monitoring wording matches the vertical.

## Files that carry the patch

- `apps/google_adapter/v1_1_0_patch1/google_adapter/service.py`
- `apps/demo_monitoring_ui/v1_0_5/demo_monitoring_ui/payloads.py`
- `apps/demo_monitoring_ui/v1_0_5/demo_monitoring_ui/static/cockpit.html`
- `apps/demo_monitoring_ui/v1_0_6_patch1/demo_monitoring_ui/app.py`
