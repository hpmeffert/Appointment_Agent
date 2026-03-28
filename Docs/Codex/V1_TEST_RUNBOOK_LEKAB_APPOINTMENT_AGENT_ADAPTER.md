# V1_TEST_RUNBOOK_LEKAB_APPOINTMENT_AGENT_ADAPTER

## Purpose
Standardized automated and manual verification runbook for the LEKAB Adapter Service.
This runbook must produce a SUMMARY artifact after execution.
Do not commit generated artifacts.

## Preconditions
- valid test environment
- LEKAB test credentials or mocked equivalents
- callback receiver reachable in test environment
- representative saved job(s) available, preferably GMM-based appointment templates
- test addressbook available
- artifact output path configured outside repo-tracked directories

## Test Matrix
| Area | Test | Expected Result |
|---|---|---|
| Auth | Token fetch | access token returned and cached |
| Auth | Bad credentials | deterministic auth failure |
| Auth | Revoke token | revoke call completes safely |
| Dispatch | List saved jobs | jobs returned with id/name/type |
| Dispatch | Start saved job | runtime id returned |
| Dispatch | Invalid params | validation or upstream error captured |
| Callback | JOB_START | mapped to internal started event |
| Callback | JOB_ASSIGN | mapped to internal assigned event |
| Callback | JOB_FINISH | mapped to internal finished event |
| Callback | Duplicate POST | duplicate ignored idempotently |
| Addressbook | List address books | available books returned |
| Addressbook | List tags | tag metadata returned |
| Addressbook | Find contact by address | contact resolved |
| Addressbook | Add contact | contact created |
| Addressbook | Update contact | contact updated |
| Addressbook | Delete contact | contact removed |
| Resilience | Timeout/retry | deterministic behavior |
| Security | Log review | no secrets present |

## Automated Execution Steps
1. Run unit tests
2. Run integration tests with mocked upstreams
3. Run selected sandbox tests if available
4. Run callback replay/idempotency tests
5. Run logging/redaction verification
6. Generate SUMMARY artifact

Suggested SUMMARY sections:
- environment
- commit/revision
- counts passed/failed/skipped
- notable logs
- known issues
- next actions

## Manual Validation
### A. Saved Job Discovery
- retrieve appointment-related saved jobs
- verify IDs and job types

### B. Job Start
- start a known saved appointment job
- verify runtime id and message/jobname override behavior

### C. Callback Path
- trigger JOB_START/JOB_ASSIGN/JOB_FINISH samples
- verify internal event mapping and duplicate suppression

### D. Addressbook Sync
- add a test contact with SMS/VOICE/EMAIL
- update tags
- resolve by phone/address
- delete the contact
- verify traceability

### E. Failure Cases
- invalid token
- invalid jobid
- malformed callback payload
- transient upstream failure
- log redaction

## Required Test Artifacts
Generate and store outside the repo:
- `SUMMARY_LEKAB_ADAPTER.md`
- structured test log
- optional junit xml
- optional redacted callback capture set

## Exit Criteria
The run is acceptable when:
- all critical tests pass
- no high-severity secret leakage occurs
- callback mapping is correct
- auth/dispatch/addressbook flows work
- failures are deterministic and documented
