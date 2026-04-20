# User Guide Demo Monitoring UI v1.2.1

Version: v1.2.1
Language: EN

## What you can do now

The cockpit now shows both appointment logic and message traffic.

The new `Message Monitor` page helps you understand:
- what the system sent
- what the customer sent back
- if the message used `RCS` or `SMS`
- which appointment journey the message belongs to

## Simple meaning of important words

- `outbound`
  The platform sent this message.
- `inbound`
  The customer sent this message back.
- `channel`
  The technical path, for example `RCS` or `SMS`.
- `status`
  The current state of the message.
- `journey_id`
  The workflow id that connects the message to one customer journey.
- `booking_reference`
  The appointment reference connected to the message.

## Filters

You can filter by:
- `channel`
- `direction`
- `status`

This helps you focus on only one part of the conversation.

## Detail view

When you click one message row, the detail card shows:
- provider reference
- customer/contact reference
- phone number
- journey relation
- appointment relation
- full body text
- quick actions if available
