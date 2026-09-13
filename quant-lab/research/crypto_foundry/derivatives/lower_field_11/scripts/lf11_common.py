"""LOWER-FIELD-11 shared frame builders.

LF11 asks WHAT ARE THE LOCAL LAWS governing load, damage, absorption,
propagation, memory, containment and sign asymmetry. It does NOT re-establish
phenomena (LF8/9/10 did). This layer rebuilds the LF10 master event frame and
adds the instruments LF11 needs:

- PRIOR-SHOCK BURDEN RECONSTRUCTION: for each event, per-asset trailing-shock
  history across many candidate constructions (count, sum-abs, max-abs,
  days-since, exp/power weighted, downside/upside-only, same/opposite-dir).
- CAPACITY FAMILIES: structural / liquidity / rank-health / stress / recovery
  energy from the LF10 coordinates.
- SHOCK MEMORY KERNEL: per-asset weighted-cumulative burden under an
  exponential vs power-law vs finite-window memory kernel.
- ABSORPTION vs CONTAINMENT labels: re-derive LF10 shock_outcome and a
  contagion spread flag so the two can be compared as distinct response laws.
- CONTAGION CONTINUOUS SPACE: latency / acceleration / first-secondary /
  peak / radius / breadth / depth / persistence / decay / reactivation /
  generations coordinates built from the peer-forward instruments.
- DECOUPLING EXIT PATHS: how persistent-decoupling rows resolve forward.

Research only: no strategy, no PnL, no execution.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_10" / "scripts"))
import lf10_common as L10  # noqa: E402
import lf9_common as C9       # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent          # lower_field_11/
C = C9.C
A = C9.A
CACHE = ROOT / "cache"

_fmt = A._fmt
_med = C9._med
_mean = C9._mean
_purged_auc = A._purged_auc
MIN_SUPPORT = C9.MIN_SUPPORT

ABS_CLS = ["<2%", "2-5%", "5-10%", "10-20%", "20%+"]
SIG_CLS = ["<2σ", "2-3σ", "3-4σ", "4σ+"]

SUB_PERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]


# ---------------------------------------------------------------------------
# Base event frame (LF10 master frame, cached)
# ---------------------------------------------------------------------------

def base_frame(use_cache: bool = True) -> pd.DataFrame:
    """LF10 master frame (cached parquet) as the base for LF11.""" 
    df = L10.base_frame(use_cache=True)
    return df


# ---------------------------------------------------------------------------
# Prior-shock burden reconstruction (per-asset trailing history)
# ---------------------------------------------------------------------------

def shock_load_primitives(snap: pd.DataFrame) -> pd.DataFrame:
    """Decompose the CURRENT shock into primitives (Section 6).

    absolute magnitude, sigma surprise, duration, direction, acceleration,
    gap/jump proxy, liquidity context, peer-relative displacement,
    rank-relative displacement.
    """
    d = snap.copy()
    d = d.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    r3 = d["ret_3d"].abs()
    a1 = d["abs_ret"]
    d["load_duration"] = np.select([r3 >= 1.5 * a1, r3 >= 1.05 * a1],
                                   ["MULTI_DAY", "SUSTAINED_1_3D"], default="IMPULSE")
    d["gap_jump"] = (d["abs_ret"] / d["sigma"].clip(lower=1e-6)).clip(upper=20)
    d["accel_shock"] = (d["ret_3d"].abs() - a1).clip(lower=0)
    d["peer_rel_disp"] = d["peer_std_ret"].fillna(d["peer_std_ret"].median())
    d["rank_rel_disp"] = -d["rank_vel_7d"]  # negative => rank deteriorating
    d["load_direction"] = np.where(d["event_sign_b"] > 0, "UP", "DOWN")
    d["load_liquidity"] = d["liq_proxy"]
    return d


def prior_shock_burden(snap: pd.DataFrame, windows=(30, 90, 180, 365)) -> pd.DataFrame:
    """Trailing-shock burden auto-features per asset-event (Section 7).

    For each event, scan the asset's earlier snapshots within each trailing
    window and build candidate burden constructions (count, sum-abs, max-abs,
    days-since, same/opposite-direction, downside/upside-only). Returned
    columns are used by the kernel / accumulation tests.

    O(Σ n_events_per_asset^2) but the panel is only 3.6k events across ~700
    assets (max ~44 per asset), so this is fast in practice.
    """
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    n = len(d)
    dates = d["historical_date"].to_numpy(dtype="datetime64[ns]")
    cids = d["cmc_id"].to_numpy()
    ab = d["abs_ret"].to_numpy(dtype=float)
    sd = d["event_sign_b"].to_numpy()
    out = {"days_since_prior": np.full(n, np.nan)}
    colnames = []
    for w in windows:
        for base in [f"cnt_prev_{w}d", f"sumabs_prev_{w}d", f"maxabs_prev_{w}d",
                     f"cnt_down_prev_{w}d", f"cnt_up_prev_{w}d", f"cnt_same_prev_{w}d",
                     f"cnt_opp_prev_{w}d", f"sumabs_same_prev_{w}d", f"sumabs_opp_prev_{w}d"]:
            out[base] = np.full(n, np.nan)
            colnames.append(base)
    # contiguous asset ranges on sorted frame (already grouped by cmc_id)
    ranges = []
    start = 0
    for k in range(1, n):
        if cids[k] != cids[start]:
            ranges.append((start, k))
            start = k
    ranges.append((start, n))
    for (s0, s1) in ranges:
        rng = list(range(s0, s1))  # already temporal within asset
        for i, ev in enumerate(rng):
            if i == 0:
                continue
            t0 = dates[ev]
            sgn = np.sign(sd[ev])
            for w in windows:
                acc = [j for j in rng[:i] if (t0 - dates[j]) <= np.timedelta64(w, "D")]
                if not acc:
                    continue
                aa = np.array(acc)
                sdacc = sd[aa]
                same = int(np.sum(sdacc == sgn))
                opp = int(np.sum(sdacc != sgn))
                out[f"cnt_prev_{w}d"][ev] = float(len(acc))
                out[f"sumabs_prev_{w}d"][ev] = float(np.sum(ab[aa]))
                out[f"maxabs_prev_{w}d"][ev] = float(np.max(ab[aa]))
                out[f"cnt_down_prev_{w}d"][ev] = float(np.sum(sdacc < 0))
                out[f"cnt_up_prev_{w}d"][ev] = float(np.sum(sdacc > 0))
                out[f"cnt_same_prev_{w}d"][ev] = float(same)
                out[f"cnt_opp_prev_{w}d"][ev] = float(opp)
                out[f"sumabs_same_prev_{w}d"][ev] = float(np.sum(ab[aa][sdacc == sgn]))
                out[f"sumabs_opp_prev_{w}d"][ev] = float(np.sum(ab[aa][sdacc != sgn]))
            out["days_since_prior"][ev] = float(
                (t0 - dates[rng[i - 1]]) / np.timedelta64(1, "D"))
    df_out = pd.DataFrame(out, index=d.index)
    return df_out


# ---------------------------------------------------------------------------
# Shock memory kernels (Section 8)
# ---------------------------------------------------------------------------

def memory_kernel_weights(days, kernel="exp", half_life=45.0):
    """Weight a prior event at `days` lag under a decay kernel.

    exp:      2^(-days/half_life)
    power:    (1 + days/7)^(-beta), beta=1.0
    finite:   1 if days <= half_life else 0
    """
    days = np.asarray(days, dtype=float)
    if kernel == "exp":
        return np.power(2.0, -days / half_life)
    if kernel == "power":
        return np.power(1.0 + days / 7.0, -1.0)
    if kernel == "finite":
        return (days <= half_life).astype(float)
    return np.ones_like(days)


def shock_memory_burden(snap: pd.DataFrame, kernels=("exp", "power", "finite")) -> pd.DataFrame:
    """Weighted-cumulative prior-shock burden under each memory kernel. Columns
    mem_{kernel}_cnt / mem_{kernel}_sum over a 365d lookback."""
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    n = len(d)
    dates = d["historical_date"].to_numpy(dtype="datetime64[ns]")
    cids = d["cmc_id"].to_numpy()
    ab = d["abs_ret"].to_numpy(dtype=float)
    from itertools import groupby
    idx = np.argsort(cids, kind="stable")
    ranges = []
    start = 0
    cur = cids[idx[0]]
    for k in range(1, n):
        if cids[idx[k]] != cur:
            ranges.append((start, k, cur))
            start = k
            cur = cids[idx[k]]
    ranges.append((start, n, cur))
    out = {}
    for k in kernels:
        out[f"mem_{k}_cnt"] = np.full(n, np.nan)
        out[f"mem_{k}_sum"] = np.full(n, np.nan)
    for (s0, s1, _cid) in ranges:
        rng = sorted(idx[s0:s1].tolist(), key=lambda r: dates[r])
        for i, ev in enumerate(rng):
            t0 = dates[ev]
            prior = [j for j in rng[:i] if (t0 - dates[j]) <= np.timedelta64(365, "D")]
            for k in kernels:
                if not prior:
                    continue
                w = memory_kernel_weights([(t0 - dates[j]).astype("timedelta64[s]") / 86400.0
                                           for j in prior], kernel=k)
                out[f"mem_{k}_sum"][ev] = float(np.sum(w * ab[prior]))
                out[f"mem_{k}_cnt"][ev] = float(np.sum(w))
    df_out = pd.DataFrame(out, index=d.index)
    return df_out


# ---------------------------------------------------------------------------
# Capacity families (Section 3)
# ---------------------------------------------------------------------------
# Candidate families map onto the LF10 coordinates.

CAPACITY_FAMILIES = {
    "STRUCTURAL": ["peer_corr", "roll_turnover_30d", "entropy_30d", "unique_peers_7d"],
    "LIQUIDITY": ["liq_proxy", "volume_24h_usd", "log10_mcap"],
    "RANK_HEALTH": ["rank", "rank_vel_7d"],
    "STRESS": ["peer_stress", "peer_std_ret", "mem_exp_sum", "cnt_prev_90d"],
    "RECOVERY": ["out_rejoin", "rejoin_vel"],
}


def capacity_features(snap: pd.DataFrame) -> pd.DataFrame:
    """Return event-level capacity-family coordinates (identity-mapped + a few
    derived stress/recovery proxies). Some will be NaN for rows where the LF10
    coordinate is absent; callers dropna per-family."""
    d = snap.copy()
    if "mem_exp_sum" not in d.columns:
        mb = shock_memory_burden(d)
        d = pd.concat([d, mb], axis=1)
    return d


# ---------------------------------------------------------------------------
# Local capacity surface (Section 4): STRUCTURAL INTEGRITY x ACCUMULATED LOAD
# ---------------------------------------------------------------------------
# Structural integrity (higher = healthier): invert churn, avg of coherence +
# membership-stability + rank-health. Accumulated load = exp-kernel burden.

def local_capacity_axis(snap: pd.DataFrame) -> pd.DataFrame:
    d = snap.copy()
    if "mem_exp_sum" not in d.columns:
        mb = shock_memory_burden(d)
        d = pd.concat([d, mb], axis=1)
    med_turn = d["roll_turnover_30d"].median()
    med_liq = d["liq_proxy"].median()
    med_rank = d["rank"].median()
    d["struct_integrity"] = (
        0.4 * d["peer_corr"].clip(0, 1)
        + 0.3 * (d["roll_turnover_30d"] <= med_turn).astype(float)
        + 0.3 * (d["rank"] <= med_rank).astype(float)
    )
    d["structural_cap"] = d["peer_corr"].clip(0, 1)
    d["liquidity_cap"] = (d["liq_proxy"] >= med_liq).astype(float)
    d["rankhealth_cap"] = (d["rank"] <= med_rank).astype(float)
    d["stress_cap"] = (~d["peer_stress"].astype(bool)).astype(float)
    d["recovery_cap"] = (d["out_rejoin"].fillna(0) == 1).astype(float)
    d["accumulated_load"] = d["mem_exp_sum"].fillna(0.0)
    return d


# ---------------------------------------------------------------------------
# Contagion continuous-space geometry (Section 16)
# ---------------------------------------------------------------------------

def _first_reaction_latency(row, hs=(1, 3, 7, 14, 30)):
    for h in hs:
        v = row.get(f"peer_neg_frac{h}", np.nan)
        if pd.notna(v) and v >= 0.30:
            return float(h)
    return np.nan


def _peak_time(row, hs=(1, 3, 7, 14, 30)):
    vals = {h: row.get(f"peer_neg_frac{h}", np.nan) for h in hs}
    pk = max(hs, key=lambda h: vals[h] if pd.notna(vals[h]) else -9.0)
    return float(pk)


def contagion_continuous_space(snap: pd.DataFrame) -> pd.DataFrame:
    """Build per-event contagion temporal/spatial coordinates from the current
    shock itself (latency, acceleration, first-secondary, peak, radius,
    breadth, depth, persistence, decay, generations)."""
    d = snap.copy()
    hs = [1, 3, 7, 14, 30]
    for rt in ["neg", "touch"]:
        for h in hs:
            key = f"peer_{rt}_frac{h}"
            if key not in d.columns:
                d[key] = np.nan
    lat = np.full(len(d), np.nan)
    peak = np.full(len(d), np.nan)
    for i, (_, row) in enumerate(d.iterrows()):
        lat[i] = _first_reaction_latency(row, hs)
        peak[i] = _peak_time(row, hs)
    d["latency_T1"] = lat
    d["peak_time_T3"] = peak
    d["radius_T7"] = d["peer_touch_frac7"]
    d["breadth_T7"] = d["peer_neg_frac7"]
    d["depth_T30"] = (-d["peer_med_fwd30"]).clip(lower=0)
    d["persistence_T30"] = d["peer_neg_frac30"]
    d["CONT_SPEED"] = ((d["peer_neg_frac3"] - d["peer_neg_frac1"]).clip(lower=0) / 2.0)
    d["CONT_RADIUS"] = d["radius_T7"]
    d["CONT_DEPTH"] = d["depth_T30"]
    d["CONT_PERSIST"] = d["persistence_T30"]
    # decay from peak to T30
    d["CONT_DECAY"] = d["peer_neg_frac30"] - d["peer_neg_frac1"]
    # generations: G1 = immediate peers (1d), G2 = neighborhood (7d),
    # G3 = broader (30d) descriptive (not infection causality).
    d["G1_fraction"] = d["peer_neg_frac1"]
    d["G2_fraction"] = d["peer_neg_frac7"] - d["peer_neg_frac1"].clip(lower=0)
    d["G3_fraction"] = d["peer_neg_frac30"] - d["peer_neg_frac7"].clip(lower=0)
    return d


# ---------------------------------------------------------------------------
# Persistent-decoupling exit paths (Section 25)
# ---------------------------------------------------------------------------
# For a PERSISTENT_DECOUPLING event, look forward (chronologically within the
# asset) to see whether the asset rejoins / forms a new neighborhood /
# deteriorates / normalizes / stays isolated.

def decoupling_exit_paths(snap: pd.DataFrame) -> pd.DataFrame:
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    # next snapshot per asset
    ndec = d["out_decouple"].shift(-1)
    ndec = d.loc[d["cmc_id"] == d["cmc_id"].shift(-1), "out_decouple"].shift(-1)
    # simpler: build explicit next-DECOUPLE flag
    d["next_decouple"] = d.groupby("cmc_id")["out_decouple"].shift(-1)
    d["is_persistent"] = (d["out_decouple"] == 1)
    # exit: 0.5-1.0 in forward metrics
    d["exit_rejoin"] = d["out_rejoin"].fillna(0)
    d["exit_normalized"] = (~(d.set_index(d.index)["out_decouple"].fillna(0).astype(bool))
                            & d["price_up_30"].fillna(0).astype(bool)).astype(float)
    # forwarded rejoin velocity
    d["exit_new_neighborhood"] = d["rejoin_vel"].fillna(0)
    d["exit_rank_deteriorate"] = (d["rank_vel_7d"] < 0).astype(float)
    return d


def contagion_reactivation(snap: pd.DataFrame) -> pd.DataFrame:
    """Reactivation / second-wave: rows where a state already propagating
    (out_contagion) coincides with a fresh high shock after a quiet gap, or
    where out_relapse marks a restart."""
    d = snap.copy()
    d["reactivation"] = (d["out_relapse"].fillna(0) == 1).astype(float)
    # fresh shock after >= 60d quiet
    d["days_since"] = d.groupby("cmc_id")["historical_date"].diff().dt.days
    d["fresh_after_gap"] = ((d["days_since"] >= 60) & (d["abs_ret"] >= 0.10)).astype(float)
    return d


# ---------------------------------------------------------------------------
# Aggregate master construction (cached)
# ---------------------------------------------------------------------------

def master_frame(use_cache: bool = True) -> pd.DataFrame:
    cache_p = CACHE / "lf11_master_frame.parquet"
    if use_cache and cache_p.exists() and cache_p.stat().st_size > 0:
        return pd.read_parquet(cache_p)

    base = base_frame(use_cache=True)
    base = shock_load_primitives(base)
    burden = prior_shock_burden(base)
    base = pd.concat([base.reset_index(drop=True), burden.reset_index(drop=True)], axis=1)
    mb = shock_memory_burden(base)
    base = pd.concat([base.reset_index(drop=True), mb.reset_index(drop=True)], axis=1)
    base = local_capacity_axis(base)
    base = contagion_continuous_space(base)
    base = decoupling_exit_paths(base)
    base = contagion_reactivation(base)
    base.to_parquet(cache_p, index=False)
    return base


if __name__ == "__main__":
    df = master_frame()
    print("LF11 master frame rows:", df.shape, flush=True)