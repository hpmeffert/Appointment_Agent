# Google Demo Actions v1.1.0 Patch 2 User Guide

Version: v1.1.0-patch2
Audience: User
Language: EN

## What changed

The Google demo buttons now do different real actions.

Before this patch, `Prepare` behaved too much like `Generate`.

Now:

- `Prepare` gives you a preview
- `Generate` creates demo appointments
- `Delete` removes demo appointments
- `Reset` clears and recreates demo appointments

## Main UI route

- `http://localhost:8080/ui/demo-monitoring/v1.1.0-patch2`

## Simple button meaning

### `Prepare Demo Calendar`

Use this when you want to show what would be created.

It is safe because it does not write appointments yet.

### `Generate Demo Appointments`

Use this when you want real demo output.

In `simulation` mode it stays local.
In `test` mode it writes to the configured Google test calendar.

### `Delete Demo Appointments`

Use this to clean up demo-generated entries.

### `Reset Demo Calendar`

Use this when you want to start fresh.

## Visible feedback

After each action the UI now shows:

- loading state
- success message
- error message if something fails
- generated or deleted counts

## Important parameters

### `mode`

Tells the system whether to stay safe locally or use the Google test calendar.

### `timeframe`

Tells the system which time window to use.

### `count`

Tells the system how many appointments to prepare or create.

### `vertical`

Tells the system which business story to use for the demo data.
