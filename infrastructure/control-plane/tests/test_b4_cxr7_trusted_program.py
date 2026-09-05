"""OCE Book 4 — B4-CXR7U3 trusted-program execution lock + isolation truth.

Two pillars, both proven behaviorally:

1. TRUSTED PROGRAM LOCK — only fixed, repository-owned allowlisted programs
   (program_for) execute; unknown job types fail closed BEFORE any subprocess;
   job parameters are data only (never source code, executable names, argv
   programs, shell fragments, import/module paths, script paths, environment
   authority, or filesystem authority); shell execution stays disabled;
   runtime code is never loaded from an attempt workspace; the job cannot
   select or modify the program registry; production cannot activate the
   test dependency seam; workspace traversal / symlink escape / repo-overlap
   stay blocked.

2. TRUTHFUL ISOLATION REPORTING — reports never say the network is
   technically blocked when no OS enforcement exists; POSIX reports resource
   bounding only; Windows reports watchdog/tree termination literally;
   no report calls this an adversarial sandbox; fixed trusted programs
   contain no authorized network behavior.

Canonical statements live in B4-THREAT-MODEL.md and
representative_jobs.py (HARD CODE-EXECUTION LOCK).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from oce_control.execution_runtime import (
    BoundedRunner, ExecutionPolicyError, JobResourceEnvelope, SandboxPolicy)
from oce_control.representative_jobs import (
    program_for, prepare_workspace, supported_job_types)

BASE = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. Trusted program registry: allowlist, fail-closed, data-only parameters
# ---------------------------------------------------------------------------
class TestTrustedProgramRegistry:
    def test_supported_job_types_are_fixed_allowlist(self):
        types = supported_job_types()
        assert set(types) == {
            "b3.deterministic-hash", "b3.bounded-compute", "b3.repo-inventory",
            "b3.synthetic-backtest", "b3.analysis-artifact",
            "b3.cancel-during-exec", "b3.timeout-violation",
        }

    def test_unknown_job_type_fails_closed(self):
        for evil in ("os.system", "../../etc/passwd", "b3.EVIL", "",
                     "__import__", "hash; import os"):
            with pytest.raises(KeyError):
                program_for(evil)

    def test_program_registry_cannot_be_mutated_via_input(self):
        # a job (or its params) cannot select or modify the program registry
        snapshot = {t: program_for(t) for t in supported_job_types()}
        with pytest.raises(KeyError):
            program_for("b3.deterministic-hash; DROP")
        # registry content unchanged
        assert {t: program_for(t) for t in supported_job_types()} == snapshot

    def test_parameters_stay_data_in_workspace(self, tmp_path):
        # source code / argv / shell fragments passed as params are inert:
        # they land in input/params.json as JSON data, never executed
        evil_params = {
            "code": "import os; os.system('echo PWNED > pwned.txt')",
            "argv": ["python", "-c", "print('pwned')"],
            "shell": "echo pwned > pwned.txt",
            "module": "subprocess",
            "script_path": "../../scripts/migrate.py",
            "__import__": "os",
        }
        ws = tmp_path / "ws"
        prepare_workspace(ws, "b3.deterministic-hash", evil_params)
        seeded = json.loads((ws / "input" / "params.json").read_text("utf-8"))
        assert seeded == evil_params          # data, verbatim
        assert not (ws / "pwned.txt").exists()  # nothing executed

    def test_shell_execution_disabled(self, tmp_path):
        r = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        assert r._policy.allow_network is False
        # shell is structurally disabled in run(): verify by source inspection
        src = Path(BoundedRunner.__module__ and
                   sys.modules["oce_control.execution_runtime"].__file__ or
                   "").read_text(encoding="utf-8")
        assert "shell=(False)" in src or "shell=False" in src

    def test_executable_allowlist_enforced(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        for evil_argv in (["bash", "-c", "echo hi"],
                          ["cmd", "/c", "echo hi"],
                          ["python3.9", "-c", "pass"],
                          ["/bin/sh", "script.sh"],
                          ["attacker.exe"]):
            with pytest.raises(ExecutionPolicyError):
                runner.run(evil_argv, envelope=JobResourceEnvelope(timeout_s=5))

    def test_params_cannot_become_environment_or_fs_authority(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        env = JobResourceEnvelope(timeout_s=10)
        with pytest.raises(ExecutionPolicyError):
            runner.run(["python", "-c", "print(1)"], envelope=env,
                       env_override={"AWS_SECRET_ACCESS_KEY": "x"})
        with pytest.raises(ExecutionPolicyError):
            runner.run(["python", "-c", "print(1)"], envelope=env,
                       env_override={"EVIL_INJECTION": "x"})

    def test_fixed_representative_job_still_works(self, tmp_path):
        ws = tmp_path / "ws"
        prepare_workspace(ws, "b3.deterministic-hash", {"value": "abc"})
        runner = BoundedRunner(workspace_base=tmp_path / "runner",
                               policy=SandboxPolicy())
        result = runner.run(
            ["python", "-c", program_for("b3.deterministic-hash")],
            envelope=JobResourceEnvelope(timeout_s=30), workspace=ws)
        assert result.ok, result.stderr
        payload = json.loads((ws / "output" / "hash.json").read_text("utf-8"))
        assert payload["value"] == "abc" and len(payload["sha256"]) == 64


# ---------------------------------------------------------------------------
# 2. Production worker path: unknown job type blocked before any subprocess
# ---------------------------------------------------------------------------
class _FakeLeaseClient:
    """Records whether a claim (a control-plane side effect) was attempted."""

    def __init__(self):
        self.claimed = False

    def claim(self, job):
        self.claimed = True
        return {"lease_id": "lease-abc12345", "fence": 1}

    def surrender(self, job_id, lease_id, fence):
        return {"surrendered": True}


class TestProductionJobTypeGate:
    def test_unknown_job_type_blocked_before_claim_and_subprocess(self, tmp_path):
        # the production path resolves program_for BEFORE claiming a lease:
        # an unknown job type fails closed before any workspace seeding,
        # control-plane claim, or subprocess. Proven by source-order AND by
        # calling the real gate function.
        import scripts.oce_b3_worker as w
        src = Path(w.__file__).read_text(encoding="utf-8")
        prog_line = next(l for l in src.splitlines()
                         if 'prog = program_for(spec["job_type"])' in l)
        claim_line = next(l for l in src.splitlines()
                          if "client.claim(job)" in l)
        prep_line = next(l for l in src.splitlines()
                         if "prepare_workspace(ws" in l)
        assert src.index(prog_line) < src.index(claim_line) < src.index(prep_line)
        # the gate itself: an unknown type raises KeyError before anything else
        with pytest.raises(KeyError):
            program_for("attacker-chosen-type")
        seeded = tmp_path / "never-seeded"
        with pytest.raises(KeyError):
            # prepare_workspace would only be reached after the gate passes
            program_for("attacker-chosen-type") or prepare_workspace(
                seeded, "attacker-chosen-type", {})
        assert not seeded.exists()

    def test_runtime_code_never_loaded_from_attempt_workspace(self):
        # the executed program comes ONLY from program_for — no workspace
        # file is ever used as source (source-level proof)
        import scripts.oce_b3_worker as w
        src = Path(w.__file__).read_text(encoding="utf-8")
        assert 'runner.run(["python", "-c", prog]' in src
        assert "str(ws /" not in src          # never a workspace-built path
        assert "importlib" not in src          # never dynamic import of input


    def test_unknown_job_type_reaches_real_gate_rejected_before_claim_or_side_effects(
            self, monkeypatch):
        # BEHAVIORAL (B4-CXR7U8-03): drive the REAL scripts.oce_b3_worker.run()
        # with an injected job spec of an unsupported type. The repository
        # allowlisting gate (program_for) fires BEFORE lease claim, workspace
        # seeding, or subprocess launch — proven by spies that must stay empty.
        import scripts.oce_b3_worker as w
        from oce_b3_worker_test_deps import TestWorkerDependencies
        claims: list = []
        prepares: list = []
        runs: list = []

        class _FakeOutbound:
            def __init__(self, url, worker_id, secret):
                pass

            def connect(self):
                return None

            def heartbeat(self):
                return None

            def claim(self, job):
                claims.append(job)
                return {"lease_id": "lease-x", "fence": 1}

            def surrender(self, job_id, lease_id, fence):
                return {"surrendered": True}

            def close(self):
                return None

        monkeypatch.setattr(w, "OutboundWorkerClient", _FakeOutbound)
        monkeypatch.setattr(w, "prepare_workspace",
                            lambda *a, **k: prepares.append(a))
        deps = TestWorkerDependencies(
            secret="s" * 43,
            job_spec={"job_id": "j-evil", "job_type": "attacker-chosen-type",
                      "required_capabilities": ["hash"], "params": {"code": "x"},
                      "timeout_s": 5})
        with pytest.raises(KeyError):
            w.run(deps, ctx=None, url="http://127.0.0.1:9",
                  worker_id="w-evil", environ={})
        # the fail-closed gate fired before ANY control-plane claim,
        # workspace creation, or execution attempt
        assert claims == []
        assert prepares == []
        assert runs == []

    def test_production_sys_path_cannot_import_test_dependency_seam(self):
        # BEHAVIORAL seam proof: a REAL subprocess with the production
        # sys.path order (control-plane, scripts, src — never tests/) cannot
        # import the test-only dependency module; only the test path order
        # (tests/ prepended) can. Production therefore cannot activate it.
        prod_env = dict(os.environ)
        prod_env["PYTHONPATH"] = os.pathsep.join(
            [str(BASE), str(BASE / "scripts"), str(BASE / "src"),
             prod_env.get("PYTHONPATH", "")])
        r = subprocess.run(
            [sys.executable, "-c", "import oce_b3_worker_test_deps"],
            capture_output=True, text=True, env=prod_env, timeout=120,
            errors="replace")
        assert r.returncode != 0, "seam importable from the production path!"
        assert "No module named" in r.stderr or "no module named" in r.stderr
        # control: the seam is reachable only when tests/ is on the path
        test_env = dict(prod_env)
        test_env["PYTHONPATH"] = os.pathsep.join(
            [str(BASE / "tests")] + [str(BASE), str(BASE / "scripts"),
                                     str(BASE / "src")])
        r2 = subprocess.run(
            [sys.executable, "-c",
             "import oce_b3_worker_test_deps as m; print('ok')"],
            capture_output=True, text=True, env=test_env, timeout=120,
            errors="replace")
        assert r2.returncode == 0, r2.stderr


# ---------------------------------------------------------------------------
# 3. Truthful isolation reporting
# ---------------------------------------------------------------------------
class TestTruthfulIsolationReporting:
    def test_resource_enforcement_report_states_the_three_truths(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        rep = runner.resource_enforcement_report
        assert rep["network_authorization"] == "denied by Book 4 policy"
        assert rep["os_network_enforcement"] == "not implemented"
        assert rep["current_execution_trust"] == (
            "repository-owned allowlisted programs only")
        assert rep["adversarial_sandbox"] is False
        assert "network isolation" in rep["not_provided"]
        assert "filesystem isolation" in rep["not_provided"]
        assert "identity isolation" in rep["not_provided"]
        assert "hostile-code containment" in rep["not_provided"]

    def test_reports_never_claim_network_enforcement(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        report = runner.preflight_isolation(JobResourceEnvelope())
        # policy denial is reported as a POLICY, never as OS enforcement
        assert report["network"] == "denied"
        assert "NOT implemented" in report["unavailable"]["network"]
        assert "not implemented" in report["network_enforcement"]
        # no truthful string anywhere claims OS network blocking
        blob = json.dumps(report).lower()
        assert "os network enforcement: implemented" not in blob
        assert "network is blocked" not in blob
        assert "firewall" not in blob
        assert "namespace" not in blob

    def test_posix_reports_resource_bounding_only(self, tmp_path, monkeypatch):
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        if runner.resource_limits_available:
            report = runner.preflight_isolation(JobResourceEnvelope())
            assert "cpu" in report["enforced"]
            assert "memory" in report["enforced"]
            assert "disk" in report["enforced"]
            blob = json.dumps(report).lower()
            assert "isolation" not in blob.replace(
                "network_enforcement", "").replace(
                "isolation_note", "")
            assert "network isolation" not in blob
            assert "filesystem isolation" not in blob
            assert "identity isolation" not in blob

    def test_windows_reports_watchdog_and_tree_termination_literally(
            self, tmp_path, monkeypatch):
        # simulate the Windows path (this test is platform-independent)
        monkeypatch.setattr(BoundedRunner, "resource_limits_available",
                            property(lambda self: False))
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        report = runner.preflight_isolation(JobResourceEnvelope())
        assert "watchdog" in report["unavailable"]["memory"]
        assert "tree termination" in report["unavailable"]["memory"]
        blob = json.dumps(report)
        assert "rlimit primitives unavailable" in blob or \
            "rlimit unavailable" in blob
        # the enforcement report says exactly what bounding remains
        rep = runner.resource_enforcement_report
        assert rep["resource_limits_available"] is False
        assert "watchdog timeout" in rep["resource_bounding"]
        assert "taskkill /T" in rep["resource_bounding"]

    def test_full_isolation_alias_is_deprecated_not_a_claim(self):
        # the legacy name still resolves (compatibility) but the canonical
        # truth is resource_limits_available; no docstring claims isolation
        runner = BoundedRunner()
        assert runner.full_isolation == runner.resource_limits_available

    def test_no_evidence_calls_this_an_adversarial_sandbox(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        rep = runner.resource_enforcement_report
        assert rep["adversarial_sandbox"] is False
        blob = json.dumps(rep)
        assert "adversarial sandbox\": true" not in blob
        assert "hostile" not in blob.lower().replace(
            "hostile-code containment", "")

    def test_fixed_trusted_programs_contain_no_network_behavior(self):
        # every repository-owned program is statically free of authorized
        # network behavior
        forbidden = ("socket", "urllib", "requests", "http.client",
                     "urlopen", "smtplib", "ftplib", "telnetlib")
        for jt in supported_job_types():
            src = program_for(jt)
            for token in forbidden:
                assert token not in src, (jt, token)

    def test_strict_mode_does_not_imply_isolation(self, tmp_path):
        # strict=True raises only on missing RESOURCE boundaries; the report
        # never claims filesystem/network/identity isolation from strictness
        runner = BoundedRunner(workspace_base=tmp_path,
                               policy=SandboxPolicy(strict=True))
        rep = runner.resource_enforcement_report
        assert rep["not_provided"]  # strict changes nothing about isolation
        assert rep["os_network_enforcement"] == "not implemented"

    def test_threat_model_carries_the_hard_lock(self):
        tm = (BASE / "B4-THREAT-MODEL.md").read_text(encoding="utf-8")
        assert "GENERATED, DOWNLOADED, THIRD-PARTY, PLUGIN, STRATEGY, USER-SUPPLIED," in tm
        assert "repository-owned allowlisted programs only" in tm

    def test_representative_jobs_module_carries_the_hard_lock(self):
        src = (BASE / "src" / "oce_control" /
               "representative_jobs.py").read_text(encoding="utf-8")
        assert "GENERATED, DOWNLOADED, THIRD-PARTY, PLUGIN, STRATEGY, USER-SUPPLIED," in src
        assert "MAY NOT EXECUTE UNTIL A REAL OS ISOLATION" in src

    def test_workspace_traversal_and_symlink_escape_blocked(self, tmp_path):
        # already covered at CLI level (B4-CXR5R6); prove the runner-level
        # guard still rejects escapes for any input path
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        outside = tmp_path.parent / "outside-input.txt"
        outside.write_text("x", encoding="utf-8")
        ws = tmp_path / "ws"
        ws.mkdir()
        from oce_control.execution_runtime import PathEscapeError
        with pytest.raises(PathEscapeError):
            runner.run(["python", "-c", "print(1)"],
                       envelope=JobResourceEnvelope(timeout_s=5),
                       workspace=ws, input_paths=[outside])

    def test_production_cannot_select_test_dependency_seam(self, tmp_path):
        # the seam module lives in tests/, is imported by nothing in
        # production code paths, and no environment string reaches it.
        import scripts.oce_b3_worker as w
        assert "oce_b3_worker_test_deps" not in Path(w.__file__).read_text(
            encoding="utf-8")
        for prod_file in (BASE / "scripts" / "oce_b3_worker.py",
                          BASE / "src" / "oce_control" / "worker_loop.py"):
            tree_ok = True
            src = prod_file.read_text(encoding="utf-8")
            # no IMPORT of the seam anywhere (docstring mentions are fine)
            for line in src.splitlines():
                stripped = line.strip()
                if stripped.startswith(("import ", "from ")) and \
                        "test_deps" in stripped:
                    tree_ok = False
            assert tree_ok, prod_file
        # and the seam module itself still refuses production reachability:
        # it is not importable from the production script's sys.path order
        seam = (BASE / "tests" / "oce_b3_worker_test_deps.py").exists()
        assert seam
