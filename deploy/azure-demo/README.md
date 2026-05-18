# Azure Demo Package for v1.3.11d

This directory contains the simple hosted demo package for `v1.3.11d`.

## Files

- `.env.azure.demo.example`
  A ready-to-copy environment template with the current demo defaults.
- `docker-compose.azure.demo.yml`
  A compose file for a hosted Docker demo runtime.

## Start

```bash
cp deploy/azure-demo/.env.azure.demo.example deploy/azure-demo/.env.azure.demo
docker compose \
  -f deploy/azure-demo/docker-compose.azure.demo.yml \
  --env-file deploy/azure-demo/.env.azure.demo \
  up --build -d
```

## Stop

```bash
docker compose -f deploy/azure-demo/docker-compose.azure.demo.yml down
```

## Reset

```bash
docker compose -f deploy/azure-demo/docker-compose.azure.demo.yml down -v
```
