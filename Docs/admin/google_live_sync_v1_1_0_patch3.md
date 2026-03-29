# Google Live Sync v1.1.0 Patch 3

Version: v1.1.0-patch3
Audience: Admin
Language: EN

## What this patch adds

This patch adds real live-sync and conflict-check endpoints for the Google test calendar path.

## Main ideas

- read live occupancy from Google before booking-critical actions
- detect conflicts before unsafe changes
- detect stale provider references
- make live versus simulation status visible

## Main routes

- `POST /api/google/v1.1.0-patch3/live-sync/status`
- `POST /api/google/v1.1.0-patch3/live-sync/conflict-check`

## Important parameters

### `mode`

- `simulation`
- `test`

### `timeframe`

- `day`
- `week`
- `month`

### `start_time`

Start of the slot that should be checked.

### `end_time`

End of the slot that should be checked.

### `provider_reference`

Existing Google event reference that should still exist.

### `exclude_provider_reference`

Useful for reschedule checks so the current event does not block itself.

## Conflict types

- `slot_occupied`
- `provider_reference_stale`

## Monitoring labels used

- `google.sync.read.started`
- `google.sync.read.completed`
- `google.conflict.detected`
- `google.provider_reference.stale`
- `calendar.slot.revalidated`
