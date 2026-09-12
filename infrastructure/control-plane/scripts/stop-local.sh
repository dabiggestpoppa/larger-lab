#!/usr/bin/env bash
#
# stop-local.sh — stop the OCE Book 2 local runtime (B2-R6/R7).
# Runtime-owned PID tracking (never pkill -f). The durable postgres
# volume is preserved; only `oce_local destroy --yes` removes it.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/oce_local.py" stop "$@"
