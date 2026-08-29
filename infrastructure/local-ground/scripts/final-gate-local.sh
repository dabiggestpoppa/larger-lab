#!/usr/bin/env bash
#
# final-gate-local.sh — thin wrapper over the independent gate.
#   final-gate-local.sh <evidence-dir> <commit> <tree>
# The real logic lives in independent-gate.py (machine-parseable, 32 checks).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/independent-gate.py" "${1:?evidence dir}" "${2:?commit}" "${3:?tree}"
exit $?