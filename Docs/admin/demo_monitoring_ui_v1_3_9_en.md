# Demo Monitoring UI v1.3.9 Patch 9

## What changed

Patch 9 extends the `v1.3.9` cockpit with the calendar regression fix on top of the staged interactive journey, LEKAB auth diagnostics, and Google demo calendar linkage.

The main additions are:

- visible reply buttons in `Messages and Customer Journey`
- shared button definitions for UI simulation and real RCS suggestions
- guided follow-up steps for relative window, date proposal, and time proposal
- visible operator state for selected button, current journey step, and selection source
- real-mode payload visibility for outbound RCS suggestion buttons
- persisted `customer_journey_message` mirroring for the live Dashboard panel
- `/rime/seturl` runtime callback URL configuration through the active LEKAB settings
- real callback follow-up messages that can move the journey to the next visible button set
- restored Google Calendar write formatting after the real confirm step

## Guided interaction steps

The staged journey now supports:

1. Initial choice
   `Confirm`, `Reschedule`, `Cancel`
2. Relative scheduling choice
   `This week`, `Next week`, `This month`, `Next month`, `Next free slot`
3. Date choice
   explicit proposed dates
4. Time choice
   explicit proposed times

## Shared contracts

The scenario catalog now carries:

- `available_actions`
- `suggestion_buttons`
- `next_step_map`
- `real_channel_payload`
- `journey_step_type`

These values are reused in:

- the cockpit UI
- simulation click handling
- scenario artifacts
- outbound real-mode message payloads

## Operator-visible behavior

The operator can now see:

- which button set is active
- which button was selected last
- whether the path came from `simulation_click` or `real_callback_or_test_path`
- which journey step is currently active
- which RCS suggestion payload is prepared in real mode

## Version visibility

The visible cockpit version is `v1.3.9-patch9`.

It is exposed in:

- the cockpit header
- the help payload
- the route contract

## Runtime notes

- No breaking API change was introduced for the `v1.3.9` base route.
- Patch aliases from `v1.3.9-patch1` through `v1.3.9-patch9` resolve to the same current shell.
- Scenario evidence files still write to `runtime-artifacts/demo-scenarios/v1_3_9`.
- Those runtime artifacts must remain local and must not be committed.
- Real-mode reminder sends now reuse the persisted LEKAB runtime settings instead of a cockpit-only placeholder path.
- The callback URL bridge stores and reports the active incoming and receipt callback URLs used for `/rime/seturl`.
- LEKAB `/rime/seturl` now uses the provider-specific payload fields `channels`, `incomingtype`, `incomingurl`, `receipttype`, and `receipturl`.
- Webhook.site input must use the capture URL `https://webhook.site/<tokenId>` for `/rime/seturl`, while callback fetch uses the token API path `https://webhook.site/token/<tokenId>/...`.
- The callback normalization path now accepts both GET-style callback parameters and POST payloads before mirroring the result back into the Dashboard Demonstrator.
- Google demo generation and confirmed booking writes now use the selected address as the source of truth for title, structured description, and stable correlation/booking/appointment/address metadata.
