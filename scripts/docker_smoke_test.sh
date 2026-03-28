#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"

echo "Checking root endpoint..."
curl -fsS "${BASE_URL}/" >/dev/null

echo "Checking health endpoint..."
curl -fsS "${BASE_URL}/health" | grep -q '"status":"ok"'

echo "Checking demo UI..."
curl -fsS "${BASE_URL}/ui/demo-monitoring/v1.0.2" | grep -q "Appointment Agent Demo + Monitoring v1.0.2"

echo "Checking scenario API..."
curl -fsS "${BASE_URL}/api/demo-monitoring/v1.0.2/scenarios" | grep -q 'standard-booking'

echo "Checking help API..."
curl -fsS "${BASE_URL}/api/demo-monitoring/v1.0.2/help" | grep -q 'combined'

echo "Checking docs route..."
curl -fsS "${BASE_URL}/docs/demo?lang=en" | grep -q 'Demo Guide'

echo "Docker smoke test passed for ${BASE_URL}"
