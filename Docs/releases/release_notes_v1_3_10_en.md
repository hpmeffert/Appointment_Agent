# Release Notes v1.3.10 (EN)

## Summary
Version `v1.3.10` introduces safer appointment identification and future-only slot proposal behavior for the Appointment Agent demonstrator and orchestration paths.

## Highlights
- Added stronger appointment identification inputs:
  - reservation-style reference
  - appointment or calendar reference
  - correlation reference
  - customer number
  - normalized phone number
- Added explicit multiple-appointment selection behavior before confirm, cancel, or reschedule can mutate anything.
- Added future-only slot filtering with a default minimum lead time of `30 minutes`.
- Added selected-slot revalidation before mutation.
- Preserved protected `v1.x` single-match flows.

## Safety
- No mutation on ambiguous appointment targets
- No mutation on no-match states
- No stale or already elapsed same-day slot proposals
- Silence threshold default remains `1300 ms`

## Documentation
- User Guide updated
- Demo Guide updated with 3 scenarios
- Admin Guide updated
- Release Notes updated in DE and EN
