# Release Notes v1.3.2

Version: v1.3.2
Language: EN

## What changed

- kept the Reminder Scheduler UI line close to `v1.3.1`
- added a small `Time` page so timezone and DST stay visible
- showed near-term reminder behavior in the cockpit without changing the overall style
- kept the reminder policy setup page
- kept the live reminder preview
- kept the reminder job overview
- kept the lifecycle tab with planned, dispatching, sent, failed, skipped, and cancelled states
- added a clear admin guide, user guide, demo guide, and release notes in simple language
- kept the Incident-style shell and simple operator language

## Why this matters

- reminder planning is now easier to explain
- the operator can see policy, preview, jobs, and lifecycle states in one place
- the operator can also see timezone and DST notes in one place
- the platform is ready for the next backend step

## Verification

- UI route: `/ui/reminder-scheduler/v1.3.2`
- UI payload route: `/api/reminder-ui/v1.3.2/payload`
- config route: `/api/reminders/v1.3.2/config`
- preview route: `/api/reminders/v1.3.2/config/preview`
- jobs route: `/api/reminders/v1.3.2/jobs`
- health route: `/api/reminders/v1.3.2/health`
