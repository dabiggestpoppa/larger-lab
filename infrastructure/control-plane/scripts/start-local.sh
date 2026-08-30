#!/usr/bin/env bash
#
# start-local.sh — one-command OCE Book 2 local runtime (B2-R6).
#
# Brings up the complete runtime on the operator's computer:
#   PostgreSQL (authoritative) + Redis (transport) + FastAPI service +
#   operator console (served by the API at /console) + scheduler loop
#   (in-app) + worker loop (separate process).
#
#   bash scripts/start-local.sh
#   -> open http://127.0.0.1:8080/console  (grant ids printed at startup)
#   -> Ctrl+C stops the API + worker (stack stays up; use stop-local.sh)
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-test-secret-b2-pg-001}"
DSN="postgresql://oce_control_admin:${POSTGRES_PASSWORD}@127.0.0.1:5433/oce_control"
export POSTGRES_DSN="$DSN"
export PYTHONPATH="$BASE_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

cd "$BASE_DIR"

echo "==> starting PostgreSQL + Redis (durable postgres volume preserved)"
docker compose -f compose/compose.yml up -d
if ! python3 - <<'PY' 2>&1 | tail -1
import sys
sys.path.insert(0, "tests")
import oce_b2_compose as oc
oc.stack_up()
print("postgres + redis healthy")
PY
then
  echo "FATAL: stack did not become healthy" >&2
  exit 1
fi

echo "==> applying migrations"
python3 scripts/migrate.py up --db "$DSN" || { echo "FATAL: migrations failed" >&2; exit 1; }

WORKER_PID=""
cleanup() {
  if [ -n "$WORKER_PID" ]; then
    kill "$WORKER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "==> starting worker loop"
python3 -m oce_control.worker_loop &
WORKER_PID=$!

echo "==> starting API + console at http://127.0.0.1:8080/console"
echo "    (grant ids are printed above; console uses the 'read' grant)"
python3 -m oce_control.http_api
