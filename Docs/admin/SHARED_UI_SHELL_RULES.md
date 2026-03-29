# Shared UI Shell Rules

Version: v1.1.0-patch5
Audience: Admin
Language: EN

## Goal

New UI versions should reuse one stable shell instead of redesigning the whole cockpit.

## Stable shell parts

- header
- navigation
- language switch
- theme switch
- help access
- dashboard and monitoring frame
- Google Demo Control page

## Practical rule

If a future patch needs new content, prefer:

- adding a card
- adding a control inside an existing section
- adding a new metric block

Do not start by redesigning:

- header
- top navigation
- whole page layout
- theme logic
- language control placement
- Google Demo Control placement

## Stable page order

- Dashboard
- Monitoring
- Settings
- Google Demo Control
- Help
