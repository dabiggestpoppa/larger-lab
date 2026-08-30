#!/usr/bin/env bash
#
# start-local.sh — one-command OCE Book 2 local runtime (B2-R6/R7).
# Delegates to the deterministic lifecycle CLI (PID-file ownership, no
# pkill, loopback-only ports, generated local secret — never a predictable
# default password):
#
#   bash scripts/start-local.sh
#   -> open http://127.0.0.1:8080/console
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/oce_local.py" start "$@"
