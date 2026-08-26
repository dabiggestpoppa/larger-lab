#!/usr/bin/env bash
#
# OCE Cloud Ground — Independent Final Gate
# B1-I1R3H — Gate Closure
#
# Independently verifies the final evidence directory. Never trusts
# self-authored status fields; recomputes everything from the artifacts.
#
# Usage: final-gate.sh <evidence-dir> <expected-commit> <expected-tree>
#
# Exit 0 only when the gate result is READY_FOR_OPERATOR_REVIEW.
set -uo pipefail

EVIDENCE_DIR="${1:-}"
EXPECTED_COMMIT="${2:-}"
EXPECTED_TREE="${3:-}"

if [ -z "$EVIDENCE_DIR" ] || [ -z "$EXPECTED_COMMIT" ] || [ -z "$EXPECTED_TREE" ]; then
    echo "GATE-FAIL: usage: final-gate.sh <evidence-dir> <expected-commit> <expected-tree>" >&2
    exit 1
fi

python3 - "$EVIDENCE_DIR" "$EXPECTED_COMMIT" "$EXPECTED_TREE" <<'PYEOF'
import hashlib
import json
import os
import subprocess
import sys

ev_dir, expected_commit, expected_tree = sys.argv[1], sys.argv[2], sys.argv[3]
errors = []
warnings = []


def load(name):
    path = os.path.join(ev_dir, name)
    if not os.path.exists(path):
        errors.append(f"MISSING-ARTIFACT: {name}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        errors.append(f"UNPARSEABLE: {name}: {e}")
        return None


results = load("static-validation-results.json")
stage = load("stage-status.json")
adv = load("adversarial-results.json")
manifest = load("evidence-manifest.json")

required_files = [
    "static-validation-results.json",
    "static-validation-summary.md",
    "adversarial-results.json",
    "stage-status.json",
    "evidence-manifest.json",
    "worktree-cleanup.json",
    "regression-output.txt",
    "stage-log.txt",
]
for name in required_files:
    if not os.path.exists(os.path.join(ev_dir, name)):
        errors.append(f"MISSING-ARTIFACT: {name}")

if results is None or stage is None or adv is None:
    for e in errors:
        print(f"  GATE: {e}", file=sys.stderr)
    print("GATE-RESULT: FAILED")
    sys.exit(1)

run_id_env = os.environ.get("OCE_RUN_ID", "").strip()

# ── RUN_ID consistency everywhere ────────────────────────────────
ids = {
    "static-validation-results": results.get("run_id", ""),
    "stage-status": stage.get("run_id", ""),
    "adversarial-results": adv.get("run_id", ""),
    "evidence-manifest": (manifest or {}).get("run_id", "") if manifest else "",
}
if run_id_env:
    ids["environment"] = run_id_env
distinct = {v for v in ids.values() if v}
if len(distinct) != 1:
    errors.append(f"RUN-ID-MIXED: {ids}")
elif not distinct.pop():
    errors.append("RUN-ID-MISSING everywhere")

# ── Version agreement (no hardcoded literal; artifacts must agree) ──
versions = {
    "static.validator_version": results.get("validator_version", ""),
    "static.schema_version": results.get("schema_version", ""),
    "stage.validator_version": stage.get("validator_version", ""),
    "adv.schema_version": adv.get("schema_version", ""),
    "adv.validator_version": adv.get("validator_version", ""),
    "manifest.schema_version": (manifest or {}).get("schema_version", "") if manifest else "",
    "manifest.validator_version": (manifest or {}).get("validator_version", "") if manifest else "",
}
bad_versions = {k: v for k, v in versions.items() if not v}
if bad_versions:
    errors.append(f"VERSION-MISSING: {bad_versions}")
present = {v for k, v in versions.items() if v}
if len(present) > 1:
    errors.append(f"VERSION-MISMATCH across artifacts: {sorted(present)}")

# ── Identity: commit/tree must match the actual checkout ────────
def git(*args_):
    r = subprocess.run(["git"] + list(args_), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

actual_commit = git("-C", os.environ.get("OCE_PROJ_ROOT", "."), "rev-parse", "HEAD")
actual_tree = git("-C", os.environ.get("OCE_PROJ_ROOT", "."), "rev-parse", "HEAD^{tree}")
if actual_commit != expected_commit:
    errors.append(f"COMMIT: gate-arg={expected_commit[:12]} checkout={str(actual_commit)[:12]}")
if actual_tree != expected_tree:
    errors.append(f"TREE: gate-arg={expected_tree[:12]} checkout={str(actual_tree)[:12]}")
if results.get("tested_commit", "") != expected_commit:
    errors.append(f"EVIDENCE-COMMIT: evidence={results.get('tested_commit', '')[:12]} != {expected_commit[:12]}")
if results.get("tested_tree", "") != expected_tree:
    errors.append(f"EVIDENCE-TREE: evidence={results.get('tested_tree', '')[:12]} != {expected_tree[:12]}")
if stage.get("implementation_commit", "") != expected_commit:
    errors.append(f"STAGE-COMMIT mismatch")
if stage.get("implementation_tree", "") != expected_tree:
    errors.append(f"STAGE-TREE mismatch")

# ── Branch identity through explicit rules ──────────────────────
contract_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "contracts",
    "checkpoint-identity-data.json")
try:
    with open(contract_path, "r", encoding="utf-8") as f:
        contract = json.load(f)
    expected_branch = contract.get("authorized_branch", "")
except Exception as e:
    expected_branch = ""
    errors.append(f"CONTRACT: cannot read authorized_branch: {e}")

observed_git = results.get("observed_git_branch", "")
trusted_ref = results.get("trusted_ci_ref") or ""
checkout_state = results.get("checkout_state", "")
provenance = results.get("branch_provenance", "")

if checkout_state == "attached":
    if provenance != "git-symbolic-ref":
        errors.append(f"BRANCH-PROVENANCE: attached but provenance={provenance}")
    identity = observed_git
else:
    if not trusted_ref:
        errors.append(f"BRANCH-IDENTITY: detached checkout without trusted ref (observed={observed_git}, provenance={provenance})")
        identity = observed_git
    elif provenance not in ("GITHUB_REF_NAME", "explicit-trusted-ref"):
        errors.append(f"BRANCH-PROVENANCE: detached but provenance={provenance}")
    identity = trusted_ref
if identity and expected_branch and identity != expected_branch:
    errors.append(f"BRANCH: identity={identity} expected={expected_branch}")
if results.get("tested_branch", "") != observed_git:
    errors.append(f"OBSERVED-SUBSTITUTION: tested_branch={results.get('tested_branch','')} != observed={observed_git}")
if results.get("repository", "") != "dabiggestpoppa/larger-lab":
    errors.append(f"REPOSITORY: {results.get('repository', '')}")
if stage.get("repository", results.get("repository", "")) not in ("dabiggestpoppa/larger-lab", None):
    errors.append(f"STAGE-REPOSITORY: {stage.get('repository')}")

# ── Totals match actual entries ──────────────────────────────────
totals = results.get("totals", {})
entries = results.get("results", [])
computed = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
for r in entries:
    res = r.get("result", "")
    if res in computed:
        computed[res] += 1
computed_total = sum(computed.values())
if totals.get("total", -1) != computed_total:
    errors.append(f"TOTALS: declared={totals.get('total')} computed={computed_total}")
for k in ("PASS", "FAIL", "BLOCKED", "SKIPPED"):
    if totals.get(k, -1) != computed[k]:
        errors.append(f"TOTALS[{k}]: declared={totals.get(k)} computed={computed[k]}")

# ── Mandatory outcomes ───────────────────────────────────────────
mandatory_fail = [r["check_id"] for r in entries
                  if r.get("mandatory") and r.get("result") == "FAIL"]
mandatory_blocked = [r["check_id"] for r in entries
                     if r.get("mandatory") and r.get("result") == "BLOCKED"]
skipped_mandatory = [r["check_id"] for r in entries
                     if r.get("mandatory") and r.get("result") == "SKIPPED"]
if mandatory_fail:
    errors.append(f"MANDATORY-FAIL: {mandatory_fail}")
if mandatory_blocked:
    errors.append(f"MANDATORY-BLOCKED: {mandatory_blocked}")
if skipped_mandatory:
    errors.append(f"MANDATORY-SKIPPED: {skipped_mandatory}")

# Final-phase evidence must include the adversarial checks.
final_check_ids = {r.get("check_id") for r in entries}
for needed in ("FAIL-CLOSED", "META-TEST-EVIDENCE", "RUN-ID-CONSISTENCY", "EVIDENCE-CONSISTENCY"):
    if needed not in final_check_ids:
        errors.append(f"FINAL-PHASE-INCOMPLETE: missing check {needed}")

# ── Adversarial suite ────────────────────────────────────────────
if adv.get("suite_result", "") != "PASS":
    errors.append(f"ADVERSARIAL-SUITE: suite_result={adv.get('suite_result', '')}")
neg = adv.get("negative_tests", [])
meta = adv.get("meta_tests", [])
if not neg:
    errors.append("ADVERSARIAL-SUITE: no negative tests")
if not meta:
    errors.append("ADVERSARIAL-SUITE: no meta tests")

for t in neg:
    tid = t.get("test_id", "?")
    lifecycle_ok = (
        t.get("result") == "PASS"
        and t.get("baseline_result") == "PASS"
        and t.get("baseline_exit") == 0
        and t.get("mutation_result") == "FAIL"
        and t.get("mutation_exit") != 0
        and t.get("post_restore_result") == "PASS"
        and t.get("post_restore_exit") == 0
        and t.get("original_sha256") not in ("", "N/A", None)
        and t.get("restored_sha256") not in ("", "N/A", None)
        and t.get("original_sha256") == t.get("restored_sha256")
        and t.get("expected_check")
    )
    if not lifecycle_ok:
        errors.append(f"NEGATIVE-LIFECYCLE-INCOMPLETE: {tid}")

for t in meta:
    tid = t.get("test_id", "?")
    rejection_ok = (
        t.get("fixture_type")
        and t.get("invalid_condition")
        and t.get("expected_rejection")
        and t.get("observed_rejection") in ("FAIL", "BLOCKED")
        and t.get("rejection_exit") != 0
        and t.get("result") == "PASS"
    )
    if not rejection_ok:
        errors.append(f"META-REJECTION-INCOMPLETE: {tid}")

adv_totals = adv.get("totals", {})
adv_actual = len(neg) + len(meta)
if adv_totals.get("total", -1) != adv_actual:
    errors.append(f"ADV-TOTALS: declared={adv_totals.get('total')} actual={adv_actual}")

# ── Manifest hashes must match actual files ──────────────────────
if manifest is None:
    errors.append("MANIFEST: missing evidence-manifest.json")
else:
    man_artifacts = {a.get("path"): a for a in manifest.get("artifacts", [])}
    for name in required_files:
        p = os.path.join(ev_dir, name)
        if not os.path.exists(p):
            continue  # already reported MISSING-ARTIFACT
        if name == "evidence-manifest.json":
            continue  # manifest cannot hash itself
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        recorded = man_artifacts.get(name, {}).get("sha256", "")
        if recorded != h.hexdigest():
            errors.append(f"MANIFEST-HASH: {name} recorded={recorded[:16]} actual={h.hexdigest()[:16]}")

# ── Authoritative source clean & worktree cleanup ────────────────
proj_root = os.environ.get("OCE_PROJ_ROOT", ".")
st = subprocess.run(["git", "-C", proj_root, "status", "--porcelain"],
                    capture_output=True, text=True)
if st.stdout.strip():
    errors.append(f"SOURCE-DIRTY: {len(st.stdout.strip().splitlines())} entries")
cleanup = load("worktree-cleanup.json")
if cleanup is None:
    errors.append("WORKTREE-CLEANUP: worktree-cleanup.json missing — cannot prove disposable worktree was removed and pruned")
else:
    if cleanup.get("removed") is not True:
        errors.append(f"WORKTREE-CLEANUP: removed={cleanup.get('removed')} — worktree removal not proven")
    if cleanup.get("pruned") is not True:
        errors.append(f"WORKTREE-CLEANUP: pruned={cleanup.get('pruned')} — worktree prune not proven")

# ── Gate verdict from stage status must be truthful ──────────────
gate_status = stage.get("gate_status", "")
if errors:
    print("GATE-RESULT: FAILED", flush=True)
    for e in errors:
        print(f"  GATE-ERROR: {e}", flush=True)
    for w in warnings:
        print(f"  GATE-WARN: {w}", flush=True)
    sys.exit(1)

if gate_status != "READY_FOR_OPERATOR_REVIEW":
    print(f"GATE-RESULT: BLOCKED (stage-status declares {gate_status} but no mandatory failures found)", flush=True)
    sys.exit(1)

print("GATE-RESULT: READY_FOR_OPERATOR_REVIEW", flush=True)
for w in warnings:
    print(f"  GATE-WARN: {w}", flush=True)
print(f"  GATE: run_id={ids.get('static-validation-results', '?')[:16]} "
      f"commit={expected_commit[:12]} totals={totals} "
      f"negative={len(neg)} meta={len(meta)}", flush=True)
sys.exit(0)
PYEOF
