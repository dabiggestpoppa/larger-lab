#!/usr/bin/env bash
#
# stop-local.sh — stop the OCE Book 2 local runtime (B2-R6).
# Kills the API + worker processes and tears down the compose stack
# WITHOUT removing the durable postgres volume (B2-R7 semantics).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> stopping worker + API processes"
pkill -f "oce_control.worker_loop" 2>/dev/null || true
pkill -f "oce_control.http_api" 2>/dev/null || true

echo "==> compose down (durable postgres volume preserved)"
cd "$BASE_DIR"
docker compose -f compose/compose.yml down

echo "stopped."
