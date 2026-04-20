# Release Notes v1.3.9 Patch 9

## Highlights

- Raised the visible cockpit release to `v1.3.9-patch9`
- Added staged interactive reply buttons to `Messages and Customer Journey`
- Added shared button sets for initial, relative, date, and time choices
- Added shared `available_actions`, `suggestion_buttons`, `next_step_map`, and `real_channel_payload` fields to the scenario model
- Added guided simulation controls for `Reschedule -> relative window -> date -> time`
- Added real-mode RCS suggestion payload visibility in the same journey panel
- Added `patch4`, `patch5`, `patch6`, `patch7`, `patch8`, and `patch9` route aliases to the current shell contract
- Hardened LEKAB provider test connection behavior for OAuth/password mode and 401 diagnostics
- Added persisted `/rime/seturl` callback URL registration for incoming and receipt callbacks
- Corrected Webhook.site handling so capture URLs and token-API fetch URLs are no longer mixed in the runtime settings
- Corrected the LEKAB `/rime/seturl` payload schema to use `channels`, `incomingtype`, `incomingurl`, `receipttype`, and `receipturl`
- Connected real-mode reminder sends to the active LEKAB runtime settings and callback mirror path
- Hardened Google Demo Control validation, refresh behavior, and address-link persistence
- Improved generated Google event titles, full address details, and linkage metadata when a selected address is present
- Restored confirmed Google Calendar writes to the deterministic format `<Appointment Type> – <Customer Name>` with structured address/context descriptions and stable `correlation_id`, `booking_reference`, `appointment_id`, and `address_id` metadata

## Runtime notes

- No breaking change to the `v1.3.9` base route
- The visible version in header and help is now `v1.3.9-patch9`
- Real-mode scenario runs still use the configured output channel path
- Real-mode callback results can now update the visible button state and drive follow-up outbound messages
- LEKAB callback ingestion now normalizes both GET-style callback parameters and POST payloads into the same internal event path
- Scenario artifacts still write only to `runtime-artifacts/demo-scenarios/v1_3_9`

## Defaults

- Silence Threshold default remains `1300ms`
- Interactive journey starts with `Confirm`, `Reschedule`, and `Cancel`
- Reschedule follow-up starts with relative scheduling buttons before explicit dates and times
