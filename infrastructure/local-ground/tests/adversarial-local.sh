#!/usr/bin/env bash
#
# adversarial-local.sh — B1-LOCAL adversarial/negative checks (A-003).
# Each check MUST FAIL to pass. Fail-closed behavior is the point.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$SCRIPT_DIR/../scripts"
FAIL=0

check() { # name expected_rc cmd...
  local name="$1" expected="$2"; shift 2
  "$@" >/dev/null 2>&1
  local rc=$?
  if [ "$rc" -eq "$expected" ]; then
    echo "PASS: $name (rc=$rc as expected)"
  else
    echo "FAIL: $name (rc=$rc, expected $expected)"
    FAIL=1
  fi
}

# 1. cloud apply with no authorization must DENY (nonzero).
check "cloud apply denied without authorization" 5 \
  env OCE_RUNTIME_TARGET=cloud bash "$SCRIPTS/oce-ctl" deploy apply --target cloud

# 2. bootstrap with missing secrets must fail closed (3).
env -u POSTGRES_PASSWORD -u ARTIFACT_SECRET_KEY bash "$SCRIPTS/bootstrap-local.sh" >/dev/null 2>&1
rc=$?
if [ "$rc" -eq 3 ]; then echo "PASS: bootstrap fail-closed without secrets (rc=3)"; else echo "FAIL: bootstrap without secrets rc=$rc (expected 3)"; FAIL=1; fi

# 3. unauthorized worker rejected (nonzero).
TMP=$(mktemp -d)
cat > "$TMP/bad.json" <<'JSON'
{ "task_id": "adv-1", "parent_agent": "po", "purpose": "x",
  "allowed_paths": ["/root"], "allowed_tools": ["aws"], "authority": "bounded",
  "budget": 0, "time_limit_s": 1, "expected_outputs": [], "forbidden_actions": [] }
JSON
check "unauthorized worker rejected" 1 \
  env OCE_RUNTIME_TARGET=local bash "$SCRIPTS/worker-admit.sh" admit "$TMP/bad.json"

# 4. corrupt backup rejected (3).
bash "$SCRIPTS/backup.sh" --out "$TMP/bk" >/dev/null 2>&1
echo '{"tampered":1}' > "$TMP/bk/.backup-content/state.json"
check "corrupt backup rejected" 3 \
  env OCE_RUNTIME_TARGET=local bash "$SCRIPTS/restore.sh" --from "$TMP/bk"

# 5. unknown runtime target rejected (2).
check "unknown runtime target rejected" 2 \
  env OCE_RUNTIME_TARGET=not-a-target bash "$SCRIPTS/oce-ctl" local status

rm -rf "$TMP"
echo ""
if [ "$FAIL" -eq 0 ]; then echo "ADVERSARIAL: ALL PASS"; else echo "ADVERSARIAL: FAILURES PRESENT"; fi
exit $FAIL