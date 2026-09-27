#!/usr/bin/env bash
#
# run-b2-validation.sh — OCE Book 2 control-plane validation runner (B2-R8).
# Sole authoritative orchestration for the B2 gate; invoked EXACTLY once by
# the dedicated CI workflow and usable locally. Thin wrapper: the real
# fail-closed 23-step orchestration lives in run_b2_validation.py so the
# evidence logic is unit-testable.
#
# Environment:
#   OCE_RUN_ID        — required, single authoritative run id (12+ hex)
#   OCE_EVIDENCE_DIR  — evidence dir OUTSIDE the repository (created if absent)
#   OCE_CI_MODE       — "true" in CI (authoritative; zero skips enforced)
#   GITHUB_REF_NAME / GITHUB_REPOSITORY / OCE_EXPECTED_* — identity
#
# Exit code: 0 only when every step passes; nonzero (1=FAIL, 2=BLOCKED)
# otherwise. Every attempt writes truthful evidence.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/run_b2_validation.py" "$@"
