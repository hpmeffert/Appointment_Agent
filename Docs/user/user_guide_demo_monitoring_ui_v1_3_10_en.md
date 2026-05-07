# Appointment Agent User Guide v1.3.10 (EN)

## Scope
Version `v1.3.10` improves two core behaviors in the Appointment Agent demonstrator:
- safer appointment identification
- future-only slot proposals

The goal is that the system identifies the correct appointment first and only then offers valid future dates and times.

## What Changed
- The system can now work with stronger appointment references such as reservation-style references, appointment/calendar references, correlation references, customer numbers, and normalized phone numbers.
- If several future appointments match the same customer, the system no longer guesses. It asks which appointment should be changed.
- Slot proposals are future-only and respect a minimum lead time.
- A selected slot is rechecked before mutation so stale or past slots are not confirmed accidentally.

## Customer Experience
### 1. Clear appointment targeting
If the customer has only one relevant future appointment, the flow continues directly.

### 2. Explicit selection for multiple appointments
If more than one appointment fits, the system asks the customer which appointment should be confirmed, cancelled, or rescheduled.

### 3. Future-only slot proposals
The system only proposes slots that are still valid in the future. Old or already elapsed same-day slots are filtered out.

## Expected Behaviors
- `Confirm` keeps the current appointment when the target is safely resolved.
- `Reschedule` only continues when the target appointment is known.
- `Cancel` only affects the resolved appointment and never guesses across multiple appointments.
- `No match` results in a safe clarification or no-op response.

## Safety Defaults
- Minimum lead time: `30 minutes`
- Maximum slot proposal window: bounded by configured booking window limits
- Maximum offered dates/times: limited by the active flow configuration
- Silence threshold default: `1300 ms`

## Typical Flow
1. Reminder arrives.
2. Customer selects `Reschedule`.
3. System resolves which appointment is meant.
4. If multiple appointments exist, the system asks which one should be changed.
5. The system proposes future-only slots.
6. Customer selects a slot.
7. The slot is validated again before booking mutation.

## Notes
- `v1.3.10` is additive and should not break protected `v1.x` behavior.
- Ambiguous appointment actions are intentionally blocked until the target is explicit.
