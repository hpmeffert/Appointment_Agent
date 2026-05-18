# Demo Operations and Startup v1.3.11d

## What this document is for

This guide explains how sales or an operator should start, check, use, and reset the hosted demo runtime.

## Startup concept

The startup concept is intentionally simple:

1. copy the Azure demo env file
2. start Docker Compose
3. wait for health to become green
4. open the combined demo cockpit

## Startup commands

```bash
cp deploy/azure-demo/.env.azure.demo.example deploy/azure-demo/.env.azure.demo
docker compose \
  -f deploy/azure-demo/docker-compose.azure.demo.yml \
  --env-file deploy/azure-demo/.env.azure.demo \
  up --build -d
```

## Health checks after startup

Check:

- `/health`
- `/ui/demo-monitoring/v1.3.10`
- `/docs/demo`

## Main demo operating flow

### Story 1

Open the combined demo cockpit and show:

- Dashboard
- Message Monitor
- Reminder
- Addresses

### Story 2

Open Google Demo Control and show:

- simulation mode
- appointment generation
- address-aware demo behavior

### Story 3

Open the address database and show:

- address linkage
- cross-module context
- reminder and message relationship

## Safe demo defaults

For a hosted sales system, these defaults are recommended:

- Google in mock mode
- LEKAB in mock mode
- one persistent Docker volume
- explicit reset before an important demo if needed

## Reset concept

If the demo should be fresh again:

```bash
docker compose -f deploy/azure-demo/docker-compose.azure.demo.yml down -v
docker compose \
  -f deploy/azure-demo/docker-compose.azure.demo.yml \
  --env-file deploy/azure-demo/.env.azure.demo \
  up --build -d
```

## What operators should not do

- do not put real production secrets into shared docs
- do not turn on real integrations unless you intend to test them
- do not delete random container files by hand
