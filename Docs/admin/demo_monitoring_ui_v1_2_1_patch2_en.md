# Admin Guide Demo Monitoring UI v1.2.1-patch2

Version: v1.2.1-patch2
Audience: Admin
Language: EN

## Patch goal

`v1.2.1-patch2` fixes two onboarding problems:
- buttons in day mode were too weak visually
- the documentation around the cockpit and LEKAB settings was too thin

This patch keeps the runtime behavior stable but raises operator clarity and documentation quality.

## Platform overview

The Appointment Agent platform is modular:

- `LEKAB Adapter`
  Messaging adapter for outbound and inbound RCS/SMS style traffic.
- `Appointment Orchestrator`
  Decision layer for appointment journeys.
- `Google Adapter`
  Scheduling adapter for slot search, hold, booking, and live conflict handling.
- `Service Bus`
  Internal contract layer that keeps adapters replaceable.

This matters because the UI should explain one platform, not one isolated feature.

![Annotated cockpit overview](/docs/assets/screenshots/v1_2_1_patch2/cockpit-overview.svg)

## New documentation baseline

This patch requires:
- demo guide for presenters
- user guide for operators
- admin guide with parameter explanations
- release notes as a separate document

Important rule:
- release notes must not be mixed into the demo guide

## Day-mode button fix

Action buttons in day mode now use:
- grey background
- white text
- stronger border
- more visible shadow

Affected areas:
- demo mode buttons
- operator panel buttons
- story buttons
- slot buttons
- communication action buttons
- settings action buttons

## RCS settings page behavior

The page is reachable through:
- `Settings`
- `Settings -> RCS`

The page reads and saves values in a local SQLite-backed configuration store.

Important behavior:
- normal fields are returned directly
- secret fields are stored but returned masked as `********`
- blank secret input means `keep the existing secret`
- readiness is calculated from required values and adapter state

![Annotated RCS settings page](/docs/assets/screenshots/v1_2_1_patch2/rcs-settings.svg)

## Parameter reference

### Environment / Workspace

- `environment_name`
  Human-readable label for operators.
  Example: `Demo EU`
  Impact: helps operators know which environment they are editing.
- `workspace_id`
  Technical LEKAB tenant or workspace id.
  Example: `appointment-agent-demo`
  Impact: changes which provider workspace receives messaging traffic.
- `messaging_environment`
  Runtime channel environment.
  Example: `test`
  Impact: separates demo/testing from future production use.
- `dispatch_base_url`
  Base URL for dispatch actions.
  Example: `https://dispatch.example.test`
  Impact: changes where workflow dispatch requests go.
- `rime_base_url`
  Base URL for RCS-rich messaging requests.
  Example: `https://rime.example.test`
  Impact: affects RCS delivery preparation.
- `sms_base_url`
  Base URL for SMS requests.
  Example: `https://sms.example.test`
  Impact: affects SMS delivery path.
- `addressbook_base_url`
  Base URL for contact lookup.
  Example: `https://addressbook.example.test`
  Impact: affects future contact resolution.

### Authentication

- `auth_base_url`
  Base URL for auth requests.
  Example: `https://auth.example.test`
  Impact: wrong value blocks token retrieval.
- `auth_client_id`
  Technical client id.
  Example: `appointment-agent-demo-client`
  Impact: identifies the application during auth.
- `auth_client_secret`
  Secret paired with the client id.
  Example: hidden
  Impact: required for authenticated provider access.
- `auth_username`
  Technical service user.
  Example: `demo-operator`
  Impact: identifies the operator or service account.
- `auth_password`
  Password for the service user.
  Example: hidden
  Impact: required for authenticated provider access.
- `token_endpoint`
  Relative token path.
  Example: `/oauth/token`
  Impact: defines where token requests are sent.
- `revoke_endpoint`
  Optional revoke path.
  Example: `/oauth/revoke`
  Impact: future token cleanup and session control.

### RCS / Messaging

- `rcs_enabled`
  Turns the RCS path on or off.
  Impact: readiness becomes false when RCS is disabled.
- `rcs_sender_profile`
  Name shown to the customer in RCS contexts.
  Example: `Appointment Agent`
  Impact: affects sender recognizability.
- `default_template_context`
  Template family or business context.
  Example: `appointment_journey`
  Impact: affects which message content gets selected.
- `callback_url`
  Inbound callback target.
  Example: `https://demo.example.test/api/lekab/v1.2.1/messages/inbound`
  Impact: affects inbound reply and delivery-status handling.
- `channel_priority`
  Channel order.
  Example: `RCS_FIRST`
  Impact: changes whether RCS or SMS is attempted first.
- `sms_fallback_enabled`
  Allows SMS when RCS is not possible.
  Impact: increases reach, but may increase SMS cost.

### SMS

- `sms_enabled`
  Enables or disables SMS behavior.
  Impact: blocks fallback when false.
- `sms_sender_name`
  Branded SMS sender.
  Example: `APPT`
  Impact: affects what customers see as sender.
- `sms_length_mode`
  Long-text behavior.
  Example: `auto_split`
  Impact: changes whether texts split or truncate.
- `default_language`
  Default message language.
  Example: `en`
  Impact: affects templates when no other language is specified.

### Addressbook / Contact Resolution

- `addressbook_enabled`
  Enables contact resolution support.
  Impact: controls whether addressbook lookups are part of the flow.
- `contact_lookup_mode`
  Defines lookup order.
  Example: `phone_first`
  Impact: changes how customer contact resolution is attempted.
- `phone_normalization_mode`
  Phone formatting style.
  Example: `E164`
  Impact: improves provider-neutral sending and lookup consistency.

## Readiness logic

The page shows:
- `ready / not ready`
- missing required fields
- warnings such as `SMS fallback is enabled`
- active channel mode

`Test Connection` currently checks adapter readiness, not a real remote provider handshake.
