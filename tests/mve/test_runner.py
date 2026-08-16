"""Runner orchestration + persistence tests (R0.5.6/7/8/9/10)."""
import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from mve import runner as mvr  # noqa: E402
from mve.persistence import PersistenceError, persist_run, sha256_file  # noqa: E402

RUNNER = os.path.join(REPO_ROOT, "research", "mve", "run_mve_research.py")


def run_cli(*args, **kw):
    return subprocess.run(
        [sys.executable, RUNNER, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        **kw,
    )


def make_config(tmp_path, **overrides):
    base = dict(
        task="diagnostic",
        phase_id=None,
        asset="EURUSD",
        timeframe="H1",
        start="2023-08-01",
        end="2023-08-31",
        seed=42,
        output_root=str(tmp_path / "out"),
        repo_root=REPO_ROOT,
    )
    base.update(overrides)
    return mvr.ResearchConfig(**base)


# ---------------------------------------------------------------------------
# CLI parsing + phase isolation + no auto-advance
# ---------------------------------------------------------------------------

def test_cli_dry_run_phase4():
    p = run_cli("--phase", "4", "--dry-run")
    assert p.returncode == 0
    assert "PHASE4" in p.stdout
    assert "BLOCKED_SCIENTIFIC_IMPLEMENTATION" in p.stdout


def test_cli_invalid_phase_fails():
    p = run_cli("--phase", "9")
    assert p.returncode != 0


def test_cli_requires_phase_or_diagnostic():
    p = run_cli()
    assert p.returncode != 0


def test_phase4_fails_closed_no_output_written(tmp_path):
    p = run_cli("--phase", "4", "--output", str(tmp_path / "o"))
    assert p.returncode == 1
    assert "BLOCKED_SCIENTIFIC_IMPLEMENTATION" in p.stdout
    # No phase4 output, and certainly no auto-advance to phase5.
    assert not os.path.exists(os.path.join(REPO_ROOT, str(tmp_path / "o"), "phase4"))
    assert not os.path.exists(os.path.join(REPO_ROOT, str(tmp_path / "o"), "phase5"))


def test_phase5_prerequisite_gate(tmp_path):
    # Phase 5 requires completed Phase 4 artifacts, which do not exist.
    p = run_cli("--phase", "5", "--output", str(tmp_path / "o"))
    assert p.returncode == 1
    assert "requires completed phase artifacts" in p.stdout


def test_phase_isolation_never_advances(tmp_path):
    p = run_cli("--phase", "6", "--output", str(tmp_path / "o"))
    assert p.returncode == 1
    # Even a blocked/advanced phase must not create downstream phase dirs.
    for ph in ["phase4", "phase5", "phase6", "phase7"]:
        assert not os.path.exists(os.path.join(REPO_ROOT, str(tmp_path / "o"), ph))


# ---------------------------------------------------------------------------
# Persistence + manifest + config hashing
# ---------------------------------------------------------------------------

def test_diagnostic_persists_nonempty_outputs(tmp_path):
    cfg = make_config(tmp_path)
    result = mvr.run_diagnostic(cfg)
    out = result["output_dir"]
    for f in ["DIAGNOSTIC_OHLCV.csv", "DIAGNOSTIC_SUMMARY.json", "DIAGNOSTIC_SUMMARY.md", "RUN_MANIFEST.json"]:
        p = os.path.join(out, f)
        assert os.path.exists(p), f
        assert os.path.getsize(p) > 0, f
    # CSV has real rows.
    with open(os.path.join(out, "DIAGNOSTIC_OHLCV.csv")) as f:
        assert len(f.readlines()) > 2


def test_manifest_complete_provenance(tmp_path):
    cfg = make_config(tmp_path)
    result = mvr.run_diagnostic(cfg)
    m = json.load(open(os.path.join(result["output_dir"], "RUN_MANIFEST.json")))
    for key in [
        "git_sha", "branch", "requested_phase", "canonical_data_path",
        "canonical_sha256", "m5_row_count", "h1_row_count", "h1_fingerprint",
        "slice_start", "slice_end", "config_hash", "deterministic_seed",
        "input_artifact_hashes", "output_hashes", "execution_timestamp",
        "runner_version", "runner_status",
    ]:
        assert key in m, key
    assert len(m["git_sha"]) == 40
    assert m["canonical_sha256"].startswith("630b8a40")
    assert m["m5_row_count"] == 216820
    assert m["h1_row_count"] == 18089


def test_config_hash_changes_with_config(tmp_path):
    a = make_config(tmp_path, seed=42)
    b = make_config(tmp_path, seed=43)
    assert a.config_hash() != b.config_hash()
    c = make_config(tmp_path, start="2023-08-02")
    assert a.config_hash() != c.config_hash()


def test_output_hashes_match_recomputed_files(tmp_path):
    cfg = make_config(tmp_path)
    result = mvr.run_diagnostic(cfg)
    out = result["output_dir"]
    m = json.load(open(os.path.join(out, "RUN_MANIFEST.json")))
    for fname, recorded in m["output_hashes"].items():
        recomputed = sha256_file(os.path.join(out, fname))
        assert recorded == recomputed, fname


def test_stale_artifact_rejection(tmp_path):
    out = tmp_path / "x"
    persist_run(str(out), "hashA", {"a.txt": "hello"}, {"config_hash": "hashA"})
    # Same config hash -> allowed overwrite.
    persist_run(str(out), "hashA", {"a.txt": "hello"}, {"config_hash": "hashA"})
    # Different config hash -> refuse.
    with pytest.raises(PersistenceError, match="Refusing to overwrite"):
        persist_run(str(out), "hashB", {"a.txt": "hello"}, {"config_hash": "hashB"})


def test_missing_canonical_data_fails(tmp_path):
    cfg = make_config(tmp_path, repo_root=str(tmp_path / "empty"))
    os.makedirs(cfg.repo_root, exist_ok=True)
    with pytest.raises(mvr.RunnerError, match="prerequisites missing"):
        mvr.run_diagnostic(cfg)


def test_corrupt_prior_artifact_fails(tmp_path):
    # Phase 5 with a prior phase4 manifest that is corrupt JSON must fail closed.
    p4 = os.path.join(REPO_ROOT, "results", "mve", "phase4")
    os.makedirs(p4, exist_ok=True)
    with open(os.path.join(p4, "RUN_MANIFEST.json"), "w") as f:
        f.write("{ not valid json")
    try:
        cfg = make_config(tmp_path, task="phase", phase_id=5)
        with pytest.raises(mvr.RunnerError):
            mvr.execute_phase(cfg)
    finally:
        os.remove(os.path.join(p4, "RUN_MANIFEST.json"))
        try:
            os.rmdir(p4)
        except OSError:
            pass


def test_diagnostic_rerun_deterministic(tmp_path):
    cfg = make_config(tmp_path)
    r1 = mvr.run_diagnostic(cfg)
    out = r1["output_dir"]

    def read_artifacts():
        return {
            f: open(os.path.join(out, f), "rb").read()
            for f in ["DIAGNOSTIC_OHLCV.csv", "DIAGNOSTIC_SUMMARY.json", "DIAGNOSTIC_SUMMARY.md"]
        }

    a1 = read_artifacts()
    r2 = mvr.run_diagnostic(cfg)
    a2 = read_artifacts()

    # Data artifacts byte-identical.
    assert a1 == a2

    # Manifests equal except execution_timestamp.
    m1 = json.load(open(os.path.join(out, "RUN_MANIFEST.json")))
    # re-run then compare
    r2 = mvr.run_diagnostic(cfg)
    m2 = json.load(open(os.path.join(out, "RUN_MANIFEST.json")))
    t1 = m1.pop("execution_timestamp")
    t2 = m2.pop("execution_timestamp")
    assert m1 == m2
    assert t1 != t2  # timestamps differ, content does not
