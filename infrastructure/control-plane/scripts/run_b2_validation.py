#!/usr/bin/env python3
"""OCE Book 2 — authoritative validation runner (B2-R8, fail closed).

Sole authoritative orchestration for the B2 gate. Both local invocation
and GitHub Actions run this exactly once (the workflow invokes
scripts/run-b2-validation.sh, a thin wrapper around this module).

Every attempt — PASS, FAIL, or BLOCKED — produces truthful evidence in an
evidence directory OUTSIDE the repository. The execution order is fixed
(see the mission's 23 steps); the final evidence manifest is generated
LAST so its SHA-256 values describe the final uploaded files.

Normal successful cleanup happens BEFORE the independent gate; cleanup
failure blocks promotion. The abnormal-exit trap still attempts cleanup,
but only as best-effort tidiness.

Usage: run_b2_validation.py
Env:   OCE_RUN_ID (required, 12+ hex), OCE_EVIDENCE_DIR, OCE_CI_MODE,
       GITHUB_REPOSITORY, GITHUB_REF_NAME, OCE_EXPECTED_REPO,
       OCE_EXPECTED_BRANCH, OCE_EXPECTED_COMMIT, OCE_EXPECTED_TREE
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # infrastructure/control-plane
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "tests"))

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

COMPOSE_FILE = BASE_DIR / "compose" / "compose.yml"
RUN_ID_RE = re.compile(r"^[0-9a-f]{12,}$")

# Truthful stage identity. Book 2's workflow leaves these as-is; the Book 3
# worker-fabric workflow sets OCE_BLOCK_LABEL=B3 and
# OCE_STAGE_LABEL=B3-WORKER-FABRIC-CLOSURE (+ OCE_BOOK_LABEL="Book 3") so the
# evidence is reported under the CORRECT book (defect 15: no B3 evidence is
# falsely labeled Book 2, and vice-versa).
def stage_label() -> str:
    return os.environ.get("OCE_STAGE_LABEL", "B2-CONTROL-PLANE-CLOSURE")


def block_label() -> str:
    return os.environ.get("OCE_BLOCK_LABEL", "B2")


def book_label() -> str:
    return os.environ.get("OCE_BOOK_LABEL", "Book 2")


class Fail(Exception):
    """Raised to fail the run with an explicit reason (FAIL/BLOCKED)."""

    def __init__(self, reason: str, rc: int = 1):
        super().__init__(reason)
        self.reason = reason
        self.rc = rc


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(args: list[str], cwd: Path = BASE_DIR) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                          text=True, timeout=60)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class Runner:
    """23-step evidence orchestration. Fail closed at every step."""

    def __init__(self, run_id: str, evidence: Path, ci_mode: bool):
        self.run_id = run_id
        self.evidence = evidence
        self.ci_mode = ci_mode
        self.log: list[str] = []
        self.pytest_rc = -1
        self.completed_normally = False

        self.repo = os.environ.get("GITHUB_REPOSITORY", "")
        self.ci_ref = os.environ.get("GITHUB_REF_NAME", "")
        self.branch = self._git_stdout(["branch", "--show-current"]) or self.ci_ref
        self.commit = self._git_stdout(["rev-parse", "HEAD"])
        self.tree = self._git_stdout(["rev-parse", "HEAD^{tree}"])
        self.origin_url = self._git_stdout(["remote", "get-url", "origin"])
        self.dirty_before = self._git_dirty()
        self.env_kind = "ci" if ci_mode else "local"

        self.ctx = {
            "run_id": run_id,
            "schema_version": SCHEMA_VERSION,
            "validator_version": VALIDATOR_VERSION,
            "repository": self.repo or b2_registry.EXPECTED_REPO,
            "branch": self.branch,
            "ci_ref": self.ci_ref,
            "implementation_commit": self.commit,
            "implementation_tree": self.tree,
            "environment": self.env_kind,
        }

    # -- helpers -----------------------------------------------------------

    def _git_stdout(self, args: list[str]) -> str:
        r = _git(args)
        return r.stdout.strip() if r.returncode == 0 else ""

    def _git_dirty(self) -> list[str]:
        r = _git(["status", "--porcelain"])
        return [l for l in r.stdout.splitlines() if l.strip()]

    def record(self, msg: str) -> None:
        self.log.append(msg)

    def _run(self, cmd: list[str], cwd: Path | None = None, env: dict | None = None,
             timeout: int = 600) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, cwd=str(cwd or BASE_DIR), env=env or os.environ,
                              capture_output=True, text=True, timeout=timeout)

    def _write_json(self, name: str, data: dict) -> None:
        (self.evidence / name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _env(self) -> dict:
        env = dict(os.environ)
        from oce_control import local_secrets as ls
        env["POSTGRES_PASSWORD"] = ls.ensure_runtime_secret()
        env["POSTGRES_DSN"] = ls.postgres_dsn()
        env["PYTHONPATH"] = str(BASE_DIR / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return env

    # -- steps -------------------------------------------------------------

    def step_identity(self) -> None:
        """Steps 1-6: validate run id, evidence dir, identity, cleanliness."""
        if not RUN_ID_RE.fullmatch(self.run_id or ""):
            raise Fail(f"BLOCKED: malformed OCE_RUN_ID {self.run_id!r}", rc=2)
        if self.repo and self.repo != EXPECTED_REPO:
            raise Fail(f"BLOCKED: repository {self.repo} != {EXPECTED_REPO}", rc=2)
        if self.ci_ref and self.ci_ref != EXPECTED_BRANCH:
            raise Fail(f"BLOCKED: branch {self.ci_ref} != {EXPECTED_BRANCH}", rc=2)
        if not self.commit or not self.tree:
            raise Fail("BLOCKED: could not resolve git commit/tree", rc=2)
        self.record(f"identity: repo={self.repo or EXPECTED_REPO} branch={self.branch} "
                    f"commit={self.commit} tree={self.tree} env={self.env_kind}")
        self._write_json("source-identity.json", {
            **self.ctx,
            "origin_url": self.origin_url,
            "expected_repository": EXPECTED_REPO,
            "expected_branch": EXPECTED_BRANCH,
            "observed_branch": self.branch,
            "trusted_ci_ref": self.ci_ref,
            "captured_at": now_iso(),
        })
        self._write_json("source-cleanliness.json", {
            "before": {"clean": not self.dirty_before, "dirty_files": self.dirty_before},
            "after": {"clean": None, "dirty_files": None},
            **self.ctx,
        })
        self.record("source-cleanliness: before "
                    + ("CLEAN" if not self.dirty_before else f"DIRTY {self.dirty_before}"))

    def step_tool_versions(self) -> None:
        """Step 7: record tool versions."""
        versions: dict[str, str] = {}
        tools = {"python": [sys.executable, "--version"],
                 "pytest": [sys.executable, "-m", "pytest", "--version"],
                 "docker": ["docker", "--version"],
                 "docker-compose": ["docker", "compose", "version"]}
        for tool, args in tools.items():
            try:
                r = self._run(args, timeout=60)
                versions[tool] = ((r.stdout or r.stderr).strip()
                                  if r.returncode == 0 else "unavailable")
            except (FileNotFoundError, OSError):
                versions[tool] = "unavailable"
        self._write_json("tool-versions.json", {"versions": versions, **self.ctx})
        self.record("tools: " + "; ".join(f"{k}={v[:40]}" for k, v in versions.items()))

    def step_compose_up(self) -> None:
        """Steps 8-9: start the compose stack; verify PostgreSQL + Redis readiness."""
        self.record("compose: starting stack (postgres authoritative, redis disposable)")
        import oce_b2_compose as oc
        try:
            oc.stack_up()
        except Exception as exc:
            raise Fail(f"FAIL: compose stack failed to become healthy: {exc}")
        self.record("compose: postgres + redis healthy")
        self._write_json("stack-readiness.json", {
            "postgres": "healthy", "redis": "healthy", **self.ctx})

    def step_migrations(self) -> None:
        """Step 10: apply numbered migrations; fail closed on any error."""
        env = self._env()
        # B4-CXR5R1: NO --db — a password-bearing DSN must never enter
        # process argv. The migration child resolves the governed connection
        # internally from its own pinned activation context.
        r = self._run([sys.executable, str(BASE_DIR / "scripts" / "migrate.py"),
                       "up"], env=env, timeout=600)
        applied = re.findall(r"applied (\d{4})", r.stdout or "")
        self._write_json("migration-results.json", {
            "ok": r.returncode == 0,
            "applied_versions": applied,
            "output": (r.stdout or "")[-4000:],
            **self.ctx,
        })
        if r.returncode != 0:
            raise Fail(f"FAIL: migrations failed rc={r.returncode}:\n{(r.stdout or '')[-1500:]}")
        self.record(f"migrations: ok ({len(applied)} applied)")

    def step_pytest(self) -> None:
        """Step 11: full suite with junit.xml + human-readable output."""
        self.record("pytest: running complete mandatory registry (zero skips in CI)")
        env = self._env()
        r = self._run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "-rs", "--tb=short",
             "-p", "no:cacheprovider",
             "--junitxml", str(self.evidence / "junit.xml")],
            env=env, timeout=3600)
        (self.evidence / "pytest-output.txt").write_text(r.stdout or "", encoding="utf-8")
        self.pytest_rc = r.returncode
        self.record(f"pytest: rc={self.pytest_rc}")

    def step_registry(self) -> None:
        """Step 12: junit -> totals, test-registry.json, per-category results."""
        import xml.etree.ElementTree as ET
        junit_path = self.evidence / "junit.xml"
        if not junit_path.exists():
            raise Fail("FAIL: junit.xml missing after pytest")
        root = ET.parse(str(junit_path)).getroot()
        suite = root.find("testsuite") or root
        testcases = list(suite.iter("testcase"))
        node_ids = [f"{tc.get('classname')}::{tc.get('name')}" for tc in testcases]
        skipped = [n for n, tc in zip(node_ids, testcases) if tc.find("skipped") is not None]
        failed = [n for n, tc in zip(node_ids, testcases) if tc.find("failure") is not None]
        errors = [n for n, tc in zip(node_ids, testcases) if tc.find("error") is not None]
        collected = int(suite.get("tests", len(testcases)))
        executed = collected - len(skipped)
        passed = executed - len(failed) - len(errors)

        cats: dict[str, dict] = {}
        for cat in expected_counts():
            cat_ids = [n for n in MANDATORY_TEST_IDS if category_of(n) == cat]
            ran = [n for n in cat_ids if n in node_ids]
            skipped_cat = [n for n in ran if n in skipped]
            failed_cat = [n for n in ran if n in failed]
            cats[cat] = {
                "expected": len(cat_ids),
                "executed": len(ran) - len(skipped_cat),
                "passed": len(ran) - len(skipped_cat) - len(failed_cat),
                "skipped": skipped_cat,
                "failed": failed_cat,
                "missing": [n for n in cat_ids if n not in node_ids],
                "ids": ran,
            }
            (self.evidence / ARTIFACT_CATEGORY_FILE[cat]).write_text(
                json.dumps({"category": cat, **cats[cat], **self.ctx}, indent=2),
                encoding="utf-8")

        self._write_json("test-registry.json", {
            "expected_total": len(MANDATORY_TEST_IDS),
            "collected_total": collected,
            "executed_total": executed,
            "passed_total": passed,
            "failed_total": len(failed),
            "error_total": len(errors),
            "skipped_total": len(skipped),
            "duplicate_ids": sorted({n for n in node_ids if node_ids.count(n) > 1}),
            "categories": cats,
            **self.ctx,
        })
        self.record(f"registry: collected={collected} executed={executed} "
                    f"passed={passed} failed={len(failed)} errors={len(errors)} "
                    f"skipped={len(skipped)}")

    def step_cleanup(self) -> None:
        """Steps 13-15 + 17: NORMAL cleanup BEFORE the gate; verified; blocks promotion."""
        self.record("cleanup: compose down (durable postgres volume preserved)")
        env = self._env()
        down = self._run(["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
                         env=env, timeout=600)
        containers = subprocess.run(
            ["docker", "ps", "-aq", "--filter", "name=b2-local"],
            capture_output=True, text=True, timeout=60).stdout.strip()
        net = subprocess.run(["docker", "network", "inspect", "b2_local"],
                             capture_output=True, text=True, timeout=60)
        vol_pg = subprocess.run(["docker", "volume", "inspect", "b2_local_postgres_data"],
                                capture_output=True, text=True, timeout=60)
        vol_redis = subprocess.run(["docker", "volume", "inspect", "b2_local_redis_data"],
                                   capture_output=True, text=True, timeout=60)
        removed = (down.returncode == 0 and not containers and net.returncode != 0)
        cleanup = {
            "compose_down_rc": down.returncode,
            "containers_remaining": containers.splitlines() or [],
            "containers_removed": not containers,
            "network_present": net.returncode == 0,
            "networks_removed": net.returncode != 0,
            "durable_postgres_volume_preserved": vol_pg.returncode == 0,
            "redis_volume_state": "present" if vol_redis.returncode == 0 else "absent",
            "removed": removed,
            "checked_at": now_iso(),
            **self.ctx,
        }
        self._write_json("cleanup-results.json", cleanup)
        self.record("cleanup: " + ("OK (containers+networks removed, postgres volume preserved)"
                                   if removed else "FAILED"))
        if not removed:
            raise Fail(f"FAIL: cleanup not verified: {json.dumps(cleanup)}")

    def step_source_after(self) -> None:
        """Step 16: source cleanliness after execution."""
        dirty = self._git_dirty()
        data = json.loads((self.evidence / "source-cleanliness.json").read_text())
        data["after"] = {"clean": not dirty, "dirty_files": dirty}
        self._write_json("source-cleanliness.json", data)
        self.record("source-cleanliness: after " + ("CLEAN" if not dirty else f"DIRTY {dirty}"))

    def step_gate(self) -> None:
        """Step 18: independent gate (pass A)."""
        self.record("gate: independent-gate-b2.py")
        r = self._run([sys.executable, str(BASE_DIR / "scripts" / "independent-gate-b2.py"),
                       str(self.evidence), str(self.pytest_rc)])
        sys.stdout.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")
        self.gate_rc = r.returncode
        if self.gate_rc != 0:
            raise Fail(f"FAIL: independent gate rejected the run (rc={self.gate_rc})")

    def step_close_logs(self) -> None:
        """Step 19: close all mutable logs — stage-log.txt is frozen NOW,
        before the manifest is generated, so its hash describes the final file."""
        (self.evidence / "stage-log.txt").write_text(
            "\n".join(self.log) + "\n", encoding="utf-8")

    def step_stage_status(self) -> None:
        """Step 20: final stage status reflecting the actual result."""
        gate = json.loads((self.evidence / "independent-gate.json").read_text())
        status = "PASS" if gate.get("gate") == "PASS" else "FAIL"
        self._write_json("stage-status.json", {
            "block": block_label(),
            "stage": stage_label(),
            "stage_status": status,
            "gate_status": status,
            "pytest_exit": self.pytest_rc,
            "exit_status": 0 if status == "PASS" else 1,
            "gate_checks": gate.get("checks", []),
            "cloud_mutations": 0,
            "cloud_cost_state": "ZERO",
            "cloud_deployment_state": "NOT_DEPLOYED",
            "cloud_activation_state": "DEFERRED_BY_OPERATOR",
            "recorded_at": now_iso(),
            **self.ctx,
        })

    def step_summary(self) -> None:
        """validation-summary.md — human-readable reconciliation (pre-manifest)."""
        reg = json.loads((self.evidence / "test-registry.json").read_text())
        stage = json.loads((self.evidence / "stage-status.json").read_text())
        cleanup = json.loads((self.evidence / "cleanup-results.json").read_text())
        lines = [
            f"# OCE {book_label()} — Validation Summary",
            "",
            f"- Run ID: `{self.run_id}`",
            f"- Repository: `{self.repo or EXPECTED_REPO}`",
            f"- Branch (observed): `{self.branch}` / trusted CI ref: `{self.ci_ref or 'n/a'}`",
            f"- Implementation commit: `{self.commit}`",
            f"- Implementation tree: `{self.tree}`",
            f"- Schema version: `{SCHEMA_VERSION}` / validator: `{VALIDATOR_VERSION}`",
            f"- Environment: `{self.env_kind}`",
            f"- Stage status: `{stage['stage_status']}`",
            f"- Tests: collected={reg['collected_total']} executed={reg['executed_total']} "
            f"passed={reg['passed_total']} failed={reg['failed_total']} "
            f"errors={reg['error_total']} skipped={reg['skipped_total']}",
            "- Per category:",
        ]
        for cat, c in reg["categories"].items():
            lines.append(f"  - {cat}: expected={c['expected']} executed={c['executed']} "
                         f"passed={c['passed']} skipped={len(c['skipped'])} failed={len(c['failed'])}")
        lines.append(f"- Cleanup: containers_removed={cleanup['containers_removed']} "
                     f"networks_removed={cleanup['networks_removed']} "
                     f"postgres_volume_preserved={cleanup['durable_postgres_volume_preserved']}")
        lines.append("- Cloud: mutations=0, recurring cost=$0, not deployed, deferred")
        (self.evidence / "validation-summary.md").write_text("\n".join(lines) + "\n",
                                                             encoding="utf-8")

    def step_manifest(self) -> None:
        """Step 21: final evidence manifest GENERATED LAST (after stage-log closes)."""
        manifest = {
            "manifest_version": "1.0.0",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "generated_at": now_iso(),
            "files": {},
        }
        for name in sorted(p.name for p in self.evidence.iterdir() if p.is_file()):
            if name == "evidence-manifest.json":
                continue  # generated last; never self-referential
            manifest["files"][name] = {
                "sha256": sha256_file(self.evidence / name),
                "size": (self.evidence / name).stat().st_size,
            }
        self._write_json("evidence-manifest.json", manifest)
        print("manifest: generated last, hashing all final files")

    def step_final_verify(self) -> None:
        """Steps 22-23: read-only final package verifier (gate --final).
        NOTE: no record() here — the stage log was closed in step 19 and
        the manifest was generated in step 21; nothing mutable may follow."""
        r = self._run([sys.executable, str(BASE_DIR / "scripts" / "independent-gate-b2.py"),
                       "--final", str(self.evidence), str(self.pytest_rc)])
        sys.stdout.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")
        if r.returncode != 0:
            raise Fail(f"FAIL: final package verification rejected the run (rc={r.returncode})")

    # -- orchestration -----------------------------------------------------

    def run(self) -> int:
        steps = [
            self.step_identity,
            self.step_tool_versions,
            self.step_compose_up,
            self.step_migrations,
            self.step_pytest,
            self.step_registry,
            self.step_cleanup,
            self.step_source_after,
            self.step_gate,
            self.step_close_logs,
            self.step_stage_status,
            self.step_summary,
            self.step_manifest,
            self.step_final_verify,
        ]
        for step in steps:
            self.record(f"[{step.__name__}]")
            step()
        self.completed_normally = True
        print(f"GATE PASS: {self.run_id} — {book_label()} validation succeeded, "
              f"evidence in {self.evidence}")
        return 0


def write_failure_evidence(evidence: Path, run_id: str, ctx: dict, reason: str,
                           log: list[str], rc: int) -> None:
    """Write truthful FAIL/BLOCKED evidence (stage-status + manifest)."""
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "stage-log.txt").write_text("\n".join(log + [f"FAILURE: {reason}"]) + "\n",
                                            encoding="utf-8")
    status = "BLOCKED" if rc == 2 else "FAIL"
    stage = {
        "block": block_label(),
        "stage": stage_label(),
        "stage_status": status,
        "gate_status": status,
        "failure": reason,
        "pytest_exit": -1,
        "exit_status": rc,
        "cloud_mutations": 0,
        "cloud_cost_state": "ZERO",
        "cloud_deployment_state": "NOT_DEPLOYED",
        "cloud_activation_state": "DEFERRED_BY_OPERATOR",
        "recorded_at": now_iso(),
        **ctx,
    }
    (evidence / "stage-status.json").write_text(json.dumps(stage, indent=2),
                                                encoding="utf-8")
    manifest = {"manifest_version": "1.0.0", "run_id": run_id, "files": {}}
    for name in sorted(p.name for p in evidence.iterdir() if p.is_file()):
        if name == "evidence-manifest.json":
            continue
        manifest["files"][name] = {
            "sha256": sha256_file(evidence / name),
            "size": (evidence / name).stat().st_size,
        }
    (evidence / "evidence-manifest.json").write_text(json.dumps(manifest, indent=2),
                                                     encoding="utf-8")


def main() -> int:
    run_id = os.environ.get("OCE_RUN_ID", "")
    import tempfile
    ev_arg = os.environ.get("OCE_EVIDENCE_DIR")
    evidence = Path(ev_arg).resolve() if ev_arg else Path(
        tempfile.gettempdir()) / f"oce-b2-evidence-{run_id or 'x'}"
    ci_mode = os.environ.get("OCE_CI_MODE") == "true"
    evidence.mkdir(parents=True, exist_ok=True)

    # Fail closed: evidence must live OUTSIDE the repository.
    try:
        evidence.relative_to(BASE_DIR)
        inside = True
    except ValueError:
        inside = False
    if inside:
        print("FATAL: OCE_EVIDENCE_DIR must be outside the repository", file=sys.stderr)
        return 2

    runner = Runner(run_id, evidence, ci_mode)
    try:
        return runner.run()
    except Fail as exc:
        print(f"{exc.reason}", file=sys.stderr)
        # Best-effort abnormal cleanup (only the NORMAL path can block promotion).
        try:
            env = dict(os.environ)
            subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
                           cwd=str(BASE_DIR), env=env, capture_output=True, text=True,
                           timeout=300)
        except Exception:
            pass
        write_failure_evidence(evidence, run_id, runner.ctx, exc.reason,
                               runner.log, exc.rc)
        print(f"failure evidence written to {evidence}", file=sys.stderr)
        return exc.rc
    except Exception as exc:  # unexpected — still produce truthful evidence
        print(f"FAIL: unexpected error: {exc!r}", file=sys.stderr)
        try:
            subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
                           cwd=str(BASE_DIR), capture_output=True, text=True, timeout=300)
        except Exception:
            pass
        write_failure_evidence(evidence, run_id, runner.ctx, f"unexpected error: {exc!r}",
                               runner.log, 1)
        return 1


if __name__ == "__main__":
    sys.exit(main())
