# Admin Guide Demo Monitoring UI v1.2.1

Version: v1.2.1
Language: EN

## What changed

`v1.2.1` turns the public demonstrator into a messaging-aware cockpit.

New parts:
- `Message Monitor` page
- `Communications Reports` page
- `LEKAB Adapter v1.2.1` for normalized RCS/SMS traffic

## Architecture in simple words

The UI does not read raw LEKAB responses directly.

Instead, the flow is:
1. LEKAB-style provider traffic enters the adapter
2. the adapter normalizes it into one internal message model
3. the Message Monitor reads that normalized model
4. the report page shows the same data in a more presentation-friendly way

This keeps the platform ready for future channels like WhatsApp, chat, or voice.

## LEKAB source basis

The adapter structure was shaped from these local LEKAB API documents:
- `DispatchWebService.pdf`
- `SMSRESTWebService.pdf`
- `AddressbookWebService.pdf`
- `RimeRESTWebService.pdf`

Important ideas taken from them:
- authentication/token handling
- workflow dispatch direction
- RCS rich messaging send direction
- SMS send direction
- addressbook lookup direction

## Main API routes

- `/api/lekab/v1.2.1/help`
- `/api/lekab/v1.2.1/auth/token`
- `/api/lekab/v1.2.1/addressbook/resolve`
- `/api/lekab/v1.2.1/messages/send/rcs`
- `/api/lekab/v1.2.1/messages/send/sms`
- `/api/lekab/v1.2.1/messages/inbound`
- `/api/lekab/v1.2.1/messages/status`
- `/api/lekab/v1.2.1/messages`
- `/api/lekab/v1.2.1/messages/{message_id}`
- `/api/lekab/v1.2.1/monitor`

## Normalized message model

Each message record uses one provider-neutral structure.

Important parameters:
- `message_id`
  The internal platform id. The UI uses this as the stable row/detail key.
- `provider_message_id`
  The message id from the external provider side.
- `provider_job_id`
  A workflow or batch style provider job id if one exists.
- `provider`
  The provider family, currently `lekab`.
- `channel`
  The communication channel, for example `RCS` or `SMS`.
- `direction`
  `outbound` means the platform sent the message. `inbound` means the customer sent it.
- `status`
  The current message state, for example `accepted`, `delivered`, `received`, or `failed`.
- `customer_id`
  The internal customer id if already known.
- `contact_reference`
  A contact-oriented reference used for addressbook or customer lookup.
- `phone_number`
  The phone number connected to the message.
- `journey_id`
  The appointment or communication flow id.
- `booking_reference`
  The appointment reference if the message belongs to a booking.
- `message_type`
  The type of content, for example `text`, `card`, or `reply`.
- `body`
  The full text or main text body.
- `preview_text`
  A short version used in list/table views.
- `actions`
  Optional reply buttons or quick actions for future interactive messaging.
- `provider_payload`
  Provider-specific details stored for diagnostics and operator detail views.
- `metadata`
  Extra platform context such as customer name or demo flags.
- `created_at`
  When the message was first stored.
- `updated_at`
  When the message was last updated.

## Message Monitor page

The page shows:
- summary cards
- filters for `channel`, `direction`, and `status`
- a traffic list
- a detail panel

The detail panel explains one selected message with:
- provider ids
- customer/contact reference
- phone number
- journey/booking relation
- body
- actions
- provider payload

## Communications Reports page

This page follows the customer/report style from the Incident Demo.

It is meant for:
- sales demos
- admin walkthroughs
- explaining why message traffic is useful in appointment automation

## Inline comment rule

For `v1.2.1`, meaningful inline comments were added around:
- message normalization
- provider-to-platform mapping
- monitor payload shaping
- shared persistence paths
- UI rendering logic where the behavior is not obvious
