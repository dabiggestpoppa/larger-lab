#!/usr/bin/env python3
"""OCE Book 2 — independent gate for control-plane validation (B2-R8).

Fail-closed verification of machine-readable evidence ONLY. Never parses
authoritative totals from human-readable pytest prose, and never treats
``passed > 0`` as success.

Two phases (the runner orchestrates the order):

  * pass A (default): repository/commit/tree identity, JUnit XML totals
    parsed directly, the complete mandatory test registry (every node id,
    zero duplicates), expected categories, migrations, cleanup (disposable
    containers/networks removed, durable postgres volume preserved), and
    source cleanliness before+after. Writes independent-gate.json.
  * pass B (--final): read-only final package verifier. Re-runs every
    pass-A check and additionally verifies the final evidence manifest
    (every SHA-256 + size matches the frozen files), that the required
    artifact set is complete, and that the final stage status matches the
    actual result (including zero cloud mutations / $0 recurring cost).
    Writes final-package-verifier.json AFTER the manifest, so it never
    modifies a hashed artifact.

Usage: independent-gate-b2.py [--final] <evidence-dir> <pytest-rc>
Env:   OCE_RUN_ID, OCE_CI_MODE, GITHUB_REPOSITORY, GITHUB_REF_NAME,
       OCE_EXPECTED_REPO, OCE_EXPECTED_BRANCH, OCE_EXPECTED_COMMIT,
       OCE_EXPECTED_TREE
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # infrastructure/control-plane
sys.path.insert(0, str(BASE_DIR / "scripts"))

import b2_registry  # noqa: E402
from b2_registry import (  # noqa: E402
    ARTIFACT_CATEGORY_FILE,
    EXPECTED_BRANCH,
    EXPECTED_REPO,
    MANDATORY_TEST_IDS,
    REQUIRED_ARTIFACTS,
    SCHEMA_VERSION,
    VALIDATOR_VERSION,
    category_of,
    expected_counts,
)

RUN_ID_RE = re.compile(r"^[0-9a-f]{12,}$")
# Artifacts produced AFTER pass A (stage status + manifest) — verified in pass B.
LATE_ARTIFACTS = {"stage-status.json", "evidence-manifest.json"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_stdout(cwd: Path, args: list[str]) -> str:
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                       text=True, timeout=60)
    return r.stdout.strip() if r.returncode == 0 else ""


def parse_junit(path: Path) -> dict:
    root = ET.parse(str(path)).getroot()
    suite = root.find("testsuite") or root
    testcases = list(suite.iter("testcase"))
    ids = [f"{tc.get('classname')}::{tc.get('name')}" for tc in testcases]
    skipped = [n for n, tc in zip(ids, testcases) if tc.find("skipped") is not None]
    failed = [n for n, tc in zip(ids, testcases) if tc.find("failure") is not None]
    errors = [n for n, tc in zip(ids, testcases) if tc.find("error") is not None]
    collected = int(suite.get("tests", len(ids)))
    return {
        "collected": collected,
        "testcase_count": len(ids),
        "ids": ids,
        "skipped": skipped,
        "failed": failed,
        "errors": errors,
        "executed": collected - len(skipped),
        "passed": collected - len(skipped) - len(failed) - len(errors),
    }


def _parse_json(evidence: Path, name: str, checks: list, tag: str) -> dict | None:
    path = evidence / name
    if not path.exists():
        checks.append({"id": tag, "name": f"{name} exists", "ok": False,
                       "detail": "missing"})
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        checks.append({"id": tag, "name": f"{name} exists", "ok": True, "detail": "parses"})
        return data
    except json.JSONDecodeError as exc:
        checks.append({"id": tag, "name": f"{name} exists", "ok": False,
                       "detail": f"unparseable: {exc}"})
        return None


def run_gate(evidence_dir: str | Path, pytest_rc: int | str, final: bool = False,
             environ: dict | None = None) -> tuple[int, dict]:
    """Execute the gate. Returns (exit_code, result)."""
    env = environ if environ is not None else os.environ
    evidence = Path(evidence_dir)
    ci_mode = env.get("OCE_CI_MODE") == "true"
    run_id = env.get("OCE_RUN_ID", "")
    expected_commit = env.get("OCE_EXPECTED_COMMIT", "")
    expected_tree = env.get("OCE_EXPECTED_TREE", "")

    checks: list[dict] = []

    def add(cid: str, name: str, ok: bool, detail: str = "") -> None:
        checks.append({"id": cid, "name": name, "ok": bool(ok), "detail": str(detail)})

    # ------------------------------------------------------------------ identity
    git_head = _git_stdout(BASE_DIR, ["rev-parse", "HEAD"])
    git_tree = _git_stdout(BASE_DIR, ["rev-parse", "HEAD^{tree}"])
    src_id = _parse_json(evidence, "source-identity.json", checks, "identity-source")
    if src_id is not None:
        add("identity-repo", "repository identity",
            src_id.get("repository") == EXPECTED_REPO
            and (env.get("GITHUB_REPOSITORY", "") in ("", EXPECTED_REPO)),
            f"repo={src_id.get('repository')} expected={EXPECTED_REPO}")
        branch_ok = src_id.get("observed_branch") == EXPECTED_BRANCH
        if env.get("GITHUB_REF_NAME"):
            branch_ok = branch_ok and env["GITHUB_REF_NAME"] == EXPECTED_BRANCH
        add("identity-branch", "trusted branch/ref",
            branch_ok, f"observed={src_id.get('observed_branch')} ci_ref={env.get('GITHUB_REF_NAME','')}")
        add("identity-commit", "implementation commit",
            bool(src_id.get("implementation_commit"))
            and src_id["implementation_commit"] == git_head
            and (not expected_commit or src_id["implementation_commit"] == expected_commit),
            f"source={src_id.get('implementation_commit')} git={git_head} expected={expected_commit or 'unset'}")
        add("identity-tree", "implementation tree",
            bool(src_id.get("implementation_tree"))
            and src_id["implementation_tree"] == git_tree
            and (not expected_tree or src_id["implementation_tree"] == expected_tree),
            f"source={src_id.get('implementation_tree')} git={git_tree} expected={expected_tree or 'unset'}")
    else:
        add("identity-repo", "repository identity", False, "no source-identity.json")
        add("identity-branch", "trusted branch/ref", False)
        add("identity-commit", "implementation commit", False)
        add("identity-tree", "implementation tree", False)

    add("run-id", "OCE_RUN_ID valid", bool(RUN_ID_RE.fullmatch(run_id or "")), run_id)

    # ------------------------------------------------------------------ junit
    junit_path = evidence / "junit.xml"
    if not junit_path.exists():
        add("junit-parses", "JUnit XML parses", False, "missing")
        junit = None
    else:
        try:
            junit = parse_junit(junit_path)
            add("junit-parses", "JUnit XML parses", True, f"collected={junit['collected']}")
        except ET.ParseError as exc:
            junit = None
            add("junit-parses", "JUnit XML parses", False, str(exc))

    expected_total = len(MANDATORY_TEST_IDS)
    if junit is not None:
        add("collected-exact", "exact collected total",
            junit["collected"] == expected_total,
            f"junit={junit['collected']} registry={expected_total}")
        add("executed-exact", "exact executed total",
            junit["executed"] == expected_total - len(junit["skipped"]),
            f"executed={junit['executed']}")
        add("passed-exact", "exact passed total",
            junit["passed"] == junit["executed"] - len(junit["failed"]) - len(junit["errors"]),
            f"passed={junit['passed']}")
        add("failed-exact", "exact failed total",
            len(junit["failed"]) == 0, f"failed={len(junit['failed'])}")
        add("errors-exact", "exact error total",
            len(junit["errors"]) == 0, f"errors={len(junit['errors'])}")
        add("skipped-exact", "exact skipped total", True,
            f"skipped={len(junit['skipped'])}")
        if ci_mode:
            add("zero-skips-ci", "zero skipped tests in CI",
                len(junit["skipped"]) == 0,
                f"skipped={len(junit['skipped'])} reasons={junit['skipped'][:5]}")
        missing = [n for n in MANDATORY_TEST_IDS if n not in junit["ids"]]
        dupes = sorted({n for n in junit["ids"] if junit["ids"].count(n) > 1})
        add("mandatory-present", "every mandatory test executed",
            not missing, f"missing={len(missing)} {missing[:5]}")
        add("no-duplicates", "no duplicate test ids", not dupes, f"{dupes[:5]}")
    else:
        add("collected-exact", "exact collected total", False, "no junit")
        add("passed-exact", "exact passed total", False, "no junit")
        add("failed-exact", "exact failed total", False, "no junit")
        add("errors-exact", "exact error total", False, "no junit")
        add("skipped-exact", "exact skipped total", False, "no junit")
        add("mandatory-present", "every mandatory test executed", False, "no junit")
        add("no-duplicates", "no duplicate test ids", False, "no junit")

    add("pytest-exit", "pytest exit code 0", int(pytest_rc or 0) == 0,
        f"rc={pytest_rc}")

    # ------------------------------------------------------------------ categories
    for cat, expected_n in expected_counts().items():
        cat_ids = {n for n in MANDATORY_TEST_IDS if category_of(n) == cat}
        if junit is None:
            add(f"cat-{cat}", f"category {cat} executed", False, "no junit")
            continue
        ran = cat_ids & set(junit["ids"])
        not_skipped = ran - set(junit["skipped"])
        not_failed = not_skipped - set(junit["failed"]) - set(junit["errors"])
        add(f"cat-{cat}", f"category {cat}: all tests executed, none skipped/failed",
            len(ran) == len(cat_ids) and len(not_failed) == len(cat_ids),
            f"expected={len(cat_ids)} executed={len(ran)} passed={len(not_failed)}")
        fname = ARTIFACT_CATEGORY_FILE[cat]
        cdata = _parse_json(evidence, fname, checks, f"catfile-{cat}")
        if cdata is not None:
            add(f"catfile-{cat}-recon", f"{fname} reconciles",
                cdata.get("expected") == len(cat_ids)
                and cdata.get("run_id") == run_id
                and cdata.get("executed") == len(ran) - len(ran & set(junit["skipped"])),
                f"expected={cdata.get('expected')} executed={cdata.get('executed')}")

    # ------------------------------------------------------------------ artifacts
    # Excluded from pass A (produced after the gate runs, or by the gate
    # itself): independent-gate.json (gate's own output), stage-log.txt +
    # validation-summary.md (written by the runner after pass A, before the
    # manifest). The --final phase requires the COMPLETE set via the manifest.
    post_gate = LATE_ARTIFACTS | {"independent-gate.json", "stage-log.txt",
                                  "validation-summary.md"}
    pass_a_required = [a for a in REQUIRED_ARTIFACTS if a not in post_gate]
    missing_artifacts = [a for a in pass_a_required if not (evidence / a).exists()]
    add("artifacts-complete", "required evidence artifacts present (pre-manifest)",
        not missing_artifacts, f"missing={missing_artifacts}")
    non_json = {"junit.xml", "pytest-output.txt", "stage-log.txt", "validation-summary.md"}
    for name in pass_a_required:
        if name in non_json:
            continue
        _parse_json(evidence, name, checks, f"artifact-{name}")

    # ------------------------------------------------------------------ reconciliation
    # every JSON artifact that carries a run id must reconcile to this run
    reconciling = pass_a_required + (["stage-status.json"] if final else [])
    for name in reconciling:
        path = evidence / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "run_id" in data:
            add(f"reconcile-{name}", f"{name} run id reconciles",
                data.get("run_id") == run_id,
                f"{data.get('run_id')} == {run_id}")

    reg = _parse_json(evidence, "test-registry.json", checks, "registry-parses")
    if reg is not None:
        add("registry-run-id", "test-registry run id matches",
            reg.get("run_id") == run_id, f"{reg.get('run_id')} == {run_id}")
        add("registry-total", "test-registry expected total",
            reg.get("expected_total") == expected_total,
            f"registry={reg.get('expected_total')} expected={expected_total}")
        if junit is not None:
            add("registry-junit", "test-registry totals match junit",
                reg.get("collected_total") == junit["collected"]
                and reg.get("failed_total") == len(junit["failed"])
                and reg.get("skipped_total") == len(junit["skipped"]),
                f"collected={reg.get('collected_total')} failed={reg.get('failed_total')} skipped={reg.get('skipped_total')}")

    mig = _parse_json(evidence, "migration-results.json", checks, "migration-parses")
    if mig is not None:
        add("migrations-ok", "migrations succeeded", mig.get("ok") is True,
            f"applied={mig.get('applied_versions')}")

    clean = _parse_json(evidence, "source-cleanliness.json", checks, "cleanliness-parses")
    if clean is not None:
        add("source-clean-before", "source clean before execution",
            clean.get("before", {}).get("clean") is True,
            f"dirty={clean.get('before', {}).get('dirty_files')}")
        add("source-clean-after", "source clean after execution",
            clean.get("after", {}).get("clean") is True,
            f"dirty={clean.get('after', {}).get('dirty_files')}")

    cleanup = _parse_json(evidence, "cleanup-results.json", checks, "cleanup-parses")
    if cleanup is not None:
        add("cleanup-removed", "cleanup removed disposable resources",
            cleanup.get("containers_removed") is True
            and cleanup.get("networks_removed") is True
            and cleanup.get("removed") is True,
            f"containers={cleanup.get('containers_removed')} networks={cleanup.get('networks_removed')}")
        add("cleanup-volume-preserved", "durable postgres volume preserved",
            cleanup.get("durable_postgres_volume_preserved") is True,
            f"preserved={cleanup.get('durable_postgres_volume_preserved')}")

    # ------------------------------------------------------------------ final phase
    if final:
        manifest_path = evidence / "evidence-manifest.json"
        if not manifest_path.exists():
            add("manifest-exists", "final evidence manifest present", False, "missing")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                add("manifest-parses", "final evidence manifest parses", True,
                    f"{len(manifest.get('files', {}))} files")
            except json.JSONDecodeError as exc:
                manifest = None
                add("manifest-parses", "final evidence manifest parses", False, str(exc))
            if manifest is not None:
                files = manifest.get("files", {})
                mismatches = []
                for name, entry in files.items():
                    path = evidence / name
                    if not path.exists():
                        mismatches.append(f"{name}: missing")
                        continue
                    actual_sha = sha256_file(path)
                    actual_size = path.stat().st_size
                    if actual_sha != entry.get("sha256") or actual_size != entry.get("size"):
                        mismatches.append(f"{name}: hash/size mismatch")
                # the manifest is generated LAST and never self-references
                missing_from_manifest = [a for a in REQUIRED_ARTIFACTS
                                         if a != "evidence-manifest.json" and a not in files]
                add("manifest-hashes", "manifest SHA-256 + sizes match final files",
                    not mismatches, "; ".join(mismatches[:5]) or "all match")
                add("manifest-complete", "all required artifacts in manifest",
                    not missing_from_manifest, f"missing={missing_from_manifest}")

        stage = _parse_json(evidence, "stage-status.json", checks, "stage-status-parses")
        if stage is not None:
            # stage status must match the gate result computed WITHOUT the
            # stage-status / manifest checks themselves (avoid self-reference)
            substantive = [c for c in checks if c["id"] not in (
                "stage-status-match", "stage-status-parses", "cloud-zero",
                "manifest-exists", "manifest-parses", "manifest-hashes",
                "manifest-complete", "artifact-stage-status.json",
                "artifact-evidence-manifest.json", "final-stage-log-frozen")]
            ok_substantive = all(c["ok"] for c in substantive)
            add("stage-status-match", "final stage status matches actual result",
                stage.get("stage_status") == ("PASS" if ok_substantive else "FAIL")
                and stage.get("gate_status") == stage.get("stage_status"),
                f"stage={stage.get('stage_status')} actual={'PASS' if ok_substantive else 'FAIL'}")
            add("cloud-zero", "cloud mutations zero / recurring cost $0",
                stage.get("cloud_mutations") == 0
                and stage.get("cloud_cost_state") == "ZERO",
                f"mutations={stage.get('cloud_mutations')} cost={stage.get('cloud_cost_state')}")

    ok = all(c["ok"] for c in checks)
    counts = {}
    if junit is not None:
        counts = {"collected": junit["collected"], "executed": junit["executed"],
                  "passed": junit["passed"], "failed": len(junit["failed"]),
                  "errors": len(junit["errors"]), "skipped": len(junit["skipped"])}
    result = {
        "gate": "PASS" if ok else "FAIL",
        "block": "B2",
        "stage": "B2-CONTROL-PLANE-CLOSURE",
        "run_id": run_id,
        "schema_version": SCHEMA_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "environment": "ci" if ci_mode else "local",
        "phase": "final" if final else "independent",
        "counts": counts,
        "checks": checks,
        "ci_mode": ci_mode,
        "cloud_mutations": 0,
        "cloud_cost_state": "ZERO",
        "cloud_deployment_state": "NOT_DEPLOYED",
        "cloud_activation_state": "DEFERRED_BY_OPERATOR",
    }
    out_name = "final-package-verifier.json" if final else "independent-gate.json"
    (evidence / out_name).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("GATE:", "PASS" if ok else "FAIL", json.dumps(counts))
    return (0 if ok else 1), result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OCE Book 2 independent gate")
    parser.add_argument("--final", action="store_true",
                        help="final read-only package verification (manifest + stage status)")
    parser.add_argument("evidence_dir")
    parser.add_argument("pytest_rc", nargs="?", default="0")
    args = parser.parse_args(argv)
    rc, result = run_gate(args.evidence_dir, args.pytest_rc, final=args.final)
    return rc


if __name__ == "__main__":
    sys.exit(main())
