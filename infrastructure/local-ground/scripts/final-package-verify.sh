#!/usr/bin/env bash
#
# final-package-verify.sh â€” READ-ONLY verification of the exact final evidence
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 - "$EVIDENCE" "$COMMIT" "$TREE" "$SCRIPT_DIR" <<'PY'
import hashlib, json, os, subprocess, sys
ev, commit, tree, script_dir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
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
if man.get("repository") != "dabiggestpoppa/larger-lab":
    errs.append(f"manifest repository != dabiggestpoppa/larger-lab ({man.get('repository')!r})")
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
    tm = open(os.path.join(ev, "test-mode.txt"), encoding="utf-8").read().strip()
    if tm != "AUTHORITATIVE_CI":
        errs.append(f"test-mode.txt is {tm!r}, expected AUTHORITATIVE_CI")
    cc = json.load(open(os.path.join(ev, "container-cleanup.json"), encoding="utf-8"))
    if not (cc.get("cleanup") == "ok" and cc.get("containers_removed") is True
            and cc.get("networks_removed") is True and cc.get("volumes_removed") is True):
        errs.append("container cleanup not verified in CI mode")
    # Recovery evidence: verified postgres promotion must have run and succeeded
    try:
        rr = json.load(open(os.path.join(ev, "postgres-recovery-receipt.json"), encoding="utf-8"))
    except Exception:
        rr = {}
        errs.append("missing postgres-recovery-receipt.json in CI mode")
    if rr and (rr.get("exit_status") != 0 or rr.get("promoted") is not True
               or rr.get("redis_restored") is not False or not rr.get("source_archive_sha256")):
        errs.append("postgres recovery receipt does not show verified promotion")
cleanup = json.load(open(os.path.join(ev, "cleanup.json"), encoding="utf-8"))
if not (cleanup.get("cleanup") == "ok" or (cleanup.get("removed") is True and cleanup.get("pruned") is True)):
    errs.append("cleanup not confirmed")
# R8/R9: the immutable operation index is the authoritative recovery record.
ops_root = os.path.join(ev, "operations")
if not os.path.isfile(os.path.join(ops_root, "index.json")):
    errs.append("missing operations/index.json (immutable operation index)")
else:
    r = subprocess.run([sys.executable,
                        os.path.join(script_dir, "recovery-ops.py"),
                        "verify", "--ops-root", ops_root],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        errs.append("operation index verification failed: " + (r.stdout + r.stderr).strip())

print("FINAL PACKAGE VERIFIER (read-only): " + ("PASS" if not errs else "FAIL"))
for e in errs:
    print("  FAIL:", e)
sys.exit(0 if not errs else 1)
PY
exit $?