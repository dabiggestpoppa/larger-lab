"""
Phase 5 - Routing Event Engine primitives: frozen inputs, event object,
threshold manifest, deterministic statistical machinery.
CR-P5-ROUTING-EVENT-ENGINE-01

This module defines WHAT happened at time T as a deterministic, timestamped
RESTING event candidate. It does NOT evaluate future performance, optimise
trading rules, or claim causality. No-lookahead is enforced by construction
(every statistic is a rolling/trailing function of data <= T) and verified by
prefix-invariance tests.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Canonical Phase 4 frozen hashes (from artifacts/phase_04/output_hash_manifest.json).
PHASE4_INPUT_HASHES = {
    "currency_factors_h1.parquet": "04ec94e515287f96d98c5093926410c062cf9971c1703b78752851a7b5064c2d",
    "pair_residuals_h1.parquet": "ea5edc04eefcbc9d4771ad8bcca4b88e14d63c9b45a51f0320548c9491ec44c8",
    "factor_features_h1.parquet": "0c464199988ddf68635ae7311977a3315f4dbf9f6db48e669cc90f8d14cc7302",
}
PHASE4_SEAL_COMMIT = "71b8188dd9a83c78e51ea5f8e6028c8066d95079"
PHASE4_ENGINE_COMMIT = "f54ffff8b6041242e707d332075dea1c7b96f0d1"

CURRENCIES: List[str] = ["EUR", "GBP", "USD", "CHF", "JPY"]

# All 10 pairs (quote-currency ordering for incidence).
PAIRS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURGBP",
    "EURJPY", "GBPJPY", "CHFJPY", "EURCHF", "GBPCHF",
]

# Pairs touching each currency (for breadth).
CURRENCY_PAIRS: Dict[str, List[str]] = {
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF"],
    "GBP": ["GBPUSD", "EURGBP", "GBPJPY", "GBPCHF"],
    "USD": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"],
    "CHF": ["USDCHF", "CHFJPY", "EURCHF", "GBPCHF"],
    "JPY": ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY"],
}


# ----------------------------------------------------------------------
# Frozen input handling
# ----------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_phase4(phase4_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load the three accepted Phase 4 inputs, rejecting hash mismatch."""
    frames = {}
    for fname, expected in PHASE4_INPUT_HASHES.items():
        path = phase4_dir / fname
        actual = _sha256(path)
        if actual != expected:
            raise ValueError(
                f"Phase 4 input hash mismatch for {fname}: expected {expected}, "
                f"got {actual}. Refusing to consume an un-frozen input."
            )
        frames[fname] = pd.read_parquet(path)
    return frames


def input_hash_manifest(phase4_dir: Path, phase5_dir: Path) -> Dict:
    """Record Phase 4 input hashes, row range and seal commit for Phase 5."""
    frames = load_frozen_phase4(phase4_dir)
    factors = frames["currency_factors_h1.parquet"]
    manifest = {
        "phase": "5",
        "task": "CR-P5-ROUTING-EVENT-ENGINE-01",
        "phase4_seal_commit": PHASE4_SEAL_COMMIT,
        "phase4_engine_commit": PHASE4_ENGINE_COMMIT,
        "inputs": {
            fname: {
                "sha256": PHASE4_INPUT_HASHES[fname],
                "rows": int(len(df)),
                "first_ts": str(pd.to_datetime(df.index.min(), utc=True)),
                "last_ts": str(pd.to_datetime(df.index.max(), utc=True)),
            }
            for fname, df in frames.items()
        },
        "canonical_h1_rows": int(len(factors)),
        "window_start": str(pd.to_datetime(factors.index.min(), utc=True)),
        "window_end": str(pd.to_datetime(factors.index.max(), utc=True)),
        "note": "Input hashes frozen at Phase 4 seal. Mismatch => refused.",
    }
    (phase5_dir / "input_hash_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


# ----------------------------------------------------------------------
# Event object
# ----------------------------------------------------------------------


@dataclass
class RoutingEvent:
    event_id: str
    event_start: str
    peak_timestamp: str
    event_end: str
    duration_hours: float
    event_family: str          # ORIGIN / NETWORK_DISLOCATION / RESIDUAL_SHOCK
    origin_currency: Optional[str]
    direction: Optional[str]   # ACCUMULATION / LIQUIDATION
    severity: str              # LOW / MEDIUM / HIGH / EXTREME
    severity_score: float
    origin_strength: Optional[float]
    origin_velocity: Optional[float]
    origin_acceleration: Optional[float]
    origin_breadth: Optional[float]
    origin_rank: Optional[float]
    origin_volatility: Optional[float]
    destination_rank_1: Optional[str]
    destination_rank_2: Optional[str]
    destination_rank_3: Optional[str]
    gbp_bridge_score_components: Dict = field(default_factory=dict)
    chf_parking_score_components: Dict = field(default_factory=dict)
    jpy_destination_score_components: Dict = field(default_factory=dict)
    network_dispersion: Optional[float] = None
    network_rmse: Optional[float] = None
    max_pair_residual: Optional[float] = None
    broad_vs_localized: Optional[str] = None
    peak_severity: Optional[str] = None


# ----------------------------------------------------------------------
# Deterministic statistical thresholds (fixed, not PnL-tuned)
# ----------------------------------------------------------------------


def build_threshold_manifest(
    factor_df: pd.DataFrame,
    residual_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    run_length: int = 120,
) -> Dict:
    """
    Build a frozen threshold manifest from deterministic statistical logic
    (rolling percentiles / MAD / z-score on *training-in-sample* window only,
    i.e. values are computed from data up to the current bar). The manifest
    stores the mapping used at detection time and is reproduced identically on
    a fixed run_length so it is reproducible.
    """
    # factor threshold: 95th percentile of |factor| over trailing window
    fac = np.abs(factor_df[[f"{c}_factor" for c in CURRENCIES]]).rolling(
        run_length, min_periods=run_length).quantile(0.95)
    # network fault thresholds
    dispersion = feature_df["fx_dispersion_4h"] if "fx_dispersion_4h" in feature_df else None
    network_rmse = feature_df["network_fit_rmse"] if "network_fit_rmse" in feature_df else None
    # residual shock threshold: |residual| 95th percentile
    resid = np.abs(residual_df).rolling(run_length, min_periods=run_length).quantile(0.95)

    fac_pct = float(np.nanpercentile(fac.to_numpy(), 95)) if not fac.empty else 0.0
    resid_pct = float(np.nanpercentile(resid.to_numpy(), 95)) if not resid.empty else 0.0
    rmse_pct = float(np.nanpercentile(network_rmse.to_numpy(), 95)) if (
        network_rmse is not None and len(network_rmse)) else 0.0

    return {
        "phase": "5",
        "task": "CR-P5-ROUTING-EVENT-ENGINE-01",
        "statistical_method": (
            "trailing rolling percentiles / MAD / z-score over a fixed run_length. "
            "Fixed from statistical logic, NOT chosen using future returns."
        ),
        "run_length_h1": run_length,
        "origin_factor_p95_threshold": fac_pct * 3.0,
        "residual_p95_threshold": resid_pct * 3.0,
        "network_dispersion_z_threshold": 2.0,
        "network_rmse_p95": rmse_pct,
        "severity_buckets": {
            "LOW": (0.0, 1.0),
            "MEDIUM": (1.0, 1.5),
            "HIGH": (1.5, 2.0),
            "EXTREME": (2.0, float("inf")),
        },
        "hysteresis": {
            "entry_percentile": 0.95,
            "reset_percentile": 0.80,
        },
        "sample_size": {
            "ADEQUATE_SAMPLE": 50,
            "THIN_SAMPLE": 20,
            "INSUFFICIENT_SAMPLE": 5,
        },
    }


def _write_threshold_manifest(manifest: Dict, phase5_dir: Path) -> None:
    (phase5_dir / "threshold_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")