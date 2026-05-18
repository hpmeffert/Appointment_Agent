# Release Manifest v1.3.11d

## Release type

Hosted demo package release for Azure-oriented sales usage.

## Main intent

Package the currently proven Appointment Agent demo runtime into a documented Docker-based hosted demo setup.

## Component version map

- Demo package label: `v1.3.11d`
- Core runtime line: `v1.4.0`
- Main demo cockpit: `v1.3.10`
- Address database cockpit: `v1.3.9`
- Reminder cockpit and APIs: `v1.3.6`
- LEKAB monitoring/settings: `v1.3.8`
- Docker baseline: `v1.4.0`

## Included deployment files

- `deploy/azure-demo/.env.azure.demo.example`
- `deploy/azure-demo/docker-compose.azure.demo.yml`
- `deploy/azure-demo/README.md`

## Included documentation files

- `Docs/admin/demo_hosting_v1_3_11d_en.md`
- `Docs/admin/demo_hosting_v1_3_11d_de.md`
- `Docs/user/user_guide_v1_3_11d_en.md`
- `Docs/user/user_guide_v1_3_11d_de.md`
- `Docs/demo/demo_guide_v1_3_11d_en.md`
- `Docs/demo/demo_guide_v1_3_11d_de.md`
- `Docs/releases/release_notes_v1_3_11d_en.md`
- `Docs/releases/release_notes_v1_3_11d_de.md`
- `Docs/release_packages/v1_3_11d/*`

## Main routes for hosted demo use

- `/ui/demo-monitoring/v1.3.10`
- `/ui/address-database/v1.3.9`
- `/ui/reminder-scheduler/v1.3.6`
- `/health`
- `/docs/demo`
- `/docs/user`
- `/docs/admin`
