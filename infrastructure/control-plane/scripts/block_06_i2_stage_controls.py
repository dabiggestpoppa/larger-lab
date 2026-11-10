#!/usr/bin/env python3
"""B6-I2 stage-scope negative controls.

Proves, against a local detached worktree of the exact head (no clone, no shared ref mutation):

* strict B6-I0 mode still resolves with no later-stage authority;
* the B6-I2 head resolves as B6-I2 with the B6-I2 surfaces added;
* the B6-I1 declared authority is a proper subset of the B6-I2 authority and lacks I2 surfaces;
* a renamed branch cannot spoof identity;
* an I3 artifact is refused;
* a missing registration is refused rather than silently falling back.

Usage:
  python infrastructure/control-plane/scripts/block_06_i2_stage_controls.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import block_06_stage_scope as scope  # noqa: E402

DOCS = "docs/oce-golden-system"
I1_SCOPE = f"{DOCS}/OCE_BLOCK_06_I1_SCOPE_DERIVATION_v1.0.json"
I2_REG = f"{DOCS}/OCE_BLOCK_06_I2_STAGE_SCOPE_REGISTRATION_v1.0.json"
AMENDMENT = f"{DOCS}/OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json"
AMENDMENT_DOC = f"{DOCS}/OCE_BLOCK_06_I2_PROOF_CLOSURE_AMENDMENT_v1.0.json"
BASE = "4496d548078660efd7ad4f93e7fff461d34ea538"
PROBE_BRANCH = "oce-book-6-i9-probe"


def git(cwd, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def commit(cwd, message: str) -> None:
    git(cwd, "add", "-A")
    proc = git(cwd, "-c", "user.email=ci@example.com", "-c", "user.name=ci",
               "commit", "-qm", message)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def check(name: str, ok: bool, detail=None) -> dict:
    return {"control": name, "ok": bool(ok), "detail": detail}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    results: list[dict] = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="b6i2-controls-"))
    work = tmp / "wt"
    try:
        i0 = scope.resolve(root, "i0")
        results.append(check("i0_strict_mode", i0["mode"] == "i0" and i0["stage"] == "B6-I0"
                             and i0["allowed"] == ()))

        i2 = scope.resolve(root, "auto")
        i2_allowed = set(i2["allowed"])
        results.append(check("i2_resolves", i2["mode"] == "i2" and i2["stage"] == "B6-I2",
                             {"mode": i2["mode"], "stage": i2["stage"]}))
        results.append(check("i2_contains_i2_surfaces",
                             "oce/templates/" in i2_allowed and "oce/harness/" in i2_allowed))

        i1_scope = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
        i1_allowed = set(i1_scope["allowed_paths"])
        results.append(check("i1_authority_preserved", i1_allowed <= i2_allowed,
                             sorted(i1_allowed - i2_allowed)[:5]))
        results.append(check("authority_sets_distinct",
                             i1_allowed != i2_allowed and i0["allowed"] == ()
                             and not i1_allowed & {"oce/templates/", "oce/harness/"},
                             len(i2_allowed - i1_allowed)))

        amendment_paths = set(json.loads((root / AMENDMENT).read_text(encoding="utf-8"))
                              ["authorized_paths"])
        i1_exact = i1_allowed | amendment_paths
        results.append(check("i1_exact_authority",
                             not i1_exact & {"oce/templates/", "oce/harness/"},
                             sorted(i1_exact & {"oce/templates/", "oce/harness/"})))
        results.append(check("i2_is_i1_plus_i2_only",
                             i2_allowed == i1_exact | set(i2["amendment"])
                             | {"oce/templates/", "oce/harness/"},
                             sorted(i2_allowed - (i1_exact | set(i2["amendment"])
                                                  | {"oce/templates/", "oce/harness/"}))))
        amendment = json.loads((root / AMENDMENT_DOC).read_text(encoding="utf-8"))
        results.append(check("proof_closure_frozen",
                             amendment["status"] == "FROZEN"
                             and amendment["frozen_before_results"] is True
                             and amendment["floors"]["test_nodes"] == 30
                             and amendment["m13"]["governed_rows"] == 12
                             and amendment["local_start"]["mode"]
                             == "SUBPROCESS_START_WITH_READINESS"))
        prior = git(root, "diff", "--quiet", f"{BASE}..HEAD", "--",
                    "infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
                    "infrastructure/control-plane/tests/test_block_06_i1_authority_and_boundary.py")
        results.append(check("prior_tests_restored", prior.returncode == 0, prior.returncode))
        for wf in (".github/workflows/block-06-i0-validation.yml",
                   ".github/workflows/block-06-i1-validation.yml"):
            text = (root / wf).read_text(encoding="utf-8")
            results.append(check(f"replay_pinned/{wf.rsplit('/', 1)[-1]}",
                                 "96e3b817" in text and "6783bf76" in text
                                 and "REPLAY_WT" in text))

        add = git(root, "worktree", "add", "--detach", "--quiet", str(work), "HEAD")
        results.append(check("worktree_ready", add.returncode == 0, add.stderr[-300:]))
        if add.returncode == 0:
            before = scope.resolve(work, "auto")
            branch = git(work, "checkout", "-q", "-b", PROBE_BRANCH)
            after = scope.resolve(work, "auto")
            results.append(check("branch_name_cannot_spoof",
                                 branch.returncode == 0 and after["stage"] == "B6-I2"
                                 and after["mode"] == before["mode"]
                                 and after["identity"] == before["identity"], after["stage"]))

            later = work / DOCS / "OCE_BLOCK_06_I3_SCOPE_DERIVATION_v1.0.json"
            later.write_text("{}\n", encoding="utf-8")
            commit(work, "probe-i3")
            try:
                scope.resolve(work, "auto")
                results.append(check("i3_refused", False, "resolved despite an I3 artifact"))
            except scope.StageScopeError as exc:
                results.append(check("i3_refused", exc.check == "stage/later_stage_absent",
                                     exc.check))
            git(work, "reset", "-q", "--hard", "HEAD~1")

            (work / I2_REG).unlink()
            commit(work, "probe-missing-registration")
            try:
                scope.resolve(work, "auto")
                results.append(check("missing_registration_refused", False,
                                     "resolved without it"))
            except scope.StageScopeError as exc:
                results.append(check("missing_registration_refused",
                                     exc.check in ("stage/base_moved", "stage/identity_missing",
                                                   "stage/identity_unknown"), exc.check))
    finally:
        git(root, "worktree", "remove", "--force", str(work))
        git(root, "branch", "-D", PROBE_BRANCH)
        shutil.rmtree(tmp, ignore_errors=True)

    ok = bool(results) and all(row["ok"] for row in results)
    payload = {"controls": len(results), "passed": sum(1 for row in results if row["ok"]),
               "status": "PASS" if ok else "FAIL", "results": results}
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
