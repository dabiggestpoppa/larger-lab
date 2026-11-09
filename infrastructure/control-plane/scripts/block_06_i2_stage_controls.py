#!/usr/bin/env python3
"""B6-I2 stage-scope negative controls.

Proves, against throwaway clones of the real history, that:

* strict B6-I0 mode still resolves with no later-stage authority;
* a pre-B6-I2 head still resolves as B6-I1 with the B6-I1 authority set;
* the B6-I2 head resolves as B6-I2 with a strictly larger set that contains the B6-I2 surfaces;
* the three authority sets are pairwise distinct;
* a branch rename cannot spoof identity;
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

I0_MERGE = "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e"
I1_HEAD = "96e3b81714321f4eea7abcb300ef471e93be0962"
I2_REG = "docs/oce-golden-system/OCE_BLOCK_06_I2_STAGE_SCOPE_REGISTRATION_v1.0.json"


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
    try:
        clone = tmp / "clone"
        proc = git(tmp, "clone", "--quiet", "--no-hardlinks", f"file://{root}", str(clone))
        if proc.returncode != 0:
            print(proc.stdout + proc.stderr)
            return 2

        i0 = scope.resolve(clone, "i0")
        results.append(check("i0_strict_mode", i0["mode"] == "i0" and i0["stage"] == "B6-I0"
                             and i0["allowed"] == ()))

        proc = git(clone, "checkout", "--quiet", "--detach", I1_HEAD)
        results.append(check("i1_head_checkout", proc.returncode == 0, proc.stderr[-300:]))
        git(clone, "update-ref", "refs/remotes/origin/main", I0_MERGE)
        i1 = scope.resolve(clone, "auto")
        i1_allowed = set(i1["allowed"])
        results.append(check("i1_resolves_distinctly",
                             i1["mode"] == "later" and i1["stage"] == "B6-I1"
                             and "oce/api/" in i1_allowed,
                             {"mode": i1["mode"], "stage": i1["stage"]}))
        results.append(check("i1_lacks_i2_surfaces",
                             not any(p.startswith(("oce/templates/", "oce/harness/"))
                                     for p in i1_allowed)))

        git(clone, "checkout", "--quiet", "--detach", "HEAD@{1}")
        proc = git(clone, "rev-parse", "HEAD")
        head = proc.stdout.strip()
        git(clone, "update-ref", "refs/remotes/origin/main", I1_HEAD)
        i2 = scope.resolve(clone, "auto")
        i2_allowed = set(i2["allowed"])
        results.append(check("i2_resolves_on_i2_head",
                             i2["mode"] == "i2" and i2["stage"] == "B6-I2"
                             and head != I1_HEAD, {"mode": i2["mode"], "head": head[:12]}))
        results.append(check("i2_contains_i2_surfaces",
                             "oce/templates/" in i2_allowed and "oce/harness/" in i2_allowed))
        results.append(check("i2_contains_i1_authority", i1_allowed <= i2_allowed,
                             sorted(i1_allowed - i2_allowed)[:5]))
        results.append(check("authority_sets_distinct",
                             i1_allowed != i2_allowed and i0["allowed"] == ()
                             and i2_allowed != set()))

        branch = git(clone, "checkout", "-q", "-B", "oce-book-6-i9")
        renamed = scope.resolve(clone, "auto")
        results.append(check("branch_name_cannot_spoof",
                             branch.returncode == 0 and renamed["stage"] == "B6-I2",
                             renamed.get("stage")))

        later = clone / "docs/oce-golden-system/OCE_BLOCK_06_I3_SCOPE_DERIVATION_v1.0.json"
        later.write_text("{}\n", encoding="utf-8")
        commit(clone, "probe-i3")
        try:
            scope.resolve(clone, "auto")
            results.append(check("i3_refused", False, "resolved despite an I3 artifact"))
        except scope.StageScopeError as exc:
            results.append(check("i3_refused", exc.check == "stage/later_stage_absent", exc.check))
        later.unlink()
        commit(clone, "drop-probe-i3")

        reg = clone / I2_REG
        reg.unlink()
        commit(clone, "probe-missing-registration")
        try:
            scope.resolve(clone, "auto")
            results.append(check("missing_registration_refused", False, "resolved without it"))
        except scope.StageScopeError as exc:
            results.append(check("missing_registration_refused",
                                 exc.check in ("stage/base_moved", "stage/identity_missing",
                                               "stage/unknown_mode", "stage/identity_unknown"),
                                 exc.check))
    finally:
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
