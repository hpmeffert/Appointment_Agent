# Seed and Reset Strategy v1.3.11d

## Goal

The hosted demo must be easy to recover when a sales demo changes too much state.

## Strategy

There are two safe operating modes:

### 1. Persistent demo mode

Use the running named Docker volume.

This is useful when:

- you want to keep prepared address data
- you want the system to feel stable across restarts
- you do not need a full reset before every demo

### 2. Reset demo mode

Remove the Docker volume and start again.

This is useful when:

- a demo changed too many records
- the state should look fresh again
- you want a clean training or presentation baseline

## Reset command

```bash
docker compose -f deploy/azure-demo/docker-compose.azure.demo.yml down -v
```

Then start again:

```bash
docker compose \
  -f deploy/azure-demo/docker-compose.azure.demo.yml \
  --env-file deploy/azure-demo/.env.azure.demo \
  up --build -d
```

## Seed behavior in this release

`v1.3.11d` uses the currently available demo defaults and runtime-generated demo records. It does not yet introduce a separate production-style seeding service.

That means:

- the environment starts with the configured runtime defaults
- additional demo data is created through the existing demo flows
- reset is volume-based and very easy to understand

## Future extension

Later we can add:

- explicit seed scripts
- multiple seed profiles
- reset-to-baseline snapshots
