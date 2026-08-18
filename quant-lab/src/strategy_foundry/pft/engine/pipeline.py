"""Pre-economic A1 pipeline.

Runs the frozen kernels (K1/K2/K3/K4 -> FSM -> gross cap -> fade) over
the DEVELOPMENT partition of the synchronized panel and produces
feature/signal/state ledgers, an activation census, the signal funnel,
feature distributions, and an invalid-state ledger. NO PnL is computed;
drawdown/leg-stop overlays are fixture-only.

Protected partitions (CONFIRMATION/HOLDOUT) fail closed: the pipeline
raises if asked to compute on them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..governance.partitions import PartitionGuard, ProtectedPartitionError
from . import k1 as k1_mod
from . import k2 as k2_mod
from . import k3 as k3_mod
from . import k4 as k4_mod
from . import parkinson
from . import portfolio as port_mod
from . import returns as ret_mod

SIGNAL_ASSETS = ["W", "E", "C", "I"]


def _panel_arrays(panel: pd.DataFrame, asset: str) -> dict:
    return {
        "close": panel[f"{asset}.close_carried"].to_numpy(dtype=float),
        "high": panel[f"{asset}.high_carried"].to_numpy(dtype=float),
        "low": panel[f"{asset}.low_carried"].to_numpy(dtype=float),
        "observed": panel[f"{asset}.observed"].to_numpy(dtype=bool),
        "stale": panel[f"{asset}.stale"].to_numpy(dtype=bool),
        "stale_age": panel[f"{asset}.stale_age_hours"].to_numpy(dtype=float),
    }


def run_pre_economic(panel: pd.DataFrame, partition: str = "DEVELOPMENT") -> dict:
    """Run the pre-economic pipeline on one partition of the panel."""
    guard = PartitionGuard()
    if partition not in ("DEVELOPMENT",):
        raise ProtectedPartitionError(
            f"pre-economic pipeline only authorized on DEVELOPMENT; got {partition!r}")
    sub = panel[panel["partition"] == partition].copy()
    if len(sub) == 0:
        raise ValueError("no slots in requested partition")
    # Fail closed: protected slots must never enter the computation.
    guard.guard(partition)

    n = len(sub)
    assets = {a: _panel_arrays(sub, a) for a in SIGNAL_ASSETS}
    ec = _panel_arrays(sub, "EC")

    # ------------------------------------------------------------------
    # Returns (A1.F01)
    # ------------------------------------------------------------------
    r = {}
    for a in SIGNAL_ASSETS:
        rr, rv, rreason = ret_mod.log_return(assets[a]["close"], assets[a]["stale"])
        r[a] = {"r": rr, "valid": rv, "reason": rreason}
    r_ec, r_ec_valid, r_ec_reason = ret_mod.log_return(ec["close"], ec["stale"])

    # ------------------------------------------------------------------
    # Parkinson (A1.F02) + K2 (F03/F04/F05)
    # ------------------------------------------------------------------
    sigma_w, sigma_w_valid, sigma_w_reason = parkinson.parkinson_14h(
        assets["W"]["high"], assets["W"]["low"], assets["W"]["observed"])
    gamma, gamma_valid, gamma_reason = k2_mod.gamma_raw(
        assets["W"]["high"], assets["W"]["low"], assets["W"]["close"],
        assets["W"]["observed"])
    gamma_bar, gamma_bar_valid, gamma_bar_reason = k2_mod.gamma_sma3(gamma, gamma_valid)
    accel, accel_valid, accel_reason = k2_mod.acceleration(sigma_w, sigma_w_valid)
    w1, w1_active, w1_reason = k2_mod.k2_weight(
        gamma_bar, gamma_bar_valid, accel, accel_valid)

    # ------------------------------------------------------------------
    # K1 (F06/F07/F08)
    # ------------------------------------------------------------------
    psi = np.column_stack([
        r["W"]["r"], np.abs(r["W"]["r"]),
        r["E"]["r"], np.abs(r["E"]["r"]),
        r["C"]["r"], np.abs(r["C"]["r"]),
    ])
    stale_gt_2h = np.array(
        (assets["W"]["stale_age"] > 2) | (assets["I"]["stale_age"] > 2), dtype=bool)
    k1 = k1_mod.k1_kernel(psi, r["I"]["r"], stale_gt_2h)

    # ------------------------------------------------------------------
    # K3 (F09/F10/F11/F12)
    # ------------------------------------------------------------------
    z = {}
    z_valid = {}
    for a in SIGNAL_ASSETS:
        zz, zv = k3_mod.zscore_720(r[a]["r"], r[a]["valid"])
        z[a] = zz
        z_valid[a] = zv
    d, d_valid = k3_mod.vr_distances(z)
    # epsilon per slot
    med = np.nanmedian(d, axis=1)
    eps = 0.45 * med + 0.015 * sigma_w
    # raw classification per slot (schedule applied after)
    raw_class = np.array([""] * n, dtype=object)
    for t in range(n):
        if d_valid[t] and np.isfinite(eps[t]):
            raw_class[t] = k3_mod.classify_distances(d[t], eps[t])
    ny_hour = sub["canonical_ny"].dt.hour.to_numpy()
    eff_class = k3_mod.frozen_classification(raw_class, ny_hour)
    mult = np.array([k3_mod.TOPOLOGY_MULT[c] for c in eff_class], dtype=float)
    ols = k3_mod.k3_ols(d[:, 3], d[:, 0], d[:, 1], d_valid)  # EC, WE, WC pair columns
    w2, alpha2, base2, w2_reason = k3_mod.k3_alpha(
        d[:, 3], ols["dhat"], r["E"]["r"], r["C"]["r"], mult, ols["valid"])

    # ------------------------------------------------------------------
    # K4 (F13/F14)
    # ------------------------------------------------------------------
    b, b_valid, b_reason = k4_mod.rv6(r_ec, r_ec_valid)
    a_t = r["W"]["r"] * sigma_w
    a_valid = r["W"]["valid"] & sigma_w_valid
    alpha_d, alpha_valid, alpha_reason = k4_mod.commutator(a_t, b, a_valid, b_valid)
    w_total, wt_valid, wt_reason = k4_mod.w_total(alpha_d, alpha_valid)

    # ------------------------------------------------------------------
    # FSM / gross cap / fade (F15/F16/F17)
    # ------------------------------------------------------------------
    fsm = port_mod.cluster_fsm(w_total, w1, w2, k1["w3"])
    w_cap = port_mod.gross_cap(fsm["w_base"])
    fade = port_mod.fade_sequence(w_cap)

    # ------------------------------------------------------------------
    # Ledger
    # ------------------------------------------------------------------
    ledger = pd.DataFrame(index=sub.index)
    ledger["canonical_ny"] = sub["canonical_ny"].values
    for a in SIGNAL_ASSETS:
        ledger[f"{a}.observed"] = assets[a]["observed"]
        ledger[f"{a}.stale"] = assets[a]["stale"]
    ledger["r_W"] = r["W"]["r"]
    ledger["r_E"] = r["E"]["r"]
    ledger["r_C"] = r["C"]["r"]
    ledger["r_I"] = r["I"]["r"]
    ledger["r_EC"] = r_ec
    ledger["sigma_W"] = sigma_w
    ledger["gamma"] = gamma
    ledger["gamma_bar"] = gamma_bar
    ledger["accel"] = accel
    ledger["w1"] = w1
    ledger["w1_active"] = w1_active
    ledger["delta_phi"] = k1["delta_phi"]
    ledger["w3"] = k1["w3"]
    ledger["K1_VALID"] = k1["K1_VALID"]
    ledger["K1_reason"] = k1["reason"]
    ledger["D_EC"] = d[:, 3]
    ledger["D_WE"] = d[:, 0]
    ledger["D_WC"] = d[:, 1]
    ledger["epsilon"] = eps
    ledger["topology_raw"] = raw_class
    ledger["topology_frozen"] = eff_class
    ledger["Dhat_EC"] = ols["dhat"]
    ledger["K3_OLS_VALID"] = ols["valid"]
    ledger["K3_OLS_reason"] = ols["reason"]
    ledger["alpha2"] = alpha2
    ledger["w2"] = w2
    ledger["RV6_EC"] = b
    ledger["alpha_D"] = alpha_d
    ledger["w_total"] = w_total
    ledger["fsm_state"] = fsm["state"]
    ledger["w_base_0"] = fsm["w_base"][:, 0]
    ledger["w_base_1"] = fsm["w_base"][:, 1]
    ledger["w_base_2"] = fsm["w_base"][:, 2]
    ledger["w_cap_0"] = w_cap[:, 0]
    ledger["w_cap_1"] = w_cap[:, 1]
    ledger["w_cap_2"] = w_cap[:, 2]
    ledger["w_fade_0"] = fade["w_fade"][:, 0]
    ledger["w_fade_1"] = fade["w_fade"][:, 1]
    ledger["w_fade_2"] = fade["w_fade"][:, 2]
    ledger["fade_phase"] = fade["phase"]
    ledger["fade_reason"] = fade["reason"]
    ledger["stale_W_gt2h"] = stale_gt_2h

    # ------------------------------------------------------------------
    # Invalid-state ledger (fail-closed reason codes)
    # ------------------------------------------------------------------
    invalid = pd.DataFrame({
        "slot": sub.index,
        "canonical_ny": sub["canonical_ny"].values,
        "K1_reason": k1["reason"],
        "K2_gamma_reason": gamma_reason,
        "K2_accel_reason": accel_reason,
        "K2_w1_reason": w1_reason,
        "K3_OLS_reason": ols["reason"],
        "K3_w2_reason": w2_reason,
        "K4_RV6_reason": b_reason,
        "K4_alpha_reason": alpha_reason,
        "K4_wt_reason": wt_reason,
    })
    invalid = invalid[invalid.apply(lambda row: any(v not in ("", "VALID", "ACTIVE",
                                                              "INACTIVE") for v in row[2:]),
                                    axis=1)]

    return {
        "ledger": ledger,
        "invalid_state_ledger": invalid,
        "meta": {
            "partition": partition,
            "slots": int(n),
            "start": sub.index.min().isoformat(),
            "end": sub.index.max().isoformat(),
            "data_generation": "PFT-DATA-GEN-001",
        },
    }
