# Release Notes Reminder Scheduler v1.3.6

Version: v1.3.6
Language: EN

## Summary

`v1.3.6` is a combined demonstrator bridge release.

It turns the reminder cockpit into a combined demonstrator for:
- appointment source
- Google linkage
- appointment details
- reminder policy
- reminder preview
- reminder jobs
- health and diagnostics

## What changed

- The cockpit now tells the full story from the appointment source to the reminder jobs.
- Google linkage demo endpoints and reminder linkage demo endpoints are now available in the same release line.
- The same visual style stays in place.
- The header and help page show the version.
- The text uses simple words for new users.
- The docs explain the parameters in plain language.
- The demo guide includes three short story scenarios.

## Important parameters

- `silence_threshold_ms`
  Default is `1300 ms`.
- `reminder_offsets_minutes`
  The planned reminder times before the appointment.
- `google_calendar_id`
  The calendar used for the linked appointment.
- `appointment_type`
  The type of appointment.
- `job_status`
  The state of a reminder job.

## What is in the release

- UI route: `/ui/reminder-scheduler/v1.3.6`
- Payload route: `/api/reminder-ui/v1.3.6/payload`
- Help route: `/api/reminder-ui/v1.3.6/help`
- Config route: `/api/reminder-ui/v1.3.6/config`
- Preview route: `/api/reminder-ui/v1.3.6/config/preview`
- Jobs route: `/api/reminder-ui/v1.3.6/jobs`
- Health route: `/api/reminder-ui/v1.3.6/health`

## Notes for the team

- Keep the look and feel stable.
- Keep the explanations short and clear.
- Keep the version visible in the product and in the help text.
