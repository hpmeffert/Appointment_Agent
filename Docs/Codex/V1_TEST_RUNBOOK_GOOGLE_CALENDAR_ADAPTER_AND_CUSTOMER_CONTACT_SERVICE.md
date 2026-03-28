# V1_TEST_RUNBOOK_GOOGLE_CALENDAR_ADAPTER_AND_CUSTOMER_CONTACT_SERVICE

## Purpose
Standardized verification runbook for:
- Google Calendar Adapter
- Customer Contact Service
- optional Google People integration

Generate a SUMMARY artifact after execution.
Do not commit runtime artifacts.

## Preconditions
- Google test credentials or mocked equivalents
- one or more test calendars
- Customer Contact Service database available
- optional Google People test access if enabled
- artifact output path outside tracked repo directories

## Test Matrix

| Area | Test | Expected Result |
|---|---|---|
| Calendar | FreeBusy request | valid request generated |
| Calendar | Slot search | normalized slots returned |
| Calendar | Booking create | external event id returned |
| Calendar | Booking update | change persisted |
| Calendar | Booking cancel | booking removed/cancelled |
| Calendar | DST handling | correct timezone-safe behavior |
| Contact | Resolve by phone | customer matched correctly |
| Contact | Resolve by email | customer matched correctly |
| Contact | Create customer | record created |
| Contact | Update customer | record updated |
| Contact | Consent rules | policy respected |
| People | Connections list | contacts imported/listed when enabled |
| People | Search contacts | warmup + search works when enabled |
| Combined | Resolve + slot search + booking | end-to-end path works |
| Security | Log review | no secrets exposed |

## Automated Execution Steps
1. Run unit tests
2. Run integration tests with mocked Google APIs
3. Run optional sandbox/live tests if configured
4. Run DST/timezone edge-case tests
5. Run redaction/logging checks
6. Generate SUMMARY artifact

## Manual Validation
### A. Availability
- verify slot search over at least two calendars
- verify business-rule filtering works

### B. Booking
- create a booking
- verify returned event id is stored
- update the booking
- cancel the booking

### C. Customer resolution
- resolve existing customer by mobile
- resolve by email
- create ad hoc customer if policy allows

### D. Google People optional path
- import/list connections
- search a known contact
- confirm platform record mapping

## Required Test Artifacts
Generate outside repo:
- `SUMMARY_GOOGLE_CALENDAR_AND_CONTACT_SERVICE.md`
- structured test log
- optional junit xml
- optional redacted request/response traces

## Exit Criteria
The run is acceptable when:
- all critical tests pass
- no high-severity security issue appears
- booking and customer resolution work
- optional Google People path is safe and isolated
