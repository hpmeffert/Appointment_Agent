# Release Notes v1.3.11d

## Release type

Hosted demo package release for Azure-oriented sales usage.

## Highlights

- Added a dedicated hosted demo release package for `v1.3.11d`
- Added `deploy/azure-demo/.env.azure.demo.example`
- Added `deploy/azure-demo/docker-compose.azure.demo.yml`
- Added a dedicated Azure demo package README
- Added a structured release package documentation directory under `Docs/release_packages/v1_3_11d`
- Updated `.env.example` to point the demo base path to `/ui/demo-monitoring/v1.3.10`
- Updated `docker-compose.yml` default demo base path to `/ui/demo-monitoring/v1.3.10`
- Refreshed the root `README.md` to summarize the currently available platform functionality and hosted demo setup

## Main packaged runtime map

- package label: `v1.3.11d`
- runtime line: `v1.4.0`
- combined cockpit: `v1.3.10`
- address database: `v1.3.9`
- reminder line: `v1.3.6`
- LEKAB settings and monitor: `v1.3.8`

## Admin focus

This release documents:

- Docker topology
- database strategy
- seed and reset strategy
- Azure environment parameters
- demo operations and startup concept

## User and demo focus

This release explains:

- how to start the hosted demo
- which route is the main cockpit entry
- which defaults are safest for sales demos
- how to explain the hosted demo story in three simple scenarios
