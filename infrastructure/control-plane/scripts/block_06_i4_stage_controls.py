#!/usr/bin/env python3
"""B6-I4 stage-scope negative controls, run against a detached worktree of the exact head."""
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
I3_REG = f"{DOCS}/OCE_BLOCK_06_I3_STAGE_SCOPE_REGISTRATION_v1.0.json"
I4_REG = f"{DOCS}/OCE_BLOCK_06_I4_STAGE_SCOPE_REGISTRATION_v1.0.json"
BASE = "f0bd9bdd3f776b33d3b70b5b441966e2c80e1f14"
I3_HEAD = "eda33f43e6d058891a8009e98e968c9f00252220"
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
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="b6i4-controls-"))
    work = tmp / "wt"
    try:
        i0 = scope.resolve(root, "i0")
        results.append(check("i0_strict_mode", i0["mode"] == "i0" and i0["allowed"] == ()))
        i4 = scope.resolve(root, "auto")
        allowed = set(i4["allowed"])
        results.append(check("i4_resolves", i4["mode"] == "i4" and i4["stage"] == "B6-I4",
                             {"mode": i4["mode"], "stage": i4["stage"]}))
        results.append(check("i4_operator_surface", "oce/operator/" in allowed))
        results.append(check("i4_service_surface", "oce/services/" in allowed))
        i1_allowed = set(json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))["allowed_paths"])
        results.append(check("i1_authority_preserved", i1_allowed <= allowed,
                             sorted(i1_allowed - allowed)[:5]))
        i2_prefixes = set(json.loads((root / I2_REG).read_text(encoding="utf-8"))
                          ["this_stage"]["allowed_prefixes"])
        results.append(check("i2_authority_preserved", i2_prefixes <= allowed,
                             sorted(i2_prefixes - allowed)[:5]))
        i3_prefixes = set(json.loads((root / I3_REG).read_text(encoding="utf-8"))
                          ["this_stage"]["allowed_prefixes"])
        results.append(check("i3_authority_preserved", i3_prefixes <= allowed,
                             sorted(i3_prefixes - allowed)[:5]))
        added = {p for p in allowed if p.startswith("oce/")
                 and not p.startswith(tuple(i1_allowed))
                 and not p.startswith(tuple(i2_prefixes))
                 and not p.startswith(tuple(i3_prefixes))}
        results.append(check("i4_adds_services", added == {"oce/services/"}, sorted(added)))
        prior = git(root, "diff", "--quiet", f"{BASE}..HEAD", "--",
                    "infrastructure/control-plane/tests/test_block_06_i3_contract.py",
                    "infrastructure/control-plane/tests/test_block_06_i3_evidence.py")
        results.append(check("prior_tests_unchanged", prior.returncode == 0, prior.returncode))
        frozen = git(root, "diff", "--name-only", f"{I3_HEAD}..HEAD", "--", DOCS)
        results.append(check("i3_packet_frozen",
                             not [p for p in frozen.stdout.splitlines()
                                  if "OCE_BLOCK_06_I3_" in p], frozen.stdout))
        i3_wf = (root / ".github/workflows/block-06-i3-validation.yml").read_text(encoding="utf-8")
        results.append(check("i3_workflow_present_frozen",
                             "B6-I3" in i3_wf and "018b164f249bbf075334d5d03ad37e80dcbbede0" in i3_wf))
        add = git(root, "worktree", "add", "--detach", "--quiet", str(work), "HEAD")
        results.append(check("worktree_ready", add.returncode == 0, add.stderr[-300:]))
        if add.returncode == 0:
            before = scope.resolve(work, "auto")
            branch = git(work, "checkout", "-q", "-b", PROBE_BRANCH)
            after = scope.resolve(work, "auto")
            results.append(check("branch_cannot_spoof",
                                 branch.returncode == 0 and after["stage"] == "B6-I4"
                                 and after["identity"] == before["identity"], after["stage"]))
            later = work / DOCS / "OCE_BLOCK_06_I5_SCOPE_DERIVATION_v1.0.json"
            later.write_text("{}\n", encoding="utf-8")
            commit(work, "probe-i5")
            try:
                scope.resolve(work, "auto")
                results.append(check("i5_refused", False, "resolved despite an I5 artifact"))
            except scope.StageScopeError as exc:
                results.append(check("i5_refused", exc.check == "stage/later_stage_absent",
                                     exc.check))
            git(work, "reset", "-q", "--hard", "HEAD~1")
            (work / I4_REG).unlink()
            commit(work, "probe-missing-registration")
            try:
                scope.resolve(work, "auto")
                results.append(check("missing_registration_refused", False, "resolved without it"))
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
