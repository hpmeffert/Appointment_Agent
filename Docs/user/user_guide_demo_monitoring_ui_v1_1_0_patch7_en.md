# User Guide Demo Monitoring UI v1.1.0 Patch 7

Version: v1.1.0-patch7
Audience: User
Language: EN

## What is new for you

The demo is no longer only a screen with text.

You can now click:

- `Keep`
- `Reschedule`
- `Cancel`
- `Call Me`
- real slot buttons with date and time labels

## What the buttons mean

- `Keep`
  The appointment stays as it is.

- `Reschedule`
  The demo opens a new slot-selection step.

- `Cancel`
  The demo moves into the cancellation path.

- `Call Me`
  The demo shows a callback or human-handover path.

## What happens after a click

When you click a button, the screen updates in several places:

- the chat transcript grows
- the current story summary changes
- the operator summary changes
- monitoring shows a new technical event

## What slot buttons do

A slot button is a clickable appointment choice like `Friday 09:00`.

When you click one:

- the selected slot is remembered
- the next matching demo step opens if available
- monitoring logs `slot.option.selected`

## How Dashboard, Monitoring, and Google Demo Control fit together

- `Dashboard`
  Shows the story and the interactive communication.

- `Monitoring`
  Shows the technical events and trace information.

- `Google Demo Control`
  Prepares, generates, deletes, or resets demo calendar entries.

## Important note

Interactive communication in Patch 7 is demo logic inside the cockpit.

Google calendar creation and deletion still happen through `Google Demo Control`.
