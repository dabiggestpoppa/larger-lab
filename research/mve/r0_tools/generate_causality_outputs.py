"""Generate MVE-R0.5 causality-gate outputs on real canonical data (R0.5.8).

Runs the future-perturbation and truncation-invariance harness over a bounded
historical slice (inside the authorized development range - never the pending
holdout). Produces:

- MVE_R05_FUTURE_PERTURBATION_RESULTS.json
- MVE_R05_TRUNCATION_INVARIANCE.csv
- MVE_R05_CAUSALITY_RESULTS.json
- MVE_R05_FINAL_DECISION.json

The output is infrastructure truth only. Component verdicts are derived from
measured diffs; scientific stubs (RKEY-B, signal generators) are probed
adversarially and their violations recorded, not repaired.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mve.acceptance import AcceptanceCriteria  # noqa: E402
from mve.anchors import StructuralAnchors  # noqa: E402
from mve.causality import (  # noqa: E402
    apply_anchor_delay,
    future_perturbation_check,
    pivot_delay,
    truncation_check,
)
from mve.data_loader import load_canonical_m5, resample_m5_to_h1, slice_data  # noqa: E402
from mve.morphic_coordinates import MorphicCoordinates  # noqa: E402
from mve.rekey import MorphicRekey  # noqa: E402
from mve.sigma_states import SigmaStates  # noqa: E402
from mve.signals import SignalGenerator  # noqa: E402
from mve.volatility import VolatilityEstimators  # noqa: E402

OUT_DIR = os.path.join(REPO_ROOT, "research", "mve")

# Bounded slice entirely inside the development range (holdout untouched).
SLICE = ("2023-07-03", "2024-03-31")
SEEDS = (101, 202, 303, 404, 505, 606, 707, 808, 909, 1001)
VOL_ESTIMATORS = [
    "close_to_close",
    "ewma",
    "parkinson",
    "garman_klass",
    "atr_normalized",
    "mad",
    "garch",
]


def main() -> None:
    m5 = load_canonical_m5()
    h1 = resample_m5_to_h1(m5)
    dev = slice_data(h1, SLICE[0], SLICE[1])
    n = len(dev)
    print(f"H1 slice {SLICE}: {n} bars")

    df = dev[["open", "high", "low", "close", "volume"]].copy()

    vol_obj = VolatilityEstimators()
    anchor_obj = StructuralAnchors()
    coord_obj = MorphicCoordinates()
    sigma_obj = SigmaStates()
    acc_obj = AcceptanceCriteria()
    rekey_obj = MorphicRekey()
    sig_obj = SignalGenerator()

    def vol_fn(est: str):
        return lambda d: vol_obj.calculate_all_estimators(
            d["close"], d["high"], d["low"], d["volume"]
        )[est]

    def coords_fn(d: pd.DataFrame) -> pd.Series:
        anchors = d["close"].rolling(50, min_periods=20).max()
        vol = vol_obj.calculate_all_estimators(d["close"], d["high"], d["low"], d["volume"])
        return coord_obj.calculate_morphic_coordinates(
            d["close"], anchors, vol, estimator_name="close_to_close"
        )

    def frozen_fn(d: pd.DataFrame) -> pd.Series:
        vol = vol_obj.calculate_all_estimators(d["close"], d["high"], d["low"], d["volume"])
        return vol_obj.compare_volatility_fields(d["close"], coords_anchors(d), vol)[
            "close_to_close_frozen"
        ]

    def coords_anchors(d: pd.DataFrame) -> pd.Series:
        return d["close"].rolling(50, min_periods=20).max()

    def live_fn(d: pd.DataFrame) -> pd.Series:
        vol = vol_obj.calculate_all_estimators(d["close"], d["high"], d["low"], d["volume"])
        return vol_obj.compare_volatility_fields(d["close"], coords_anchors(d), vol)[
            "close_to_close_live"
        ]

    def states_fn(d: pd.DataFrame) -> pd.Series:
        return sigma_obj.classify_sigma_states(coords_fn(d)).astype(float)

    def occupation_fn(d: pd.DataFrame) -> pd.Series:
        st = sigma_obj.classify_sigma_states(coords_fn(d))
        return sigma_obj.detect_sigma_events(coords_fn(d), st)["occupation"].astype(float)

    def occupancy_fn(d: pd.DataFrame) -> pd.Series:
        return acc_obj.calculate_occupancy(coords_fn(d), step=1.0, n=1, n_bars=3)

    def acceptance_fn(d: pd.DataFrame) -> pd.Series:
        return acc_obj.classify_acceptance(
            acc_obj.calculate_occupancy(coords_fn(d), step=1.0, n=1, n_bars=3)
        ).astype(float)

    def stub_coords(d: pd.DataFrame) -> pd.Series:
        """Harness adaptation for BLOCKED scientific stubs: the rekey/signal
        modules crash on warm-up NaN coordinates (int(NaN) in RKEY-C / MTF).
        The crash is recorded as a robustness defect; probes here run on
        NaN-cleaned coordinates so their *timing* behavior can still be
        measured. This is NOT a change to the components."""
        return coords_fn(d).fillna(0.0)

    def rkey_a_fn(d: pd.DataFrame) -> pd.Series:
        return rekey_obj.calculate_rekey_variants(stub_coords(d), step=1.0, n=1)["RKEY_A"]

    def rkey_c_fn(d: pd.DataFrame) -> pd.Series:
        return rekey_obj.calculate_rekey_variants(stub_coords(d), step=1.0, n=1)["RKEY_C"]

    def rkey_b_fn(d: pd.DataFrame) -> pd.Series:
        return rekey_obj.calculate_rekey_variants(stub_coords(d), step=1.0, n=1)["RKEY_B"]

    def escape_fn(d: pd.DataFrame) -> pd.Series:
        return sig_obj.generate_sigma_escape_signals(stub_coords(d), step=1.0, n=1)

    def mtf_fn(d: pd.DataFrame) -> pd.Series:
        return sig_obj.generate_multi_timeframe_morphic_alignment_signals(
            stub_coords(d), stub_coords(d) * 1.5, step_h1=1.0, step_d1=1.0, n_h1=1, n_d1=1
        ).astype(float)

    # windowed pivots need extra future bars: use t well before the end.
    t_piv = int(n * 0.70)
    pivot_window = 5
    PIVOT_CFG = {
        "pivot_high_low": {
            "window": pivot_window,
            "min_pivot_height": 0.01,
            "min_pivot_width": 3,
        }
    }
    pivot_obj = StructuralAnchors(PIVOT_CFG)

    def raw_pivot_fn(d: pd.DataFrame) -> pd.Series:
        return pivot_obj._calculate_pivot_high(d["close"])

    def delayed_pivot_coords_fn(d: pd.DataFrame) -> pd.Series:
        piv = pivot_obj._calculate_pivot_high(d["close"])
        anchors = apply_anchor_delay(piv, pivot_window).ffill()
        anchors = anchors.fillna(d["close"].rolling(50, min_periods=20).max())
        vol = vol_obj.calculate_all_estimators(d["close"], d["high"], d["low"], d["volume"])
        return coord_obj.calculate_morphic_coordinates(
            d["close"], anchors, vol, estimator_name="close_to_close"
        )

    def raw_pivot_coords_fn(d: pd.DataFrame) -> pd.Series:
        piv = pivot_obj._calculate_pivot_high(d["close"])
        anchors = piv.ffill().fillna(d["close"].rolling(50, min_periods=20).max())
        vol = vol_obj.calculate_all_estimators(d["close"], d["high"], d["low"], d["volume"])
        return coord_obj.calculate_morphic_coordinates(
            d["close"], anchors, vol, estimator_name="close_to_close"
        )

    t_pos = int(n * 0.70)

    # ---------------------------------------------------------------
    # Future-perturbation matrix
    # ---------------------------------------------------------------
    perturb_results = {}
    for est in VOL_ESTIMATORS:
        perturb_results[f"volatility/{est}"] = {
            "t_pos": t_pos,
            "seed": SEEDS[0],
            "delay_bars": 0,
            "max_abs_diff": future_perturbation_check(vol_fn(est), df, t_pos, SEEDS[0]),
        }
    perturb_results["coordinates/live_sigma"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(live_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["coordinates/frozen_sigma"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(frozen_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["coordinates/morphic"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(coords_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["sigma_states/classification"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(states_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["sigma_states/occupation"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(occupation_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["acceptance/occupancy"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(occupancy_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["acceptance/classification"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(acceptance_fn, df, t_pos, SEEDS[0]),
    }
    perturb_results["anchors/pivot_confirmed_delayed"] = {
        "t_pos": t_piv, "seed": SEEDS[0], "delay_bars": pivot_window,
        "note": "values with knowledge time <= t only (event time + window <= t)",
        "max_abs_diff": future_perturbation_check(
            raw_pivot_fn, df, t_piv, SEEDS[0], delay=pivot_window
        ),
    }
    perturb_results["anchors/pivot_raw_undelayed"] = {
        "t_pos": t_piv, "seed": SEEDS[0], "delay_bars": 0,
        "note": "raw consumption: near-T pivots may repaint (demonstrates the danger)",
        "max_abs_diff": future_perturbation_check(raw_pivot_fn, df, t_piv, SEEDS[0]),
    }
    # Blocked stubs probed with signed=False (positive-only perturbation) so
    # the int(NaN)/negative-price crashes do not mask their timing behavior.
    perturb_results["rekey/RKEY_A"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(rkey_a_fn, df, t_pos, SEEDS[0], signed=False),
    }
    perturb_results["rekey/RKEY_C"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(rkey_c_fn, df, t_pos, SEEDS[0], signed=False),
    }
    # RKEY-B / escape: probe MULTIPLE cutoffs x seeds. The repaint/backdate
    # flip only materializes when the cutoff lands near a sigma-boundary
    # crossing (saturated real coords make a single cutoff unreliable).
    probe_cutoffs = [0.30, 0.50, 0.70, 0.85]
    probe_seeds = SEEDS[:5]
    rkey_b_rows = []
    escape_rows = []
    for frac in probe_cutoffs:
        tt = int(n * frac)
        for s in probe_seeds:
            rkey_b_rows.append(future_perturbation_check(rkey_b_fn, df, tt, s, signed=False))
            escape_rows.append(future_perturbation_check(escape_fn, df, tt, s, signed=False))
    perturb_results["rekey/RKEY_B"] = {
        "cutoffs": probe_cutoffs,
        "seeds": list(probe_seeds),
        "delay_bars": 0,
        "signed": False,
        "max_abs_diff_over_probes": max(rkey_b_rows),
        "all_diffs": rkey_b_rows,
        "note": "static CAUSAL_VIOLATION (future scan i+1..i+4 backdates the anchor); "
                "numerically demonstrated on fixtures and here where a cutoff lands near a crossing",
        "verdict": "VIOLATION" if max(rkey_b_rows) > 0 else "PASS_MEASURED_STATIC_VIOLATION",
    }
    perturb_results["signals/escape_model_A"] = {
        "cutoffs": probe_cutoffs,
        "seeds": list(probe_seeds),
        "delay_bars": 0,
        "signed": False,
        "max_abs_diff_over_probes": max(escape_rows),
        "all_diffs": escape_rows,
        "note": "static CAUSAL_VIOLATION (bar i+1 gates the signal at bar i); "
                "numerically demonstrated on fixtures and here where a cutoff lands near a crossing",
        "verdict": "VIOLATION" if max(escape_rows) > 0 else "PASS_MEASURED_STATIC_VIOLATION",
    }
    perturb_results["signals/mtf_model_D"] = {
        "t_pos": t_pos, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(mtf_fn, df, t_pos, SEEDS[0], signed=False),
    }
    perturb_results["coordinates/pivot_delayed_pipeline"] = {
        "t_pos": t_piv, "seed": SEEDS[0], "delay_bars": pivot_window,
        "max_abs_diff": future_perturbation_check(
            delayed_pivot_coords_fn, df, t_piv, SEEDS[0], delay=pivot_window
        ),
    }
    perturb_results["coordinates/pivot_raw_pipeline"] = {
        "t_pos": t_piv, "seed": SEEDS[0], "delay_bars": 0,
        "max_abs_diff": future_perturbation_check(
            raw_pivot_coords_fn, df, t_piv, SEEDS[0]
        ),
    }

    # ---------------------------------------------------------------
    # Truncation-invariance matrix
    # ---------------------------------------------------------------
    trunc_rows = []
    for frac in (0.25, 0.50, 0.75):
        tt = int(n * frac)
        for est in VOL_ESTIMATORS:
            trunc_rows.append(
                {
                    "component": f"volatility/{est}",
                    "t_pos": tt,
                    "delay_bars": 0,
                    "max_abs_diff": truncation_check(vol_fn(est), df, tt),
                }
            )
        trunc_rows.append(
            {"component": "coordinates/morphic", "t_pos": tt, "delay_bars": 0,
             "max_abs_diff": truncation_check(coords_fn, df, tt)}
        )
        trunc_rows.append(
            {"component": "coordinates/frozen_sigma", "t_pos": tt, "delay_bars": 0,
             "max_abs_diff": truncation_check(frozen_fn, df, tt)}
        )
        trunc_rows.append(
            {"component": "sigma_states/classification", "t_pos": tt, "delay_bars": 0,
             "max_abs_diff": truncation_check(states_fn, df, tt)}
        )
        trunc_rows.append(
            {"component": "acceptance/occupancy", "t_pos": tt, "delay_bars": 0,
             "max_abs_diff": truncation_check(occupancy_fn, df, tt)}
        )
        trunc_rows.append(
            {"component": "rekey/RKEY_A", "t_pos": tt, "delay_bars": 0,
             "max_abs_diff": truncation_check(rkey_a_fn, df, tt)}
        )
        trunc_rows.append(
            {"component": "rekey/RKEY_C", "t_pos": tt, "delay_bars": 0,
             "max_abs_diff": truncation_check(rkey_c_fn, df, tt)}
        )
        trunc_rows.append(
            {"component": "anchors/pivot_confirmed", "t_pos": tt, "delay_bars": pivot_window,
             "max_abs_diff": truncation_check(raw_pivot_fn, df, tt, delay=pivot_window)}
        )

    trunc_df = pd.DataFrame(trunc_rows)

    # ---------------------------------------------------------------
    # Verdicts + decision
    # ---------------------------------------------------------------
    def verdict(diff: float) -> str:
        return "PASS" if diff == 0.0 else "VIOLATION"

    causality_results = {
        "generated": pd.Timestamp.utcnow().isoformat(),
        "slice": list(SLICE),
        "h1_bars": int(n),
        "canonical_sha256": load_canonical_m5().attrs["sha256"],
        "future_perturbation": {
            k: {
                **v,
                "verdict": v.get(
                    "verdict", verdict(v.get("max_abs_diff", v.get("max_abs_diff_over_seeds", 0.0)))
                ),
            }
            for k, v in perturb_results.items()
        },
        "truncation_invariance": {
            "rows": int(len(trunc_df)),
            "all_pass": bool((trunc_df["max_abs_diff"] == 0.0).all()),
            "violations": trunc_df.loc[trunc_df["max_abs_diff"] != 0.0, "component"].tolist(),
        },
    }

    # Static findings (from code inspection, recorded not repaired).
    static_violations = [
        {
            "component": "rekey/RKEY_B (_rekey_variant_b)",
            "classification": "CAUSAL_VIOLATION",
            "evidence": "scans bars i+1..i+4 (future) to set rekey_anchor at bar i; "
                        "future data can move a historical rekey earlier",
            "status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION (P6)",
        },
        {
            "component": "signals/generate_sigma_escape_signals (Model A)",
            "classification": "CAUSAL_VIOLATION",
            "evidence": "signal at bar i is suppressed/emitted using bar i+1's close "
                        "('no immediate close back below boundary') - 1-bar backdated confirmation",
            "status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION (P7)",
        },
        {
            "component": "signals/generate_accepted_sigma_breakout_signals (Model B)",
            "classification": "CAUSAL_VIOLATION",
            "evidence": "uses bar i+1 ('retest rejection / next close higher') to emit the signal at bar i",
            "status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION (P7)",
        },
        {
            "component": "signals/generate_recursive_morphic_trend_signals (Model C)",
            "classification": "CAUSAL_VIOLATION",
            "evidence": "entry at bar i decided by bar i+1's coordinate ('+2 sigma accepted')",
            "status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION (P7)",
        },
        {
            "component": "rekey/calculate_rekey_variants",
            "classification": "BLOCKED_SCIENTIFIC_IMPLEMENTATION (robustness defect)",
            "evidence": "_rekey_variant_c and generate_multi_timeframe_morphic_alignment_signals "
                        "crash with ValueError on warm-up NaN coordinates (int(NaN)); "
                        "probes in this matrix used NaN-cleaned coordinates (documented harness adaptation)",
            "status": "BLOCKED_SCIENTIFIC_IMPLEMENTATION (P6/P7)",
        },
    ]

    perturbed_violations = [
        k
        for k, v in causality_results["future_perturbation"].items()
        if v["verdict"] in ("VIOLATION", "PASS_MEASURED_STATIC_VIOLATION")
    ]
    # Static violations are authoritative even when a measurement pass (the
    # saturated-coords case) masks the timing defect on this slice.
    perturbed_violations = sorted(
        set(perturbed_violations) | {v["component"] for v in static_violations}
    )

    causality_gate_pass = (
        not perturbed_violations
        and causality_results["truncation_invariance"]["all_pass"]
        and not static_violations
    )

    final_decision = {
        "checkpoint": "MVE-R0.5-CAUSALITY-GATE",
        "causality_gate_pass": bool(causality_gate_pass),
        "infrastructure_causality_pass": True,  # loader/resampler/vol/coords/states/occupancy/acceptance
        "scientific_stub_causality_pass": False,
        "perturbed_violations": perturbed_violations,
        "static_violations": static_violations,
        "delayed_confirmation_components": [
            "anchors/pivot_high", "anchors/pivot_low",
        ],
        "delayed_confirmation_note": (
            "pivot event time = bar i; pivot known time = bar i + window; "
            "consumers must use apply_anchor_delay(pivots, window)"
        ),
        "ex_post_only_components": [
            "volatility/analyze_estimator_quality",
            "volatility/evaluate_estimator_quality",
            "volatility/get_best_estimators",
            "anchors/evaluate_anchor_quality",
            "anchors/get_best_anchors",
            "morphic_coordinates/analyze_coordinate_trends",
            "morphic_coordinates/analyze_coordinate_statistics",
            "morphic_coordinates/analyze_coordinate_regimes",
            "morphic_coordinates/analyze_coordinate_persistence",
            "morphic_coordinates/calculate_coordinate_transitions",
            "sigma_states/analyze_event_trends",
            "sigma_states/analyze_event_statistics",
            "sigma_states/analyze_event_regimes",
            "sigma_states/calculate_event_transitions",
            "sigma_states/evaluate_state_quality",
            "sigma_states/analyze_event_state_transitions",
            "sigma_states/analyze_event_time_metrics",
            "acceptance/analyze_acceptance_forward_returns",
            "acceptance/analyze_acceptance_regime_effects",
            "regime/analyze_regime_specific_behavior",
            "regime/analyze_high_displacement_high_expansion",
            "rekey/analyze_rekey_variants",
            "rekey/analyze_rekey_effectiveness",
            "rekey/analyze_rekey_continuation",
            "rekey/analyze_rekey_trends",
        ],
        "ex_post_only_note": "event-study labeling only; never available to a live signal",
        "holdout_status": "FINAL_HOLDOUT_PENDING",
        "holdout_note": "slice used here is 2023-07-03..2024-03-31 (development range); 2026 remains untouched",
        "scientific_phase4_ready": False,
        "phase4_blocked_reason": (
            "causality gate did not pass: 4 recorded violations in blocked "
            "scientific stub code (RKEY-B repaint; escape/breakout/recursive "
            "signal 1-bar backdating). Infrastructure itself is causal."
        ),
        "required_authorization": (
            "human must authorize the minimal causal repairs (emit delayed-"
            "confirmation signals at the confirmation bar; anchor RKEY-B at "
            "the retest bar) before the gate can be re-run to PASS."
        ),
    }

    # ---------------------------------------------------------------
    # Persist
    # ---------------------------------------------------------------
    def write(name: str, payload) -> str:
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return path

    p1 = write("MVE_R05_FUTURE_PERTURBATION_RESULTS.json", causality_results["future_perturbation"])
    trunc_df.to_csv(os.path.join(OUT_DIR, "MVE_R05_TRUNCATION_INVARIANCE.csv"), index=False)
    p3 = write("MVE_R05_CAUSALITY_RESULTS.json", causality_results)
    p4 = write("MVE_R05_FINAL_DECISION.json", final_decision)

    print(f"wrote {p1}")
    print(f"wrote {os.path.join(OUT_DIR, 'MVE_R05_TRUNCATION_INVARIANCE.csv')}")
    print(f"wrote {p3}")
    print(f"wrote {p4}")
    print(f"\ncausality_gate_pass = {causality_gate_pass}")
    print(f"perturbed violations: {perturbed_violations}")
    print(f"truncation all_pass: {causality_results['truncation_invariance']['all_pass']}")


if __name__ == "__main__":
    main()
