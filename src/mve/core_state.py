"""Core-State Wrapper for CEREBUS MVE (P7.5 CORE STATE SEAL).

Deterministic per-bar morphic field state built ONLY from sealed causal
primitives:

    price -> causal anchors (trailing extremes) -> causal volatility
           -> morphic coordinates -> sigma state -> transition description

This module is a SEAL artifact. It:

- reuses the sealed coordinate primitive (`coordinate_fields`,
  `per_boundary_signals`) and the sealed close_to_close volatility estimator,
- reproduces exactly the canonical anchor / volatility / coordinate / sigma
  series of the sealed P7 pipeline (parity contract),
- contains NO predictive features, NO strategy logic, NO PnL, and does NOT
  consume acceptance science, rekey science, or Models A-E.

The core state is a CAUSAL REPRESENTATION OF MARKET STRUCTURE. It is not a
validated trading strategy, a positive-EV signal, a deployable engine, or
profitable alpha.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mve.p4_acceptance import (  # noqa: E402  (sealed coordinate primitive only)
    P4_TRAILING_MIN_PERIODS,
    P4_TRAILING_WINDOW,
    coordinate_fields,
    per_boundary_signals,
)
from mve.volatility import VolatilityEstimators  # noqa: E402  (sealed)

# Frozen sigma quantization step (matches the sealed P7 control_fields and the
# P4/P6 band conventions).
STEP = 1.0

ANCHOR_TYPE = "trailing_extreme_50"

# Columns required on the input H1 frame.
_REQUIRED_COLS = ("open", "high", "low", "close", "volume")


def build_core_state(h1: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic core-state records from causal H1 bars.

    Input: DataFrame indexed by timestamp with open/high/low/close/volume.
    Output: DataFrame of core-state records. All inputs at bar t use data
    with index <= t (trailing anchors are shift(1) delayed), so every row is
    causally known at its own timestamp (causal_known_time == timestamp).

    No future bars, no centered windows, no whole-sample normalization.
    """
    missing = [c for c in _REQUIRED_COLS if c not in h1.columns]
    if missing:
        raise ValueError(f"core_state: missing required columns {missing}")

    close = h1["close"].astype(float)
    high = h1["high"].astype(float)
    low = h1["low"].astype(float)
    volume = h1["volume"].astype(float)

    # --- causal volatility (sealed close_to_close estimator) ----------------
    vol = VolatilityEstimators().calculate_all_estimators(
        close, high, low, volume
    )["close_to_close"]
    vol = vol.astype(float)

    # --- causal trailing-extreme anchors (shift(1): known at bar t) ---------
    trail_hi = (
        close.rolling(P4_TRAILING_WINDOW, min_periods=P4_TRAILING_MIN_PERIODS)
        .max()
        .shift(1)
    )
    trail_lo = (
        close.rolling(P4_TRAILING_WINDOW, min_periods=P4_TRAILING_MIN_PERIODS)
        .min()
        .shift(1)
    )

    # --- morphic coordinates (sealed coordinate primitive) ------------------
    coord = coordinate_fields(h1, trail_hi, trail_lo, vol)
    # Signed coordinate, upper family, close basis — exactly the canonical
    # series consumed by the sealed P7 pipeline.
    sig = per_boundary_signals(coord, 1.0, 1.0)
    x = sig["x"].astype(float)

    n = len(h1)
    xv = x.to_numpy(dtype=float)

    # --- sigma state (frozen quantization, P7 convention) -------------------
    sigma = np.full(n, np.nan, dtype=float)
    for i in range(n):
        xi = xv[i]
        if np.isnan(xi):
            continue
        s = np.sign(xi) * np.floor(abs(xi) / STEP)
        sigma[i] = s if s != 0 else 0.0
    sigma_s = pd.Series(sigma, index=h1.index)

    # --- unsigned band (P4/P6 convention) ------------------------------------
    with np.errstate(invalid="ignore"):
        band = np.floor(np.abs(xv) / STEP)
    band_s = pd.Series(band, index=h1.index)

    # --- state age: consecutive bars in the same sigma_state (causal) -------
    state_age = np.zeros(n, dtype=float)
    for i in range(1, n):
        a, b = sigma[i - 1], sigma[i]
        if np.isnan(a) or np.isnan(b):
            state_age[i] = 0.0
        elif a == b:
            state_age[i] = state_age[i - 1] + 1.0
        else:
            state_age[i] = 0.0

    # --- transition type vs previous bar -------------------------------------
    prev_sigma = sigma_s.shift(1)
    transition = np.full(n, "STAY", dtype=object)
    for i in range(n):
        a, b = sigma[i], (sigma[i - 1] if i > 0 else np.nan)
        if np.isnan(a) or np.isnan(b):
            transition[i] = "NA"
        elif a > b:
            transition[i] = "UP"
        elif a < b:
            transition[i] = "DOWN"
        else:
            transition[i] = "STAY"

    # --- distance to nearest sigma boundary (fractional part of |x|) --------
    with np.errstate(invalid="ignore"):
        dist = np.abs(xv) - np.floor(np.abs(xv) / STEP) * STEP
    dist_s = pd.Series(dist, index=h1.index)

    # --- coordinate velocity / acceleration (backward-looking) --------------
    vel = x.diff()
    acc = vel.diff()

    # --- anchor age: bars since the trailing extreme last changed -----------
    anchor_age = np.full(n, np.nan, dtype=float)
    up_vals = trail_hi.to_numpy(dtype=float)
    for i in range(n):
        if np.isnan(up_vals[i]):
            continue
        if i == 0 or np.isnan(up_vals[i - 1]) or up_vals[i] != up_vals[i - 1]:
            anchor_age[i] = 0.0
        else:
            anchor_age[i] = anchor_age[i - 1] + 1.0

    # --- data quality ---------------------------------------------------------
    primitive_ok = (
        trail_hi.notna() & trail_lo.notna() & vol.notna() & x.notna()
    )
    data_quality = primitive_ok.astype(float)
    vol_quality = vol.notna().astype(float)

    out = pd.DataFrame(
        {
            "timestamp": h1.index,
            "anchor_type": ANCHOR_TYPE,
            "anchor_up": trail_hi.astype(float).to_numpy(),
            "anchor_lo": trail_lo.astype(float).to_numpy(),
            "volatility_estimate": vol.to_numpy(),
            "volatility_quality": vol_quality.to_numpy(),
            "coordinate": x.to_numpy(),
            "abs_coordinate": np.abs(xv),
            "sigma_band": band_s.to_numpy(),
            "sigma_state": sigma_s.to_numpy(),
            "previous_sigma_state": prev_sigma.to_numpy(),
            "state_age": state_age,
            "transition_type": transition,
            "distance_to_nearest_sigma_boundary": dist_s.to_numpy(),
            "coordinate_velocity": vel.to_numpy(),
            "coordinate_acceleration": acc.to_numpy(),
            "anchor_age": anchor_age,
            "data_quality": data_quality.to_numpy(),
            "causal_known_time": h1.index,
        },
        index=h1.index,
    )
    return out


CORE_STATE_SCHEMA = {
    "timestamp": "bar time (index); causal_known_time == timestamp",
    "anchor_type": "trailing_extreme_50 (constant)",
    "anchor_up": "causal trailing max of close, rolling 50, shift(1)",
    "anchor_lo": "causal trailing min of close, rolling 50, shift(1)",
    "volatility_estimate": "sealed close_to_close volatility",
    "volatility_quality": "1.0 if volatility_estimate not NaN else 0.0",
    "coordinate": "signed morphic coordinate (close basis, upper family)",
    "abs_coordinate": "|coordinate|",
    "sigma_band": "unsigned band floor(|x|/STEP) — P4/P6 convention",
    "sigma_state": "signed quantization sign(x)*floor(|x|/STEP) — P7 convention",
    "previous_sigma_state": "sigma_state.shift(1)",
    "state_age": "consecutive bars in the same sigma_state (causal)",
    "transition_type": "UP/DOWN/STAY vs previous sigma_state; NA when undefined",
    "distance_to_nearest_sigma_boundary": "|x| - floor(|x|/STEP)*STEP",
    "coordinate_velocity": "coordinate - coordinate.shift(1)",
    "coordinate_acceleration": "velocity - velocity.shift(1)",
    "anchor_age": "bars since the trailing extreme last changed",
    "data_quality": "1.0 if anchor_up/anchor_lo/vol/coordinate all valid",
    "causal_known_time": "timestamp (all inputs at bar t use data <= t)",
}
