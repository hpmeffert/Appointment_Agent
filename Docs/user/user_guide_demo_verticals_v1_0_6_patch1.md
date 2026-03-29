# Demo Verticals v1.0.6 Patch 1 User Guide

Version: v1.0.6-patch1
Audience: User
Language: EN

## What this patch does

This patch makes the vertical demo content feel more real.

That means:

- the appointment titles sound like real appointments
- the reminder texts match the chosen industry
- the example customers fit the scenario
- the operator can explain the demo more clearly

## Main route

- `http://localhost:8080/ui/demo-monitoring/v1.0.6-patch1`

## The three vertical buttons

### `Dentist`

Use this when you want a very easy and personal example.

The system will show things like:

- `Dental Check-up - Dr. Zahn`
- `Tooth Cleaning - Dr. Zahn`
- `Follow-up Appointment - Dr. Zahn`

Example reminder:

- `Reminder: You have a dental check-up tomorrow at 10:00 with Dr. Zahn.`

Example customers:

- `Anna Becker`
- `Julia Hoffmann`
- `Markus Weber`

### `Stadtwerke Wallbox`

Use this when you want to show a technician visit at a customer home.

The system will show things like:

- `Wallbox Inspection - Home Visit`
- `EV Charger Safety Check`
- `Charging Station Maintenance Visit`

Example reminder:

- `Reminder: Your wallbox inspection is scheduled for tomorrow at 14:00.`

Example customers:

- `Familie Schneider`
- `Julia Hoffmann`
- `Markus Weber`

### `District Heating`

Use this when you want a more technical utility example.

The system will show things like:

- `District Heating Transfer Station Inspection`
- `Nahwaerme Uebergabestation Check`
- `Heat Transfer Unit Service Visit`

Example reminder:

- `Reminder: Your district heating transfer station inspection is scheduled for tomorrow at 09:00.`

Example customers:

- `Familie Schneider`
- `Hausverwaltung Nordblick`
- `Anna Becker`

## Important parameters

### `vertical`

This tells the system which business scenario to use.

Possible values:

- `dentist`
- `wallbox`
- `district_heating`

If you change `vertical`, the system also changes:

- titles
- descriptions
- reminder texts
- customer names
- monitoring labels

### `timeframe`

This tells the system for which time window it should create demo appointments.

Possible values:

- `day`
- `week`
- `month`

Simple meaning:

- `day` means only a small short-term demo set
- `week` means a normal demo set for the next days
- `month` means a larger future-looking demo set

### `count`

This tells the system how many demo appointments it should generate.

Examples:

- `3` creates a small set
- `6` creates a more realistic medium set
- `10` gives you more data for a bigger demo

### `action`

This tells the system what to do with the demo data.

Possible values:

- `generate`
- `delete`
- `reset`

Simple meaning:

- `generate` creates new demo appointments
- `delete` removes generated demo appointments
- `reset` first removes old demo appointments and then creates fresh ones

### `mode`

This tells the system whether it should stay safe in simulation or use the Google test calendar.

Possible values:

- `simulation`
- `test`

Simple meaning:

- `simulation` uses local fake data only
- `test` writes only to the configured Google test calendar

## Good first demo order

1. Start with `Dentist` because it is easy to understand.
2. Switch to `Stadtwerke Wallbox` to show a field-service scenario.
3. End with `District Heating` to show a more technical infrastructure use case.

## What changed compared to `v1.0.6`

- better appointment wording
- better reminder wording
- more realistic customer placeholders
- stronger utility and healthcare language
- more helpful operator explanation in the cockpit
