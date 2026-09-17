"""LOWER-FIELD-10 shared loaders and frame builders.

LF10 is the shock & contagion cartography checkpoint. It goes from
"phenomena are real" (LF9) to "what are the internal dimensions / species /
temporal geometry of local physical shock, contagion, decoupling and
directional asymmetry."

SAMPLING FRAME. The honest place to observe peer metrics is the LF8
primary-family (HYBRID_10) snapshot panel of isolated-stress events — that is
where per-peer returns, rolling membership and PIT relational state are
actually measured. The LF9 continuous asset-day panel holds carried (stale)
values of most peer metrics, so we use the *snapshot* frame as the analysis
frame and the continuous panel for daily-coverage clocks and for the MECH-15
global field surface. Two new instruments are built on top:

- peer-forward: from the LF5 pit_returns_wide matrix + per-event peer sets,
  how each event's exact T0 peers behave over the following 1/3/7/14/30 days
  (median cumulative return, negative fraction, deep-touch fraction). This is
  the genuine propagation instrument for the contagion maps.
- topology churn: consecutive-snapshot peer-set differences — who leaves /
  enters, overlap, old-vs-new neighborhood coherence, rank, directional
  composition, stress, vol, and forward health of dropped vs added neighbors.

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_9" / "scripts"))
import lf9_common as C9  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent          # lower_field_10/
C = C9.C            # lf8_common
A = C9.A            # lf8_analyze
PRIMARY = C9.PRIMARY
MIN_SUPPORT = C9.MIN_SUPPORT
STATE_ORDER = C9.STATE_ORDER
STATE_ORDER_EXT = C9.STATE_ORDER
FRESH = ["FRESH_0_7", "STALE_8_30"]

_fmt = A._fmt
_med = C9._med
_mean = C9._mean

# ---------------------------------------------------------------------------
# Base snapshot frame (cached) with every continuous coordinate we will use.
# ---------------------------------------------------------------------------

# Continuous relational / neighborhood coordinates (event-level, real peers).
# each: (code, label, source column(s) or expression)
COORD_DEFS = [
    ("abs_resid", "peer residual magnitude (|res|)", ["res"]),
    ("res_z", "peer residual z-score", ["res_z"]),
    ("peer_corr", "neighborhood coherence", ["peer_corr"]),
    ("roll_turnover_30d", "membership turnover (30d)", ["roll_turnover_30d"]),
    ("entropy_30d", "membership entropy (30d)", ["entropy_30d"]),
    ("state_trans_rate", "relational-state transition rate (chrono)", ["state_changed"]),
    ("deg_decouple", "degree of decoupling (fwd 30d)", ["out_decouple"]),
    ("rejoin_vel", "rejoin velocity (fwd 30d)", ["out_rejoin"]),
    ("contagion_breadth", "contagion breadth (fwd 7d)", ["out_contagion"]),
    ("peer_stress", "peer stress (0/1)", ["peer_stress"]),
    ("peer_dispersion", "peer dispersion", ["peer_std_ret"]),
    ("rank_health_diff", "local rank-health differential", ["rank_vel_7d"]),
    ("nbr_momentum", "neighborhood momentum (peer med ret)", ["peer_med_ret"]),
    ("time_since_transition", "days since last relational transition", ["state_age_d"]),
    ("persist_duration", "persistence duration (days in current state)", ["state_age_d"]),
]

# Topology churn descriptive dimensions used for churn anatomy/species.
CHURN_DIMS = ["churn_turnover", "old_coherence", "new_coherence", "rank_migration",
              "old_peer_stress", "new_peer_stress", "old_vol_q", "new_vol_q",
              "sign_aligned_frac", "sign_opposed_frac", "added_peer_fwd7",
              "dropped_peer_fwd7", "jaccard_overlap"]


def base_frame(use_cache: bool = True) -> pd.DataFrame:
    """The master event frame: LF8 primary snapshot panel + forward outcomes +
    MECH-15 cell overlay + continuous coordinates + peer-forward + topology
    churn anatomy + shock-outcome class. Cached to cache/lf10_master_frame.parquet
    (heavy to rebuild).
    """
    cache_p = C9.CACHE / "lf10_master_frame.parquet"
    if use_cache and cache_p.exists() and cache_p.stat().st_size > 0:
        return pd.read_parquet(cache_p)

    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    snap["abs_ret"] = snap["ret_1d"].abs()
    snap["sigma"] = snap["sigma_t0"].clip(lower=0.0)
    snap["event_sign_b"] = np.sign(snap.get("event_sign", np.sign(snap["ret_1d"])))
    snap["side"] = np.where(snap["event_sign_b"] > 0, "UP", "DOWN")
    snap["rank_depth"] = snap["rank_band"].map(C9._rank_depth_band)
    snap["vol_q"] = pd.qcut(snap["vol_30d"].fillna(snap["vol_30d"].median()).rank(method="first"),
                            5, labels=["V1", "V2", "V3", "V4", "V5"]).astype(str)

    # MECH-15 field surfaces joined by date (16/6/8/4 cell + forcing + activation)
    mc = C9._mcell_partitions()
    d = pd.to_datetime(snap["historical_date"]).dt.normalize()
    fm = mc.set_index("d")
    snap["mcell"] = d.map(fm["mcell"])
    snap["mcell6"] = d.map(fm["mcell6"])
    snap["mcell8"] = d.map(fm["mcell8"])
    snap["mcell4"] = d.map(mc.set_index("d")["cell4"])
    snap["forcing"] = d.map(fm["forcing"])
    snap["spatial_activation"] = d.map(fm["spatial_activation"])
    snap["ent_resid_day"] = d.map(fm["ent_resid"])

    # continuous-coordinate scalars (mostly already present; materialize aliases)
    snap["abs_resid"] = snap["res"].abs()
    snap["state_trans_rate"] = snap["state_changed"].astype(float)
    snap["peer_dispersion"] = snap["peer_std_ret"]
    snap["rank_health_diff"] = snap["rank_vel_7d"]
    snap["nbr_momentum"] = snap["peer_med_ret"]
    snap["time_since_transition"] = snap["state_age_d"]
    snap["persist_duration"] = snap["state_age_d"]
    snap["deg_decouple"] = snap["out_decouple"].fillna(0)
    snap["rejoin_vel"] = snap["out_rejoin"].fillna(0)
    snap["contagion_breadth"] = snap["out_contagion"].fillna(0)

    # --- peer-forward (propagation) + topology churn + shock-outcome class ---
    pf = peer_forward(snap)
    topo = topology_churn(snap)
    snap = pd.concat([snap.reset_index(drop=True), pf.reset_index(drop=True),
                      topo.reset_index(drop=True)], axis=1)
    snap = add_shock_outcome(snap)

    snap.to_parquet(cache_p, index=False)
    return snap


def load_base_frame() -> pd.DataFrame:
    return base_frame()


# ---------------------------------------------------------------------------
# Peer forward instrument (contagion propagation)
# ---------------------------------------------------------------------------

_PF_CACHE = {}


def peer_forward(snap: pd.DataFrame, horizons=(1, 3, 7, 14, 30), thr=0.02,
                 key="default") -> pd.DataFrame:
    """Per-event forward health of the event's exact T0 peer set. Columns
    peer_med_fwd{h}, peer_neg_frac{h}, peer_touch_frac{h} (fraction of peers
    with cumulative forward return <= -thr). Cached in-process.
    """
    if key in _PF_CACHE:
        return _PF_CACHE[key]
    prm = C.load_peer_map(PRIMARY)
    sets = prm.groupby("event_index")["peer_id"].apply(lambda s: frozenset(s)).to_dict()
    dates, assets, Rm = C._wide_returns()
    dpos = {dd: i for i, dd in enumerate(dates)}
    apos = {aa: i for i, aa in enumerate(assets)}
    out = pd.DataFrame(index=snap.index)
    ev = snap["event_index"].to_numpy()
    evdates = snap["historical_date"].to_numpy()
    for h in horizons:
        med = np.full(len(snap), np.nan)
        neg = np.full(len(snap), np.nan)
        touch = np.full(len(snap), np.nan)
        for i in range(len(snap)):
            ei = ev[i]
            di = dpos.get(pd.Timestamp(evdates[i]))
            if di is None:
                continue
            t = dates[di]
            hi = di
            while hi + 1 < len(dates) and dates[hi + 1] <= t + pd.Timedelta(days=h):
                hi += 1
            vals = []
            negn = 0
            touchn = 0
            for pid in sets.get(ei, ()):
                pi = apos.get(pid)
                if pi is None:
                    continue
                x = float(np.nansum(Rm[di + 1:hi + 1, pi]))
                if np.isfinite(x):
                    vals.append(x)
                    if x < 0:
                        negn += 1
                    if x <= -thr:
                        touchn += 1
            if vals:
                med[i] = float(np.median(vals))
                neg[i] = negn / len(vals)
                touch[i] = touchn / len(vals)
        out[f"peer_med_fwd{h}"] = med
        out[f"peer_neg_frac{h}"] = neg
        out[f"peer_touch_frac{h}"] = touch
    _PF_CACHE[key] = out
    return out


# ---------------------------------------------------------------------------
# Topology churn instrument
# ---------------------------------------------------------------------------

def topology_churn(snap: pd.DataFrame) -> pd.DataFrame:
    """Per-event topology-churn anatomy: consecutive-snapshot peer-set
    differences within each asset, old/new characteristics, and forward health
    of dropped vs added neighbors (from the wide return matrix).
    """
    prm = C.load_peer_map(PRIMARY)
    prm["peer_return"] = pd.to_numeric(prm["peer_return"], errors="coerce")
    sets = prm.groupby("event_index")["peer_id"].apply(lambda s: frozenset(s)).to_dict()
    pret = (prm.assign(sign=np.sign(prm["peer_return"].fillna(0.0)))
            .groupby("event_index")["sign"].apply(lambda s: dict(zip(
                prm.loc[s.index, "peer_id"], s))).to_dict())
    dates, assets, Rm = C._wide_returns()
    dpos = {dd: i for i, dd in enumerate(dates)}
    apos = {aa: i for i, aa in enumerate(assets)}

    s = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    prev_ei = s.groupby("cmc_id")["event_index"].shift()
    prev_ret = s.groupby("cmc_id")["ret_1d"].shift()
    n = len(s)
    out = pd.DataFrame(index=s.index, dtype=float)
    out["churn_turnover"] = s["turnover_prev"]
    out["jaccard_overlap"] = np.nan
    out["old_peer_count"] = np.nan
    out["new_peer_count"] = s["peer_count"].astype(float)
    out["added_peers"] = np.nan
    out["dropped_peers"] = np.nan
    out["old_coherence"] = np.nan
    out["new_coherence"] = s["peer_corr"]
    out["sign_aligned_frac"] = np.nan
    out["sign_opposed_frac"] = np.nan
    for h in (7, 14, 30):
        out[f"added_peer_fwd{h}"] = np.nan
        out[f"dropped_peer_fwd{h}"] = np.nan
    # rank migration (chronological rank delta)
    out["rank_migration"] = s["rank"] - s.groupby("cmc_id")["rank"].shift()
    out["old_peer_stress"] = np.nan
    out["old_vol_q"] = np.nan
    out["new_vol_q"] = np.nan

    # real old-neighborhood stress: previous event's peer_stress
    ps_map = dict(zip(s["event_index"], s["peer_stress"]))
    old_stress = prev_ei.map(lambda e: ps_map.get(e, np.nan) if not pd.isna(e) else np.nan)
    out["old_peer_stress"] = old_stress
    out["new_peer_stress"] = s["peer_stress"].astype(float)
    # vol quantile global mapping (for old/new vol context)
    vol_med = s["vol_30d"].median()
    old_vol = s.groupby("cmc_id")["vol_30d"].shift()
    out["old_vol_q"] = (old_vol > vol_med).astype(float)
    out["new_vol_q"] = (s["vol_30d"] > vol_med).astype(float)

    def _subset_fwd(peer_list, t_date, h, apos, dpos, dates, Rm):
        di = dpos.get(pd.Timestamp(t_date))
        if di is None or not peer_list:
            return np.nan
        t = dates[di]
        hi = di
        while hi + 1 < len(dates) and dates[hi + 1] <= t + pd.Timedelta(days=h):
            hi += 1
        vals = []
        for pid in peer_list:
            pi = apos.get(pid)
            if pi is None:
                continue
            x = float(np.nansum(Rm[di + 1:hi + 1, pi]))
            if np.isfinite(x):
                vals.append(x)
        return float(np.median(vals)) if vals else np.nan

    prev_ei_by_idx = prev_ei.to_numpy()
    prev_ret_np = prev_ret.to_numpy()
    sidx = s.index.to_numpy()
    eis = s["event_index"].to_numpy()
    sign_asset = np.sign(s["ret_1d"].to_numpy())
    datesnp = s["historical_date"].to_numpy()
    for i in range(n):
        ei = eis[i]
        new = sets.get(ei, frozenset())
        old_ei = prev_ei_by_idx[i]
        if pd.isna(old_ei):
            continue
        old = sets.get(old_ei, frozenset())
        if not new or not old:
            continue
        inter = new & old
        added = new - old
        dropped = old - new
        out.iat[i, out.columns.get_loc("jaccard_overlap")] = len(inter) / max(len(new | old), 1)
        out.iat[i, out.columns.get_loc("old_peer_count")] = len(old)
        out.iat[i, out.columns.get_loc("added_peers")] = len(added)
        out.iat[i, out.columns.get_loc("dropped_peers")] = len(dropped)
        # directional composition: fraction of NEW peers whose return signs with asset
        nsign = pret.get(ei, {})
        if nsign:
            aligned = sum(1 for pid in new if np.sign(nsign.get(pid, 0.0)) == np.sign(sign_asset[i]))
            out.iat[i, out.columns.get_loc("sign_aligned_frac")] = aligned / len(new)
            opposed = sum(1 for pid in new if np.sign(nsign.get(pid, 0.0)) == -np.sign(sign_asset[i]))
            out.iat[i, out.columns.get_loc("sign_opposed_frac")] = opposed / len(new)
        # old-neighborhood coherence proxy: fraction of OLD peers aligned with the OLD asset move
        osign = pret.get(old_ei, {})
        if osign and not pd.isna(prev_ret_np[i]):
            oal = sum(1 for pid in old if np.sign(osign.get(pid, 0.0)) == np.sign(np.sign(prev_ret_np[i])))
            out.iat[i, out.columns.get_loc("old_coherence")] = oal / len(old)
        t_date = datesnp[i]
        for h in (7, 14, 30):
            out.iat[i, out.columns.get_loc(f"added_peer_fwd{h}")] = _subset_fwd(list(added), t_date, h, apos, dpos, dates, Rm)
            out.iat[i, out.columns.get_loc(f"dropped_peer_fwd{h}")] = _subset_fwd(list(dropped), t_date, h, apos, dpos, dates, Rm)
    return out


# ---------------------------------------------------------------------------
# Absorbed / reorganized / propagated / persistent classification
# ---------------------------------------------------------------------------

TRANSPORT_ORDER = ["REJOIN", "CONTAGION", "DECOUPLING", "NORMALIZED", "ISOLATED", "OTHER"]


def shock_outcome_class(snap: pd.DataFrame) -> pd.Series:
    """Classify each shock into ABSORBED / REORGANIZED / PROPAGATED /
    PERSISTENT using PIT state-change + turnover + forward transport.
    ABSORBED: no state change + no high churn + normalized/rejoin-forward.
    REORGANIZED: state change driven by local churn (turnover) w/o broad transport.
    PROPAGATED: contagion-forward (peers drag) or peer-stress surge.
    PERSISTENT: decoupling / isolating forward with high persistence (state_age).
    """
    state_changed = snap.get("state_changed", pd.Series(0, index=snap.index)).fillna(0)
    high_turn = snap["roll_turnover_30d"].fillna(0) >= snap["roll_turnover_30d"].median()
    propagated = (snap["out_contagion"].fillna(0) == 1)
    persistent = (snap["out_decouple"].fillna(0) == 1) | (snap["out_relapse"].fillna(0) == 1)
    absorbed = (~(state_changed.astype(bool))) & (~high_turn) & (~propagated) & (~persistent)
    reorganized = (state_changed.astype(bool)) & (~propagated) & (~persistent)
    # persistent takes precedence over reorganized
    cls = np.where(persistent, "PERSISTENT",
                   np.where(propagated, "PROPAGATED",
                            np.where(reorganized, "REORGANIZED",
                                     np.where(absorbed, "ABSORBED", "REORGANIZED"))))
    return pd.Series(cls, index=snap.index)


def add_shock_outcome(snap: pd.DataFrame) -> pd.DataFrame:
    snap = snap.copy()
    snap["shock_outcome"] = shock_outcome_class(snap)
    return snap