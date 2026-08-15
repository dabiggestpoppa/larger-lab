"""
Phase 6 - Forward Routing Study gate.
CR-P6-FORWARD-ROUTING-STUDY-01

Fail-closed infrastructure gate. Phase 6 can PASS even if every hypothesis
fails; truth matters more than finding an edge.

The gate is built BEFORE the report (so the report can cite it) but written to
disk AFTER the report is generated (so the gate's own file and the report are
both present when it is certified).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

# Every required Phase 6 artifact EXCEPT the gate file and the report itself;
# those two are certified via explicit flags at write time.
REQUIRED_OUTPUTS = [
    "p5_event_freeze.json",
    "input_hash_manifest.json",
    "split_manifest.json",
    "event_forward_currency_factors.parquet",
    "event_forward_pair_returns.parquet",
    "destination_probability_matrix.csv",
    "destination_transition_matrix.csv",
    "gbp_bridge_analysis.csv",
    "chf_parking_analysis.csv",
    "jpy_destination_analysis.csv",
    "residual_leadlag_analysis.csv",
    "residual_decay_analysis.csv",
    "network_dislocation_outcomes.csv",
    "factor_mfe_mae.csv",
    "pair_mfe_mae.csv",
    "sleeper_score_analysis.csv",
    "development_results.csv",
    "holdout_results.csv",
    "subperiod_stability.csv",
    "multiple_testing_results.csv",
    "candidate_relationships_frozen.json",
    "overlap_sensitivity.csv",
]

REQUIRED_FLAGS = [
    "phase5_hashes_frozen",
    "fixed_horizons",
    "split_frozen_before_discovery",
    "event_level_outcomes_generated",
    "destination_matrices_generated",
    "bridge_test_generated",
    "parking_test_generated",
    "jpy_test_generated",
    "residual_leadlag_generated",
    "network_study_generated",
    "overlap_sensitivity_generated",
    "multiple_testing_generated",
    "candidates_frozen",
    "holdout_evaluated_after_freeze",
    "no_future_leakage",
]


def build_gate(phase6_dir: Path, flags: Dict, report_present: bool = False) -> Dict:
    """Build the gate dict without writing it (used by the report)."""
    present = {f: (phase6_dir / f).exists() for f in REQUIRED_OUTPUTS}
    all_present = all(present.values())
    all_flags = all(flags.get(k, False) for k in REQUIRED_FLAGS)
    report_ok = report_present or (phase6_dir / "PHASE_6_ROUTING_STUDY.md").exists()
    gate_passed = bool(all_present and all_flags and report_ok)
    return {
        "phase": "6",
        "task": "CR-P6-FORWARD-ROUTING-STUDY-01",
        "gate_passed": gate_passed,
        "phase_6_complete": bool(all_present),
        "phase_7_cleared": gate_passed,
        "outputs_present": present,
        "missing_outputs": [k for k, v in present.items() if not v],
        "report_generated": report_ok,
        "flags": {k: bool(flags.get(k, False)) for k in REQUIRED_FLAGS},
        "failed_flags": [k for k in REQUIRED_FLAGS if not flags.get(k, False)],
        "failures": [k for k, v in present.items() if not v]
                  + [k for k in REQUIRED_FLAGS if not flags.get(k, False)]
                  + ([] if report_ok else ["PHASE_6_ROUTING_STUDY.md"]),
        "note": "Phase 6 is an empirical outcome study. A PASS does not imply "
                "any hypothesis was supported; it certifies the measurement "
                "infrastructure and the development/holdout discipline.",
    }


def write_gate(phase6_dir: Path, flags: Dict, report_present: bool = True) -> Dict:
    """Write the Phase 6 gate. Runs AFTER the report exists."""
    gate = build_gate(phase6_dir, flags, report_present=report_present)
    (phase6_dir / "phase_6_gate.json").write_text(
        json.dumps(gate, indent=2, default=str), encoding="utf-8")
    return gate
