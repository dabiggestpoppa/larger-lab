#!/usr/bin/env bash
#
# final-package-verify.sh — READ-ONLY verification of the exact final evidence
# package. It MUST NOT write, move, or modify any evidence file. It re-checks
# the final manifest (hashes/sizes), final status, independent-gate result,
# RUN_ID, identities, totals, cleanup, and cloud fields, printing the result
# to the CI/local log so the outcome is visible.
#
#   final-package-verify.sh <evidence-dir> <commit> <tree>
set -uo pipefail

EVIDENCE="${1:?evidence dir}"
COMMIT="${2:?commit}"
TREE="${3:?tree}"

python3 - "$EVIDENCE" "$COMMIT" "$TREE" <<'PY'
import hashlib, json, os, sys
ev, commit, tree = sys.argv[1], sys.argv[2], sys.argv[3]
errs = []
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

man = json.load(open(os.path.join(ev, "evidence-manifest.json"), encoding="utf-8"))
for art in man.get("artifacts", []):
    p = os.path.join(ev, art["path"])
    if not os.path.isfile(p):
        errs.append(f"missing artifact {art['path']}"); continue
    if sha(p) != art.get("sha256") or os.path.getsize(p) != art.get("size"):
        errs.append(f"hash/size mismatch {art['path']}")
st = json.load(open(os.path.join(ev, "stage-status.json"), encoding="utf-8"))
ig = json.load(open(os.path.join(ev, "independent-gate.json"), encoding="utf-8"))
if st.get("run_id") != man.get("run_id"):
    errs.append("RUN_ID mismatch between status and manifest")
if ig.get("run_id") != man.get("run_id"):
    errs.append("RUN_ID mismatch between gate and manifest")
if man.get("implementation_commit") != commit:
    errs.append("manifest commit != tested commit")
if man.get("implementation_tree") != tree:
    errs.append("manifest tree != tested tree")
if st.get("cloud_activation_state") != "DEFERRED_BY_OPERATOR":
    errs.append("cloud_activation_state not deferred")
if st.get("cloud_deployment_state") != "NOT_DEPLOYED":
    errs.append("cloud_deployment_state not NOT_DEPLOYED")
if st.get("cloud_cost_state") != "ZERO":
    errs.append("cloud_cost_state not ZERO")
if st.get("cloud_mutations") != 0:
    errs.append("cloud_mutations != 0")
if ig.get("result") != "PASS":
    errs.append(f"independent gate result is {ig.get('result')!r}, expected PASS")
if ig.get("totals", {}).get("FAIL", 1) != 0:
    errs.append("independent gate has failing checks")
ts = json.load(open(os.path.join(ev, "test-summary.json"), encoding="utf-8"))
t = ts.get("totals", {})
if t.get("failed", 1) != 0 or t.get("errors", 1) != 0:
    errs.append("test-summary has failures/errors")
mode = ig.get("mode")
if mode == "AUTHORITATIVE_CI":
    if ts.get("mandatory_skipped", 1) != 0:
        errs.append("mandatory skipped tests in CI mode")
    if ts.get("container_backed", {}).get("executed") != ts.get("container_backed", {}).get("collected"):
        errs.append("container-backed tests not all executed in CI mode")
cleanup = json.load(open(os.path.join(ev, "cleanup.json"), encoding="utf-8"))
if not (cleanup.get("cleanup") == "ok" or (cleanup.get("removed") is True and cleanup.get("pruned") is True)):
    errs.append("cleanup not confirmed")

print("FINAL PACKAGE VERIFIER (read-only): " + ("PASS" if not errs else "FAIL"))
for e in errs:
    print("  FAIL:", e)
sys.exit(0 if not errs else 1)
PY
exit $?