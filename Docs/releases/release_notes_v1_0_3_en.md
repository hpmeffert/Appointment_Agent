# Release Notes v1.0.3 (EN)

- Hardened the Docker runtime so the Appointment Agent can be built and started with `docker compose up --build`.
- Added a Linux-safe docs path resolution so documentation routes work inside Docker too.
- Added `/health` for lightweight runtime checks.
- Added Docker helper scripts for startup and smoke validation.
- Added a new appointment reminder flow with keep, reschedule, cancel, and call-me actions.
- Added reminder demo scenarios and reminder-aware audit / CRM preparation paths.
- Switched the shared app release header and help output to `v1.0.3`.
- Expanded README, Docker notes, admin guide, user guide, and demo guide for the Docker runtime release.
