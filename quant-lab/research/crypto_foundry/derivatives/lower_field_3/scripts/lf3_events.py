"""Generate LF3 primary event families, rank-neighborhood context, isolation
scores, and all-loner forward outcomes."""
from __future__ import annotations
import numpy as np
import pandas as pd
import lf3_common as C


def add_event_context(d: pd.DataFrame) -> pd.DataFrame:
    d = C.add_basic_event_features(d)
    # Keep only the columns required for event membership and context before
    # adding flags; this prevents pandas from consolidating the 700MB cache.
    keep = ["historical_date", "cmc_id", "rank", "rank_band", "ret_1d", "sigma_t0",
            "ret_3d", "ret_14d", "fwd1_cum", "fwd2_cum", "fwd3_cum", "fwd5_cum", "fwd7_cum", "fwd10_cum", "fwd14_cum", "fwd21_cum", "fwd30_cum",
            "listing_age_days", "volume_24h_usd", "mkt_vol_30d", "btc_ret_1d",
            "eth_ret_1d", "top500_breadth_30d", "momentum_state",
            "rank_vel_7d", "rank_vel_14d", "rank_vel_30d"]
    d = d[[c for c in keep if c in d.columns]].copy()
    d["z1"] = C.z1(d)
    d["event_sign"] = np.sign(d["ret_1d"].to_numpy(float))
    d["event_sign_label"] = np.where(d["event_sign"] > 0, "UP", "DOWN")
    d["is_2s"] = d["z1"] >= 2
    d["is_3s"] = d["z1"] >= 3
    d["is_4s"] = d["z1"] >= 4
    # Same-date band participation, a separate neighborhood from rank window.
    ext = d[d["is_2s"] & d["event_sign"].ne(0)]
    counts = ext.groupby(["historical_date", "rank_band", "event_sign"]).size().rename("cluster_n")
    d = d.join(counts, on=["historical_date", "rank_band", "event_sign"])
    d["cluster_n"] = d["cluster_n"].fillna(0).astype(int)
    d["participation"] = np.select(
        [d["cluster_n"].eq(1), d["cluster_n"].between(2, 5),
         d["cluster_n"].between(6, 20), d["cluster_n"].gt(20)],
        ["ISOLATED", "LOCAL_CLUSTER", "BAND_BROAD", "MULTI_BAND"], default="NONE")
    return d


def event_rows(d):
    # Filter only after all full-panel causal features exist; the event copy is
    # now small enough to hold the contextual columns and outcomes.
    ev = d[d["is_2s"] & d["event_sign"].ne(0)].copy()
    ev["event_family"] = ev["participation"] + "_" + ev["event_sign_label"]
    ev["amp_level"] = pd.cut(ev["z1"], [2, 3, 4, np.inf], labels=["2s", "3s", "4s+"], right=False).astype(str)
    ev["raw_amp_level"] = pd.cut(ev["ret_1d"].abs(), [.10, .15, .20, np.inf], labels=["10pct", "15pct", "20pct+"], right=False).astype(str)
    return ev


def rank_neighbors(d, ev, width=50):
    # Vectorized as-of same-date rank neighborhood. To bound memory, process
    # dates in batches and aggregate only event rows.
    base = d[["historical_date", "cmc_id", "rank", "ret_1d", "z1"]]
    evx = ev[["historical_date", "cmc_id", "rank", "ret_1d", "event_sign"]].copy()
    evx["event_index"] = ev.index
    result = []
    for date, eg in evx.groupby("historical_date", sort=False):
        ng = base[base["historical_date"] == date]
        left = eg.assign(_key=1)
        right = ng.rename(columns={"cmc_id": "neighbor_cmc_id", "rank": "neighbor_rank", "ret_1d": "neighbor_ret", "z1": "neighbor_z1"}).assign(_key=1)
        pairs = left.merge(right, on=["historical_date", "_key"], how="inner")
        pairs = pairs[(pairs["neighbor_cmc_id"] != pairs["cmc_id"]) &
                      (pairs["neighbor_rank"].sub(pairs["rank"]).abs() <= width)]
        if pairs.empty:
            continue
        pairs["same_sign"] = np.sign(pairs["neighbor_ret"]) == pairs["event_sign"]
        agg = pairs.groupby("event_index", sort=False).agg(
            rank_neighbor_n=("neighbor_ret", lambda s: s.replace([np.inf, -np.inf], np.nan).notna().sum()),
            rank_neighbor_median_ret=("neighbor_ret", "median"),
            rank_neighbor_p10_ret=("neighbor_ret", lambda s: s.quantile(.10)),
            rank_neighbor_p90_ret=("neighbor_ret", lambda s: s.quantile(.90)),
            rank_neighbor_same_sign=("same_sign", "mean"),
            rank_neighbor_tail_share=("neighbor_z1", lambda s: (s >= 2).mean()),
            rank_neighbor_std=("neighbor_ret", "std"),
        ).reset_index()
        event_ret = pairs.groupby("event_index")["ret_1d"].first()
        agg["rank_context_isolation"] = (event_ret.reindex(agg["event_index"]).to_numpy() - agg["rank_neighbor_median_ret"].to_numpy()).__abs__() / (agg["rank_neighbor_std"].to_numpy() + 1e-12)
        result.append(agg)
    return pd.concat(result, ignore_index=True) if result else pd.DataFrame(columns=["event_index", "rank_neighbor_n"])


def outcomes(ev, d):
    # Join forward fields already generated on the continuous LF2 frame.
    cols = ["historical_date", "cmc_id", "rank_band", "rank", "event_sign",
            "event_family", "amp_level", "raw_amp_level", "z1", "ret_1d",
            "participation", "cluster_n", "listing_age_days", "volume_24h_usd",
            "mkt_vol_30d", "btc_ret_1d", "eth_ret_1d", "top500_breadth_30d",
            "momentum_state", "rank_vel_7d", "rank_vel_14d"]
    cols = [c for c in cols if c in ev.columns]
    out = ev[cols].copy()
    for h in C.H:
        out[f"fwd{h}"] = ev[C.FWD[h]].to_numpy(float)
        out[f"signed_fwd{h}"] = out["event_sign"] * out[f"fwd{h}"]
        out[f"rev{h}"] = out[f"signed_fwd{h}"] < 0
        out[f"giveback{h}"] = np.clip(np.maximum(0, -out[f"signed_fwd{h}"]) /
                                         out["ret_1d"].abs(), 0, 10)
        out[f"new_extreme{h}"] = out[f"signed_fwd{h}"] >= out["ret_1d"].abs()
        out[f"recover1s{h}"] = out[f"signed_fwd{h}"] >= ev["sigma_t0"].to_numpy(float) * np.sqrt(h)
        out[f"rank_delta{h}"] = np.nan
    return out


def purge_events(ev, days=30):
    keep = []
    for cid, g in ev.sort_values("historical_date").groupby("cmc_id", sort=False):
        last = None
        for idx, r in g.iterrows():
            date = pd.Timestamp(r["historical_date"])
            if last is None or (date - last).days > days:
                keep.append(idx); last = date
    return ev.loc[keep]


def main():
    # Read only the event/context columns; the LF2 cache is ~700MB with all
    # source features and should never be duplicated in memory.
    cols = ["historical_date", "cmc_id", "rank", "rank_band", "ret_1d", "sigma_t0",
            "ret_3d", "ret_14d", "fwd1_cum", "fwd2_cum", "fwd3_cum", "fwd5_cum", "fwd7_cum", "fwd10_cum", "fwd14_cum", "fwd21_cum", "fwd30_cum",
            "listing_age_days", "volume_24h_usd", "mkt_vol_30d", "btc_ret_1d",
            "eth_ret_1d", "top500_breadth_30d", "momentum_state",
            "rank_vel_7d", "rank_vel_14d", "rank_vel_30d"]
    d = pd.read_parquet(C.LF2_CACHE, columns=cols)
    d = add_event_context(d)
    ev = event_rows(d)
    nn = rank_neighbors(d, ev, 50).set_index("event_index")
    ev = ev.copy()
    ev.index.name = "event_index"
    for c in nn.columns:
        ev[c] = nn[c].reindex(ev.index)
    # Separate scores: absolute isolation is complement of rank-neighbor sign share.
    ev["absolute_isolation"] = 1 - ev["rank_neighbor_same_sign"]
    ev["behavioral_isolation"] = ev["rank_context_isolation"]
    # Emit only finite numeric scores; missing/zero-scale neighborhoods remain
    # explicit NaN rather than becoming artificial infinite isolation.
    for col in ["absolute_isolation", "behavioral_isolation", "rank_context_isolation"]:
        ev[col] = ev[col].replace([np.inf, -np.inf], np.nan)
    ev["correlation_isolation"] = np.nan  # schema-reserved; no valid trailing-corr source in LF2 cache
    ev["state_isolation"] = np.nan       # schema-reserved; no master score imputation
    ev["corr_neighbor_status"] = "NOT_AVAILABLE_LF2_CACHE"
    ev["behavior_neighbor_status"] = "DEFERRED_TO_MECH7_OR_REBUILDER"
    ev["state_neighbor_status"] = "DEFERRED_TO_MECH7_OR_REBUILDER"
    # Output 03 is a parquet by specification; keep it as a compact event table.
    ev.to_parquet(C.RESULTS / "03_CONTEXTUAL_ISOLATION_SCORES.parquet", index=False)
    ev.to_csv(C.RESULTS / "_lf3_events_internal.csv", index=False)
    # All isolated downside shocks, all amplitude levels, with forward geometry.
    loner = ev[(ev["participation"] == "ISOLATED") & (ev["event_sign"] < 0)].copy()
    for h in C.H:
        loner[f"signed_fwd{h}"] = loner["event_sign"] * loner[C.FWD[h]]
        loner[f"rev{h}"] = loner[f"signed_fwd{h}"] < 0
        loner[f"giveback{h}"] = np.clip(np.maximum(0, -loner[f"signed_fwd{h}"]) /
                                          loner["ret_1d"].abs(), 0, 10)
        loner[f"recover1s{h}"] = loner[f"signed_fwd{h}"] >= loner["sigma_t0"] * np.sqrt(h)
        loner[f"new_extreme{h}"] = loner[f"signed_fwd{h}"] >= loner["ret_1d"].abs()
    # Preserve censoring but never emit infinities from zero/near-zero scales.
    num = loner.select_dtypes(include=[np.number]).columns
    loner[num] = loner[num].replace([np.inf, -np.inf], np.nan)
    loner.to_csv(C.RESULTS / "04_ALL_LONER_OUTCOMES.csv", index=False)
    print("events", len(ev), "loner_down", len(loner), "neighbor matched", int(ev["rank_neighbor_n"].notna().sum()))


if __name__ == "__main__":
    main()
