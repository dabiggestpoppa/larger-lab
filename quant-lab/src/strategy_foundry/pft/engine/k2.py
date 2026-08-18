"""K2 — Brent range-asymmetry / volatility acceleration kernel.

A1.F03.GAMMA_RAW      gamma = ((H-C) - (C-L)) / (H-L); H==L -> 0
A1.F04.GAMMA_SMA3     gamma_bar = (gamma_t + gamma_{t-1} + gamma_{t-2}) / 3
A1.F05.ACCELERATION   A_t = sigma_t/sigma_{t-1} - 1; prev sigma==0 -> 0
"""

from __future__ import annotations

import numpy as np

GAMMA_SMA_WINDOW = 3


def gamma_raw(high: np.ndarray, low: np.ndarray, close: np.ndarray,
              valid_bars: np.ndarray | None = None) -> tuple:
    """gamma = ((H-C) - (C-L))/(H-L); H==L -> 0. Invalid OHLC -> INVALID."""
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    n = len(high)
    out = np.full(n, np.nan)
    valid = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    if valid_bars is None:
        valid_bars = np.ones(n, dtype=bool)

    for i in range(n):
        h, l, c = high[i], low[i], close[i]
        if not (np.isfinite(h) and np.isfinite(l) and np.isfinite(c)):
            reasons[i] = "INVALID: non-finite OHLC"
            continue
        if h == l:
            out[i] = 0.0
            valid[i] = True
            reasons[i] = "H_EQ_L_ZERO"
            continue
        if not valid_bars[i]:
            # carried/stale bar: no fresh range information
            out[i] = 0.0
            valid[i] = True
            reasons[i] = "STALE_ZERO"
            continue
        out[i] = ((h - c) - (c - l)) / (h - l)
        valid[i] = True
    return out, valid, reasons


def gamma_sma3(gamma: np.ndarray, valid: np.ndarray) -> tuple:
    """Three-hour arithmetic smooth. Insufficient history -> INVALID."""
    n = len(gamma)
    out = np.full(n, np.nan)
    out_valid = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if t < GAMMA_SMA_WINDOW - 1:
            reasons[t] = "INVALID: insufficient history (<3 bars)"
            continue
        window = gamma[t - 2 : t + 1]
        if not np.all(np.isfinite(window)):
            reasons[t] = "INVALID: non-finite gamma in window"
            continue
        out[t] = float(window.mean())
        out_valid[t] = True
    return out, out_valid, reasons


def acceleration(sigma: np.ndarray, valid: np.ndarray) -> tuple:
    """A_t = sigma_t/sigma_{t-1} - 1; previous sigma==0 -> 0; non-finite -> 0."""
    n = len(sigma)
    out = np.full(n, np.nan)
    out_valid = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if t < 1:
            reasons[t] = "INVALID: no previous sigma"
            continue
        s_prev, s_now = sigma[t - 1], sigma[t]
        if not (np.isfinite(s_prev) and np.isfinite(s_now)):
            reasons[t] = "INVALID: non-finite sigma"
            continue
        if s_prev == 0.0:
            out[t] = 0.0
            out_valid[t] = True
            reasons[t] = "PREV_SIGMA_ZERO"
            continue
        out[t] = s_now / s_prev - 1.0
        out_valid[t] = True
    return out, out_valid, reasons


def k2_weight(gamma_bar, gamma_bar_valid, accel, accel_valid,
              gamma_threshold=0.10, accel_threshold=0.025) -> tuple:
    """w1 = -0.45 * sign(gamma_bar) * min(A/0.04, 1); inactive -> w1=0.

    The leading negative sign is intentional in v2.2 (a positive
    close-skew with rising volatility produces a SHORT oil-target... the
    v2.2 corrected direction).
    """
    n = len(gamma_bar)
    w1 = np.zeros(n)
    reasons = np.array([""] * n, dtype=object)
    active = np.zeros(n, dtype=bool)
    for t in range(n):
        if not (gamma_bar_valid[t] and accel_valid[t]):
            reasons[t] = "INACTIVE: gamma_bar or accel invalid"
            continue
        if np.abs(gamma_bar[t]) <= gamma_threshold:
            reasons[t] = f"INACTIVE: |gamma_bar|={abs(gamma_bar[t]):.4f} <= {gamma_threshold}"
            continue
        if accel[t] <= accel_threshold:
            reasons[t] = f"INACTIVE: accel={accel[t]:.4f} <= {accel_threshold}"
            continue
        w1[t] = -0.45 * np.sign(gamma_bar[t]) * min(accel[t] / 0.04, 1.0)
        active[t] = True
        reasons[t] = "ACTIVE"
    return w1, active, reasons
