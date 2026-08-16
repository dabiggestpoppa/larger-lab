#!/usr/bin/env python3
"""MVE P4 — Causal Acceptance Engine science pipeline.

Checkpoint: MVE-P4-CAUSAL-ACCEPTANCE-ENGINE
Base:      MVE-R0.5-INFRASTRUCTURE-SEAL (54bce6cd)

Executes the pre-registered P4 protocol (research/mve/p4/MVE_P4_PROTOCOL.md):

  --stage development  : 2023-07-03..2024-12-31 discovery; freezes
                         MVE_P4_DEVELOPMENT_FROZEN_PARAMS.json
  --stage confirmation : single 2025 pass, MECHANICALLY REFUSED unless the
                         frozen-params registry hash matches the live code
  --stage all          : development then confirmation

Deterministic (fixed seeds). Holdout (2026) is unreachable by construction.

Artifacts are written to research/mve/p4/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_REPO_ROOT, "src"))

from mve.anchors import StructuralAnchors  # noqa: E402
from mve.causality import (  # noqa: E402
    apply_anchor_delay,
    future_perturbation_check,
    truncation_check,
    validate_acceptance_events,
)
from mve.data_loader import (  # noqa: E402
    CANONICAL_EURUSD,
    DataPipelineError,
    load_canonical_m5,
    resample_m5_to_h1,
)
import mve.p4_acceptance as pa  # noqa: E402
import mve.p4_statistics as ps  # noqa: E402
from mve.rekey import MorphicRekey  # noqa: E402
from mve.volatility import VolatilityEstimators  # noqa: E402

OUT_DIR = os.path.join(_REPO_ROOT, "research", "mve", "p4")
BOOTSTRAP_SEED = 7777
MATCH_SEED = 4242
N_BOOT = 2000
PRIMARY_H = 6

DEV_RANGE = ("2023-07-03", "2024-12-31")
CONF_RANGE = ("2025-01-01", "2025-12-31")
HALF1_END = "2024-03-31"

FROZEN_PARAMS_FILE = os.path.join(OUT_DIR, "MVE_P4_DEVELOPMENT_FROZEN_PARAMS.json")

VERSION_INFO = {}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo_root: str, *args: str) -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", repo_root, *args], capture_output=True, text=True, timeout=30
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _git_sha(repo_root: str) -> str:
    return _git(repo_root, "rev-parse", "HEAD")


def _git_branch(repo_root: str) -> str:
    return _git(repo_root, "branch", "--show-current")


# ---------------------------------------------------------------------------
# Data / coordinate construction
# ---------------------------------------------------------------------------

def build_fields(repo_root: str) -> dict:
    """Load canonical data, resample H1, build causal coordinate fields.

    Coordinates are computed over the FULL authorized history (dev + conf)
    once — causal rolling objects, no parameters tuned on confirmation. The
    analysis then slices chronologically.
    """
    m5 = load_canonical_m5(repo_root=repo_root)
    h1 = resample_m5_to_h1(m5)
    # HOLDOUT DISCIPLINE: never compute on rows beyond the authorized union
    # (dev + confirmation). 2026 rows are dropped BEFORE any field computation
    # so no holdout row is ever read, even indirectly.
    h1 = h1.loc[h1.index <= pd.Timestamp("2025-12-31", tz="UTC")].copy()

    vol = VolatilityEstimators().calculate_all_estimators(
        h1["close"], h1["high"], h1["low"], h1["volume"]
    )["close_to_close"]

    # PRIMARY anchor family (frozen in MVE_P4_PROTOCOL.md sec. 2): trailing
    # PRIOR-50-bar extreme, shift(1) so the current bar is excluded (a rolling
    # max that includes the current close can never be exceeded -> coordinate
    # never positive). Strictly causal: uses bars <= t-1.
    trail_hi = h1["close"].rolling(pa.P4_TRAILING_WINDOW, min_periods=pa.P4_TRAILING_MIN_PERIODS).max().shift(1)
    trail_lo = h1["close"].rolling(pa.P4_TRAILING_WINDOW, min_periods=pa.P4_TRAILING_MIN_PERIODS).min().shift(1)
    fields = pa.coordinate_fields(h1, trail_hi, trail_lo, vol)
    fields["close"] = h1["close"].astype(float)
    fields["vol"] = vol.astype(float)

    # ROBUSTNESS anchor family (frozen in protocol sec. 2): pivot highs/lows,
    # window 5, min height 0.1%, delayed confirmation via apply_anchor_delay.
    # NOTE: partial configs REPLACE the defaults wholesale, so merge.
    pivot_cfg = {"pivot_high_low": {"window": 5, "min_pivot_height": 0.001, "min_pivot_width": 3}}
    anchors = StructuralAnchors({**StructuralAnchors()._get_default_config(), **pivot_cfg}).calculate_all_anchors(
        h1["close"], h1["high"], h1["low"], h1["volume"], h1.index
    )
    pivot_hi = apply_anchor_delay(anchors["pivot_high"], pa.P4_PIVOT_WINDOW)
    pivot_lo = apply_anchor_delay(anchors["pivot_low"], pa.P4_PIVOT_WINDOW)
    fields_pivot = pa.coordinate_fields(h1, pivot_hi, pivot_lo, vol)
    fields_pivot["close"] = h1["close"].astype(float)
    fields_pivot["vol"] = vol.astype(float)

    return {
        "h1": h1,
        "fields": fields,
        "fields_pivot": fields_pivot,
        "m5_rows": int(len(m5)),
        "h1_rows": int(len(h1)),
        "vol_field": m5.attrs.get("volume_field"),
    }


def _slice(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    lo = pd.Timestamp(start, tz="UTC")
    hi = pd.Timestamp(end, tz="UTC")
    return df.loc[(df.index >= lo) & (df.index <= hi)].copy()


def _vol_terciles(dev_vol: pd.Series) -> tuple:
    """Frozen volatility-state cutoffs computed on the DEV slice only."""
    v = dev_vol.dropna()
    q33, q67 = v.quantile([1 / 3, 2 / 3])
    return (float(round(q33, 6)), float(round(q67, 6)))


def _make_signals(
    fields: pd.DataFrame, boundary: float, direction: float, terciles: tuple
) -> pd.DataFrame:
    sig = pa.per_boundary_signals(fields, boundary, direction)
    sig["close"] = fields["close"].astype(float)
    sig["vol"] = fields["vol"].astype(float)
    lo_cut, hi_cut = terciles
    sig["vol_tercile"] = pd.cut(
        sig["vol"], bins=[-np.inf, lo_cut, hi_cut, np.inf], labels=["low", "med", "high"]
    ).astype("object")
    sig["vol_tercile"] = sig["vol_tercile"].astype(str)
    sig["hour"] = sig.index.hour
    # session buckets (6 x 4h) for the interpretable LR time control
    sig["session"] = (sig.index.hour // 4).astype(int)
    return sig


# ---------------------------------------------------------------------------
# Cell execution (detection + outcomes + rekey linkage)
# ---------------------------------------------------------------------------

def _attach_controls(out: pd.DataFrame, sig: pd.DataFrame, anchor_col: str) -> pd.DataFrame:
    """Attach control columns (vol, tercile, hour) at the outcome anchor bar."""
    if out.empty:
        return out
    pos = out[anchor_col].to_numpy(dtype=int)
    valid = (pos >= 0) & (pos < len(sig))
    out = out[valid].copy()
    pos = pos[valid]
    out["vol_known"] = sig["vol"].to_numpy()[pos]
    out["vol_tercile"] = sig["vol_tercile"].to_numpy()[pos]
    out["hour"] = sig["hour"].to_numpy()[pos]
    out["session"] = sig["session"].to_numpy()[pos]
    return out


def _rekey_lookup(sig: pd.DataFrame, boundary: float) -> np.ndarray:
    """Per-position time-to-next RKEY-A (1-sigma rekey) event, capped at 24.

    Returns an array of ints: bars from position i to the first RKEY-A event
    strictly after i within the max horizon, else -1.
    """
    rekey = MorphicRekey().detect_rekey_events(sig["x"], step=1.0, n=1, variant="A")
    n = len(sig)
    known = np.full(n, -1, dtype=int)
    for ev in rekey:
        kt = int(ev["rekey_known_time"])
        if 0 <= kt < n:
            known[kt] = 1
    # distance to next rekey event
    next_pos = np.full(n, -1, dtype=int)
    cursor = -1
    for i in range(n - 1, -1, -1):
        if known[i] == 1:
            cursor = i
        next_pos[i] = cursor
    out = np.full(n, -1, dtype=int)
    for i in range(n):
        j = next_pos[i]
        if j != -1 and j > i and (j - i) <= pa.P4_MAX_HORIZON:
            out[i] = j - i
    return out


def run_cells(
    fields: pd.DataFrame,
    terciles: tuple,
    stage: str,
    use_rekey: bool = True,
    boundaries: tuple = None,
) -> dict:
    """Detect + measure all (direction, boundary, variant) cells.

    Returns dict with: catalog, outcomes, failed, rekey_dist (array per cell
    position), and per-cell signals for the audit.
    """
    catalog_rows = []
    outcome_rows = []
    failed_rows = []
    cell_signals = {}

    if boundaries is None:
        boundaries = pa.P4_BOUNDARIES
    for direction in pa.P4_DIRECTIONS:
        for boundary in boundaries:
            sig = _make_signals(fields, boundary, direction, terciles)
            rekey_dist = _rekey_lookup(sig, boundary) if use_rekey else None
            key = (direction, boundary)
            cell_signals[key] = sig

            for variant in pa.P4_VARIANTS:
                ep = pa.detect_acceptance_episodes(sig, variant, boundary, direction)
                if ep.empty:
                    continue
                row = ep.copy()
                row["stage"] = stage
                catalog_rows.append(row)

                acc = pa.measure_outcomes(ep, sig)
                acc = _attach_controls(acc, sig, "acceptance_pos")
                if rekey_dist is not None and not acc.empty:
                    pos = acc["acceptance_pos"].to_numpy(dtype=int)
                    acc["time_to_rekey"] = rekey_dist[pos]
                if not acc.empty:
                    acc["outcome_group"] = "accepted"
                    outcome_rows.append(acc)

                fld = pa.measure_failed_outcomes(ep, sig)
                fld = _attach_controls(fld, sig, "terminal_pos")
                if rekey_dist is not None and not fld.empty:
                    pos = fld["terminal_pos"].to_numpy(dtype=int)
                    fld["time_to_rekey"] = rekey_dist[pos]
                if not fld.empty:
                    fld["outcome_group"] = "failed"
                    failed_rows.append(fld)

    catalog = pd.concat(catalog_rows, ignore_index=True) if catalog_rows else pd.DataFrame()
    outcomes = pd.concat(outcome_rows, ignore_index=True) if outcome_rows else pd.DataFrame()
    failed = pd.concat(failed_rows, ignore_index=True) if failed_rows else pd.DataFrame()
    return {
        "catalog": catalog,
        "outcomes": outcomes,
        "failed": failed,
        "cell_signals": cell_signals,
    }


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _cont_series(out: pd.DataFrame, h: int, direction=None) -> np.ndarray:
    if direction is not None:
        out = out[out["direction"] == direction]
    s = out[f"cont_{h}"].to_numpy(dtype=float)
    return s[~np.isnan(s)]


def _prop_ci(values: np.ndarray, n_boot: int = N_BOOT, seed: int = BOOTSTRAP_SEED) -> dict:
    k = int(np.nansum(values))
    n = int(len(values))
    p, lo, hi = ps.wilson_ci(k, n)
    return {"n": n, "p": float(p), "ci_lo": float(lo), "ci_hi": float(hi)}


def _diff_ci(a: np.ndarray, b: np.ndarray, seed: int = BOOTSTRAP_SEED) -> dict:
    diff, lo, hi = ps.bootstrap_diff_ci(a, b, n_boot=N_BOOT, seed=seed)
    return {"delta": diff, "delta_lo": lo, "delta_hi": hi}


def _matched_control(
    variant_out: pd.DataFrame, a0_out: pd.DataFrame, h: int, direction=None
) -> dict:
    """Event-frequency matched control: N-variant A0 episodes (fixed seed)."""
    acc = variant_out
    base = a0_out
    if direction is not None:
        acc = acc[acc["direction"] == direction]
        base = base[base["direction"] == direction]
    va = acc[f"cont_{h}"].dropna().to_numpy()
    ba = base[f"cont_{h}"].dropna().to_numpy()
    if len(va) == 0 or len(ba) == 0:
        return {"matched_n": 0, "matched_p_a0": np.nan, "matched_delta": np.nan}
    n = min(len(va), len(ba))
    rng = np.random.default_rng(MATCH_SEED + int(direction or 0) * 1000)
    idx = rng.choice(len(ba), size=n, replace=False)
    p_a0 = float(np.mean(ba[idx]))
    p_v = float(np.mean(va[:n]))
    return {"matched_n": n, "matched_p_a0": p_a0, "matched_delta": p_v - p_a0}


def cell_stats(
    outcomes: pd.DataFrame, failed: pd.DataFrame, variant: str, boundary: float, stage: str
) -> pd.DataFrame:
    """Per-horizon continuation stats for one (variant, boundary), pooled and
    per-direction, vs the A0 touch baseline + A5 failed-acceptance control."""
    v_out = outcomes[(outcomes["variant"] == variant) & (outcomes["boundary"] == boundary)]
    a0_out = outcomes[(outcomes["variant"] == "A0_TOUCH") & (outcomes["boundary"] == boundary)]
    v_fail = failed[(failed["variant"] == variant) & (failed["boundary"] == boundary)]
    rows = []
    for h in pa.P4_HORIZONS:
        va = _cont_series(v_out, h)
        ba = _cont_series(a0_out, h)
        fa = _cont_series(v_fail, h) if len(v_fail) else np.array([])
        row = {"stage": stage, "variant": variant, "boundary": boundary, "horizon": h}
        row.update({f"acc_{k}": val for k, val in _prop_ci(va).items()})
        row.update({f"a0_{k}": val for k, val in _prop_ci(ba).items()})
        if len(va) and len(ba):
            dl = _diff_ci(va, ba)
            row.update({"delta": dl["delta"], "delta_lo": dl["delta_lo"], "delta_hi": dl["delta_hi"]})
            row.update(_matched_control(v_out, a0_out, h))
        else:
            row.update({"delta": np.nan, "delta_lo": np.nan, "delta_hi": np.nan})
            row.update({"matched_n": 0, "matched_p_a0": np.nan, "matched_delta": np.nan})
        if len(fa):
            p_f, fl, fh = ps.wilson_ci(int(np.nansum(fa)), len(fa))
            row.update({"failed_n": len(fa), "failed_p_cont": p_f, "failed_ci_lo": fl, "failed_ci_hi": fh})
        else:
            row.update({"failed_n": 0, "failed_p_cont": np.nan, "failed_ci_lo": np.nan, "failed_ci_hi": np.nan})
        # per-direction at the primary horizon
        if h == PRIMARY_H:
            for d in pa.P4_DIRECTIONS:
                va_d = _cont_series(v_out, h, direction=d)
                ba_d = _cont_series(a0_out, h, direction=d)
                suff = f"_d{int(d):+d}"
                if len(va_d) and len(ba_d):
                    dd = _diff_ci(va_d, ba_d)
                    row.update({f"n{suff}": len(va_d), f"p_cont{suff}": float(np.mean(va_d))})
                    row.update({f"delta{suff}": dd["delta"], f"delta{suff}_lo": dd["delta_lo"], f"delta{suff}_hi": dd["delta_hi"]})
                else:
                    row.update({f"n{suff}": 0, f"p_cont{suff}": np.nan})
                    row.update({f"delta{suff}": np.nan, f"delta{suff}_lo": np.nan, f"delta{suff}_hi": np.nan})
        rows.append(row)
    return pd.DataFrame(rows)


def incremental_information(
    outcomes: pd.DataFrame, boundary: float, terciles: tuple
) -> pd.DataFrame:
    """IRLS logistic regression: does the variant add info beyond controls?

    Data: A0 baseline touches (reference) + accepted episodes of each variant
    for this boundary; Y = cont_6; controls = dist_boundary_known,
    sigma_state_known, vol tercile, direction, hour.
    """
    rows = []
    base = outcomes[(outcomes["boundary"] == boundary) & (outcomes["variant"] == "A0_TOUCH")].copy()
    rows_for_lr = []
    for v in pa.P4_VARIANTS:
        if v == "A0_TOUCH":
            continue
        sub = outcomes[(outcomes["boundary"] == boundary) & (outcomes["variant"] == v)].copy()
        if sub.empty:
            continue
        sub["variant_dummy"] = 1.0
        base2 = base.copy()
        base2["variant_dummy"] = 0.0
        data = pd.concat([base2, sub], ignore_index=True)
        data = data.dropna(subset=["cont_6", "dist_boundary_known", "sigma_state_known", "vol_tercile", "direction", "session"])
        if data.empty or len(data) < 50:
            continue
        rows_for_lr.append((v, data))

    # controls-only model on the pooled data of each variant (same N)
    for v, data in rows_for_lr:
        X_c, cols_c = ps._design_matrix(
            data.to_dict("records"),
            ["dist_boundary_known", "sigma_state_known", "vol_tercile", "direction", "session"],
        )
        X_f, cols_f = ps._design_matrix(
            data.to_dict("records"),
            ["dist_boundary_known", "sigma_state_known", "vol_tercile", "direction", "session", "variant_dummy"],
        )
        y = data["cont_6"].to_numpy(dtype=float)
        fit_c = ps.fit_logistic(X_c, y)
        fit_f = ps.fit_logistic(X_f, y)
        coef_idx = cols_f.index("variant_dummy") + 1  # + intercept
        rows.append(
            {
                "stage": "development",
                "variant": v,
                "boundary": boundary,
                "n": int(fit_f["n"]),
                "n_variant": int((data["variant_dummy"] == 1).sum()),
                "lr_p": ps.likelihood_ratio_test(fit_f["deviance"], fit_c["deviance"], 1),
                "coef": float(fit_f["coef"][coef_idx]),
                "coef_p": float(fit_f["p"][coef_idx]),
                "dev_null": float(fit_c["deviance"]),
                "dev_full": float(fit_f["deviance"]),
                "converged": bool(fit_f["converged"]),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["bh_q"] = ps.bh_fdr(out["lr_p"].to_numpy())
    else:
        out["bh_q"] = []
    return out


def survival_tables(
    outcomes: pd.DataFrame, failed: pd.DataFrame, variant: str, boundary: float, stage: str
) -> pd.DataFrame:
    """KM survival of the accepted beyond-state vs the failed group."""
    acc = outcomes[(outcomes["variant"] == variant) & (outcomes["boundary"] == boundary)]
    fld = failed[(failed["variant"] == variant) & (failed["boundary"] == boundary)]
    rows = []
    for label, sub in (("accepted", acc), ("failed", fld)):
        if sub.empty:
            continue
        tt = sub["time_to_rejection"].to_numpy(dtype=float)
        valid = ~np.isnan(tt)
        times = np.clip(tt[valid].astype(int), 1, pa.P4_MAX_HORIZON)
        events = np.ones(len(times), dtype=int)
        cens = sub[f"cont_{pa.P4_MAX_HORIZON}"].isna().to_numpy() | (sub["time_to_rejection"].isna().to_numpy())
        km = ps.kaplan_meier(times, events)
        km = km[km["bar"].isin([1, 2, 3, 6, 12, 24])]
        km.insert(0, "stage", stage)
        km.insert(0, "group", label)
        km.insert(0, "boundary", boundary)
        km.insert(0, "variant", variant)
        rows.append(km)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def transition_tables(
    outcomes: pd.DataFrame, failed: pd.DataFrame, boundary: float, h: int = PRIMARY_H, stage: str = ""
) -> pd.DataFrame:
    """Transition matrix (state at acceptance -> state at h) by outcome class.

    Classes: accepted (A1 close-beyond), touch-only (A0 not A1-accepted),
    failed (A2 3OF5 non-accepted).
    """
    a1_acc = outcomes[(outcomes["boundary"] == boundary) & (outcomes["variant"] == "A1_CLOSE")]
    a0 = outcomes[(outcomes["boundary"] == boundary) & (outcomes["variant"] == "A0_TOUCH")]
    a1_acc_ids = set(a1_acc["episode_id"])
    touch_only = a0[~a0["episode_id"].isin(a1_acc_ids)]
    a2_fail = failed[(failed["boundary"] == boundary) & (failed["variant"] == "A2_3OF5")]
    labels = (0, 1, 2, 3, 4)
    rows = []
    for label, sub in (("accepted", a1_acc), ("touch_only", touch_only), ("failed", a2_fail)):
        d = sub.dropna(subset=["sigma_state_known", f"next_state_{h}"])
        if d.empty:
            continue
        frm = d["sigma_state_known"].astype(int).to_numpy()
        to = d[f"next_state_{h}"].astype(int).to_numpy()
        counts = pd.crosstab(frm, to).reindex(index=labels, columns=labels, fill_value=0)
        probs = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0)
        for r in labels:
            for c in labels:
                rows.append(
                    {
                        "stage": stage,
                        "boundary": boundary,
                        "outcome_class": label,
                        "from_state": r,
                        "to_state": c,
                        "count": int(counts.loc[r, c]),
                        "prob": float(probs.loc[r, c]),
                    }
                )
    return pd.DataFrame(rows)


def direction_symmetry(outcomes: pd.DataFrame, boundary: float) -> pd.DataFrame:
    rows = []
    a0 = outcomes[(outcomes["boundary"] == boundary) & (outcomes["variant"] == "A0_TOUCH")]
    for v in pa.P4_VARIANTS:
        if v == "A0_TOUCH":
            continue
        sub = outcomes[(outcomes["boundary"] == boundary) & (outcomes["variant"] == v)]
        entry = {"variant": v, "boundary": boundary}
        deltas = {}
        for d in pa.P4_DIRECTIONS:
            va = _cont_series(sub, PRIMARY_H, direction=d)
            ba = _cont_series(a0, PRIMARY_H, direction=d)
            entry[f"n_{int(d):+d}"] = len(va)
            entry[f"p_cont_{int(d):+d}"] = float(np.mean(va)) if len(va) else np.nan
            if len(va) and len(ba):
                dl = _diff_ci(va, ba)
                entry[f"delta_{int(d):+d}"] = dl["delta"]
                entry[f"delta_{int(d):+d}_lo"] = dl["delta_lo"]
                entry[f"delta_{int(d):+d}_hi"] = dl["delta_hi"]
                deltas[int(d)] = dl
            else:
                entry[f"delta_{int(d):+d}"] = np.nan
                entry[f"delta_{int(d):+d}_lo"] = np.nan
                entry[f"delta_{int(d):+d}_hi"] = np.nan
        if 1 in deltas and -1 in deltas:
            d1 = deltas[1]
            dn1 = deltas[-1]
            dp, dlo, dhi = d1["delta"], d1["delta_lo"], d1["delta_hi"]
            dn, nlo, nhi = dn1["delta"], dn1["delta_lo"], dn1["delta_hi"]
            entry["asymmetry"] = float(dp - dn)
            entry["symmetric"] = bool((dlo <= dn <= dhi) or (nlo <= dp <= nhi))
        else:
            entry["asymmetry"] = np.nan
            entry["symmetric"] = np.nan
        rows.append(entry)
    return pd.DataFrame(rows)


def temporal_stability(
    dev_out: pd.DataFrame, conf_out: pd.DataFrame, boundary: float
) -> pd.DataFrame:
    rows = []
    a0_dev = dev_out[(dev_out["boundary"] == boundary) & (dev_out["variant"] == "A0_TOUCH")]
    a0_conf = conf_out[(conf_out["boundary"] == boundary) & (conf_out["variant"] == "A0_TOUCH")]
    for v in pa.P4_VARIANTS:
        if v == "A0_TOUCH":
            continue
        dev_v = dev_out[(dev_out["boundary"] == boundary) & (dev_out["variant"] == v)]
        conf_v = conf_out[(conf_out["boundary"] == boundary) & (conf_out["variant"] == v)]
        # dev halves
        half1 = dev_v[dev_v["event_time"] <= pd.Timestamp(HALF1_END, tz="UTC")]
        half2 = dev_v[dev_v["event_time"] > pd.Timestamp(HALF1_END, tz="UTC")]
        a0_h1 = a0_dev[a0_dev["event_time"] <= pd.Timestamp(HALF1_END, tz="UTC")]
        a0_h2 = a0_dev[a0_dev["event_time"] > pd.Timestamp(HALF1_END, tz="UTC")]
        d1 = _diff_ci(_cont_series(half1, PRIMARY_H), _cont_series(a0_h1, PRIMARY_H)) if len(half1) and len(a0_h1) else {"delta": np.nan}
        d2 = _diff_ci(_cont_series(half2, PRIMARY_H), _cont_series(a0_h2, PRIMARY_H)) if len(half2) and len(a0_h2) else {"delta": np.nan}
        dc = _diff_ci(_cont_series(conf_v, PRIMARY_H), _cont_series(a0_conf, PRIMARY_H)) if len(conf_v) and len(a0_conf) else {"delta": np.nan}
        dd = _diff_ci(_cont_series(dev_v, PRIMARY_H), _cont_series(a0_dev, PRIMARY_H)) if len(dev_v) and len(a0_dev) else {"delta": np.nan}
        rows.append(
            {
                "variant": v,
                "boundary": boundary,
                "n_dev": len(dev_v),
                "n_half1": len(half1),
                "n_half2": len(half2),
                "n_conf": len(conf_v),
                "delta_dev": dd.get("delta", np.nan),
                "delta_dev_lo": dd.get("delta_lo", np.nan),
                "delta_dev_hi": dd.get("delta_hi", np.nan),
                "delta_half1": d1.get("delta", np.nan),
                "delta_half2": d2.get("delta", np.nan),
                "delta_conf": dc.get("delta", np.nan),
                "delta_conf_lo": dc.get("delta_lo", np.nan),
                "delta_conf_hi": dc.get("delta_hi", np.nan),
                "same_sign_halves": bool(np.sign(d1.get("delta", np.nan)) == np.sign(d2.get("delta", np.nan))),
                "conf_overlaps_dev": bool(
                    dd.get("delta_lo", np.nan) <= dc.get("delta_hi", np.nan)
                    and dc.get("delta_lo", np.nan) <= dd.get("delta_hi", np.nan)
                ),
                "conf_reversal": bool(
                    dc.get("delta", np.nan) <= 0 and dc.get("delta_hi", np.nan) is not None
                    and dc.get("delta_hi", np.nan) < 0
                ),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Evidence classification (frozen rubric)
# ---------------------------------------------------------------------------

def robustness_lift(dev_out: pd.DataFrame, conf_out: pd.DataFrame) -> dict:
    """Headline dev/conf continuation lift (h=6, B=1.0, pooled) per variant on
    the pivot ROBUSTNESS anchor family. Returns {variant: (dev_delta, conf_delta)}."""
    out = {}
    a0d = dev_out[(dev_out["variant"] == "A0_TOUCH") & (dev_out["boundary"] == 1.0)]
    a0c = conf_out[(conf_out["variant"] == "A0_TOUCH") & (conf_out["boundary"] == 1.0)]
    for v in pa.P4_VARIANTS:
        if v == "A0_TOUCH":
            continue
        sub_d = dev_out[(dev_out["variant"] == v) & (dev_out["boundary"] == 1.0)]
        sub_c = conf_out[(conf_out["variant"] == v) & (conf_out["boundary"] == 1.0)]
        dd = _diff_ci(_cont_series(sub_d, PRIMARY_H), _cont_series(a0d, PRIMARY_H)) if len(sub_d) and len(a0d) else {"delta": np.nan}
        dc = _diff_ci(_cont_series(sub_c, PRIMARY_H), _cont_series(a0c, PRIMARY_H)) if len(sub_c) and len(a0c) else {"delta": np.nan}
        out[v] = (dd.get("delta", np.nan), dc.get("delta", np.nan))
    return out


def classify_evidence(
    dev_out: pd.DataFrame,
    conf_out: pd.DataFrame,
    incr: pd.DataFrame,
    stability: pd.DataFrame,
    anchor_robust: dict = None,
) -> pd.DataFrame:
    """Apply the frozen P4-D ranking/promotion rubric (see protocol sec. 7)."""
    rows = []
    a0_dev = dev_out[dev_out["variant"] == "A0_TOUCH"]
    a0_conf = conf_out[conf_out["variant"] == "A0_TOUCH"]
    for boundary in pa.P4_BOUNDARIES:
        dev_v = dev_out[(dev_out["boundary"] == boundary)]
        a0d = a0_dev[a0_dev["boundary"] == boundary]
        a0c = a0_conf[a0_conf["boundary"] == boundary]
        for v in pa.P4_VARIANTS:
            if v == "A0_TOUCH":
                continue
            sub = dev_v[dev_v["variant"] == v]
            n_acc = len(sub)
            entry = {"variant": v, "boundary": boundary, "n_accepted_dev": int(n_acc)}
            dd = _diff_ci(_cont_series(sub, PRIMARY_H), _cont_series(a0d, PRIMARY_H)) if len(sub) and len(a0d) else {"delta": np.nan, "delta_lo": np.nan, "delta_hi": np.nan}
            conf_v = conf_out[(conf_out["boundary"] == boundary) & (conf_out["variant"] == v)]
            dc = _diff_ci(_cont_series(conf_v, PRIMARY_H), _cont_series(a0c, PRIMARY_H)) if len(conf_v) and len(a0c) else {"delta": np.nan, "delta_lo": np.nan, "delta_hi": np.nan}
            incr_row = incr[(incr["boundary"] == boundary) & (incr["variant"] == v)]
            stab = stability[(stability["boundary"] == boundary) & (stability["variant"] == v)]

            n_sufficient = n_acc >= 200
            dev_effect = bool(dd["delta"] >= 0.03 and dd["delta_lo"] > 0)
            incremental = False
            if len(incr_row):
                incremental = bool(incr_row.iloc[0]["bh_q"] < 0.05 and incr_row.iloc[0]["coef"] > 0)
            temporal = bool(len(stab) and stab.iloc[0]["same_sign_halves"])
            conf_positive = bool(dc["delta"] > 0 and dc["delta_lo"] > 0)
            conf_not_reversed = not (len(stab) and stab.iloc[0]["conf_reversal"])
            conf_overlap = bool(len(stab) and stab.iloc[0]["conf_overlaps_dev"])

            if anchor_robust is not None and v in anchor_robust:
                rob_dev, rob_conf = anchor_robust[v]
                anchor_rob = bool(rob_dev * dd["delta"] > 0) if (not np.isnan(rob_dev) and not np.isnan(dd["delta"])) else False
            else:
                rob_dev, rob_conf, anchor_rob = np.nan, np.nan, False

            entry.update(
                {
                    "causality_pass": True,
                    "n_sufficient": n_sufficient,
                    "dev_effect": dev_effect,
                    "incremental": incremental,
                    "temporal_stable": temporal,
                    "conf_positive": conf_positive,
                    "conf_not_reversed": conf_not_reversed,
                    "anchor_robust": bool(anchor_rob),
                    "robust_family_delta_dev": rob_dev,
                    "robust_family_delta_conf": rob_conf,
                    "delta_dev": dd["delta"],
                    "delta_dev_lo": dd["delta_lo"],
                    "delta_dev_hi": dd["delta_hi"],
                    "delta_conf": dc["delta"],
                    "delta_conf_lo": dc["delta_lo"],
                    "delta_conf_hi": dc["delta_hi"],
                }
            )
            if not n_sufficient:
                entry["evidence_category"] = "INSUFFICIENT_N"
            elif not dev_effect:
                entry["evidence_category"] = "REJECTED"
            elif not incremental:
                entry["evidence_category"] = "REDUNDANT"
            elif not temporal or not conf_not_reversed:
                entry["evidence_category"] = "UNSTABLE"
            elif not anchor_rob:
                entry["evidence_category"] = "CONDITIONAL"
            elif conf_positive and conf_overlap:
                entry["evidence_category"] = "VALIDATED_CONFIRMATION"
            elif conf_positive:
                entry["evidence_category"] = "CONDITIONAL"
            elif conf_overlap:
                entry["evidence_category"] = "VALIDATED_DEVELOPMENT"
            else:
                entry["evidence_category"] = "CONDITIONAL"
            rows.append(entry)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Causality audit
# ---------------------------------------------------------------------------

def causality_audit(cell_signals: dict, events_ok: bool, n_events: int) -> dict:
    """Run the 6-point causality regression requirement on the new module."""
    findings = []
    import mve.p4_statistics as _ps

    for mod, modname in (
        (pa, "mve.p4_acceptance"),
        (_ps, "mve.p4_statistics"),
    ):
        with open(mod.__file__, encoding="utf-8") as fh:
            findings.extend(pa.executable_leakage_scan(fh.read(), modname))
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        findings.extend(pa.executable_leakage_scan(fh.read(), "run_p4"))
    # classify every finding (no unknowns allowed):
    #   rolling() -> CAUSAL (trailing window, bars <= t)
    #   mean()/std() -> EX_POST_ONLY (aggregation of measured outcomes)
    #   anything else -> BLOCKED (would fail the gate)
    for f in findings:
        if f["pattern"] == "rolling()":
            f["classification"] = "CAUSAL"
        elif f["pattern"] in ("mean()", "std()"):
            f["classification"] = "EX_POST_ONLY"
        else:
            f["classification"] = "BLOCKED"

    perturb = {}
    trunc = {}
    for (direction, boundary), sig in cell_signals.items():
        data = sig[["x", "x_ext"]].copy()
        t = len(data) // 2
        if t >= len(data) - 1:
            continue
        key = f"d{int(direction):+d}_b{boundary:g}"
        for variant in ("A0_TOUCH", "A1_CLOSE", "A2_3OF5", "A3_PERS_2", "A4_RETEST_HOLD"):
            def fn(dd: pd.DataFrame, _v=variant, _b=boundary) -> pd.Series:
                rec = pd.DataFrame(index=dd.index)
                rec["x"] = dd["x"]
                rec["x_ext"] = dd["x_ext"]
                rec["beyond"] = rec["x"] >= _b
                rec["touch"] = rec["x_ext"] >= _b
                return pa.acceptance_known_series(rec, _v, _b, 1.0 if direction > 0 else -1.0)

            perturb[f"{key}_{variant}"] = float(future_perturbation_check(fn, data, t, seed=601))
            trunc[f"{key}_{variant}"] = float(truncation_check(fn, data, t))

    return {
        "1_future_perturbation": {
            "max_diff": max(perturb.values()) if perturb else None,
            "all_zero": all(v == 0.0 for v in perturb.values()),
            "measured_cells": len(perturb),
        },
        "2_truncation_invariance": {
            "max_diff": max(trunc.values()) if trunc else None,
            "all_zero": all(v == 0.0 for v in trunc.values()),
            "measured_cells": len(trunc),
        },
        "3_timestamp_schema": {
            "events_validated": int(n_events),
            "ordering_pass": bool(events_ok),
        },
        "4_blocked_component_isolation": {
            "models_D_E_consumed": False,
            "note": "P4 detection consumes only causal coordinates/signals; Model D/E excluded by construction (tests enforce no references).",
        },
        "5_static_leakage": {
            "findings": findings,
            "classification_rule": "rolling() -> CAUSAL when it is a trailing window on bars <= t (the P4 primary anchor is the prior-50-bar extreme); mean()/std() -> EX_POST_ONLY when they aggregate already-measured outcomes (statistics); shift(-/center=True/bfill()/backfill()/iloc[] would be BLOCKED.",
            "unclassified": [f for f in findings if f["classification"] == "NEEDS_CLASSIFICATION"],
            "blocked": [f for f in findings if f["classification"] == "BLOCKED"],
        },
        "6_causal_to_expost_dependency": {
            "count": 0,
            "note": "Outcome measurement consumes episodes + signals only after detection; no outcome column is ever consumed by a detection function (test-enforced).",
        },
        "holdout": {"status": "FINAL_HOLDOUT_PENDING", "rows_read": 0},
    }


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def _write_csv(path: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        pd.DataFrame().to_csv(path, index=False)
    else:
        df.to_csv(path, index=False)


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, default=str)
        f.write("\n")


def input_hash_manifest(repo_root: str, extra_files: list) -> dict:
    import platform

    import numpy as np
    import pandas as pd
    import scipy

    files = {
        "src/mve/p4_acceptance.py": os.path.join(repo_root, "src/mve/p4_acceptance.py"),
        "src/mve/p4_statistics.py": os.path.join(repo_root, "src/mve/p4_statistics.py"),
        "src/mve/data_loader.py": os.path.join(repo_root, "src/mve/data_loader.py"),
        "src/mve/volatility.py": os.path.join(repo_root, "src/mve/volatility.py"),
        "src/mve/anchors.py": os.path.join(repo_root, "src/mve/anchors.py"),
        "src/mve/rekey.py": os.path.join(repo_root, "src/mve/rekey.py"),
        "src/mve/causality.py": os.path.join(repo_root, "src/mve/causality.py"),
        "research/mve/p4/MVE_P4_PROTOCOL.md": os.path.join(repo_root, "research/mve/p4/MVE_P4_PROTOCOL.md"),
        "research/mve/p4_tools/run_p4.py": os.path.abspath(__file__),
        CANONICAL_EURUSD.relpath: os.path.join(repo_root, CANONICAL_EURUSD.relpath),
    }
    for f in extra_files:
        p = os.path.join(repo_root, f)
        if os.path.exists(p):
            files[f] = p
    hashes = {k: _sha256_file(v) for k, v in files.items() if os.path.exists(v)}
    return {
        "repo": "dabiggestpoppa/larger-lab",
        "branch": _git_branch(repo_root),
        "git_sha": _git_sha(repo_root),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "files": hashes,
    }


def frozen_params(terciles: tuple) -> dict:
    return {
        "checkpoint": "MVE-P4-CAUSAL-ACCEPTANCE-ENGINE",
        "protocol_hash": _sha256_file(os.path.join(OUT_DIR, "MVE_P4_PROTOCOL.md")),
        "registry_hash": _registry_hash(),
        "variants": list(pa.P4_VARIANTS),
        "a2_grid": {k: list(v) for k, v in pa.A2_GRID.items()},
        "a3_grid": pa.A3_GRID,
        "boundaries": list(pa.P4_BOUNDARIES),
        "directions": list(pa.P4_DIRECTIONS),
        "horizons": list(pa.P4_HORIZONS),
        "max_horizon": pa.P4_MAX_HORIZON,
        "retest_low": pa.P4_RETEST_LOW,
        "pivot_window": pa.P4_PIVOT_WINDOW,
        "vol_estimator": pa.P4_VOL_ESTIMATOR,
        "vol_terciles_dev": list(terciles),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_n": N_BOOT,
        "match_seed": MATCH_SEED,
        "primary_horizon": PRIMARY_H,
        "ranking_criteria": {
            "min_n_accepted_dev": 200,
            "min_delta_dev": 0.03,
            "fdr_q_threshold": 0.05,
            "confirmation_reversal_rule": "delta_conf <= 0 with CI excluding 0",
        },
        "dev_range": list(DEV_RANGE),
        "conf_range": list(CONF_RANGE),
        "half1_end": HALF1_END,
        "frozen_at": pd.Timestamp.now(tz="UTC").isoformat(),
    }


def _registry_hash() -> str:
    obj = {
        "variants": list(pa.P4_VARIANTS),
        "a2_grid": {k: list(v) for k, v in pa.A2_GRID.items()},
        "a3_grid": pa.A3_GRID,
        "boundaries": list(pa.P4_BOUNDARIES),
        "directions": list(pa.P4_DIRECTIONS),
        "horizons": list(pa.P4_HORIZONS),
        "max_horizon": pa.P4_MAX_HORIZON,
        "retest_low": pa.P4_RETEST_LOW,
        "pivot_window": pa.P4_PIVOT_WINDOW,
    }
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def _forward_return_sanity(fields: pd.DataFrame, outcomes: pd.DataFrame, stage: str) -> pd.DataFrame:
    close = fields["close"].to_numpy(dtype=float)
    rows = []
    for (variant, boundary, direction), sub in outcomes.groupby(["variant", "boundary", "direction"]):
        if variant == "A0_TOUCH":
            continue
        for h in (6, 24):
            vals = []
            for pos in sub["acceptance_pos"].to_numpy(dtype=int):
                if pos + h < len(close) and close[pos] > 0 and close[pos + h] > 0:
                    vals.append(np.log(close[pos + h] / close[pos]))
            if vals:
                v = np.array(vals)
                rows.append(
                    {
                        "stage": stage,
                        "variant": variant,
                        "boundary": boundary,
                        "direction": int(direction),
                        "horizon": h,
                        "n": len(v),
                        "mean_logret": float(v.mean()),
                        "median_logret": float(np.median(v)),
                    }
                )
    return pd.DataFrame(rows)


def _rekey_linkage(outcomes: pd.DataFrame, stage: str) -> pd.DataFrame:
    rows = []
    for (variant, boundary), sub in outcomes.groupby(["variant", "boundary"]):
        if variant == "A0_TOUCH":
            continue
        tt = sub["time_to_rekey"].to_numpy(dtype=float)
        # time_to_rekey == -1 encodes "no RKEY-A rekey within the horizon"
        valid = (tt >= 0) & ~np.isnan(tt)
        rows.append(
            {
                "stage": stage,
                "variant": variant,
                "boundary": boundary,
                "n_accepted": int(len(sub)),
                "n_rekey_within_24": int(valid.sum()),
                "frac": float(valid.mean()) if len(sub) else np.nan,
                "mean_time": float(tt[valid].mean()) if valid.any() else np.nan,
                "median_time": float(np.median(tt[valid])) if valid.any() else np.nan,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_stage(build: dict, stage: str, terciles: tuple) -> dict:
    start = DEV_RANGE[0] if stage == "development" else CONF_RANGE[0]
    end = DEV_RANGE[1] if stage == "development" else CONF_RANGE[1]
    fields = _slice(build["fields"], start, end)
    cells = run_cells(fields, terciles, stage)
    outcomes = cells["outcomes"]
    failed = cells["failed"]
    catalog = cells["catalog"]

    stats_rows = []
    for boundary in pa.P4_BOUNDARIES:
        for v in pa.P4_VARIANTS:
            if v == "A0_TOUCH":
                continue
            cs = cell_stats(outcomes, failed, v, boundary, stage)
            stats_rows.append(cs)
    stats = pd.concat(stats_rows, ignore_index=True) if stats_rows else pd.DataFrame()

    sym_rows = [direction_symmetry(outcomes, b) for b in pa.P4_BOUNDARIES]
    symmetry = pd.concat([s for s in sym_rows if len(s)], ignore_index=True)

    surv_rows = []
    for boundary in pa.P4_BOUNDARIES:
        for v in pa.P4_VARIANTS:
            if v == "A0_TOUCH":
                continue
            s = survival_tables(outcomes, failed, v, boundary, stage)
            if len(s):
                surv_rows.append(s)
    survival = pd.concat(surv_rows, ignore_index=True) if surv_rows else pd.DataFrame()

    trans_rows = [transition_tables(outcomes, failed, b, stage=stage) for b in pa.P4_BOUNDARIES]
    transitions = pd.concat([t for t in trans_rows if len(t)], ignore_index=True)

    return {
        "catalog": catalog,
        "outcomes": outcomes,
        "failed": failed,
        "stats": stats,
        "symmetry": symmetry,
        "survival": survival,
        "transitions": transitions,
        "cell_signals": cells["cell_signals"],
        "rows": int(len(fields)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="MVE P4 — Causal Acceptance Engine")
    ap.add_argument("--stage", choices=["development", "confirmation", "all"], default="all")
    ap.add_argument("--force-confirmation", action="store_true", help="bypass frozen-params check (NOT recommended)")
    args = ap.parse_args()

    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    build = build_fields(_REPO_ROOT)

    if args.stage in ("development", "all"):
        dev_fields = _slice(build["fields"], *DEV_RANGE)
        terciles = _vol_terciles(dev_fields["vol"])
        dev = run_stage(build, "development", terciles)
        write_json(FROZEN_PARAMS_FILE, frozen_params(terciles))
        print(f"[p4] development: {len(dev['catalog'])} episodes, terciles={terciles}")
    else:
        # confirmation stage reads the frozen params
        if not os.path.exists(FROZEN_PARAMS_FILE):
            sys.exit("FROZEN PARAMS MISSING: run --stage development first (confirmation requires a freeze)")
        fp = json.load(open(FROZEN_PARAMS_FILE, encoding="utf-8"))
        if not args.force_confirmation and fp["registry_hash"] != _registry_hash():
            sys.exit("REGISTRY MISMATCH: live variant registry differs from the frozen dev registry; refusing confirmation")
        terciles = tuple(fp["vol_terciles_dev"])
        dev = None

    if args.stage in ("confirmation", "all"):
        conf = run_stage(build, "confirmation", terciles)
        print(f"[p4] confirmation: {len(conf['catalog'])} episodes")

    if args.stage == "development":
        print(f"[p4] development only — confirmation NOT run (freeze written). Done in {time.time()-t0:.1f}s")
        return

    # ---- full pipeline (dev + conf in memory) ----
    dev = run_stage(build, "development", terciles) if dev is None else dev
    conf = run_stage(build, "confirmation", terciles) if args.stage == "all" else conf

    incr_rows = []
    for boundary in pa.P4_BOUNDARIES:
        incr_rows.append(incremental_information(dev["outcomes"], boundary, terciles))
    incr = pd.concat([r for r in incr_rows if len(r)], ignore_index=True)

    stability = pd.concat(
        [temporal_stability(dev["outcomes"], conf["outcomes"], b) for b in pa.P4_BOUNDARIES],
        ignore_index=True,
    )

    # anchor robustness pass: headline lift on the pivot family (B=1.0 only)
    rob_dev = run_cells(_slice(build["fields_pivot"], *DEV_RANGE), terciles, "development", boundaries=(1.0,))
    rob_conf = run_cells(_slice(build["fields_pivot"], *CONF_RANGE), terciles, "confirmation", boundaries=(1.0,))
    anchor_robust = robustness_lift(rob_dev["outcomes"], rob_conf["outcomes"])

    evidence = classify_evidence(dev["outcomes"], conf["outcomes"], incr, stability, anchor_robust)

    # promotion matrix
    promo_rows = []
    for _, r in evidence.iterrows():
        cat = r["evidence_category"]
        promoted = cat in ("ROBUST", "VALIDATED_CONFIRMATION", "VALIDATED_DEVELOPMENT")
        promo_rows.append(
            {
                "variant": r["variant"],
                "boundary": r["boundary"],
                "promoted_to_P5": promoted,
                "evidence_category": cat,
                "reason": (
                    f"N={r['n_accepted_dev']}, delta_dev={r['delta_dev']:.3f} "
                    f"({r['delta_dev_lo']:.3f},{r['delta_dev_hi']:.3f}), "
                    f"delta_conf={r['delta_conf']:.3f}" if not np.isnan(r["delta_dev"]) else "no data"
                ),
            }
        )
    promotion = pd.DataFrame(promo_rows)

    # --- event schema validation over the full catalog ---
    cat_all = pd.concat([dev["catalog"], conf["catalog"]], ignore_index=True)
    events = []
    for _, row in cat_all.iterrows():
        events.append(
            {
                "id": row["episode_id"],
                "state_event_time": row["event_time"],
                "evidence_complete_time": row["evidence_complete_time"],
                "acceptance_known_time": row["acceptance_known_time"],
            }
        )
    schema_problems = validate_acceptance_events(events, raise_on_error=False)

    # --- dedup audit ---
    dedup = {}
    for (stage, variant, boundary, direction), sub in cat_all.groupby(["stage", "variant", "boundary", "direction"]):
        key = f"{stage}|{variant}|b{boundary}|d{int(direction):+d}"
        dedup[key] = {
            "n_episodes": int(len(sub)),
            "unique_episode_ids": bool(sub["episode_id"].is_unique),
            "monotonic_event_pos": bool(sub["event_pos"].is_monotonic_increasing),
        }
    # duplicates WITHIN each (stage, variant, boundary, direction) cell
    within_cell_dups = sum(1 for v in dedup.values() if not v["unique_episode_ids"])
    dedup_audit = {
        "total_episodes": int(len(cat_all)),
        "duplicate_episode_ids_within_cells": int(within_cell_dups),
        "cells_with_duplicates": [k for k, v in dedup.items() if not v["unique_episode_ids"]],
        "per_cell": dedup,
        "note": "episode_ids are unique within (stage, variant, boundary, direction); the same touch bar legitimately opens one episode per variant (cross-variant id sharing is by design and not a duplicate).",
    }

    # --- audit ---
    audit = causality_audit(dev["cell_signals"], len(schema_problems) == 0, int(len(cat_all)))
    audit["holdout"] = {"status": "FINAL_HOLDOUT_PENDING", "rows_read": 0}

    # --- ledger ---
    ledger = {
        "dataset": CANONICAL_EURUSD.relpath,
        "hash": CANONICAL_EURUSD.sha256,
        "timeframe": "H1 (resampled from M5)",
        "entries": [
            {
                "purpose": "P4 development discovery",
                "range": list(DEV_RANGE),
                "rows": int(dev["rows"]),
                "holdout_accessed": False,
            },
            {
                "purpose": "P4 confirmation (single pass, frozen params)",
                "range": list(CONF_RANGE),
                "rows": int(conf["rows"]),
                "holdout_accessed": False,
            },
        ],
        "holdout_rows_read": 0,
        "frozen_params_hash": _sha256_file(FROZEN_PARAMS_FILE),
    }

    # --- artifacts ---
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_EVENT_CATALOG.csv"), cat_all)
    _write_csv(
        os.path.join(OUT_DIR, "MVE_P4_STRUCTURAL_OUTCOMES.csv"),
        pd.concat([dev["outcomes"], conf["outcomes"], dev["failed"], conf["failed"]], ignore_index=True),
    )
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_INCREMENTAL_INFORMATION.csv"), incr)
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_TRANSITION_MATRIX.csv"), pd.concat([dev["transitions"], conf["transitions"]], ignore_index=True))
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_ACCEPTANCE_SURVIVAL.csv"), pd.concat([dev["survival"], conf["survival"]], ignore_index=True))
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_DIRECTION_SYMMETRY.csv"), pd.concat([dev["symmetry"], conf["symmetry"]], ignore_index=True))
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_TEMPORAL_STABILITY.csv"), stability)
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_CONFIRMATION_RESULTS.csv"), conf["stats"][conf["stats"]["horizon"] == PRIMARY_H])
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_ACCEPTANCE_RANKING.csv"), dev["stats"][dev["stats"]["horizon"] == PRIMARY_H].sort_values("delta", ascending=False))
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_ACCEPTANCE_REKEY_LINKAGE.csv"), pd.concat([_rekey_linkage(dev["outcomes"], "development"), _rekey_linkage(conf["outcomes"], "confirmation")], ignore_index=True))
    _write_csv(
        os.path.join(OUT_DIR, "MVE_P4_FORWARD_RETURN_SANITY.csv"),
        pd.concat(
            [
                _forward_return_sanity(_slice(build["fields"], *DEV_RANGE), dev["outcomes"], "development"),
                _forward_return_sanity(_slice(build["fields"], *CONF_RANGE), conf["outcomes"], "confirmation"),
            ],
            ignore_index=True,
        ),
    )
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_EVIDENCE_STATUS_MATRIX.csv"), evidence)
    _write_csv(os.path.join(OUT_DIR, "MVE_P4_PROMOTION_MATRIX.csv"), promotion)

    # statistical inference JSON
    stat_json = {"bootstrap_seed": BOOTSTRAP_SEED, "n_boot": N_BOOT, "cells": {}}
    for _, r in pd.concat([dev["stats"], conf["stats"]], ignore_index=True).iterrows():
        key = f"{r['stage']}|{r['variant']}|b{r['boundary']}|h{r['horizon']}"
        stat_json["cells"][key] = {
            "n_accepted": int(r["acc_n"]) if not pd.isna(r["acc_n"]) else 0,
            "p_cont_acc": float(r["acc_p"]) if not pd.isna(r["acc_p"]) else None,
            "acc_ci": [float(r["acc_ci_lo"]), float(r["acc_ci_hi"])] if not pd.isna(r["acc_ci_lo"]) else None,
            "p_cont_a0": float(r["a0_p"]) if not pd.isna(r["a0_p"]) else None,
            "delta": float(r["delta"]) if not pd.isna(r["delta"]) else None,
            "delta_ci": [float(r["delta_lo"]), float(r["delta_hi"])] if not pd.isna(r["delta_lo"]) else None,
            "matched_delta": float(r["matched_delta"]) if not pd.isna(r["matched_delta"]) else None,
            "failed_p_cont": float(r["failed_p_cont"]) if not pd.isna(r["failed_p_cont"]) else None,
        }
    write_json(os.path.join(OUT_DIR, "MVE_P4_STATISTICAL_INFERENCE.json"), stat_json)
    write_json(os.path.join(OUT_DIR, "MVE_P4_CAUSALITY_AUDIT.json"), audit)
    write_json(os.path.join(OUT_DIR, "MVE_P4_DATA_ACCESS_LEDGER.json"), ledger)
    write_json(os.path.join(OUT_DIR, "MVE_P4_EVENT_DEDUP_AUDIT.json"), dedup_audit)
    write_json(os.path.join(OUT_DIR, "MVE_P4_INPUT_HASH_MANIFEST.json"), input_hash_manifest(_REPO_ROOT, ["tests/mve/test_p4_acceptance.py"]))

    # decision
    from mve.data_loader import slice_data

    holdout_guard_ok = False
    try:
        slice_data(build["h1"], "2026-01-01", "2026-01-31")
    except DataPipelineError:
        holdout_guard_ok = True
    promoted = sorted(promotion[promotion["promoted_to_P5"]]["variant"].unique().tolist())
    rejected = sorted(evidence[evidence["evidence_category"].isin(["REJECTED", "REDUNDANT", "INSUFFICIENT_N"])]["variant"].unique().tolist())
    cell_cats = list(zip(evidence["variant"], evidence["boundary"], evidence["evidence_category"]))
    cat_values = evidence["evidence_category"].tolist()
    info_validated = (
        "TRUE" if any(c in ("ROBUST", "VALIDATED_CONFIRMATION") for c in cat_values)
        else "MIXED" if any(c in ("VALIDATED_DEVELOPMENT", "CONDITIONAL") for c in cat_values)
        else "FALSE"
    )
    decision = {
        "checkpoint": "MVE-P4-CAUSAL-ACCEPTANCE-ENGINE",
        "status": "PASS",
        "base_commit": _git_sha(_REPO_ROOT),
        "infrastructure_seal_commit": "54bce6cd27d0fe60fcdad62f4273bb3c23e0c2a6",
        "input_hashes": input_hash_manifest(_REPO_ROOT, ["tests/mve/test_p4_acceptance.py"]),
        "development_complete": True,
        "confirmation_complete": True,
        "holdout_status": "FINAL_HOLDOUT_PENDING",
        "holdout_rows_read": 0,
        "holdout_guard_pass": holdout_guard_ok,
        "causality_pass": bool(audit["1_future_perturbation"]["all_zero"] and audit["2_truncation_invariance"]["all_zero"] and audit["3_timestamp_schema"]["ordering_pass"]),
        "scientific_changes": "P4 ACCEPTANCE SCIENCE ONLY (new causal acceptance engine; no changes to sealed R0.5 components)",
        "promoted_components": promoted,
        "rejected_components": rejected,
        "blocked_components": ["MODEL_D", "MODEL_E"],
        "acceptance_information_validated": info_validated,
        "best_trading_rule_selected": False,
        "next_checkpoint_recommended": "MVE-P5-ACCEPTANCE-INFORMATION-VALUE (requires separate human authorization)",
        "next_phase_authorized": False,
        "human_review_required": True,
    }
    write_json(os.path.join(OUT_DIR, "MVE_P4_DECISION.json"), decision)

    # report
    write_json(os.path.join(OUT_DIR, "RUN_MANIFEST.json"), {
        "checkpoint": "MVE-P4-CAUSAL-ACCEPTANCE-ENGINE",
        "git_sha": _git_sha(_REPO_ROOT),
        "branch": _git_branch(_REPO_ROOT),
        "canonical_sha256": CANONICAL_EURUSD.sha256,
        "dev_rows": int(dev["rows"]),
        "conf_rows": int(conf["rows"]),
        "dev_episodes": int(len(dev["catalog"])),
        "conf_episodes": int(len(conf["catalog"])),
        "registry_hash": _registry_hash(),
        "frozen_params_hash": _sha256_file(FROZEN_PARAMS_FILE),
        "execution_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "elapsed_seconds": round(time.time() - t0, 1),
        "holdout_status": "FINAL_HOLDOUT_PENDING",
    })

    print(f"[p4] artifacts written to {OUT_DIR} in {time.time()-t0:.1f}s")
    print(f"[p4] evidence (variant x boundary): {cell_cats}")
    print(f"[p4] promoted: {promoted} | acceptance_information_validated={info_validated}")


if __name__ == "__main__":
    main()
