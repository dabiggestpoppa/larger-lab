"""K1 — DMD/Koopman phase kernel.

A1.F06.DMD_OPERATOR:  A = Y X^+ ; A Phi = Phi Lambda ; eligible modes
                      0.95 < |lambda| < 1.0, Im(lambda) > 0; unit-L2 Phi.
A1.F07.MODE_PARTICIPATION: P_W = sum|Phi rows 1-2|, P_EC = sum|Phi rows 3-6|.
A1.F08.PHASE_DISTANCE: circular DeltaPhi in [0, pi].

The DMD window is a preregistered RESEARCH_CONSTANT (720 slots, the
canonical state window); the spec does not fix n.
"""

from __future__ import annotations

import numpy as np

# Preregistered research constants (spec leaves the DMD window open).
DMD_WINDOW = 720
LAMBDA_LOW = 0.95
LAMBDA_HIGH = 1.0
PHASE_THRESHOLD = 1.57
W3_PHASE_DIVISOR = 2.0
W3_MAGNITUDE_CAP = 0.35


def dmd_step(psi_window: np.ndarray) -> dict:
    """Exact DMD over one window: X = Psi[0:n-1], Y = Psi[1:n].

    psi_window: (window, 6) observable matrix. Returns eigenvalue and
    unit-L2-normalized eigenvector arrays (all modes, not just eligible).
    """
    x = psi_window[:-1].T  # 6 x (n-1)
    y = psi_window[1:].T   # 6 x (n-1)
    a = y @ np.linalg.pinv(x)  # 6 x 6
    eigvals, eigvecs = np.linalg.eig(a)
    norms = np.linalg.norm(eigvecs, axis=0)
    eigvecs = eigvecs / norms  # unit-L2 normalization
    return {"eigenvalues": eigvals, "eigenvectors": eigvecs}


def eligible_mask(eigvals: np.ndarray) -> np.ndarray:
    mag = np.abs(eigvals)
    return (mag > LAMBDA_LOW) & (mag < LAMBDA_HIGH) & (np.imag(eigvals) > 0)


def participation(eigvecs: np.ndarray, mode: int, rows_w=(0, 1), rows_ec=(2, 5)) -> tuple:
    """P_W = sum|Phi rows 1-2|, P_EC = sum|Phi rows 3-6| for one mode."""
    p_w = float(np.abs(eigvecs[rows_w[0] : rows_w[1] + 1, mode]).sum())
    p_ec = float(np.abs(eigvecs[rows_ec[0] : rows_ec[1] + 1, mode]).sum())
    return p_w, p_ec


def phase_distance(phi_w: float, phi_ec: float) -> float:
    """Circular phase distance bounded to [0, pi]."""
    d = abs(phi_w - phi_ec)
    return min(d, 2.0 * np.pi - d)


def k1_kernel(psi: np.ndarray, r_i: np.ndarray, stale_gt_2h: np.ndarray) -> dict:
    """Full rolling K1 over the observable matrix.

    psi: (n, 6) observable [r_W, |r_W|, r_E, |r_E|, r_C, |r_C|].
    r_i: (n,) DAX returns (for w3 sign).
    stale_gt_2h: (n,) True where Brent/DAX state is stale > 2h (kernel disabled).

    Outputs per-slot: K1_VALID, w3, reason, DeltaPhi.
    """
    n = len(psi)
    w3 = np.zeros(n)
    valid = np.zeros(n, dtype=bool)
    delta_phi = np.full(n, np.nan)
    reasons = np.array([""] * n, dtype=object)

    for t in range(n):
        if stale_gt_2h[t]:
            reasons[t] = "DISABLED: Brent/DAX stale > 2h"
            continue
        if t < DMD_WINDOW - 1:
            reasons[t] = "INVALID: insufficient history (<720 slots)"
            continue
        window = psi[t - DMD_WINDOW + 1 : t + 1]
        if not np.all(np.isfinite(window)):
            reasons[t] = "INVALID: non-finite observable in window"
            continue
        result = dmd_step(window)
        eigvals, eigvecs = result["eigenvalues"], result["eigenvectors"]
        mask = eligible_mask(eigvals)
        if not mask.any():
            reasons[t] = "INVALID: no eligible DMD mode"
            continue
        idx = np.where(mask)[0]
        # lambda_W = eligible mode maximizing P_W; lambda_EC = eligible mode maximizing P_EC.
        p_w_list = [participation(eigvecs, j)[0] for j in idx]
        p_ec_list = [participation(eigvecs, j)[1] for j in idx]
        j_w = idx[int(np.argmax(p_w_list))]
        j_ec = idx[int(np.argmax(p_ec_list))]
        if j_w == j_ec:
            delta_phi[t] = 0.0
            valid[t] = True
            reasons[t] = "VALID_SAME_MODE_DELTAPHI_ZERO"
        else:
            phi_w = float(np.angle(eigvals[j_w]))
            phi_ec = float(np.angle(eigvals[j_ec]))
            dp = phase_distance(phi_w, phi_ec)
            delta_phi[t] = dp
            valid[t] = True
            if dp > PHASE_THRESHOLD:
                w3[t] = -np.sign(r_i[t]) * min(dp / W3_PHASE_DIVISOR, W3_MAGNITUDE_CAP)
                reasons[t] = "ACTIVE"
            else:
                reasons[t] = "INACTIVE: DeltaPhi <= 1.57"
    return {"w3": w3, "K1_VALID": valid, "delta_phi": delta_phi, "reason": reasons}
