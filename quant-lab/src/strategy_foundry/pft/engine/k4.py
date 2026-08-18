"""K4 — antisymmetric coupling / commutator kernel.

A1.F13.RV6:  B_t = sample_std(r_EC,t-5..r_EC,t), ddof=1, hourly nonannualized.
A1.F14.COMMUTATOR: alpha_D(t) = (1/20) sum_{k=1..20}(A_{t-k}B_{t-k+1} - B_{t-k}A_{t-k+1});
                  k=1 intentionally uses current A_t, B_t.
             w_total = clip(sign(alpha_D) * min(|alpha_D|/0.0005, 1), -1, 1).
"""

from __future__ import annotations

import numpy as np

N = 20
RV6_WINDOW = 6
RV6_DDOF = 1
COMMUTATOR_DIVISOR = 0.0005


def rv6(r_ec: np.ndarray, valid: np.ndarray) -> tuple:
    """Six-return sample std (ddof=1), hourly, nonannualized."""
    n = len(r_ec)
    out = np.full(n, np.nan)
    out_valid = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if t < RV6_WINDOW - 1:
            reasons[t] = "INVALID: insufficient history (<6 returns)"
            continue
        window = r_ec[t - RV6_WINDOW + 1 : t + 1]
        win_valid = valid[t - RV6_WINDOW + 1 : t + 1]
        if not win_valid.all() or not np.all(np.isfinite(window)):
            reasons[t] = "INVALID: non-finite or invalid returns in window"
            continue
        out[t] = float(np.std(window, ddof=RV6_DDOF))
        out_valid[t] = True
    return out, out_valid, reasons


def commutator(a: np.ndarray, b: np.ndarray, a_valid: np.ndarray, b_valid: np.ndarray) -> tuple:
    """alpha_D per slot; k=1 term is A_{t-1}B_t - B_{t-1}A_t (current A_t/B_t enter)."""
    n = len(a)
    alpha = np.full(n, np.nan)
    ok = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if t < N:
            reasons[t] = "INVALID: insufficient history (<20 bars)"
            continue
        seg_a = a[t - N : t + 1]  # A_{t-20} .. A_t (21 values)
        seg_b = b[t - N : t + 1]  # B_{t-20} .. B_t (21 values)
        va = a_valid[t - N : t + 1]
        vb = b_valid[t - N : t + 1]
        if not (va.all() and vb.all() and np.all(np.isfinite(seg_a)) and np.all(np.isfinite(seg_b))):
            reasons[t] = "INVALID: non-finite or invalid A/B in window"
            continue
        total = 0.0
        for k in range(1, N + 1):
            # A_{t-k} B_{t-k+1} - B_{t-k} A_{t-k+1}
            total += seg_a[N - k] * seg_b[N - k + 1] - seg_b[N - k] * seg_a[N - k + 1]
        alpha[t] = total / N
        ok[t] = True
        reasons[t] = "VALID"
    return alpha, ok, reasons


def w_total(alpha_d: np.ndarray, valid: np.ndarray) -> tuple:
    """w_total = clip(sign(alpha_D) * min(|alpha_D|/0.0005, 1), -1, 1)."""
    n = len(alpha_d)
    out = np.zeros(n)
    ok = np.zeros(n, dtype=bool)
    reasons = np.array([""] * n, dtype=object)
    for t in range(n):
        if not valid[t] or not np.isfinite(alpha_d[t]):
            reasons[t] = "INACTIVE: alpha_D invalid"
            continue
        out[t] = float(np.clip(np.sign(alpha_d[t]) * min(abs(alpha_d[t]) / COMMUTATOR_DIVISOR, 1.0),
                               -1.0, 1.0))
        ok[t] = True
        reasons[t] = "ACTIVE"
    return out, ok, reasons
