# Demo Guide v1.3.9 Patch 9

## Patch 9 focus

Patch 9 keeps the button-driven journey and restores the known-good Google Calendar event contract after the real confirm step.

The key line is:

- "The operator now sees the same reply buttons that the real RCS payload sends, and every choice moves the journey to the next guided step."

## Story 1: Confirm the appointment

- Open `Dashboard`
- Select `Confirm appointment`
- Keep `Simulation`
- Click `Run Scenario (Simulation)`
- In `Messages and Customer Journey`, click `Confirm`

What you can say:

- "This is the shortest safe path. The customer confirms the existing appointment and the journey records the canonical confirm action."

## Story 2: Reschedule with guided relative choices

- Select `Reschedule appointment`
- Run the scenario
- Click `Reschedule`
- Click `Next week`
- Click one of the proposed dates
- Click one of the proposed times

What you can say:

- "The journey no longer stops at a free-text reschedule request. It continues through relative choice, date proposal, and time proposal with visible buttons."

## Story 3: Real-mode RCS suggestion visibility

- Keep the same or another scenario
- Switch to `Real`
- Click `Run Scenario (Real)`
- Look at `Messages and Customer Journey`
- Show the visible button row and the RCS suggestion payload note
- Explain that the row stays non-clickable in `real` mode and mirrors the real device result
- If a callback arrives, refresh the payload and show the selected real button state

What you can say:

- "The operator sees the exact suggestion set that the outbound RCS message carries. Real mode keeps the same guided journey, but now the button payload is visible too."

## Story 4: Real reschedule confirm writes the correct calendar event

- Keep `Real`
- Run a reminder-driven reschedule flow
- Click `Reschedule`
- Click a scheduling window, date, and time
- Verify the next message shows `Confirm`, `Reschedule`, `Cancel`
- Click `Confirm`
- Show the resulting Google test calendar event

What you can say:

- "After the time selection, the journey now moves into an explicit confirmation step instead of repeating time buttons."
- "The Google Calendar entry uses the selected address as the source of truth for title, description, and metadata."

## Story 5: Real callback mirror and follow-up

- Prepare valid LEKAB runtime settings
- Verify `/rime/seturl` is configured from the persisted callback URLs
- Run a real scenario or reminder path
- Click a reply button on the phone
- Show the cockpit mirror updating from the callback result
- Show the next follow-up message that the system sends back out

What you can say:

- "The Dashboard is no longer the source of the real selection. It mirrors the mobile callback and stays read-only in real mode."
- "The adapter uses the same active runtime settings for outbound send and callback URL registration."

## Story 4: Cancel from the same journey shell

- Select `Cancel appointment`
- Run the scenario
- Click `Cancel`

What you can say:

- "Cancel is no longer only inferred from reply text. It is also a visible guided action in the customer journey."

## Parameters worth naming

- `available_actions`
- `suggestion_buttons`
- `real_channel_payload`
- `current_step`
- `selected_button`
- `selected_source`
- `expected.action`
- `actual.action`
