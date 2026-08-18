"""A1.F02.PARKINSON_14H — Parkinson oil volatility.

sigma_W(t) = sqrt((1/(4 ln 2)) * (1/14) * sum_{i=0}^{13} (ln(H/L))^2) * sqrt(365*24)

Uses the 14 bars ending at t (inclusive). Insufficient history or
invalid ranges make the slot INVALID with a reason (fail closed).
"""

from __future__ import annotations

import numpy as np

WINDOW = 14
K_HL = 1.0 / (4.0 * np.log(2.0))
ANNUALIZATION = np.sqrt(365.0 * 24.0)


def parkinson_14h(high: np.ndarray, low: np.ndarray, valid_bars: np.ndarray | None = None) -> tuple:
    """Rolling 14-bar Parkinson sigma. Returns (sigma, valid, reasons)."""
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    n = len(high)
    sigma = np.full(n, np.nan)
    valid = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)

    if valid_bars is None:
        valid_bars = np.ones(n, dtype=bool)

    for t in range(n):
        if t < WINDOW - 1:
            reasons[t] = "INVALID: insufficient history (<14 bars)"
            continue
        window_high = high[t - WINDOW + 1 : t + 1]
        window_low = low[t - WINDOW + 1 : t + 1]
        bars_ok = valid_bars[t - WINDOW + 1 : t + 1]
        if not np.all(np.isfinite(window_high) & np.isfinite(window_low)):
            reasons[t] = "INVALID: non-finite H/L in window"
            continue
        hl = window_high / window_low
        terms = np.where(hl > 0, np.log(hl) ** 2, 0.0)
        # Bars that are carried/stale (not observed) are allowed but their
        # range contributes zero (they are not a fresh observed range).
        terms = np.where(bars_ok, terms, 0.0)
        value = np.sqrt(K_HL * (1.0 / WINDOW) * terms.sum()) * ANNUALIZATION
        if not np.isfinite(value):
            reasons[t] = "INVALID: non-finite sigma"
            continue
        sigma[t] = value
        valid[t] = True
    return sigma, valid, reasons
