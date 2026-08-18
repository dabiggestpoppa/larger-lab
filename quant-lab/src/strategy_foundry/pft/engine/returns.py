"""A1.F01.LOG_RETURN — log returns on H1 closes.

RAW stale/closed-market slots return r=0 with an explicit stale flag.
Non-finite inputs make the observation INVALID with a reason.
"""

from __future__ import annotations

import numpy as np

INVALID = "INVALID"


def log_return(prices: np.ndarray, stale_mask: np.ndarray | None = None) -> tuple:
    """Compute r_t = ln(P_t / P_{t-1}).

    Returns (returns, valid_mask, reasons) where returns[i] is the log
    return AT slot i (NaN where invalid). stale_mask marks slots whose
    price is carried/stale; their RAW return is exactly 0 and valid.
    """
    prices = np.asarray(prices, dtype=float)
    n = len(prices)
    returns = np.full(n, np.nan)
    valid = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)

    fine = np.isfinite(prices)
    if not fine[0]:
        reasons[0] = f"{INVALID}: non-finite price at slot 0"
    else:
        valid[0] = True
        returns[0] = 0.0

    for i in range(1, n):
        p_prev, p_now = prices[i - 1], prices[i]
        if not (np.isfinite(p_prev) and np.isfinite(p_now)):
            reasons[i] = f"{INVALID}: non-finite price at slot {i}"
            continue
        if stale_mask is not None and stale_mask[i]:
            returns[i] = 0.0
            valid[i] = True
            reasons[i] = "STALE_SLOT_ZERO"
            continue
        if p_prev <= 0 or p_now <= 0:
            reasons[i] = f"{INVALID}: non-positive price at slot {i}"
            continue
        returns[i] = np.log(p_now / p_prev)
        valid[i] = True
    return returns, valid, reasons
