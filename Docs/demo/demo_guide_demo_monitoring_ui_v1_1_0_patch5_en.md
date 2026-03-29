# Demo Guide Demo Monitoring UI v1.1.0 Patch 5

Version: v1.1.0-patch5
Audience: Demo
Language: EN

## Demo message in one sentence

This cockpit separates story, technical monitoring, configuration, and Google calendar demo control into clear top-level areas.

## Story scenario 1

- Open `Dashboard`
- Choose a standard booking scenario
- Explain that the customer story stays simple while the system still tracks trace and correlation IDs

## Story scenario 2

- Open `Google Demo Control`
- Stay in `Simulation`
- Use `Prepare Demo Calendar`
- Explain that this is safe because it does not write real Google entries

## Story scenario 3

- Stay on `Google Demo Control`
- Switch to `Test`
- Explain the warning
- Use `Generate Demo Appointments`
- Explain that only the dedicated Google test calendar is changed

## Best presenter wording

- Dashboard is for the business story.
- Monitoring is for the technical proof.
- Settings is for the operator parameters.
- Google Demo Control is for simulated or real test-calendar actions.

## Important parameters

- `mode`
  Simulation or test.

- `timeframe`
  The date window used for preparation and generation.

- `count`
  How many appointments should be created or managed.

- `vertical`
  Which business example should shape titles and descriptions.
