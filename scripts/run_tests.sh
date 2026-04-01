#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="apps:apps/shared/v1_0_0:./.vendor:${PYTHONPATH:-}"

mkdir -p \
  test-results/lekab_adapter/v1_0_0 \
  test-results/appointment_orchestrator/v1_0_0 \
  test-results/google_adapter/v1_0_0 \
  test-results/microsoft_adapter/v1_0_0

pytest tests \
  --junitxml=test-results/junit-v1_0_0.xml

cat > test-results/lekab_adapter/v1_0_0/summary-v1_0_0.md <<'EOF'
# LEKAB Adapter Test Summary v1.0.0

- Automated test suite executed through the shared repository runner.
- See `test-results/junit-v1_0_0.xml` for raw structured results.
EOF

cat > test-results/appointment_orchestrator/v1_0_0/summary-v1_0_0.md <<'EOF'
# Appointment Orchestrator Test Summary v1.0.0

- Automated test suite executed through the shared repository runner.
- See `test-results/junit-v1_0_0.xml` for raw structured results.
EOF

cat > test-results/google_adapter/v1_0_0/summary-v1_0_0.md <<'EOF'
# Google Adapter Test Summary v1.0.0

- Automated test suite executed through the shared repository runner.
- See `test-results/junit-v1_0_0.xml` for raw structured results.
EOF

cat > test-results/microsoft_adapter/v1_0_0/summary-v1_0_0.md <<'EOF'
# Microsoft Adapter Test Summary v1.0.0

- Placeholder module summary for repository baseline validation.
- See `test-results/junit-v1_0_0.xml` for raw structured results.
EOF
