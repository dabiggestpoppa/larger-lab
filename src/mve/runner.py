"""Deterministic, phase-isolated MVE research orchestration.

Responsibilities:
- execute exactly one explicitly requested phase (no auto-advance),
- fail closed when prerequisites are missing,
- persist nonempty artifacts with full provenance (RUN_MANIFEST.json),
- provide a bounded infrastructure diagnostic run (NON_RESEARCH).

Scientific phase internals are intentionally out of scope here: phases 4-7 are
marked BLOCKED_SCIENTIFIC_IMPLEMENTATION and refuse to execute until a later
checkpoint authorizes their implementation.
"""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

from mve.data_loader import (
    CANONICAL_EURUSD,
    DataPipelineError,
    load_canonical_m5,
    resample_m5_to_h1,
    slice_data,
)
from mve.persistence import PersistenceError, persist_run, sha256_file, sha256_json

RUNNER_VERSION = "0.5.0"
RUNNER_STATUS = "INFRASTRUCTURE_ONLY"


class RunnerError(Exception):
    """Runner orchestration failure (fail-closed)."""


# ---------------------------------------------------------------------------
# Phase registry + dependency map
# ---------------------------------------------------------------------------

PHASE_REGISTRY: Dict[int, Dict] = {
    4: {
        "name": "PHASE4_ACCEPTANCE",
        "title": "Causal acceptance law",
        "dependencies": [],  # no prior phase artifacts
        "environment_prereqs": ["canonical_data_pipeline", "valid_h1_dataset"],
        "output_dir": "results/mve/phase4",
        "scientific_status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION",
    },
    5: {
        "name": "PHASE5_REGIME_TRANSITIONS",
        "title": "Transition law / constraint entropy",
        "dependencies": [4],
        "environment_prereqs": ["canonical_data_pipeline", "valid_h1_dataset"],
        "output_dir": "results/mve/phase5",
        "scientific_status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION",
    },
    6: {
        "name": "PHASE6_REKEY",
        "title": "Rekey / recursive constraint law",
        "dependencies": [4, 5],
        "environment_prereqs": ["canonical_data_pipeline", "valid_h1_dataset"],
        "output_dir": "results/mve/phase6",
        "scientific_status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION",
    },
    7: {
        "name": "PHASE7_BASELINE_COMPARISON",
        "title": "Baseline falsification",
        "dependencies": [4, 5, 6],
        "environment_prereqs": ["canonical_data_pipeline", "valid_h1_dataset"],
        "output_dir": "results/mve/phase7",
        "scientific_status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION",
    },
}


@dataclass(frozen=True)
class ResearchConfig:
    """Frozen research config. Changing any field changes config_hash."""

    task: str  # "diagnostic" or "phase"
    phase_id: Optional[int]
    asset: str
    timeframe: str
    start: str
    end: str
    seed: int
    output_root: str
    repo_root: str

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d

    def config_hash(self) -> str:
        return sha256_json(self.to_dict())


def _git(repo_root: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", repo_root, *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def git_sha(repo_root: str) -> str:
    return _git(repo_root, "rev-parse", "HEAD")


def git_branch(repo_root: str) -> str:
    return _git(repo_root, "branch", "--show-current")


# ---------------------------------------------------------------------------
# Prerequisite gates
# ---------------------------------------------------------------------------

def phase_artifacts_exist(repo_root: str, phase_id: int) -> bool:
    """True only if the phase's RUN_MANIFEST.json exists AND is valid JSON with a
    config_hash. A corrupt or empty artifact counts as missing (fail-closed)."""
    import json

    manifest = os.path.join(
        repo_root, PHASE_REGISTRY[phase_id]["output_dir"], "RUN_MANIFEST.json"
    )
    if not os.path.exists(manifest):
        return False
    try:
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict) and isinstance(data.get("config_hash"), str)
    except Exception:  # noqa: BLE001
        return False


def check_phase_dependencies(repo_root: str, phase_id: int) -> List[int]:
    """Return the list of dependency phases whose artifacts are missing."""
    missing = []
    for dep in PHASE_REGISTRY[phase_id]["dependencies"]:
        if not phase_artifacts_exist(repo_root, dep):
            missing.append(dep)
    return missing


def check_environment_prereqs(repo_root: str) -> List[str]:
    """Verify canonical data pipeline is available (file + hash)."""
    missing = []
    path = os.path.join(repo_root, CANONICAL_EURUSD.relpath)
    if not os.path.exists(path):
        missing.append("canonical_data_pipeline (file missing)")
        return missing
    if sha256_file(path) != CANONICAL_EURUSD.sha256:
        missing.append("canonical_data_pipeline (hash mismatch)")
    return missing


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def build_manifest(
    config: ResearchConfig,
    m5_rows: int,
    h1_rows: int,
    h1_fingerprint: str,
    requested: str,
) -> Dict:
    """Assemble full provenance. Output hashes are attached by persist_run."""
    return {
        "git_sha": git_sha(config.repo_root),
        "branch": git_branch(config.repo_root),
        "requested_phase": requested,
        "canonical_data_path": CANONICAL_EURUSD.relpath,
        "canonical_sha256": CANONICAL_EURUSD.sha256,
        "m5_row_count": m5_rows,
        "h1_row_count": h1_rows,
        "h1_fingerprint": h1_fingerprint,
        "slice_start": config.start,
        "slice_end": config.end,
        "config_hash": config.config_hash(),
        "config": config.to_dict(),
        "runner_version": RUNNER_VERSION,
        "runner_status": RUNNER_STATUS,
        "deterministic_seed": config.seed,
        "input_artifact_hashes": {CANONICAL_EURUSD.relpath: CANONICAL_EURUSD.sha256},
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "holdout_status": "FINAL_HOLDOUT_PENDING",
    }


# ---------------------------------------------------------------------------
# Phase execution (fail-closed)
# ---------------------------------------------------------------------------

def execute_phase(config: ResearchConfig) -> Dict:
    """Execute exactly one phase. Fails closed on any missing prerequisite and
    on blocked scientific implementations. Never auto-advances."""
    phase_id = config.phase_id
    if phase_id not in PHASE_REGISTRY:
        raise RunnerError(f"Unknown phase: {phase_id}")

    phase = PHASE_REGISTRY[phase_id]

    # 1. Environment prerequisites (data pipeline).
    env_missing = check_environment_prereqs(config.repo_root)
    if env_missing:
        raise RunnerError(
            f"Phase {phase_id} environment prerequisites missing: {env_missing}"
        )

    # 2. Prior-phase artifact dependencies.
    dep_missing = check_phase_dependencies(config.repo_root, phase_id)
    if dep_missing:
        raise RunnerError(
            f"Phase {phase_id} requires completed phase artifacts for: {dep_missing}"
        )

    # 3. Scientific implementation gate (honest status).
    if phase["scientific_status"] == "BLOCKED_SCIENTIFIC_IMPLEMENTATION":
        raise RunnerError(
            f"Phase {phase_id} ({phase['name']}) scientific implementation is "
            "BLOCKED_SCIENTIFIC_IMPLEMENTATION; refusing to fabricate research "
            "output. No artifact written."
        )

    # Scientific phases are intentionally unreachable in this checkpoint.
    raise RunnerError(f"Phase {phase_id} is not implemented in this checkpoint.")


# ---------------------------------------------------------------------------
# Bounded infrastructure diagnostic (NON_RESEARCH)
# ---------------------------------------------------------------------------

def run_diagnostic(config: ResearchConfig) -> Dict:
    """Infrastructure-only diagnostic: load bounded H1 slice, instantiate MVE
    components, emit a trivial summary, persist CSV/JSON/MD, verify hashes."""
    from mve.volatility import VolatilityEstimators
    from mve.anchors import StructuralAnchors

    env_missing = check_environment_prereqs(config.repo_root)
    if env_missing:
        raise RunnerError(f"Diagnostic prerequisites missing: {env_missing}")

    try:
        m5 = load_canonical_m5(repo_root=config.repo_root)
        h1 = resample_m5_to_h1(m5)
        sliced = slice_data(h1, config.start, config.end)
    except DataPipelineError as exc:
        raise RunnerError(f"Diagnostic data error: {exc}") from exc

    # Instantiate the repaired components (smoke, not research).
    _v = VolatilityEstimators()
    _a = StructuralAnchors()

    summary = {
        "label": "NON_RESEARCH_INFRASTRUCTURE_DIAGNOSTIC",
        "rows": int(len(sliced)),
        "first_timestamp": str(sliced.index[0]),
        "last_timestamp": str(sliced.index[-1]),
        "close_mean": float(sliced["close"].mean()),
        "close_std": float(sliced["close"].std()),
        "volume_sum": int(sliced["volume"].sum()),
        "volume_field": m5.attrs.get("volume_field"),
        "components_instantiated": ["VolatilityEstimators", "StructuralAnchors"],
    }

    csv_artifact = sliced[["open", "high", "low", "close", "volume", "source_bar_count"]].copy()
    csv_artifact.index.name = "datetime"
    csv_artifact = csv_artifact.reset_index()
    slice_fingerprint = sha256_json(
        {
            "rows": int(len(sliced)),
            "first": str(sliced.index[0]),
            "last": str(sliced.index[-1]),
            "open_mean": float(sliced["open"].mean()),
            "high_mean": float(sliced["high"].mean()),
            "low_mean": float(sliced["low"].mean()),
            "close_mean": float(sliced["close"].mean()),
            "volume_sum": int(sliced["volume"].sum()),
        }
    )

    artifacts = {
        "DIAGNOSTIC_OHLCV.csv": csv_artifact,
        "DIAGNOSTIC_SUMMARY.json": summary,
        "DIAGNOSTIC_SUMMARY.md": _diagnostic_markdown(summary),
    }

    manifest = build_manifest(
        config,
        m5_rows=int(len(m5)),
        h1_rows=int(len(h1)),
        h1_fingerprint=slice_fingerprint,
        requested="DIAGNOSTIC",
    )
    manifest["output_label"] = "NON_RESEARCH_INFRASTRUCTURE_DIAGNOSTIC"

    output_dir = os.path.join(config.repo_root, config.output_root, "diagnostic")
    try:
        hashes = persist_run(output_dir, config.config_hash(), artifacts, manifest)
    except PersistenceError as exc:
        raise RunnerError(str(exc)) from exc

    return {"output_dir": output_dir, "output_hashes": hashes, "summary": summary}


def _diagnostic_markdown(summary: Dict) -> str:
    lines = [
        "# MVE INFRASTRUCTURE DIAGNOSTIC",
        "",
        f"- Label: {summary['label']}",
        f"- Rows: {summary['rows']}",
        f"- First: {summary['first_timestamp']}",
        f"- Last: {summary['last_timestamp']}",
        f"- Close mean: {summary['close_mean']:.6f}",
        f"- Volume field: {summary['volume_field']}",
        "",
        "This is a NON-RESEARCH infrastructure diagnostic. It is not alpha and",
        "must not be interpreted as scientific evidence.",
        "",
    ]
    return "\n".join(lines) + "\n"
