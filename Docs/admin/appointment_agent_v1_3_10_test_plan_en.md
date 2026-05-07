# Appointment Agent v1.3.10 Test Plan (EN)

Version: v1.3.10

## Purpose

This test plan verifies that `v1.3.10` delivers:

- safe appointment identification
- future-only slot proposals
- explicit ambiguity handling for multiple appointments
- protected `v1.3.9` route compatibility
- stable Google, LEKAB, and cockpit behavior

## Test Principles

- never accept or propose past slots
- never mutate an ambiguous appointment silently
- preserve the protected `v1.x` line
- verify both technical correctness and operator-visible behavior

## Required Environment

- local runtime on `http://localhost:8080`
- protected demo base route available on `/ui/demo-monitoring/v1.3.9`
- visible patch line shown as `v1.3.10`
- Google adapter test path available
- LEKAB monitor path available
- address database seeded with at least:
  - one customer with one appointment
  - one customer with multiple appointments
  - one customer record with `customer_number`
  - one booking with `reservation_ref`

## Required Version Checks

1. Open `/help`.
2. Verify the top-level app version remains valid for the protected release line.
3. Open `/ui/demo-monitoring/v1.3.9`.
4. Verify the shell shows the visible patch version `v1.3.10`.
5. Open:
   - `/docs/demo?lang=en`
   - `/docs/user?lang=en`
   - `/docs/admin?lang=en`
6. Verify the rendered guides are the `v1.3.10` documents.

## Automated Verification

Run:

```bash
pytest tests/appointment_orchestrator/v1_0_1/test_appointment_resolution_contract.py \
  tests/appointment_orchestrator/v1_0_1/test_appointment_resolution_candidates.py \
  tests/appointment_orchestrator/v1_0_1/test_appointment_resolution_runtime.py \
  tests/appointment_orchestrator/v1_0_1/test_appointment_resolution_multi_ux.py \
  tests/appointment_orchestrator/v1_0_1/test_appointment_mutation_policy.py \
  tests/appointment_orchestrator/v1_0_1/test_appointment_mutation_runtime.py \
  tests/appointment_orchestrator/v1_0_1/test_orchestrator_v101.py \
  tests/google_adapter/v1_1_0_patch8a/test_google_adapter_v110_patch8a.py \
  tests/google_adapter/test_calendar_formatting.py \
  tests/lekab_adapter/v1_3_8/test_lekab_reply_action_engine_v138.py \
  tests/demo_monitoring_ui/v1_3_9/test_demo_monitoring_ui_v139.py -q
```

Expected result:

- all tests green
- no regression in resolver, mutation policy, Google availability, LEKAB monitor, or cockpit shell

## Test Matrix

| ID | Area | Scenario | Expected Result |
| --- | --- | --- | --- |
| TP-01 | Versioning | Open protected base route | Base route remains `/ui/demo-monitoring/v1.3.9` |
| TP-02 | Versioning | Inspect visible shell version | Header/help shows `v1.3.10` |
| TP-03 | Docs | Open docs routes | All routes resolve to `v1.3.10` docs |
| TP-04 | Resolver | Resolve by `reservation_ref` | Exactly one appointment is resolved |
| TP-05 | Resolver | Resolve by `customer_number` | Matching appointment candidates are found |
| TP-06 | Resolver | Resolve by normalized phone variants | All supported phone formats map safely |
| TP-07 | Resolver | No appointment match | No mutation occurs |
| TP-08 | Resolver | Multiple appointments match | Selection is required before mutation |
| TP-09 | Slot safety | Same-day stale slot | Slot is rejected |
| TP-10 | Slot safety | Future slot after lead time | Slot is accepted |
| TP-11 | Slot safety | This week search | Only future-valid slots are returned |
| TP-12 | Slot safety | Next week search | Slots are inside next week only |
| TP-13 | Slot safety | This month search | No past dates/times appear |
| TP-14 | Slot safety | Next month search | Results are bounded to next month |
| TP-15 | Slot safety | Next free slot | Earliest valid future slot is returned |
| TP-16 | Google | Selected slot becomes stale before confirm | Confirm path rejects it safely |
| TP-17 | Google | Valid future reschedule | Slot proceeds to booking path |
| TP-18 | LEKAB | Ambiguous ordinal reply | Monitor preserves action metadata |
| TP-19 | UI | Customer journey output | Future-slot and selection states are visible |
| TP-20 | Regression | Existing protected route behavior | No `v1.3.9` breakage |

## Detailed Manual Cases

### Case A — Single appointment resolved by reservation reference

1. Prepare a booking with a known `reservation_ref`.
2. Trigger a reschedule or lookup flow using that reference.
3. Confirm the resolver selects exactly one appointment.

Expected:

- `resolution_status = resolved`
- no ambiguity payload
- correct appointment context retained

### Case B — Single appointment resolved by customer number

1. Prepare an address record with `customer_number`.
2. Link it to one appointment.
3. Trigger a lookup using the customer number.

Expected:

- customer number participates in resolution
- appointment context is preserved through slot search

### Case C — Multiple appointments require selection

1. Prepare one customer with at least two future appointments.
2. Trigger a reschedule or cancel request without a unique hard identifier.

Expected:

- `resolution_status = ambiguous_multiple_appointments` or equivalent selection-required state
- the system shows candidate appointments
- no cancel or reschedule is executed automatically

### Case D — No match

1. Trigger lookup with a nonexistent reservation or customer reference.

Expected:

- no appointment is mutated
- a safe review/no-match response is returned

### Case E — Same-day lead-time rejection

1. Ensure current local time is known.
2. Generate or inspect a same-day slot earlier than `now + 30 minutes`.
3. Attempt to propose or select it.

Expected:

- slot is filtered out or rejected
- no confirmation path accepts it

### Case F — Future slot acceptance

1. Generate or select a slot clearly later than the lead-time window.

Expected:

- slot survives filtering
- slot can be used in the next flow step

### Case G — Search-window correctness

1. Trigger each relative window:
   - this week
   - next week
   - this month
   - next month
   - next free slot
2. Inspect returned proposals.

Expected:

- proposals respect the chosen window
- no past date or past time is returned
- proposal count remains bounded

### Case H — Stale selected slot before confirm

1. Select a slot.
2. Simulate or force a stale timestamp condition before confirm.
3. Confirm the slot.

Expected:

- confirm path rejects the stale slot
- no incorrect booking update occurs

### Case I — LEKAB ambiguous ordinal reply metadata

1. Simulate or trigger a reply like `the first one`.
2. Open `/api/lekab/v1.3.8/monitor`.

Expected:

- message metadata includes:
  - `reply_intent`
  - `action_candidate`
  - `action_type`
  - interpretation state

### Case J — Cockpit and docs visibility

1. Open the cockpit route.
2. Open the docs routes.
3. Inspect payload/help output.

Expected:

- visible patch version is `v1.3.10`
- demo API base remains protected on `v1.3.9`
- docs routes serve the `v1.3.10` guides

## Data Validation Checklist

- `reservation_ref` is present where expected
- `customer_number` survives lookup and correlation
- `appointment_id`, `booking_reference`, and `correlation_ref` remain stable
- timezone-sensitive slot calculations remain future-correct

## Failure Conditions

Fail `v1.3.10` if any of the following occurs:

- a past slot is proposed
- a same-day slot inside the lead-time window is accepted
- multiple appointments are matched and one is mutated implicitly
- a no-match path still mutates anything
- the visible shell version is not `v1.3.10`
- the protected `v1.3.9` route breaks
- LEKAB monitor metadata is incomplete for callback interpretation

## Final Operator Sign-Off

`v1.3.10` is operator-ready only if:

- automated regression is green
- all manual critical cases pass
- ambiguity handling is explicit
- future-only slot rules are confirmed
- documentation and issue tracking are updated together
