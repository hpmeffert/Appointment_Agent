# UI Design Guardrails

Version: v1.1.0-patch5
Audience: Admin
Language: EN

## Design baseline

The Incident Demo UI is the visual baseline for the Appointment Agent demo UI.

This means:

- the header and top navigation stay stable
- the general card style stays stable
- the day and night theme logic stays stable
- the DE and EN language switch stays stable
- the help entry point stays stable
- the Google Demo Control page stays a top-level cockpit page

## What must not change without explicit approval

- top header layout
- menu order and main navigation logic
- language switch placement
- theme switch placement
- help and docs placement
- dashboard, monitoring, and settings page structure
- Google Demo Control as a top header menu item
- overall spacing and card hierarchy

## What may evolve

- new cards inside existing pages
- new monitoring metrics
- new operator controls inside dedicated cockpit pages
- new scenario buttons
- new vertical-specific content
- clearer feedback banners

## Design principles

The UI must stay:

- simple
- easy to explain
- professional
- consistent across versions
- familiar after first use

## Demo usability rule

An operator should be able to explain the UI in under 2 minutes.

## Incident reference patterns reused here

- stable admin-style top header
- clear dashboard and monitoring separation
- fixed language and theme controls
- calm card-based layout
- operator-first navigation

## Adapted, not copied literally

This repo uses the Incident Demo as a reference, not as a literal clone.

That means:

- patterns are reused
- business content is adapted
- technical monitoring is adapted
- new features must extend the baseline instead of inventing a new design language

## UI consistency checklist

Every future UI patch must verify:

1. header unchanged in principle
2. menu order unchanged unless explicitly approved
3. theme switch works in the same pattern
4. language switch works in the same pattern
5. help entry point stays in the same pattern
6. cards keep the same spacing and visual weight
7. dashboard stays demo-friendly
8. monitoring stays technically readable
9. settings stays operationally understandable
10. Google Demo Control stays a first-class top menu area
11. no random new style language is introduced
