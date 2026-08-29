#!/usr/bin/env bash
#
# final-gate-local.sh — independent gate for B1-LOCAL evidence.
#   final-gate-local.sh <evidence-dir> <commit> <tree>
# Verifies required artifacts exist and manifest hashes match (no
# expected-value substitution), then exits nonzero unless genuinely ready.
set -uo pipefail

EVIDENCE="${1:?evidence dir}"
COMMIT="${2:?commit}"
TREE="${3:?tree}"
REQUIRED=(identity.json environment-fingerprint.json acceptance-output.txt cloud-plan.txt cloud-apply-denial.txt adversarial-output.txt stage-log.txt stage-status.json evidence-manifest.json)

missing=""
for a in "${REQUIRED[@]}"; do
  [ -f "$EVIDENCE/$a" ] || missing="$missing $a"
done
if [ -n "$missing" ]; then
  echo "GATE FAIL: missing artifacts:$missing" >&2
  exit 1
fi

# Manifest hash verification (observed only).
python3 - "$EVIDENCE" <<'PY'
import hashlib, json, os, sys
ev = sys.argv[1]
man = json.load(open(os.path.join(ev, "evidence-manifest.json"), encoding="utf-8"))
fail = False
for art in man.get("artifacts", []):
    p = os.path.join(ev, art["path"])
    if not os.path.isfile(p):
        print("GATE FAIL: manifest references missing", art["path"]); fail = True; continue
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    if h.hexdigest() != art["sha256"]:
        print("GATE FAIL: hash mismatch", art["path"]); fail = True
if man.get("cloud_mutations") != 0:
    print("GATE FAIL: cloud_mutations != 0"); fail = True
if man.get("cloud_cost_state") != "ZERO":
    print("GATE FAIL: cloud_cost_state != ZERO"); fail = True
if man.get("cloud_activation_state") != "DEFERRED_BY_OPERATOR":
    print("GATE FAIL: cloud_activation_state != DEFERRED_BY_OPERATOR"); fail = True
sys.exit(1 if fail else 0)
PY
RC=$?
[ $RC -ne 0 ] && { echo "GATE FAIL: manifest verification" >&2; exit $RC; }

echo "GATE: artifacts present, manifest hashes verified, cloud fields honest."
exit 0