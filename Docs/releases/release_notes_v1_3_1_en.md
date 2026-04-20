# Release Notes v1.3.1

Version: v1.3.1
Language: EN

## What changed

- kept the Reminder Scheduler UI line but made the lifecycle states easier to see
- added a reminder policy setup page
- added a live reminder preview
- added a reminder job overview
- added a lifecycle tab with planned, dispatching, sent, failed, skipped, and cancelled states
- added a clear admin guide, user guide, demo guide, and release notes
- kept the Incident-style shell and simple operator language

## Why this matters

- reminder planning is now easier to explain
- the operator can see policy, preview, jobs, and lifecycle states in one place
- the platform is ready for the next backend step

## Verification

- UI route: `/ui/reminder-scheduler/v1.3.1`
- UI payload route: `/api/reminder-ui/v1.3.1/payload`
- config route: `/api/reminders/v1.3.1/config`
- preview route: `/api/reminders/v1.3.1/config/preview`
- jobs route: `/api/reminders/v1.3.1/jobs`
- health route: `/api/reminders/v1.3.1/health`
