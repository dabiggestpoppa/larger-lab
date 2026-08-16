"""Generate R0.5 runner outputs: failure-mode results, diagnostic evidence,
determinism report, and phase dependency map."""
import json
import os
import subprocess
import sys

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from mve import runner as mvr  # noqa: E402
from mve.persistence import sha256_file  # noqa: E402

OUT = os.path.join(REPO_ROOT, "research", "mve")
RUNNER = os.path.join(REPO_ROOT, "research", "mve", "run_mve_research.py")


def cli(*args):
    p = subprocess.run(
        [sys.executable, RUNNER, *args],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def main():
    results = {}

    # --- Failure modes (all must fail closed) ---
    rc, msg = cli("--phase", "9")
    results["invalid_phase"] = {"exit_code": rc, "fail_closed": rc != 0, "message": msg[:200]}

    rc, msg = cli("--phase", "5")
    results["missing_phase5_prerequisite"] = {"exit_code": rc, "fail_closed": rc != 0, "message": msg[:200]}

    rc, msg = cli("--diagnostic", "--slice", "2026-01-01,2026-01-31")
    results["holdout_range_rejected"] = {"exit_code": rc, "fail_closed": rc != 0, "message": msg[:200]}

    # missing canonical data (empty repo root)
    cfg = mvr.ResearchConfig("diagnostic", None, "EURUSD", "H1", "2023-08-01", "2023-08-31", 42, "results/mve", str(REPO_ROOT + "_does_not_exist"))
    try:
        mvr.run_diagnostic(cfg)
        results["missing_canonical_data"] = {"fail_closed": False, "message": "unexpectedly succeeded"}
    except mvr.RunnerError as e:
        results["missing_canonical_data"] = {"fail_closed": True, "message": str(e)[:200]}

    # hash mismatch: fake spec with wrong hash
    import mve.data_loader as dl
    bad_spec = dl.CanonicalDataSpec(
        "EURUSD", dl.CANONICAL_EURUSD.relpath, "0" * 64, dl.CANONICAL_EURUSD.size_bytes,
        dl.CANONICAL_EURUSD.rows, "", "", "UTC", "time", "timestamp", "open", "high", "low", "close",
        ("real_volume", "tick_volume"),
    )
    try:
        dl.load_canonical_m5(bad_spec, repo_root=REPO_ROOT)
        results["hash_mismatch"] = {"fail_closed": False, "message": "unexpectedly succeeded"}
    except dl.DataPipelineError as e:
        results["hash_mismatch"] = {"fail_closed": True, "message": str(e)[:200]}

    # stale artifact mismatch
    import tempfile
    from mve.persistence import persist_run, PersistenceError
    with tempfile.TemporaryDirectory() as td:
        persist_run(td, "hashA", {"a.txt": "x"}, {"config_hash": "hashA"})
        try:
            persist_run(td, "hashB", {"a.txt": "y"}, {"config_hash": "hashB"})
            results["stale_artifact_mismatch"] = {"fail_closed": False}
        except PersistenceError as e:
            results["stale_artifact_mismatch"] = {"fail_closed": True, "message": str(e)[:200]}

    with open(os.path.join(OUT, "MVE_R05_FAILURE_MODE_RESULTS.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("wrote MVE_R05_FAILURE_MODE_RESULTS.json")

    # --- Phase dependency map (from registry) ---
    dep_map = {
        str(k): {
            "name": v["name"],
            "title": v["title"],
            "dependencies": v["dependencies"],
            "environment_prereqs": v["environment_prereqs"],
            "output_dir": v["output_dir"],
            "scientific_status": v["scientific_status"],
        }
        for k, v in mvr.PHASE_REGISTRY.items()
    }
    with open(os.path.join(OUT, "MVE_R05_PHASE_DEPENDENCY_MAP.json"), "w") as f:
        json.dump(dep_map, f, indent=2)
    print("wrote MVE_R05_PHASE_DEPENDENCY_MAP.json")

    # --- Diagnostic run (fresh, final) ---
    cfg = mvr.ResearchConfig("diagnostic", None, "EURUSD", "H1", "2023-08-01", "2023-08-31", 42, "results/mve", REPO_ROOT)
    r1 = mvr.run_diagnostic(cfg)
    out = r1["output_dir"]

    diag = {
        "label": "NON_RESEARCH_INFRASTRUCTURE_DIAGNOSTIC",
        "summary": r1["summary"],
        "output_dir": "results/mve/diagnostic",
        "output_hashes": r1["output_hashes"],
        "git_sha": mvr.git_sha(REPO_ROOT),
        "branch": mvr.git_branch(REPO_ROOT),
    }
    with open(os.path.join(OUT, "MVE_R05_RUNNER_DIAGNOSTIC.json"), "w") as f:
        json.dump(diag, f, indent=2)
    print("wrote MVE_R05_RUNNER_DIAGNOSTIC.json")

    # --- Determinism (two runs, compare artifacts) ---
    def read_artifacts():
        return {
            fname: sha256_file(os.path.join(out, fname))
            for fname in ["DIAGNOSTIC_OHLCV.csv", "DIAGNOSTIC_SUMMARY.json", "DIAGNOSTIC_SUMMARY.md"]
        }

    a1 = read_artifacts()
    m1 = json.load(open(os.path.join(out, "RUN_MANIFEST.json")))
    r2 = mvr.run_diagnostic(cfg)
    a2 = read_artifacts()
    m2 = json.load(open(os.path.join(out, "RUN_MANIFEST.json")))

    t1 = m1.pop("execution_timestamp")
    t2 = m2.pop("execution_timestamp")
    determinism = {
        "data_artifacts_identical": a1 == a2,
        "manifest_identical_except_timestamp": m1 == m2,
        "timestamps_differ": t1 != t2,
        "artifact_hashes": a1,
    }
    report = f"""# MVE R0.5.8 DETERMINISM REPORT — MVE_R05_DETERMINISM_REPORT.md

## Result: {'PASS' if (a1 == a2 and m1 == m2) else 'FAIL'}

Two bounded diagnostic runs (same config hash, same seed, same slice) were
executed and compared.

- Data artifacts byte-identical (CSV/JSON/MD): **{a1 == a2}**
- RUN_MANIFEST.json identical except `execution_timestamp`: **{m1 == m2}**
- Execution timestamps differ (expected, excluded from equivalence): **{t1 != t2}**

## Artifact hashes (identical across runs)

| Artifact | SHA-256 |
|---|---|
"""
    for fname, h in a1.items():
        report += f"| {fname} | {h} |\n"
    report += "\nConfig hash: " + m1["config_hash"] + "\n"
    with open(os.path.join(OUT, "MVE_R05_DETERMINISM_REPORT.md"), "w") as f:
        f.write(report)
    print("wrote MVE_R05_DETERMINISM_REPORT.md")


if __name__ == "__main__":
    main()
