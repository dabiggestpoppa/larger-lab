"""LOWER-FIELD-8 shared configuration and loaders.

LF8 tests whether *dynamic relational state* is a more robust object than
*static peer membership*. It resolves the LF7 peer-lifetime paradox, defines
PIT-safe relational states, and measures membership entropy, neighborhood
lifecycle, formation/dissolution clocks, static-vs-rolling peer views,
reorganization response curves, loner decomposition, rejoin/contagion/
decoupling lattice and PRD-as-relational-health.

SAMPLING DESIGN (PIT-safe, frozen substrate):
The LF5 peer maps are event-anchored: each asset-day that was an ISOLATED
(>=2 sigma) move in the peer universe has a membership snapshot. LF8 therefore
observes each asset's neighborhood exactly at its local-stress dates. All
rolling-window membership metrics are computed over the asset's OWN
chronological snapshots inside the calendar window. This is the honest reading
of the frozen PIT substrate; daily re-derivation of behavioral/correlation
peer maps is out of scope (would reinvent LF5).

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_5" / "scripts"))
import lf5_common as C5  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_7" / "scripts"))
import lf7_common as C7  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent          # lower_field_8/
LF5 = ROOT.parent / "lower_field_5"
LF6 = ROOT.parent / "lower_field_6"
LF7 = ROOT.parent / "lower_field_7"
M12 = ROOT.parent.parent / "alt_rotation" / "mech_12"
M13 = ROOT.parent.parent / "alt_rotation" / "mech_13"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

EVENTS = C7.EVENTS
SUBSTRATE = C7.SUBSTRATE
PEER_FILES = C7.PEER_FILES

# Five true-peer families (LF6/LF7). CORR families carry membership identity
# but their peer_return column is fully missing (LF5 quality row: 1.0), so
# return-based relational metrics are restricted to the other families.
DEEP_FAMILIES = C7.DEEP_FAMILIES
RETURN_FAMILIES = ["BEHAVIORAL_10", "STATE", "HYBRID_10"]
PRIMARY_FAMILY = "HYBRID_10"

# Relational-state cascade (PIT-safe: uses t0 and asset-past only).
STATE_ORDER = [
    "REORGANIZING",        # membership itself is churning (rolling turnover high)
    "DECOUPLED",           # persistently out-of-step with peers
    "TRUE_ISOLATED",       # real idiosyncratic move, peers quiet
    "FALSE_ISOLATED",      # sigma-inflated small move, peers quiet (artifact)
    "PEER_STRESSED",       # neighborhood itself stressed, asset aligned/quiet
    "REJOINING",           # prior dislocation shrinking back toward peers
    "REHABILITATING",      # prior dislocation now conforming + improving
    "CONTAGIOUS",          # peers moving with/after the asset (shared move)
    "LOCALLY_CONFORMING",  # default: asset moves with its neighborhood
]
STATE_SET = set(STATE_ORDER)

WINDOWS = [7, 14, 30, 60]
H = [1, 3, 7, 14, 30, 60]
MIN_EVENTS = 50
MIN_SUPPORT = 50

DEPTH_BANDS = C7.DEPTH_BANDS
CELL4 = {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
         "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"}


def _entropy_series(counts):
    """Shannon entropy (bits) of a frequency-count series."""
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size == 0:
        return np.nan
    p = counts / counts.sum()
    return float(-(p * np.log2(p)).sum())


def load_events() -> pd.DataFrame:
    return C7.load_events()


def load_substrate_slim() -> pd.DataFrame:
    return C7.load_substrate_slim()


def load_peer_map(family: str) -> pd.DataFrame:
    return C7.load_peer_map(family)


def load_lf6_consensus() -> pd.DataFrame:
    cls = pd.read_csv(LF6 / "03_CONSENSUS_LONER_CLASSIFICATION.csv")
    cls = cls[["event_index", "final_class", "n_families_true", "n_families_voted"]]
    return cls


def load_lf7_verdicts() -> pd.DataFrame:
    """LF7 peer-validity reclassification (family-level, constant per family)."""
    return pd.read_csv(LF7 / "02_PEER_VALIDITY_RECLASSIFICATION.csv")


def load_lf7_false_loner_audit() -> pd.DataFrame:
    return pd.read_csv(LF7 / "08_FALSE_LONER_ARTIFACT_AUDIT.csv")


# ---------------------------------------------------------------------------
# Snapshot panel builder
# ---------------------------------------------------------------------------

def _peer_agg(pm, ev):
    """Per-event peer aggregates (identity + return summary)."""
    g = pm.groupby("event_index")
    pr = pm.groupby("event_index")["peer_return"]
    agg = pd.DataFrame({
        "peer_count": g["peer_id"].count(),
        "peer_med_ret": pr.median(),
        "peer_std_ret": pr.std(ddof=0),
        "peer_abs_med": pr.apply(lambda s: float(s.abs().median()) if len(s) else np.nan),
        "peer_abs_mean": pr.apply(lambda s: float(s.abs().mean()) if len(s) else np.nan),
        "peer_pos_frac": pr.apply(lambda s: float((s > 0).mean()) if len(s) else np.nan),
    })
    agg = agg.reset_index()
    agg["peer_std_ret"] = agg["peer_std_ret"].fillna(0.0)
    return agg


def _rolling_membership(snap, window_days):
    """For each snapshot, membership metrics over the asset's OWN snapshots
    inside the trailing calendar window (including current). Per-asset."""
    snap = snap.sort_values(["cmc_id", "historical_date"])
    n = len(snap)
    out = pd.DataFrame(index=snap.index, dtype=float)
    for w in [7, 14, 30, 60]:
        uniq = np.full(n, np.nan)
        eff = np.full(n, np.nan)
        conc = np.full(n, np.nan)
        ent = np.full(n, np.nan)
        ns = np.zeros(n, dtype=int)
        for cid, g in snap.groupby("cmc_id", sort=False):
            dates = g["historical_date"].to_numpy()
            sets = g["_peerset"].to_numpy()
            pos = g.index.to_numpy()
            m = len(g)
            for i in range(m):
                lo = dates[i] - pd.Timedelta(days=w)
                s = set()
                cnt = {}
                k = 0
                for j in range(i, -1, -1):
                    if dates[j] < lo:
                        break
                    k += 1
                    for pid in sets[j]:
                        s.add(pid)
                        cnt[pid] = cnt.get(pid, 0) + 1
                ns[pos[i]] = k
                if k == 0:
                    continue
                uniq[pos[i]] = len(s)
                c = np.fromiter(cnt.values(), dtype=float)
                eff[pos[i]] = 1.0 / np.sum((c / c.sum()) ** 2)
                conc[pos[i]] = c.max() / c.sum()
                ent[pos[i]] = _entropy_series(c)
        out[f"unique_peers_{w}d"] = uniq
        out[f"eff_peers_{w}d"] = eff
        out[f"conc_{w}d"] = conc
        out[f"entropy_{w}d"] = ent
        out[f"n_snap_{w}d"] = ns
    return out


def _turnover_prev(snap):
    """Jaccard turnover between consecutive snapshots (same asset)."""
    dates = snap["historical_date"].to_numpy()
    sets = snap["_peerset"].to_numpy()
    prev = []
    prev_date = []
    prev_resz = []
    for i in range(len(snap)):
        if i == 0:
            prev.append(np.nan)
            prev_date.append(np.nan)
            prev_resz.append(np.nan)
            continue
        a, b = sets[i - 1], sets[i]
        j = len(a & b) / max(len(a | b), 1)
        prev.append(1.0 - j)
        prev_date.append(float((dates[i] - dates[i - 1]) / np.timedelta64(1, "D")))
        prev_resz.append(snap["res_z"].iloc[i - 1])
    return (pd.Series(prev, index=snap.index, dtype=float),
            pd.Series(prev_date, index=snap.index, dtype=float),
            pd.Series(prev_resz, index=snap.index, dtype=float))


STATE_ORDER_EXT = STATE_ORDER + ["DISLOCATED_UNCLASSIFIED"]


def _assign_relational_state(snap, q):
    """PIT-safe relational-state cascade. Only t0 features + asset-past.

    Order matters; each state claims rows its condition dominates. The final
    fallback splits leftovers by residual: dislocated-but-unclassified rows are
    labelled explicitly rather than forced into LOCALLY_CONFORMING.
    """
    res_z = snap["res_z"].to_numpy()
    abs_ret = snap["abs_ret"].to_numpy()
    peer_std = snap["peer_std_ret"].to_numpy()
    peer_abs = snap["peer_abs_med"].to_numpy()
    turn = snap["turnover_prev"].to_numpy()
    prev_resz = snap["prev_res_z"].to_numpy()
    roll_turn = snap["roll_turnover_30d"].to_numpy()

    turn_hi = q.get("turn_hi", 0.5)
    pstd_hi = q.get("pstd_hi", 0.03)
    pabs_hi = q.get("pabs_hi", 0.03)

    reorg_turn = np.where(np.isfinite(roll_turn), roll_turn, np.nan_to_num(turn, nan=0.0))
    is_high_turn = (reorg_turn >= turn_hi) & (reorg_turn > 0)
    prev_out = np.abs(np.nan_to_num(prev_resz, nan=0.0)) > 1.5
    persistent_out = (np.abs(res_z) > 1.5) & prev_out
    real_iso = (np.abs(res_z) > 1.5) & (peer_std <= pstd_hi) & (abs_ret >= 0.02)
    false_iso = (np.abs(res_z) > 1.5) & (peer_std <= pstd_hi) & (abs_ret < 0.02)
    peer_stress = (peer_std >= pstd_hi) & (peer_abs >= pabs_hi) & (np.abs(res_z) <= 1.5)
    contagious = (np.abs(res_z) > 1.0) & (peer_std > pstd_hi) & (peer_abs > 0.01)
    rehab = prev_out & (np.abs(res_z) <= 1.0) & (np.nan_to_num(roll_turn, nan=0.0) < turn_hi)
    rejoining = prev_out & (np.abs(res_z) <= 1.5) & (np.nan_to_num(roll_turn, nan=0.0) < turn_hi)

    state = np.array([None] * len(snap), dtype=object)

    def claim(mask, name):
        nonlocal state
        m = mask & (state == None)  # noqa: E711
        state[m] = name

    claim(is_high_turn, "REORGANIZING")
    claim(persistent_out, "DECOUPLED")
    claim(real_iso, "TRUE_ISOLATED")
    claim(false_iso, "FALSE_ISOLATED")
    claim(peer_stress, "PEER_STRESSED")
    claim(contagious, "CONTAGIOUS")
    claim(rehab, "REHABILITATING")
    claim(rejoining, "REJOINING")
    claim(np.abs(res_z) > 1.5, "DISLOCATED_UNCLASSIFIED")
    claim(state == None, "LOCALLY_CONFORMING")  # noqa: E711
    return state


def build_family_panel(family: str, use_cache: bool = True) -> pd.DataFrame:
    """Full per-snapshot panel for one peer family."""
    cache_p = CACHE / f"lf8_panel_{family}.parquet"
    if use_cache and cache_p.exists():
        return pd.read_parquet(cache_p)

    ev = load_events()
    ev = ev[ev["participation"] == "ISOLATED"].copy()
    ev["event_index"] = ev.index
    ev = ev[ev["rank_band"].isin(DEPTH_BANDS)]
    pm = load_peer_map(family)
    agg = _peer_agg(pm, ev)
    snap = ev.merge(agg, on="event_index", how="inner")
    if len(snap) == 0:
        return pd.DataFrame()

    # peer sets per snapshot
    sets = pm.groupby("event_index")["peer_id"].apply(lambda s: frozenset(s))
    snap["_peerset"] = snap["event_index"].map(sets)

    snap["abs_ret"] = snap["ret_1d"].abs()
    snap["peer_med_ret"] = snap["peer_med_ret"].fillna(0.0)
    snap["res"] = snap["ret_1d"] - snap["peer_med_ret"]
    pstd = snap["peer_std_ret"].replace(0.0, np.nan)
    snap["res_z"] = snap["res"] / pstd
    snap["peer_corr"] = np.sign(snap["ret_1d"]) * snap["peer_med_ret"] / pstd
    snap["peer_corr"] = np.where(snap["res_z"].isna(), np.nan, snap["peer_corr"]).clip(-1, 1)
    snap["cell4"] = snap["field_cell"].map(CELL4)

    # rolling membership metrics (over asset's own snapshots)
    r = _rolling_membership(snap, 60)
    snap = pd.concat([snap, r], axis=1)

    # chronological ordering per asset BEFORE consecutive-snapshot features
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)

    # turnover between consecutive snapshots
    turn, days_prev, prev_resz = _turnover_prev(snap)
    snap["turnover_prev"] = turn
    snap["days_since_prev"] = days_prev
    snap["prev_res_z"] = prev_resz

    # rolling turnover: sustained churn over 30d; fall back to prev turnover
    j30 = snap["n_snap_30d"] >= 2
    snap["roll_turnover_30d"] = np.where(j30, snap["turnover_prev"],
                                          np.nan_to_num(turn, nan=np.nan))

    # family-level thresholds for the relational-state cascade
    q = {
        "turn_hi": float(np.nanquantile(snap["roll_turnover_30d"], 0.67)),
        "turn_lo": float(np.nanquantile(snap["roll_turnover_30d"], 0.33)),
        "pstd_hi": float(np.nanquantile(snap[snap["peer_std_ret"] > 0]["peer_std_ret"], 0.67)),
        "pabs_hi": float(np.nanquantile(snap["peer_abs_med"], 0.67)),
    }
    snap["peer_stress"] = ((snap["peer_std_ret"] >= q["pstd_hi"])
                           & (snap["peer_abs_med"] >= q["pabs_hi"])).astype(float)
    snap["rel_state"] = _assign_relational_state(snap, q)

    # state age: days since last state change over the asset's own series
    prev_by_asset = snap.groupby("cmc_id")["rel_state"].shift()
    changed = snap["rel_state"] != prev_by_asset
    tmp = snap[["cmc_id", "historical_date"]].copy()
    tmp["lc"] = tmp["historical_date"].where(changed)
    last_change = tmp.groupby("cmc_id")["lc"].ffill()
    snap["state_age_d"] = (snap["historical_date"] - last_change).dt.days
    snap["state_changed"] = changed.astype(int)

    # membership-stability class (rolling turnover terciles, per family)
    snap["membership_class"] = pd.qcut(
        snap["roll_turnover_30d"].rank(method="first"),
        3, labels=["STABLE_MEMBERS", "DYNAMIC_MEMBERS", "ROTATING_MEMBERS"]).astype(str)

    # LF6 consensus loner label
    cls = load_lf6_consensus()
    snap = snap.merge(cls, on="event_index", how="left")
    snap["is_true_loner"] = snap["final_class"].str.startswith("TRUE").astype(float)
    snap["is_false_loner"] = snap["final_class"].str.startswith(("BEHAVIORAL_FALSE",
                                                                 "CORR_FALSE",
                                                                 "HYBRID_FALSE",
                                                                 "STATE_FALSE")).astype(float)

    snap["family"] = family
    snap = snap.drop(columns=["_peerset"])
    snap.to_parquet(cache_p, index=False)
    return snap


def load_primary_panel(use_cache: bool = True) -> pd.DataFrame:
    return build_family_panel(PRIMARY_FAMILY, use_cache=use_cache)


# ---------------------------------------------------------------------------
# Forward outcomes (PIT-safe *assignment*, forward *measurement*)
# ---------------------------------------------------------------------------

def forward_state_4(df, h):
    """LF7-style 4-state at +h (outcome coordinate): REJOINED / DECOUPLED /
    CONTAGION / REJOINING from price-up x rank-down combinations."""
    price_down = df.get(f"signed_fwd{h}", pd.Series(dtype=float)) < 0
    price_up = ~price_down
    rv = df.get(f"fwd_rank_vel_{h}d", pd.Series(dtype=float))
    s = np.select(
        [price_up & (rv < 0), price_down & (rv > 0),
         price_down & (rv <= 0)],
        ["REJOINED", "DECOUPLED", "CONTAGION"], default="REJOINING")
    return s


def attach_forward_outcomes(snap: pd.DataFrame) -> pd.DataFrame:
    for h in [1, 3, 7, 14, 30]:
        snap[f"st4_{h}"] = forward_state_4(snap, h)
        snap[f"price_up_{h}"] = (snap[f"signed_fwd{h}"] >= 0).astype(float)
        snap[f"rank_up_{h}"] = (snap[f"fwd_rank_vel_{h}d"] > 0).astype(float)
        snap[f"recover1s{h}"] = snap[f"recover1s{h}"].fillna(False).astype(int)
    # relational health outcome booleans
    snap["out_rejoin"] = (snap["st4_30"] == "REJOINED").astype(int)
    snap["out_contagion"] = (snap["st4_7"] == "CONTAGION").astype(int)
    snap["out_decouple"] = (snap["st4_30"] == "DECOUPLED").astype(int)
    snap["out_relapse"] = (snap["signed_fwd30"] < 0).astype(int)
    snap["out_price_repair"] = snap["recover1s30"].astype(int)
    snap["out_rank_repair"] = (snap["fwd_rank_vel_30d"] > 0).astype(int)
    return snap


_WIDE_RET = None


def _wide_returns():
    """Dates x assets matrix of daily returns (LF5 cached wide panel)."""
    global _WIDE_RET
    if _WIDE_RET is None:
        w = pd.read_parquet(LF5 / "cache" / "pit_returns_wide.parquet")
        _WIDE_RET = (w.index, w.columns, w.to_numpy(dtype=float))
    return _WIDE_RET


def substrate_forward(df: pd.DataFrame, horizons=(30, 60, 90)) -> pd.DataFrame:
    """Add substrate-derived forward cumulative returns + rank at arbitrary
    horizons (survivor-sensitive: NaN where asset row missing at t+h).
    Cumulative return over (t, t+h] from the LF5 wide return matrix; rank
    at t+h from the daily substrate."""
    dates, assets, R = _wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    out = df[["event_index", "cmc_id", "historical_date"]].copy()
    for h in horizons:
        cum = np.full(len(out), np.nan)
        for i, (_, row) in enumerate(out.iterrows()):
            di = dpos.get(row["historical_date"])
            ai = apos.get(row["cmc_id"])
            if di is None or ai is None:
                continue
            t = dates[di]
            lo = di + 1
            hi = di
            while hi + 1 < len(dates) and dates[hi + 1] <= t + pd.Timedelta(days=h):
                hi += 1
            if hi >= lo:
                cum[i] = float(np.nansum(R[lo:hi + 1, ai]))
        out[f"cum_ret_{h}d"] = cum
    # rank at t+h from substrate (exact-date lookup)
    sub = pd.read_parquet(SUBSTRATE, columns=["cmc_id", "historical_date", "rank"])
    sub["historical_date"] = pd.to_datetime(sub["historical_date"])
    for h in horizons:
        lut = dict(zip(zip(sub["cmc_id"], sub["historical_date"]), sub["rank"]))
        out[f"rank_{h}d"] = [lut.get((c, t + pd.Timedelta(days=h)), np.nan)
                              for c, t in zip(out["cmc_id"], out["historical_date"])]
    return out
