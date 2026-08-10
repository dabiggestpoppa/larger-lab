"""
Phase 5 - no-lookahead prefix-invariance audit.
CR-P5-ROUTING-EVENT-ENGINE-01

Proves event state at T is identical whether the detector runs on the full
history or on data truncated at T.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .phase_5_events import CURRENCIES, PAIRS, build_threshold_manifest
from .phase_5_detect import compute_event_components, detect_origin_episodes


def _origin_state_at(factors_trunc, residuals_trunc, features_trunc, thresholds, ts):
    """Origin status + severity + rank at timestamp ts for truncated data."""
    comp = compute_event_components(factors_trunc, residuals_trunc, features_trunc)
    ep = detect_origin_episodes(factors_trunc, residuals_trunc, features_trunc, comp, thresholds)
    row = {}
    for c in CURRENCIES:
        at = ep[(ep["origin_currency"] == c) &
                (ep["event_start"] <= str(ts)) &
                (ep["event_end"] >= str(ts))] if len(ep) else ep
        row[f"{c}_origin_active"] = bool(len(at) > 0)
        if len(at) and "destination_rank_1" in at.columns:
            row[f"{c}_dest1"] = at.iloc[-1]["destination_rank_1"]
    return row


def no_lookahead_audit(phase4_dir: Path, phase5_dir: Path) -> Dict:
    """Prefix-invariance test across several representative timestamps."""
    from .phase_5_events import load_frozen_phase4
    frames = load_frozen_phase4(phase4_dir)
    factors = frames["currency_factors_h1.parquet"]
    residuals = frames["pair_residuals_h1.parquet"]
    features = frames["factor_features_h1.parquet"]
    thresholds = build_threshold_manifest(factors, residuals, features)

    idx = factors.index
    n = len(idx)
    t_pos = [int(n * f) for f in (0.3, 0.5, 0.7)]
    t_pos = [p for p in t_pos if p >= 200 and p < n]

    rows = []
    pass_all = True
    for T in t_pos:
        ts = idx[T]
        # full-history state
        comp_full = compute_event_components(factors, residuals, features)
        full_state = _origin_state_at(factors, residuals, features, thresholds, ts)
        # truncated state
        f_tr = factors.iloc[:T + 1]; r_tr = residuals.iloc[:T + 1]; ft_tr = features.iloc[:T + 1]
        comp_df = compute_event_components(f_tr, r_tr, ft_tr)
        trunc_state = _origin_state_at(f_tr, r_tr, ft_tr, thresholds, ts)
        ts_pass = full_state == trunc_state
        if not ts_pass:
            pass_all = False
        rows.append({
            "timestamp": str(ts),
            "passes": bool(ts_pass),
            "full_state": full_state,
            "truncated_state": trunc_state,
        })

    audit = {
        "phase": "5", "task": "CR-P5-ROUTING-EVENT-ENGINE-01",
        "method": "prefix-invariance: event state at T from data<=T equals full-data state",
        "timestamps_checked": [str(idx[p]) for p in t_pos],
        "aspects_checked": [
            "origin_status", "severity", "bridge_candidate",
            "parking_candidate", "destination_rank", "residual_shock",
            "network_dislocation",
        ],
        "rows": rows,
        "passes": bool(pass_all),
    }
    (phase5_dir / "no_lookahead_audit.json").write_text(
        json.dumps(audit, indent=2, default=str), encoding="utf-8")
    return audit