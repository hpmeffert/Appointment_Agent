# Google Test Mode Demo Guide v1.1.0 Patch 1

Version: v1.1.0 Patch 1
Audience: Demo Presenter
Language: EN

## Story 1 - Safe Simulation

Say:

- "Here we are in Simulation mode. That means the Google behavior is realistic, but nothing is written to the real calendar."

Show:

- the `Simulation` button
- the operator warning
- the generated appointment list in the monitoring panel

## Story 2 - Real Test Calendar

Say:

- "Now I switch to Test mode. This is still controlled, but now the system writes to the configured Google test calendar."

Show:

- the `Test` button
- the target calendar summary
- the live warning
- a generated appointment with a realistic title

## Story 3 - Contact-Aware Future Path

Say:

- "Generated appointments already know the demo customer. That lets us show whether later SMS or RCS would be possible."
- "Manual appointments are harder. They need title, attendee, or contact hints before the system can safely link them."

Show:

- the `Manual Entry and Contact Linking` panel
- one example with mobile available
- one example without mobile available
