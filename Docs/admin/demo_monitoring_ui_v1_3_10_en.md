# Appointment Agent Admin Guide v1.3.10 (EN)

## Release Intent
`v1.3.10` hardens appointment identification and future-only slot handling in the demonstrator and orchestration paths.

## Admin-Relevant Changes
- appointment identification now supports stronger reference-based resolution
- multiple matching appointments require explicit selection before mutation
- slot proposals are filtered through a future-only safety guard
- same-day slot handling now respects a minimum lead time

## Operational Defaults
- `minimum_lead_time_minutes = 30`
- `booking_window_days` remains bounded by configuration
- `silence_threshold_ms = 1300`
- adapters remain execution layers; orchestration owns resolution and mutation safety

## Verification Checklist
1. Confirm protected single-match flows still work.
2. Verify that multi-match flows require appointment selection.
3. Verify that past or stale same-day slots are not offered.
4. Verify that selected slots are rechecked before mutation.
5. Verify docs and release notes exist in DE and EN.

## Risk Notes
- Legacy static date buttons in older simulation-only paths should not be treated as the source of truth for real scheduling behavior.
- Existing protected runtime paths must remain non-breaking within the `v1.x` line.
