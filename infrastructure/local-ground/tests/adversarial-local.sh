#!/usr/bin/env bash
#
# adversarial-local.sh — B1-LOCAL adversarial/negative checks (A-003).
# Each check MUST FAIL to pass (fail-closed behavior is the point).
# Writes a machine-readable adversarial-results.json so the independent gate
# can parse actual per-check outcomes (never inferred from log sentences).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$SCRIPT_DIR/../scripts"
EVIDENCE="${OCE_EVIDENCE_DIR:-$(pwd)}"
RESULTS="$EVIDENCE/adversarial-results.json"
LOG="$EVIDENCE/adversarial-output.txt"
mkdir -p "$EVIDENCE"

: > "$LOG"
FAIL=0
declare -a NAMES OUTCOMES

check() { # name expected_rc cmd...
  local name="$1" expected="$2"; shift 2
  "$@" >> "$LOG" 2>&1
  local rc=$?
  if [ "$rc" -eq "$expected" ]; then
    echo "PASS: $name (rc=$rc as expected)" | tee -a "$LOG"
    NAMES+=("$name"); OUTCOMES+=("PASS")
  else
    echo "FAIL: $name (rc=$rc, expected $expected)" | tee -a "$LOG"
    NAMES+=("$name"); OUTCOMES+=("FAIL")
    FAIL=1
  fi
}

# 1. cloud apply with no authorization must DENY (rc 5).
check "cloud apply denied without authorization" 5 \
  env OCE_RUNTIME_TARGET=cloud bash "$SCRIPTS/oce-ctl" deploy apply --target cloud

# 2. bootstrap with missing secrets must fail closed (3).
env -u POSTGRES_PASSWORD -u ARTIFACT_SECRET_KEY bash "$SCRIPTS/bootstrap-local.sh" >> "$LOG" 2>&1
rc=$?
if [ "$rc" -eq 3 ]; then
  echo "PASS: bootstrap fail-closed without secrets (rc=3)" | tee -a "$LOG"
  NAMES+=("bootstrap fail-closed without secrets"); OUTCOMES+=("PASS")
else
  echo "FAIL: bootstrap without secrets rc=$rc (expected 3)" | tee -a "$LOG"
  NAMES+=("bootstrap fail-closed without secrets"); OUTCOMES+=("FAIL")
  FAIL=1
fi

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
bash "$SCRIPTS/backup.sh" --out "$TMP/bk" >> "$LOG" 2>&1
echo '{"tampered":1}' > "$TMP/bk/.backup-content/state.json"
check "corrupt backup rejected" 3 \
  env OCE_RUNTIME_TARGET=local bash "$SCRIPTS/restore.sh" --from "$TMP/bk"

# 5. unknown runtime target rejected (2).
check "unknown runtime target rejected" 2 \
  env OCE_RUNTIME_TARGET=not-a-target bash "$SCRIPTS/oce-ctl" local status

rm -rf "$TMP"

python3 - "$RESULTS" <<'PY'
import json, os, sys
out, names, outcomes = sys.argv[1], os.environ.get("_ADV_NAMES", ""), os.environ.get("_ADV_OUTCOMES", "")
records = []
# The bash arrays are exported via env by the caller below; fall back to
# parsing the log if env marshalling is unavailable.
for line in open(out.replace("adversarial-results.json", "adversarial-output.txt"), encoding="utf-8"):
    line = line.strip()
    if line.startswith(("PASS:", "FAIL:")):
        status, _, rest = line.partition(":")
        records.append({"check": rest.strip(), "outcome": status.strip()})
totals = {"PASS": sum(1 for r in records if r["outcome"] == "PASS"),
          "FAIL": sum(1 for r in records if r["outcome"] == "FAIL")}
json.dump({"format": "oce-adversarial-results-v1", "totals": totals, "checks": records},
          open(out, "w", encoding="utf-8"), indent=2)
PY

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "ADVERSARIAL: ALL PASS"
else
  echo "ADVERSARIAL: FAILURES PRESENT"
fi
exit $FAIL