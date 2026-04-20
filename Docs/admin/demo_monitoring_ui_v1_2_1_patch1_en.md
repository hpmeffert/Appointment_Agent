# Admin Guide Demo Monitoring UI v1.2.1-patch1

Version: v1.2.1-patch1
Language: EN

## New focus

This patch adds a dedicated `RCS Settings` page.

The page is reachable through the top header path:
- `Settings`
- `Settings -> RCS`

## What the page is for

It gives operators one structured place for LEKAB messaging setup:
- environment/workspace values
- authentication values
- RCS settings
- SMS settings
- addressbook/contact resolution settings
- diagnostics/readiness

## Save and load behavior

The page saves values into a local SQLite-backed configuration store.

Important rule:
- normal fields are returned directly
- secret fields are stored, but returned masked as `********`
- blank secret inputs mean “keep the existing secret”

## Major parameter groups

### Environment / Workspace
- `environment_name`
- `workspace_id`
- `messaging_environment`
- `dispatch_base_url`
- `rime_base_url`
- `sms_base_url`
- `addressbook_base_url`

### Authentication
- `auth_base_url`
- `auth_client_id`
- `auth_client_secret`
- `auth_username`
- `auth_password`
- `token_endpoint`
- `revoke_endpoint`

### RCS / Messaging
- `rcs_enabled`
- `rcs_sender_profile`
- `default_template_context`
- `callback_url`
- `channel_priority`
- `sms_fallback_enabled`

### SMS
- `sms_enabled`
- `sms_sender_name`
- `sms_length_mode`
- `default_language`

### Addressbook / Contact Resolution
- `addressbook_enabled`
- `contact_lookup_mode`
- `phone_normalization_mode`

## Readiness logic

The page shows:
- `ready / not ready`
- missing required fields
- warnings such as `SMS fallback is enabled`

`Test Connection` currently uses a local adapter readiness check, not a real remote provider call.
