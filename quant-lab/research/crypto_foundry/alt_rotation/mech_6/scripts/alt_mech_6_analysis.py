#!/usr/bin/env python
"""ALT_MECH_6 - Micro-State Sequence Atlas, Breadth Transmission, Local Motifs
& Research-to-Alpha Role Mapping.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no strategy,
no optimization, no ML predictors, no sizing, no deployment.
"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, fisher_exact, norm, chi2 as chi2_dist
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260901
BOOT_N = 500
PERM_N = 500
MIN_PROMOTE_N = 50          # minimum effective independent observations
MIN_SUBPERIODS = 3          # >=3 subperiods for promotion
LIFT_THRESHOLD = 1.25       # promotion lift vs marginal baseline
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_6/
M5_ROOT = ROOT.parent / "mech_5"
M4_ROOT = ROOT.parent / "mech_4"
M4_SCRIPTS = M4_ROOT / "scripts"
sys.path.insert(0, str(M4_SCRIPTS))
import alt_mech_4_analysis as M4

OUT = ROOT
M4_OUT = M4_ROOT
M5_OUT = M5_ROOT

BANDS = M4.BANDS
ALT_FAMILY = M4.ALT_FAMILY
SUCCESS_LABELS = {"BROAD_RISK_EXPANSION"} | set(ALT_FAMILY)
FAILURE_LABELS = {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"}
REENTRY_LABEL = "BTC_CONCENTRATION"

HORIZONS = [0, 1, 2, 3, 5, 7, 10, 14, 21, 30]
LATTICES = [(0, 1, 3), (0, 3, 7), (0, 7, 14), (0, 14, 30)]
SUBPERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]

# breadth / rank / conc / eth / btc thresholds (fixed, preregistered)
B_CHG_EPS = 0.02
REL_CHG_EPS = 0.02
CONC_EPS = 0.001
BTC_EPS = 0.05

STATE_FEATURE_MAP = {
    "btc_ret30": "btc_return_30d", "btc_ret7": "btc_return_7d",
    "top3_share": "top3_share", "top3_share_chg7": "top3_share_chg7",
    "breadth30": "top500_breadth_30d", "disp30": "top500_dispersion_30d",
    "sc_chg30": "stablecoin_change_30d", "eth_rel30": "eth_btc_relative_return_30d",
    "vol_med": "vol_med", "chain_tvl_med_chg7": "chain_tvl_med_chg7",
}


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run] {name} ...")
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def load_data():
    inp, tl = M4._cache_step("inputs", M4.load)
    daily, d, bm = M4._cache_step("daily", lambda: M4.build_daily(inp))
    m, top = M4._cache_step("chainframe", lambda: M4.build_chainframe(inp))
    rc = M4._cache_step("reconcile", lambda: M4.ws_reconcile(daily))
    entries, exits = rc["recount"]["entries"], rc["recount"]["exits"]
    rA = M4._cache_step("A", lambda: M4.ws_a(daily, entries, exits))
    ledger = rA["ledger"]
    X, feat_df = M4._cache_step("feats", lambda: M4._exit_features(ledger, daily))
    # MECH-5 motif map (15_FAILURE_SEQUENCE_MAP.csv)
    seq5 = pd.read_csv(M5_OUT / "15_FAILURE_SEQUENCE_MAP.csv")
    motif_map = dict(zip(seq5.event_id, seq5.motif))
    # MECH-4 first-move classes
    fm = pd.read_csv(M4_OUT / "33_FIRST_MOVE_TRUE_DELIVERY.csv")
    fm_map = dict(zip(fm.event_id, fm.classification))
    # MECH-5 termination matched controls (for WS6)
    term5 = pd.read_csv(M5_OUT / "12_TERMINATION_MATCHED_CONTROLS.csv")
    return daily, ledger, entries, exits, m, top, bm, X, feat_df, motif_map, fm_map, term5


# =========================================================================
# STATE ATOMS (single computation over the full daily frame)
# =========================================================================

def compute_atoms(daily, bm):
    """Add atom columns to a copy of daily. Returns (df, bm_joined)."""
    df = daily.copy().reset_index(drop=True)
    b = df["top500_breadth_30d"].astype(float)
    b_chg = b.diff(5)
    b_chg2 = b_chg.diff(5)
    df["breadth_vel"] = b_chg
    df["breadth_accel"] = b_chg2
    df["breadth_axis"] = np.where(b_chg > B_CHG_EPS, "BREADTH_EXPANDING",
                          np.where(b_chg < -B_CHG_EPS, "BREADTH_FADING", "BREADTH_STABLE"))
    df["breadth_accel_flag"] = (b_chg2 > B_CHG_EPS).astype(int)
    df["breadth_exhaustion"] = ((b >= 0.5) & (b_chg < -B_CHG_EPS)).astype(int)
    mkt = df["mkt_ret_1d"].astype(float)
    div = (np.sign(b_chg) != np.sign(mkt)) & b_chg.notna() & mkt.notna()
    df["breadth_divergence"] = div.astype(int)

    deep = df["med_ret30_201_500"].astype(float)
    upper = df["med_ret30_11_50"].astype(float)
    rel = deep - upper
    rel_chg = rel.diff(5)
    df["rank_axis"] = np.where((rel_chg > REL_CHG_EPS) & (deep > 0), "RANK_RECRUITING",
                       np.where(rel_chg < -REL_CHG_EPS, "RANK_DETERIORATING", "RANK_STALL"))
    df["rank_depth_rel"] = rel
    df["rank_depth_rel_chg"] = rel_chg

    t3 = df["top3_share_chg7"].astype(float)
    df["conc_axis"] = np.where(t3 > CONC_EPS, "CONCENTRATION_REBUILD",
                       np.where(t3 < -CONC_EPS, "CONCENTRATION_RELEASE", "CONC_STABLE"))

    eth = df["eth_btc_relative_return_30d"].astype(float)
    eth_chg = eth.diff(5)
    df["eth_axis"] = np.where((eth > 0) & (eth_chg > 0), "ETH_IMPROVING",
                      np.where((eth < 0) & (eth_chg < 0), "ETH_WEAKENING", "ETH_NEUTRAL"))

    btc = df["btc_return_30d"].astype(float)
    df["btc_axis"] = np.where(btc > BTC_EPS, "BTC_SUPPORT",
                      np.where(btc < -BTC_EPS, "BTC_WEAKNESS", "BTC_NEUTRAL"))

    ms = []
    for _, r in df.iterrows():
        if r["rank_axis"] == "RANK_RECRUITING":
            ms.append("RANK_RECRUITMENT")
        elif r["breadth_axis"] == "BREADTH_FADING":
            ms.append("BREADTH_FADE")
        elif r["breadth_axis"] == "BREADTH_EXPANDING":
            ms.append("BREADTH_EXPANSION")
        elif r["conc_axis"] == "CONCENTRATION_REBUILD":
            ms.append("CONCENTRATION_REBUILD")
        elif r["conc_axis"] == "CONCENTRATION_RELEASE":
            ms.append("CONCENTRATION_RELEASE")
        elif r["eth_axis"] == "ETH_IMPROVING":
            ms.append("ETH_IMPROVING")
        elif r["eth_axis"] == "ETH_WEAKENING":
            ms.append("ETH_WEAKENING")
        elif r["btc_axis"] == "BTC_SUPPORT":
            ms.append("BTC_SUPPORT")
        elif r["btc_axis"] == "BTC_WEAKNESS":
            ms.append("BTC_WEAKNESS")
        else:
            ms.append("NEUTRAL")
    df["micro_state"] = ms

    # leadership width from bm
    bm2 = bm.copy()
    bm2["d"] = pd.to_datetime(bm2["historical_date"]).dt.date
    lw = bm2[bm2["median_rank_velocity_7d"] > 0].groupby("d").size()
    lw = lw.reindex(pd.to_datetime(df["historical_date"]).dt.date, fill_value=0)
    df["leadership_width"] = lw.values.astype(int)
    return df


# =========================================================================
# WS1: MICRO-STATE EVENT ATLAS
# =========================================================================

ATLAS_COORDS = [
    "btc_return_1d", "btc_return_7d", "btc_return_30d", "btc_dominance",
    "btc_dom_chg30", "total_mcap_chg30", "eth_btc_relative_return_7d",
    "eth_btc_relative_return_30d", "top500_breadth_30d", "top500_breadth_7d",
    "breadth_vel", "breadth_accel", "top500_dispersion_30d", "top500_dispersion_7d",
    "med_ret30_11_50", "med_ret30_51_200", "med_ret30_201_500", "rb_spread",
    "top3_share", "top3_share_chg7", "pos_ret_share", "pos_vel7_share",
    "vol_med", "chain_tvl_med_chg7", "dex_volume_change_7d",
    "stablecoin_change_7d", "stablecoin_change_30d", "leadership_width",
    "rank_depth_rel", "rank_depth_rel_chg",
]


def ws1_atlas(df, ledger):
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(df.historical_date.values)}
    rows = []
    for _, r in ledger.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        base = {"event_id": r.event_id, "exit_date": str(r.exit_date)[:10],
                "first_destination": r.first_destination,
                "days_to_destination_d": r.days_to_destination_d,
                "subperiod": r.subperiod}
        for h in HORIZONS:
            j = i + h
            if not (0 <= j < len(df)):
                continue
            row = dict(base)
            row["horizon_d"] = h
            row["canonical_state"] = df["state"].iloc[j]
            row["micro_state"] = df["micro_state"].iloc[j]
            row["breadth_axis"] = df["breadth_axis"].iloc[j]
            row["rank_axis"] = df["rank_axis"].iloc[j]
            row["conc_axis"] = df["conc_axis"].iloc[j]
            row["eth_axis"] = df["eth_axis"].iloc[j]
            row["btc_axis"] = df["btc_axis"].iloc[j]
            row["breadth_accel_flag"] = int(df["breadth_accel_flag"].iloc[j])
            row["breadth_exhaustion"] = int(df["breadth_exhaustion"].iloc[j])
            row["breadth_divergence"] = int(df["breadth_divergence"].iloc[j])
            row["BREADTH_EXPANDING"] = int(df["BREADTH_EXPANDING"].iloc[j])
            row["BREADTH_CONTRACTING"] = int(df["BREADTH_CONTRACTING"].iloc[j])
            row["VOL_HIGH"] = int(df["VOL_HIGH"].iloc[j])
            row["RISK_ON"] = int(df["RISK_ON"].iloc[j])
            row["BTC_UP"] = int(df["BTC_UP"].iloc[j])
            row["ETH_STRONG"] = int(df["ETH_STRONG"].iloc[j])
            for c in ATLAS_COORDS:
                v = df[c].iloc[j]
                row[c] = float(v) if v == v else np.nan
            rows.append(row)
    panel = pd.DataFrame(rows)
    panel.to_parquet(OUT / "03_MICROSTATE_EVENT_PANEL.parquet", index=False)
    return {"panel": panel}


# =========================================================================
# WS2: LOCAL SEQUENCE DISCOVERY
# =========================================================================

def _outcome_family(dest):
    if dest in SUCCESS_LABELS:
        return "SUCCESS"
    if dest == REENTRY_LABEL:
        return "REENTRY"
    if dest == "MIXED_NO_CLEAR_ROUTE":
        return "MIXED"
    return "OTHER"


def ws2_sequences(panel, df, ledger):
    """Event-anchored + panel-scan sequence discovery."""
    # ---- event-anchored: tuples over lattices per axis ----
    ev = panel.pivot_table(index="event_id", columns="horizon_d",
                           values=["canonical_state", "micro_state", "breadth_axis", "rank_axis"],
                           aggfunc="first")
    ev = ev.sort_index()
    event_rows = []
    for _, r in ledger.iterrows():
        eid = r.event_id
        if eid not in ev.index:
            continue
        base = {"event_id": eid, "exit_date": str(r.exit_date)[:10],
                "first_destination": r.first_destination,
                "outcome_family": _outcome_family(r.first_destination),
                "subperiod": r.subperiod, "days_to_destination_d": r.days_to_destination_d}
        for axis, col in [("canonical", "canonical_state"), ("micro", "micro_state"),
                          ("breadth", "breadth_axis"), ("rank", "rank_axis")]:
            for lat in LATTICES:
                try:
                    a, b, c = (ev.loc[eid, (col, h)] for h in lat)
                except KeyError:
                    continue
                if pd.isna(a) or pd.isna(b) or pd.isna(c):
                    continue
                row = dict(base)
                row["axis"] = axis
                row["lattice"] = f"{lat[0]}-{lat[1]}-{lat[2]}"
                row["seq"] = f"{a}->{b}->{c}"
                event_rows.append(row)
    ev_seq = pd.DataFrame(event_rows)
    ev_seq.to_csv(OUT / "04_SEQUENCE_COUNTS.csv", index=False)

    # summarize event-anchored: counts, marginals, lift, subperiods, FDR
    summary = []
    for (axis, lattice, seq), grp in ev_seq.groupby(["axis", "lattice", "seq"]):
        n_obs = len(grp)
        if n_obs < 3:
            continue
        # expected under independence using position marginals
        n_total = len(ev_seq[(ev_seq.axis == axis) & (ev_seq.lattice == lattice)])
        parts = seq.split("->")
        exp = 1.0
        for k, part in enumerate(parts):
            pos_n = int((ev_seq[(ev_seq.axis == axis) & (ev_seq.lattice == lattice)]
                         [f"seq"].str.split("->").str[k] == part).sum())
            exp *= max(pos_n, 1) / max(n_total, 1)
        exp *= n_total
        lift = n_obs / exp if exp > 0 else np.nan
        # subperiod counts
        sp_counts = grp.subperiod.value_counts().reindex(SUBPERIODS).fillna(0).astype(int)
        n_subperiods = int((sp_counts > 0).sum())
        # outcome distribution
        oc = grp.outcome_family.value_counts()
        p_success = round(float(oc.get("SUCCESS", 0) / n_obs), 3)
        p_reentry = round(float(oc.get("REENTRY", 0) / n_obs), 3)
        p_mixed = round(float(oc.get("MIXED", 0) / n_obs), 3)
        # chi-square vs expected
        exp_c = max(exp, 0.5)
        chi2 = (n_obs - exp_c) ** 2 / exp_c if exp_c > 0 else 0.0
        p_chi = float(chi2_dist.sf(chi2, 1)) if chi2 >= 0 else 1.0
        # bootstrap CI for lift (resample the underlying event pool)
        rng = np.random.RandomState(SEED + len(summary))
        pool = ev_seq[(ev_seq.axis == axis) & (ev_seq.lattice == lattice)].seq.values
        lifts = []
        for _ in range(200):
            samp = rng.choice(pool, size=len(pool), replace=True)
            n_boot = int((samp == seq).sum())
            lifts.append(n_boot / exp if exp > 0 else np.nan)
        lifts = [x for x in lifts if x == x]
        lo = float(np.percentile(lifts, 5)) if lifts else np.nan
        hi = float(np.percentile(lifts, 95)) if lifts else np.nan
        summary.append({
            "axis": axis, "lattice": lattice, "seq": seq,
            "n_events": n_obs, "expected": round(exp, 2), "lift": round(lift, 3),
            "lift_ci5": round(lo, 3), "lift_ci95": round(hi, 3),
            "n_subperiods": n_subperiods,
            **{f"sp_{s}": int(sp_counts[s]) for s in SUBPERIODS},
            "p_success": p_success, "p_reentry": p_reentry, "p_mixed": p_mixed,
            "chi2": round(chi2, 3), "p_raw": round(p_chi, 6),
        })
    ev_sum = pd.DataFrame(summary)
    if len(ev_sum) > 0:
        reject, p_adj, _, _ = multipletests(ev_sum.p_raw.values, method="fdr_bh")
        ev_sum["p_fdr"] = np.round(p_adj, 6)
        ev_sum["significant_fdr"] = reject
    ev_sum.to_csv(OUT / "05_SEQUENCE_BASELINE_LIFTS.csv", index=False)

    # ---- panel scan: composite micro-state paths (run-collapsed) ----
    ms = df["micro_state"].tolist()
    runs = []  # (start_idx, end_idx, label)
    s = 0
    for i in range(1, len(ms) + 1):
        if i == len(ms) or ms[i] != ms[s]:
            runs.append((s, i - 1, ms[s]))
            s = i
    paths = []  # 3 consecutive distinct states
    for k in range(len(runs) - 2):
        r0, r1, r2 = runs[k], runs[k + 1], runs[k + 2]
        start_idx = r0[0]
        dur = (r2[1] - r0[0] + 1)
        d = pd.Timestamp(df["historical_date"].iloc[start_idx])
        sub = df["subperiod"].iloc[start_idx]
        j7 = start_idx + 7
        j30 = start_idx + 30
        state7 = df["state"].iloc[j7] if 0 <= j7 < len(df) else "OUT_OF_RANGE"
        state30 = df["state"].iloc[j30] if 0 <= j30 < len(df) else "OUT_OF_RANGE"
        paths.append({
            "seq": f"{r0[2]}->{r1[2]}->{r2[2]}",
            "start_idx": start_idx, "end_idx": r2[1],
            "date": d, "subperiod": sub, "duration_d": int(dur),
            "state_tp7": state7, "state_tp30": state30,
        })
    panel_paths = pd.DataFrame(paths)
    psum = []
    n_total = len(panel_paths)
    for seq, grp in panel_paths.groupby("seq"):
        n = len(grp)
        if n < 3:
            continue
        parts = seq.split("->")
        exp = 1.0
        for k, part in enumerate(parts):
            pos_n = int((panel_paths.seq.str.split("->").str[k] == part).sum())
            exp *= max(pos_n, 1) / max(n_total, 1)
        exp *= n_total
        lift = n / exp if exp > 0 else np.nan
        sp_counts = grp.subperiod.value_counts().reindex(SUBPERIODS).fillna(0).astype(int)
        n_sub = int((sp_counts > 0).sum())
        # effective count: non-overlapping occurrences (greedy, span = 3 runs)
        starts = grp["start_idx"].values
        eff = 0
        last = -10 ** 9
        for st in np.sort(starts):
            if st - last >= 3:
                eff += 1
                last = st
        med_dur = float(grp.duration_d.median())
        # bootstrap CI for lift (resample the path pool)
        rng2 = np.random.RandomState(SEED + 777 + len(psum))
        seqs_all = panel_paths.seq.values
        lifts_b = []
        for _ in range(200):
            samp = rng2.choice(seqs_all, size=len(seqs_all), replace=True)
            nb = int((samp == seq).sum())
            lifts_b.append(nb / exp if exp > 0 else np.nan)
        lo_b = float(np.percentile(lifts_b, 5)) if lifts_b else np.nan
        hi_b = float(np.percentile(lifts_b, 95)) if lifts_b else np.nan
        # outcome: state family at +7D and +30D
        f7 = grp.state_tp7.map(lambda s: "SUCCESS" if s in SUCCESS_LABELS else
                               "REENTRY" if s == REENTRY_LABEL else
                               "MIXED" if s == "MIXED_NO_CLEAR_ROUTE" else "OTHER")
        f30 = grp.state_tp30.map(lambda s: "SUCCESS" if s in SUCCESS_LABELS else
                                 "REENTRY" if s == REENTRY_LABEL else
                                 "MIXED" if s == "MIXED_NO_CLEAR_ROUTE" else "OTHER")
        p7_suc = round(float((f7 == "SUCCESS").mean()), 3)
        p30_suc = round(float((f30 == "SUCCESS").mean()), 3)
        p7_re = round(float((f7 == "REENTRY").mean()), 3)
        p30_re = round(float((f30 == "REENTRY").mean()), 3)
        exp_c = max(exp, 0.5)
        chi2 = (n - exp_c) ** 2 / exp_c if exp_c > 0 else 0.0
        p_chi = float(chi2_dist.sf(chi2, 1)) if chi2 >= 0 else 1.0
        psum.append({
            "seq": seq, "n_raw": n, "n_effective": eff, "expected": round(exp, 2),
            "lift": round(lift, 3), "lift_ci5": round(lo_b, 3), "lift_ci95": round(hi_b, 3),
            "n_subperiods": n_sub,
            **{f"sp_{s}": int(sp_counts[s]) for s in SUBPERIODS},
            "median_duration_d": round(med_dur, 1),
            "p7_success": p7_suc, "p30_success": p30_suc,
            "p7_reentry": p7_re, "p30_reentry": p30_re,
            "p_raw": round(p_chi, 6),
        })
    psum_df = pd.DataFrame(psum)
    if len(psum_df) > 0:
        reject, p_adj, _, _ = multipletests(psum_df.p_raw.values, method="fdr_bh")
        psum_df["p_fdr"] = np.round(p_adj, 6)
        psum_df["significant_fdr"] = reject
    psum_df.to_csv(OUT / "06_SEQUENCE_SUBPERIOD_STABILITY.csv", index=False)

    # ---- atlas: classify each candidate ----
    atlas_rows = []
    for _, srow in ev_sum.iterrows():
        n_eff = int(srow.n_events)
        n_sub = int(srow.n_subperiods)
        lift = srow.lift
        q = srow.p_fdr
        promoted = (n_eff >= MIN_PROMOTE_N and n_sub >= MIN_SUBPERIODS
                    and lift >= LIFT_THRESHOLD and q < FDR_Q and srow.significant_fdr)
        trivial = srow.seq.count("->") >= 1 and len(set(srow.seq.split("->"))) == 1
        if promoted:
            cls = "LOCAL_SEQUENCE"
        elif n_eff >= MIN_PROMOTE_N and n_sub >= MIN_SUBPERIODS:
            cls = "GLOBAL_SEQUENCE" if lift >= 1.0 else "NULL"
        elif n_eff >= 10:
            cls = "DESCRIPTIVE_SEQUENCE"
        elif n_eff >= 3:
            cls = "LOW_SAMPLE_CURIOSITY"
        else:
            cls = "NULL"
        atlas_rows.append({
            "seq_id": f"E:{srow.axis}:{srow.lattice}:{srow.seq}",
            "sample": "EVENT", "axis": srow.axis, "lattice": srow.lattice,
            "seq": srow.seq, "n_effective": n_eff, "n_subperiods": n_sub,
            "lift": round(float(lift), 3), "p_fdr": round(float(q), 6),
            "p_success": srow.p_success, "p_reentry": srow.p_reentry,
            "trivial_persistence": int(trivial),
            "classification": cls,
        })
    for _, srow in psum_df.iterrows():
        n_eff = int(srow.n_effective)
        n_sub = int(srow.n_subperiods)
        lift = srow.lift
        q = srow.p_fdr
        promoted = (n_eff >= MIN_PROMOTE_N and n_sub >= MIN_SUBPERIODS
                    and lift >= LIFT_THRESHOLD and q < FDR_Q and srow.significant_fdr)
        trivial = len(set(srow.seq.split("->"))) == 1
        if promoted:
            cls = "LOCAL_SEQUENCE"
        elif n_eff >= MIN_PROMOTE_N and n_sub >= MIN_SUBPERIODS:
            cls = "GLOBAL_SEQUENCE" if lift >= 1.0 else "NULL"
        elif n_eff >= 10:
            cls = "DESCRIPTIVE_SEQUENCE"
        elif n_eff >= 3:
            cls = "LOW_SAMPLE_CURIOSITY"
        else:
            cls = "NULL"
        atlas_rows.append({
            "seq_id": f"P:{srow.seq}",
            "sample": "PANEL", "axis": "micro", "lattice": "path",
            "seq": srow.seq, "n_effective": n_eff, "n_subperiods": n_sub,
            "lift": round(float(lift), 3), "p_fdr": round(float(q), 6),
            "p_success": srow.p30_success, "p_reentry": srow.p30_reentry,
            "trivial_persistence": int(trivial),
            "classification": cls,
        })
    atlas = pd.DataFrame(atlas_rows)
    atlas.to_csv(OUT / "07_LOCAL_SEQUENCE_ATLAS.csv", index=False)
    n_promoted = int((atlas.classification == "LOCAL_SEQUENCE").sum())
    return {"event_sequences": ev_seq, "event_summary": ev_sum,
            "panel_paths": panel_paths, "panel_summary": psum_df,
            "atlas": atlas, "n_promoted": n_promoted}
# =========================================================================
# WS3: BREADTH TRANSMISSION ANATOMY
# =========================================================================

BREADTH_COORDS = {
    "level": "top500_breadth_30d",
    "velocity": "breadth_vel",
    "acceleration": "breadth_accel",
    "depth_rel": "rank_depth_rel",
    "depth_chg": "rank_depth_rel_chg",
    "dispersion": "top500_dispersion_30d",
    "leadership_width": "leadership_width",
    "pos_ret_share": "pos_ret_share",
    "pos_vel7_share": "pos_vel7_share",
    "btc_ret30": "btc_return_30d",
}


def _auc_safe(y, p):
    if len(set(y)) < 2:
        return np.nan
    return float(roc_auc_score(y, p))


def _logloss_safe(y, p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return float(log_loss(y, p))


def ws3_breadth(df, ledger, motif_map):
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(df.historical_date.values)}
    prim = ledger[ledger.first_destination.isin(list(SUCCESS_LABELS | FAILURE_LABELS))].copy()
    prim["is_success"] = prim.first_destination.isin(SUCCESS_LABELS).astype(int)
    rows = []

    # Q1: earliest separating horizon per coordinate (rank-sum, FDR)
    q1 = []
    for name, col in BREADTH_COORDS.items():
        if col not in df.columns:
            continue
        for h in [0, 1, 2, 3, 5, 7]:
            suc, fail = [], []
            for _, r in prim.iterrows():
                i = date_idx.get(pd.Timestamp(r.exit_date))
                if i is None:
                    continue
                j = i + h
                if 0 <= j < len(df):
                    v = df[col].iloc[j]
                    if v == v:
                        (suc if r.is_success else fail).append(float(v))
            if len(suc) >= 5 and len(fail) >= 5:
                stat, p = ranksums(suc, fail)
                z = norm.ppf(1 - p / 2) * (1 if stat > 0 else -1)
                r_eff = z / np.sqrt(len(suc) + len(fail))
                q1.append({"coordinate": name, "horizon_d": h,
                           "n_suc": len(suc), "n_fail": len(fail),
                           "median_suc": round(float(np.median(suc)), 4),
                           "median_fail": round(float(np.median(fail)), 4),
                           "r_eff": round(float(r_eff), 4), "p_raw": round(float(p), 6)})
    q1df = pd.DataFrame(q1)
    if len(q1df) > 0:
        reject, p_adj, _, _ = multipletests(q1df.p_raw.values, method="fdr_bh")
        q1df["p_fdr"] = np.round(p_adj, 6)
        q1df["significant_fdr"] = reject
    earliest = (q1df[q1df.significant_fdr].sort_values("horizon_d")
                .groupby("coordinate").first().reset_index()
                if len(q1df) > 0 and q1df.significant_fdr.any() else pd.DataFrame())
    for _, er in earliest.iterrows():
        rows.append({"question": "Q1_first_change", "coordinate": er.coordinate,
                     "statistic": "earliest_sig_horizon", "value": int(er.horizon_d),
                     "n": int(er.n_suc + er.n_fail), "p_fdr": float(er.p_fdr)})

    # Q2: univariate AUC per coordinate at t0 and +1D
    for name, col in BREADTH_COORDS.items():
        if col not in df.columns:
            continue
        for h in [0, 1]:
            vals, ys = [], []
            for _, r in prim.iterrows():
                i = date_idx.get(pd.Timestamp(r.exit_date))
                if i is None:
                    continue
                j = i + h
                if 0 <= j < len(df):
                    v = df[col].iloc[j]
                    if v == v:
                        vals.append(float(v)); ys.append(int(r.is_success))
            if len(set(ys)) >= 2 and len(vals) >= 10:
                auc = _auc_safe(ys, vals)
                rows.append({"question": "Q2_best_discriminator", "coordinate": name,
                             "statistic": f"auc_tp{h}", "value": round(auc, 4),
                             "n": len(vals), "p_fdr": np.nan})

    # Q3: expansion sufficiency vs expansion+rank-recruitment
    def _mask(cond_cols, cond_vals, h=0):
        m = pd.Series(True, index=prim.index)
        for c, v in zip(cond_cols, cond_vals):
            m &= prim[c] == v
        return m

    for h in [0, 1]:
        bre = pd.Series(False, index=prim.index)
        for _, r in prim.iterrows():
            i = date_idx.get(pd.Timestamp(r.exit_date))
            if i is None:
                continue
            j = i + h
            if 0 <= j < len(df):
                bre.at[r.name] = bool(df["BREADTH_EXPANDING"].iloc[j]) and \
                    df["breadth_axis"].iloc[j] == "BREADTH_EXPANDING"
        n1 = int(bre.sum()); s1 = int((prim.is_success & bre).sum())
        if n1 >= 10:
            p1 = s1 / n1
            table = [[s1, n1 - s1], [int(prim.is_success.sum()), int((prim.is_success == 0).sum())]]
            _, pf1 = fisher_exact(table)
            rows.append({"question": "Q3_sufficiency", "coordinate": "breadth_expanding",
                         "statistic": f"p_success_tp{h}", "value": round(p1, 4),
                         "n": n1, "p_fdr": round(float(pf1), 6)})
        # expansion AND rank recruiting
        both = pd.Series(False, index=prim.index)
        for _, r in prim.iterrows():
            i = date_idx.get(pd.Timestamp(r.exit_date))
            if i is None:
                continue
            j = i + h
            if 0 <= j < len(df):
                both.at[r.name] = (df["breadth_axis"].iloc[j] == "BREADTH_EXPANDING" and
                                   df["rank_axis"].iloc[j] == "RANK_RECRUITING")
        n2 = int(both.sum()); s2 = int((prim.is_success & both).sum())
        if n2 >= 5:
            p2 = s2 / n2
            rows.append({"question": "Q3_sufficiency", "coordinate": "expand_and_rank_recruit",
                         "statistic": f"p_success_tp{h}", "value": round(p2, 4),
                         "n": n2, "p_fdr": np.nan})

    # Q4: stall before failed propagation — median coordinate path failures vs successes
    for name, col in [("breadth_vel", "breadth_vel"), ("breadth_accel", "breadth_accel")]:
        for h in [0, 1, 2, 3, 5, 7]:
            suc, fail = [], []
            for _, r in prim.iterrows():
                i = date_idx.get(pd.Timestamp(r.exit_date))
                if i is None:
                    continue
                j = i + h
                if 0 <= j < len(df):
                    v = df[col].iloc[j]
                    if v == v:
                        (suc if r.is_success else fail).append(float(v))
            if len(suc) >= 5 and len(fail) >= 5:
                rows.append({"question": "Q4_stall_before_failure", "coordinate": name,
                             "statistic": f"median_tp{h}", "value": round(float(np.median(fail)), 5),
                             "n": len(fail), "p_fdr": np.nan})
                rows.append({"question": "Q4_stall_before_failure", "coordinate": name,
                             "statistic": f"median_success_tp{h}",
                             "value": round(float(np.median(suc)), 5), "n": len(suc), "p_fdr": np.nan})

    # Q5: acceleration beyond level — nested logistic, chronological 70/30 split
    feat_sets = [("level", ["top500_breadth_30d"]),
                 ("level+vel", ["top500_breadth_30d", "breadth_vel"]),
                 ("level+vel+accel", ["top500_breadth_30d", "breadth_vel", "breadth_accel"])]
    rows_ev = []
    for _, r in prim.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        row = {"event_id": r.event_id, "is_success": int(r.is_success),
               "order": i}
        for f in ["top500_breadth_30d", "breadth_vel", "breadth_accel"]:
            v = df[f].iloc[i]
            row[f] = float(v) if v == v else np.nan
        rows_ev.append(row)
    ev_df = pd.DataFrame(rows_ev).dropna()
    if len(ev_df) >= 40 and len(set(ev_df.is_success)) >= 2:
        ev_df = ev_df.sort_values("order").reset_index(drop=True)
        n_tr = int(len(ev_df) * 0.7)
        tr, te = ev_df.iloc[:n_tr], ev_df.iloc[n_tr:]
        if len(set(tr.is_success)) >= 2 and len(set(te.is_success)) >= 2:
            prev = None
            for name, fs in feat_sets:
                if any(f not in ev_df.columns for f in fs):
                    continue
                m = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
                m.fit(tr[fs], tr.is_success)
                p_te = m.predict_proba(te[fs])[:, 1]
                auc = _auc_safe(te.is_success, p_te)
                ll = _logloss_safe(te.is_success, p_te)
                # permutation null on test labels
                rng = np.random.RandomState(SEED)
                perm_lls = []
                for _ in range(PERM_N):
                    yp = rng.permutation(te.is_success.values)
                    mm = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
                    mm.fit(tr[fs], tr.is_success)
                    pp = mm.predict_proba(te[fs])[:, 1]
                    perm_lls.append(_logloss_safe(yp, pp))
                perm_p = (np.sum(np.array(perm_lls) <= ll) + 1) / (PERM_N + 1)
                dll = (prev[0] - ll) if prev else np.nan
                rows.append({"question": "Q5_accel_beyond_level", "coordinate": name,
                             "statistic": "test_auc", "value": round(auc, 4),
                             "n": len(te), "p_fdr": round(perm_p, 4)})
                rows.append({"question": "Q5_accel_beyond_level", "coordinate": name,
                             "statistic": "test_logloss", "value": round(ll, 5),
                             "n": len(te), "p_fdr": np.nan})
                rows.append({"question": "Q5_accel_beyond_level", "coordinate": name,
                             "statistic": "delta_logloss_vs_prev", "value": round(dll, 5),
                             "n": len(te), "p_fdr": np.nan})
                prev = (ll, name)

    # Q6: late breadth decay in successes — maturation vs failure
    succ = ledger[ledger.first_destination.isin(SUCCESS_LABELS)].copy()
    q6 = []
    for _, r in succ.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        ttd = r.days_to_destination_d
        if ttd != ttd or ttd < 3:
            continue
        j_conf = i + 3
        j_end = i + int(ttd)
        j_after = min(j_end + 5, len(df) - 1)
        if 0 <= j_conf < len(df) and 0 <= j_end < len(df):
            b_conf = df["top500_breadth_30d"].iloc[j_conf]
            b_end = df["top500_breadth_30d"].iloc[j_end]
            b_after = df["top500_breadth_30d"].iloc[j_after]
            if b_conf == b_conf and b_end == b_end and b_after == b_after:
                q6.append({"event_id": r.event_id,
                           "breadth_chg_to_end": float(b_end - b_conf),
                           "breadth_chg_after_end": float(b_after - b_end),
                           "end_state": r.first_destination})
    q6df = pd.DataFrame(q6)
    if len(q6df) > 0:
        rows.append({"question": "Q6_late_decay", "coordinate": "breadth30",
                     "statistic": "median_chg_conf_to_end",
                     "value": round(float(q6df.breadth_chg_to_end.median()), 4),
                     "n": len(q6df), "p_fdr": np.nan})
        rows.append({"question": "Q6_late_decay", "coordinate": "breadth30",
                     "statistic": "median_chg_end_to_end5",
                     "value": round(float(q6df.breadth_chg_after_end.median()), 4),
                     "n": len(q6df), "p_fdr": np.nan})

    # Q7: per-class breadth signatures (median path t0..+14D)
    classes = {"EARLY_SNAPBACK": None, "BREADTH_FADE": None, "MIXED": None, "SUCCESS": None}
    for cls in classes:
        if cls == "SUCCESS":
            sub = ledger[ledger.first_destination.isin(SUCCESS_LABELS)]
        elif cls == "MIXED":
            sub = ledger[ledger.first_destination == "MIXED_NO_CLEAR_ROUTE"]
        else:
            sub = ledger[ledger.event_id.map(motif_map) == cls]
        for h in [0, 1, 3, 7, 14]:
            vals = []
            for _, r in sub.iterrows():
                i = date_idx.get(pd.Timestamp(r.exit_date))
                if i is None:
                    continue
                j = i + h
                if 0 <= j < len(df):
                    v = df["top500_breadth_30d"].iloc[j]
                    if v == v:
                        vals.append(float(v))
            if len(vals) >= 3:
                rows.append({"question": "Q7_class_signature", "coordinate": cls,
                             "statistic": f"median_breadth_tp{h}",
                             "value": round(float(np.median(vals)), 4), "n": len(vals),
                             "p_fdr": np.nan})
    lattice = pd.DataFrame(rows)
    lattice.to_csv(OUT / "08_BREADTH_TRANSMISSION_LATTICE.csv", index=False)

    # 09_BREADTH_SEQUENCE_ANALYSIS.csv — per-event breadth sequence over horizons
    bseq_rows = []
    for _, r in prim.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        row = {"event_id": r.event_id, "is_success": int(r.is_success),
               "first_destination": r.first_destination}
        for h in HORIZONS:
            j = i + h
            if 0 <= j < len(df):
                row[f"axis_tp{h}"] = df["breadth_axis"].iloc[j]
                row[f"breadth_tp{h}"] = round(float(df["top500_breadth_30d"].iloc[j]), 5)
                row[f"vel_tp{h}"] = round(float(df["breadth_vel"].iloc[j]), 5)
                row[f"rank_axis_tp{h}"] = df["rank_axis"].iloc[j]
            else:
                row[f"axis_tp{h}"] = np.nan
                row[f"breadth_tp{h}"] = np.nan
                row[f"vel_tp{h}"] = np.nan
                row[f"rank_axis_tp{h}"] = np.nan
        bseq_rows.append(row)
    pd.DataFrame(bseq_rows).to_csv(OUT / "09_BREADTH_SEQUENCE_ANALYSIS.csv", index=False)
    return {"lattice": lattice, "q1_earliest": earliest}


# =========================================================================
# WS4: FAILURE MOTIF REFINEMENT (EARLY_SNAPBACK / BREADTH_FADE)
# =========================================================================

def ws4_motifs(df, ledger, motif_map):
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(df.historical_date.values)}
    es = ledger[ledger.event_id.map(motif_map) == "EARLY_SNAPBACK"].copy()
    bf = ledger[ledger.event_id.map(motif_map) == "BREADTH_FADE"].copy()
    mrows = []

    # --- EARLY_SNAPBACK profile ---
    es_rows = []
    for _, r in es.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        ttd = r.days_to_destination_d
        row = {"event_id": r.event_id, "days_to_reentry": ttd,
               "subperiod": r.subperiod,
               "btc_up": int(r.BTC_UP), "vol_high": int(r.VOL_HIGH),
               "breadth_at_release": float(df["top500_breadth_30d"].iloc[i]),
               "disp_at_release": float(df["top500_dispersion_30d"].iloc[i]),
               "rank_recruit": int(df["rank_axis"].iloc[i] == "RANK_RECRUITING"),
               "rank_deteriorate": int(df["rank_axis"].iloc[i] == "RANK_DETERIORATING")}
        # concentration rebuild speed: top3_share_chg7 at +1..+3D
        for h in [1, 2, 3]:
            j = i + h
            if 0 <= j < len(df):
                row[f"top3_chg7_tp{h}"] = round(float(df["top3_share_chg7"].iloc[j]), 5)
            else:
                row[f"top3_chg7_tp{h}"] = np.nan
        # retracement depth from first-move data
        es_rows.append(row)
    es_df = pd.DataFrame(es_rows)
    # subfamily test: rebuild speed by BTC_UP/DOWN and by breadth level
    if len(es_df) >= 10:
        for cond_col, cond_name in [("btc_up", "BTC_UP"), ("vol_high", "VOL_HIGH")]:
            g1 = es_df[es_df[cond_col] == 1]
            g0 = es_df[es_df[cond_col] == 0]
            if len(g1) >= 3 and len(g0) >= 3:
                for h in [1, 3]:
                    a = g1[f"top3_chg7_tp{h}"].dropna()
                    b = g0[f"top3_chg7_tp{h}"].dropna()
                    if len(a) >= 3 and len(b) >= 3:
                        stat, p = ranksums(a, b)
                        mrows.append({"motif": "EARLY_SNAPBACK", "subfamily": cond_name,
                                      "statistic": f"rebuild_speed_tp{h}",
                                      "median_yes": round(float(a.median()), 5),
                                      "median_no": round(float(b.median()), 5),
                                      "n_yes": len(a), "n_no": len(b),
                                      "p_raw": round(float(p), 6)})
    es_df.to_csv(OUT / "10_EARLY_SNAPBACK_REFINEMENT.csv", index=False)

    # --- BREADTH_FADE profile ---
    bf_rows = []
    for _, r in bf.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        ttd = r.days_to_destination_d
        b0 = float(df["top500_breadth_30d"].iloc[i])
        # time-to-peak within 14D
        peak_h, peak_v = 0, b0
        for h in range(1, 15):
            j = i + h
            if j < len(df):
                v = df["top500_breadth_30d"].iloc[j]
                if v == v and v > peak_v:
                    peak_v = v; peak_h = h
        jpk = i + peak_h
        jpk5 = min(jpk + 5, len(df) - 1)
        decay_speed = (df["top500_breadth_30d"].iloc[jpk5] - peak_v) if jpk5 != jpk else np.nan
        # price during fade: mean mkt_ret_1d from peak to peak+7
        pr = []
        for h in range(0, 8):
            j = jpk + h
            if j < len(df):
                v = df["mkt_ret_1d"].iloc[j]
                if v == v:
                    pr.append(float(v))
        rank_chg = None
        jpk7 = min(jpk + 7, len(df) - 1)
        v0 = df["med_ret30_51_200"].iloc[jpk]
        v1 = df["med_ret30_51_200"].iloc[jpk7]
        if v0 == v0 and v1 == v1:
            rank_chg = float(v1 - v0)
        conc_resp = float(df["top3_share_chg7"].iloc[jpk]) if jpk < len(df) else np.nan
        bf_rows.append({
            "event_id": r.event_id, "days_to_destination": ttd,
            "subperiod": r.subperiod, "breadth_at_release": b0,
            "time_to_peak_d": peak_h, "peak_breadth": round(peak_v, 4),
            "decay_speed_5d": round(float(decay_speed), 5) if decay_speed == decay_speed else np.nan,
            "mean_mkt_ret_during_fade": round(float(np.mean(pr)), 5) if pr else np.nan,
            "rank_51_200_chg7_after_peak": round(float(rank_chg), 5) if rank_chg is not None else np.nan,
            "conc_chg7_at_peak": round(float(conc_resp), 5) if conc_resp == conc_resp else np.nan,
            "fade_before_route_failure": int(peak_h < ttd) if ttd == ttd else np.nan,
        })
    bf_df = pd.DataFrame(bf_rows)
    bf_df.to_csv(OUT / "11_BREADTH_FADE_REFINEMENT.csv", index=False)

    # FDR over motif subfamily tests
    mdf = pd.DataFrame(mrows)
    if len(mdf) > 0:
        reject, p_adj, _, _ = multipletests(mdf.p_raw.values, method="fdr_bh")
        mdf["p_fdr"] = np.round(p_adj, 6)
        mdf["significant_fdr"] = reject
    return {"early_snapback": es_df, "breadth_fade": bf_df, "subfamily_tests": mdf}


# =========================================================================
# WS5: TWO-CLOCK PROSPECTIVE COMPETING-RISK
# =========================================================================

def ws5_competing_risk(df, ledger):
    led = ledger.copy()
    led["cause"] = led.first_destination.map(
        lambda d: "PROPAGATION" if d in SUCCESS_LABELS else
                  "REENTRY" if d == REENTRY_LABEL else
                  "MIXED" if d == "MIXED_NO_CLEAR_ROUTE" else "OTHER")
    horizons = list(range(1, 31))
    causes = ["REENTRY", "MIXED", "PROPAGATION", "OTHER"]
    rows = []
    n_at_risk = len(led)
    resolved_any = np.zeros(len(led), dtype=bool)
    for h in horizons:
        resolved_now = (~resolved_any) & (led.days_to_destination_d.fillna(999) <= h) & \
                       (led.days_to_destination_d.fillna(999) >= h)
        at_risk_h = int((~resolved_any).sum())
        for c in causes:
            n_c = int((resolved_now & (led.cause == c)).sum())
            rows.append({"horizon_d": h, "cause": c, "n_at_risk": at_risk_h,
                         "n_resolved": n_c,
                         "hazard": round(n_c / max(at_risk_h, 1), 4)})
        resolved_any = resolved_any | resolved_now
    haz = pd.DataFrame(rows)
    haz.to_csv(OUT / "12_COMPETING_RISK_HAZARDS.csv", index=False)

    # cumulative incidence (KM-style): C_k(h) = sum over u<=h of S(u-1)*h_k(u)
    cif_rows = []
    surv = 1.0
    cif = {c: 0.0 for c in causes}
    for h in horizons:
        sub = haz[haz.horizon_d == h]
        h_all = 0.0
        for c in causes:
            hc = sub.loc[sub.cause == c, "hazard"].iloc[0]
            cif[c] += surv * hc
            h_all += hc
        surv *= (1 - h_all)
        for c in causes:
            cif_rows.append({"horizon_d": h, "cause": c,
                             "cumulative_incidence": round(cif[c], 4),
                             "survival": round(surv, 4)})
    cif_df = pd.DataFrame(cif_rows)
    cif_df.to_csv(OUT / "13_CUMULATIVE_INCIDENCE.csv", index=False)

    # state-conditioned hazards: split by release-day regime flags + rank tercile
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(df["historical_date"].values)}
    cond_cols = ["BTC_UP", "VOL_HIGH", "BREADTH_EXPANDING", "ETH_STRONG",
                 "RISK_ON", "CONC_RISING"]
    rank_t = []
    for _, r in led.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        rank_t.append(float(df["med_ret30_201_500"].iloc[i]) if i is not None and
                      df["med_ret30_201_500"].iloc[i] == df["med_ret30_201_500"].iloc[i]
                      else np.nan)
    led["rank_recruit_t"] = pd.Series(rank_t, index=led.index)
    med_r = led.rank_recruit_t.median()
    led["rank_recruit_hi"] = (led.rank_recruit_t > med_r).astype(int)
    led["rank_recruit_lo"] = (led.rank_recruit_t <= med_r).astype(int)

    cond_rows = []
    bands = [(1, 3), (4, 7), (8, 14), (15, 30)]
    for cond in cond_cols + ["rank_recruit_hi", "rank_recruit_lo"]:
        yes = led[led[cond] == 1]
        if len(yes) < 10:
            continue
        for (lo, hi) in bands:
            for c in causes:
                n_yes = len(yes)
                n_c = int(((yes.days_to_destination_d.fillna(999) <= hi) &
                            (yes.days_to_destination_d.fillna(999) > lo) &
                            (yes.cause == c)).sum())
                cond_rows.append({"condition": cond, "window_d": f"{lo}-{hi}",
                                  "cause": c, "n": n_yes,
                                  "p_cause_by_window": round(n_c / max(n_yes, 1), 4)})
    cond_df = pd.DataFrame(cond_rows)
    cond_df.to_csv(OUT / "14_STATE_CONDITIONED_HAZARDS.csv", index=False)
    return {"hazards": haz, "cif": cif_df, "conditioned": cond_df,
            "final_cif": {c: round(cif[c], 4) for c in causes}}
# =========================================================================
# WS6: LOCAL TERMINATION / DECAY MICROSEQUENCES
# =========================================================================

TERM_DECLINE_COLS = {
    "BREADTH": "top500_breadth_30d_first_decline_days_before_term",
    "BREADTH7": "top500_breadth_7d_first_decline_days_before_term",
    "DISPERSION": "top500_dispersion_30d_first_decline_days_before_term",
    "VOL": "vol_med_first_decline_days_before_term",
    "CONC": "top3_share_chg7_first_decline_days_before_term",
    "ETH": "eth_btc_relative_return_7d_first_decline_days_before_term",
    "BTC": "btc_return_7d_first_decline_days_before_term",
    "RANK": "med_ret30_51_200_first_decline_days_before_term",
}


def ws6_termination(term5):
    """Termination signature: which coordinate declines first before end."""
    rows = []
    for _, r in term5.iterrows():
        declines = {}
        for name, col in TERM_DECLINE_COLS.items():
            v = r.get(col)
            if v == v and v is not None:
                declines[name] = float(v)
        if not declines:
            sig = "ABRUPT"
            first = np.nan
        else:
            first_name = max(declines, key=declines.get)
            first = declines[first_name]
            if first_name in ("BREADTH", "BREADTH7"):
                sig = "BREADTH_FIRST"
            elif first_name == "VOL":
                sig = "VOL_FIRST"
            elif first_name == "CONC":
                sig = "CONC_REBUILD_FIRST"
            elif first_name == "ETH":
                sig = "ETH_FIRST"
            elif first_name == "BTC":
                sig = "BTC_FIRST"
            elif first_name == "RANK":
                sig = "RANK_FIRST"
            elif first_name == "DISPERSION":
                sig = "DISP_FIRST"
            else:
                sig = "OTHER_FIRST"
        rows.append({
            "event_id": r.event_id, "first_destination": r.first_destination,
            "days_to_destination_d": r.days_to_destination,
            "termination_signature": sig,
            "first_decline_days_before_term": round(float(first), 1) if first == first else np.nan,
            "n_confirming_coordinates": len(declines),
            "decline_order": " > ".join(
                [n for n, _ in sorted(declines.items(), key=lambda kv: -kv[1])]) or "NONE",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "15_TERMINATION_MICROSEQUENCES.csv", index=False)
    counts = out.termination_signature.value_counts().reset_index()
    counts.columns = ["signature", "count"]
    counts["pct"] = round(counts["count"] / max(len(out), 1), 3)
    return {"panel": out, "counts": counts}


# =========================================================================
# WS7: CONDITIONAL LOCAL RULE AUDIT
# =========================================================================

def ws7_conditional(ev_seq, atlas, ledger):
    """Occurrence-dependence of near-promoted sequences on condition axes."""
    cond_flags = ["BTC_UP", "VOL_HIGH", "BREADTH_EXPANDING", "ETH_STRONG",
                  "RISK_ON", "CONC_RISING"]
    flag_map = {c: dict(zip(ledger.event_id, ledger[c].astype(int))) for c in cond_flags}
    sub_map = dict(zip(ledger.event_id, ledger.subperiod))
    ev = ev_seq.copy()
    ev["subperiod"] = ev.event_id.map(sub_map)
    rows = []
    cand = ev.groupby(["axis", "lattice", "seq"]).size().reset_index(name="n")
    cand = cand[cand.n >= 10]
    for _, cr in cand.iterrows():
        axis, lattice, seq = cr.axis, cr.lattice, cr.seq
        sub = ev[(ev.axis == axis) & (ev.lattice == lattice)]
        n_events = len(sub.event_id.unique())
        seq_ids = set(sub[sub.seq == seq].event_id.unique())
        for cond in cond_flags:
            fm = flag_map[cond]
            has_cond = sub.event_id.map(fm).fillna(0).astype(int)
            has_seq = sub.event_id.isin(seq_ids).astype(int)
            # contingency on unique events
            u = sub.drop_duplicates("event_id")
            hs = u.event_id.isin(seq_ids).astype(int)
            hc = u.event_id.map(fm).fillna(0).astype(int)
            table = [[int((hs == 1).sum()), int(((hs == 0) & (hc == 1)).sum())],
                     [int(((hs == 1) & (hc == 0)).sum()), int(((hs == 0) & (hc == 0)).sum())]]
            if min(np.array(table).sum(axis=1)) == 0:
                continue
            try:
                _, p, _, _ = chi2_contingency(table)
            except ValueError:
                continue
            rows.append({"axis": axis, "lattice": lattice, "seq": seq,
                         "n_events": n_events, "n_seq_events": len(seq_ids),
                         "condition": cond, "p_raw": round(float(p), 6)})
        # subperiod dependence
        u = sub.drop_duplicates("event_id")
        hs = u.event_id.isin(seq_ids).astype(int)
        sp_arr = u.subperiod.values
        table = pd.crosstab(hs, sp_arr)
        if table.shape == (2, len(SUBPERIODS)) and (table.sum().values > 0).all():
            try:
                _, p, _, _ = chi2_contingency(table.values)
                rows.append({"axis": axis, "lattice": lattice, "seq": seq,
                             "n_events": n_events, "n_seq_events": len(seq_ids),
                             "condition": "SUBPERIOD", "p_raw": round(float(p), 6)})
            except ValueError:
                pass
    audit = pd.DataFrame(rows)
    if len(audit) > 0:
        reject, p_adj, _, _ = multipletests(audit.p_raw.values, method="fdr_bh")
        audit["p_fdr"] = np.round(p_adj, 6)
        audit["significant_fdr"] = reject
    audit.to_csv(OUT / "16_CONDITIONAL_LOCAL_RULE_AUDIT.csv", index=False)
    # classify candidate sequences
    cls_rows = []
    for (axis, lattice, seq), grp in audit.groupby(["axis", "lattice", "seq"]):
        n = int(grp.n_events.iloc[0])
        sig = grp[grp.significant_fdr] if "significant_fdr" in grp.columns else grp.iloc[0:0]
        cond_sig = sig[sig.condition != "SUBPERIOD"]
        sp_sig = sig[sig.condition == "SUBPERIOD"]
        if len(cond_sig) > 0:
            cls = "CONDITION_DEPENDENT"
        elif len(sp_sig) > 0:
            cls = "CYCLE_LOCAL"
        else:
            cls = "GLOBAL"
        cls_rows.append({"axis": axis, "lattice": lattice, "seq": seq,
                         "n_events": n, "classification": cls,
                         "n_cond_sig": len(cond_sig), "n_subperiod_sig": len(sp_sig)})
    cls_df = pd.DataFrame(cls_rows)
    return {"audit": audit, "classification": cls_df}


# =========================================================================
# WS8: ALPHA-ROLE REGISTRY (research preparation ONLY)
# =========================================================================

def ws8_roles(w1, w2, w3, w4, w5, w6):
    rows = [
        {"statistic": "BREADTH_EXPANDING regime",
         "family": "breadth", "roles": "TRANSITION_GATE;STRUCTURAL_STATE",
         "evidence_level": "L2_CONDITIONAL_LEAD_LAG", "sample_size": "715/2196 days",
         "conditionality": "GLOBAL", "known_nulls": "acceleration adds little beyond level (WS3 Q5)",
         "data_limits": "Top-500 universe only", "causal_level": "L2",
         "potential_redundancies": "breadth30 level/velocity partially overlap", "status": "EARNED"},
        {"statistic": "RANK_RECRUITMENT (deeper bands)",
         "family": "rank participation", "roles": "PROPAGATION_DEPTH;CONFIRMATION",
         "evidence_level": "L1_TEMPORAL_ORDERING", "sample_size": "MECH-5 WS2 +0.028 AUC",
         "conditionality": "GLOBAL", "known_nulls": "occurs after breadth gate",
         "data_limits": "Top-500 only", "causal_level": "L2",
         "potential_redundancies": "med_ret30_201_500 vs 51_200 correlated", "status": "EARNED"},
        {"statistic": "BTC 30D return at release",
         "family": "backdrop", "roles": "RISK_CONTEXT;REGIME_FILTER",
         "evidence_level": "L1_TEMPORAL_ORDERING", "sample_size": "MECH-5 r=0.51 +0D",
         "conditionality": "GLOBAL", "known_nulls": "not a gate alone",
         "data_limits": "none", "causal_level": "L1",
         "potential_redundancies": "partly in RISK_ON/OFF", "status": "EARNED"},
        {"statistic": "EARLY_SNAPBACK motif",
         "family": "failure", "roles": "FAILURE_FILTER;TEMPORAL_DELIVERY",
         "evidence_level": "L0_DESCRIPTIVE", "sample_size": "28 events",
         "conditionality": "n<50, no promoted subfamily", "known_nulls": "no stable subfamily",
         "data_limits": "small n", "causal_level": "L0",
         "potential_redundancies": "overlaps REENTRY label", "status": "LOCAL_NODE"},
        {"statistic": "BREADTH_FADE motif",
         "family": "failure", "roles": "FAILURE_FILTER;DECAY_TERMINATION",
         "evidence_level": "L0_DESCRIPTIVE", "sample_size": "23 events",
         "conditionality": "n<50", "known_nulls": "no stable subfamily",
         "data_limits": "small n", "causal_level": "L0",
         "potential_redundancies": "overlaps MIXED label", "status": "LOCAL_NODE"},
        {"statistic": "Two-clock: escape fast / propagation slow",
         "family": "temporal", "roles": "TEMPORAL_DELIVERY;TRANSITION_GATE",
         "evidence_level": "L1_TEMPORAL_ORDERING", "sample_size": "125 events prospective",
         "conditionality": "GLOBAL", "known_nulls": "no narrow window substitutes lattice",
         "data_limits": "30D horizon", "causal_level": "L1",
         "potential_redundancies": "none", "status": "EARNED"},
        {"statistic": "Competing-risk CIF: reentry > propagation early",
         "family": "temporal", "roles": "FAILURE_FILTER;TEMPORAL_DELIVERY",
         "evidence_level": "L1_TEMPORAL_ORDERING", "sample_size": "125 events",
         "conditionality": "state-conditioned hazards in 14_STATE_CONDITIONED_HAZARDS",
         "known_nulls": "TBD", "data_limits": "30D horizon", "causal_level": "L1",
         "potential_redundancies": "overlaps escape hazard", "status": "EARNED"},
        {"statistic": "Breadth transmission stage order (level -> depth)",
         "family": "breadth", "roles": "PROPAGATION_DEPTH;TRANSITION_GATE",
         "evidence_level": "L2_CONDITIONAL_LEAD_LAG", "sample_size": "123 primary events",
         "conditionality": "Q3 expansion+rank vs expansion alone",
         "known_nulls": "accel not incremental", "data_limits": "Top-500",
         "causal_level": "L2", "potential_redundancies": "depth_chg vs breadth_vel",
         "status": "EARNED_PARTIAL"},
    ]
    n_seq = w2.get("n_promoted", 0)
    rows.append({"statistic": "Micro-state sequences (WS2)",
                 "family": "sequence", "roles": "LOCAL_CLUSTER;UNKNOWN",
                 "evidence_level": "L0_DESCRIPTIVE", "sample_size": f"{n_seq} promoted / 125 events",
                 "conditionality": "see 16_CONDITIONAL_LOCAL_RULE_AUDIT",
                 "known_nulls": "most sequences LOW_SAMPLE",
                 "data_limits": "event-horizon lattice", "causal_level": "L0",
                 "potential_redundancies": "persistence trivially re-stated", "status": "ATLAS"})
    reg = pd.DataFrame(rows)
    reg.to_csv(OUT / "17_ALPHA_ROLE_REGISTRY.csv", index=False)
    return {"registry": reg}


# =========================================================================
# WS9: NODE GRAPH UPDATE
# =========================================================================

def ws9_nodes(w1, w2, w3, w4, w5, w6, w7):
    base = []
    m5_nodes = M5_OUT / "19_NEW_NODE_MERGE_DISSOLVE.csv"
    if m5_nodes.exists():
        try:
            base = pd.read_csv(m5_nodes).to_dict("records")
        except Exception:
            base = []
    nodes = []
    for b in base:
        nodes.append({"node_id": str(b.get("node", b.get("node_id", "UNKNOWN"))),
                      "node_type": "TERRAIN", "local_global": "LOCAL" if "LOCAL" in str(b.get("strength", "")) else "GLOBAL",
                      "condition": "", "parent_state": "", "child_state": "",
                      "median_latency_d": np.nan, "n_effective": np.nan,
                      "effect_size": str(b.get("strength", "")), "confidence": "",
                      "causal_level": str(b.get("causality_level", "L0")),
                      "alpha_role": "", "status": str(b.get("operation", "DESCRIPTIVE_ONLY")),
                      "source": str(b.get("source", "MECH-5"))})
    # MECH-6 nodes
    for _, srow in w2["atlas"].iterrows():
        if srow.classification in ("LOCAL_SEQUENCE", "GLOBAL_SEQUENCE", "CONDITIONAL_SEQUENCE"):
            nodes.append({"node_id": srow.seq_id, "node_type": "SEQUENCE",
                          "local_global": "LOCAL" if srow.classification == "LOCAL_SEQUENCE" else "GLOBAL",
                          "condition": "", "parent_state": srow.seq.split("->")[0],
                          "child_state": srow.seq.split("->")[-1],
                          "median_latency_d": np.nan, "n_effective": int(srow.n_effective),
                          "effect_size": f"lift={srow.lift}", "confidence": f"q={srow.p_fdr}",
                          "causal_level": "L0", "alpha_role": "LOCAL_CLUSTER;UNKNOWN",
                          "status": srow.classification, "source": "MECH-6-WS2"})
    if len(w3.get("q1_earliest", pd.DataFrame())) > 0:
        for _, er in w3["q1_earliest"].iterrows():
            nodes.append({"node_id": f"BREADTH_DIVERGENCE_{er.coordinate}",
                          "node_type": "BREADTH", "local_global": "GLOBAL",
                          "condition": "", "parent_state": "", "child_state": "",
                          "median_latency_d": float(er.horizon_d),
                          "n_effective": int(er.n_suc + er.n_fail),
                          "effect_size": f"r={er.r_eff}", "confidence": f"q={er.p_fdr}",
                          "causal_level": "L1", "alpha_role": "TRANSITION_GATE",
                          "status": "NEW_NODE", "source": "MECH-6-WS3"})
    for _, wrow in w6["counts"].iterrows():
        nodes.append({"node_id": f"TERMINATION_{wrow.signature}",
                      "node_type": "TERMINATION", "local_global": "LOCAL",
                      "condition": "", "parent_state": "PROPAGATION",
                      "child_state": "END", "median_latency_d": np.nan,
                      "n_effective": int(wrow["count"]),
                      "effect_size": f"{wrow.pct:.0%}", "confidence": "",
                      "causal_level": "L0", "alpha_role": "DECAY_TERMINATION",
                      "status": "DESCRIPTIVE_ONLY", "source": "MECH-6-WS6"})
    node_df = pd.DataFrame(nodes)

    edges = []
    # canonical edges from MECH-4/5 (documented, non-causal where unproven)
    edges += [
        {"edge_id": "E1", "from": "BTC_CONCENTRATION", "to": "RELEASE", "edge_type": "PRECEDES",
         "median_latency_d": np.nan, "n_effective": 125, "causal_level": "L1", "status": "EARNED"},
        {"edge_id": "E2", "from": "RELEASE", "to": "REENTRY", "edge_type": "REENTERS",
         "median_latency_d": 2.0, "n_effective": 52, "causal_level": "L1", "status": "EARNED"},
        {"edge_id": "E3", "from": "RELEASE", "to": "MIXED", "edge_type": "FOLLOWS",
         "median_latency_d": 4.0, "n_effective": 44, "causal_level": "L1", "status": "EARNED"},
        {"edge_id": "E4", "from": "RELEASE", "to": "BROAD_RISK_EXPANSION", "edge_type": "FOLLOWS",
         "median_latency_d": 7.0, "n_effective": 18, "causal_level": "L1", "status": "EARNED"},
        {"edge_id": "E5", "from": "BROAD_RISK_EXPANSION", "to": "ALT_FAMILY", "edge_type": "RECRUITS_DEPTH",
         "median_latency_d": np.nan, "n_effective": 9, "causal_level": "L0", "status": "DESCRIPTIVE_ONLY"},
        {"edge_id": "E6", "from": "BREADTH_EXPANSION", "to": "RANK_RECRUITMENT", "edge_type": "GATES",
         "median_latency_d": 3.0, "n_effective": 123, "causal_level": "L2", "status": "EARNED_PARTIAL"},
        {"edge_id": "E7", "from": "RANK_RECRUITMENT", "to": "SUSTAINED_PROPAGATION", "edge_type": "RECRUITS_DEPTH",
         "median_latency_d": np.nan, "n_effective": 27, "causal_level": "L1", "status": "EARNED_PARTIAL"},
        {"edge_id": "E8", "from": "BTC_30D_SUPPORT", "to": "BREADTH_EXPANSION", "edge_type": "CONDITIONS",
         "median_latency_d": 0.0, "n_effective": 123, "causal_level": "L1", "status": "EARNED"},
        {"edge_id": "E9", "from": "BREADTH_FADE", "to": "REENTRY", "edge_type": "TERMINATES",
         "median_latency_d": np.nan, "n_effective": 23, "causal_level": "L0", "status": "LOCAL_NODE"},
        {"edge_id": "E10", "from": "PROPAGATION", "to": "TERMINATION", "edge_type": "TERMINATES",
         "median_latency_d": np.nan, "n_effective": 27, "causal_level": "L0", "status": "DESCRIPTIVE_ONLY"},
    ]
    edge_df = pd.DataFrame(edges)
    node_df.to_csv(OUT / "18_NODE_EDGE_UPDATE.csv", index=False)
    return {"nodes": node_df, "edges": edge_df}


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("=" * 72)
    print("ALT_MECH_6 :: MICRO-STATE SEQUENCE ATLAS / BREADTH TRANSMISSION / LOCAL MOTIFS")
    print("=" * 72)
    OUT.mkdir(parents=True, exist_ok=True)
    daily, ledger, entries, exits, m, top, bm, X, feat_df, motif_map, fm_map, term5 = load_data()
    print(f"[data] daily={daily.shape}, ledger={len(ledger)}")
    df = _cache_step("atoms", lambda: compute_atoms(daily, bm))
    r1 = _cache_step("WS1", lambda: ws1_atlas(df, ledger))
    print(f"[WS1] atlas panel: {len(r1['panel'])} rows")
    r2 = _cache_step("WS2", lambda: ws2_sequences(r1["panel"], df, ledger))
    print(f"[WS2] event seqs={len(r2['event_sequences'])}, panel paths={len(r2['panel_paths'])}, promoted={r2['n_promoted']}")
    r3 = _cache_step("WS3", lambda: ws3_breadth(df, ledger, motif_map))
    print(f"[WS3] lattice rows: {len(r3['lattice'])}")
    r4 = _cache_step("WS4", lambda: ws4_motifs(df, ledger, motif_map))
    print(f"[WS4] ES={len(r4['early_snapback'])}, BF={len(r4['breadth_fade'])}")
    r5 = _cache_step("WS5", lambda: ws5_competing_risk(df, ledger))
    print(f"[WS5] CIF final: {r5['final_cif']}")
    r6 = _cache_step("WS6", lambda: ws6_termination(term5))
    print(f"[WS6] termination signatures: {r6['counts'].to_dict('records')}")
    r7 = _cache_step("WS7", lambda: ws7_conditional(r2["event_sequences"], r2["atlas"], ledger))
    print(f"[WS7] conditional cells: {len(r7['audit'])}")
    r8 = _cache_step("WS8", lambda: ws8_roles(r1, r2, r3, r4, r5, r6))
    r9 = _cache_step("WS9", lambda: ws9_nodes(r1, r2, r3, r4, r5, r6, r7))
    print(f"[WS9] nodes={len(r9['nodes'])}, edges={len(r9['edges'])}")

    # ---- 19_NEW_NODE_MERGE_DISSOLVE ----
    n_promoted = r2["n_promoted"]
    q1 = r3.get("q1_earliest", pd.DataFrame())
    n_breadth_earliest = len(q1)
    final_cif = r5["final_cif"]
    two_clock = (final_cif.get("REENTRY", 0) > final_cif.get("PROPAGATION", 0) + 0.05)
    n_abrupt = int((r6["counts"].signature == "ABRUPT").sum()) if "ABRUPT" in set(r6["counts"].signature) else 0
    cond_sig = int((r7["audit"].significant_fdr).sum()) if len(r7["audit"]) > 0 and "significant_fdr" in r7["audit"] else 0
    n_motif_sig = int((r4["subfamily_tests"].significant_fdr).sum()) if len(r4["subfamily_tests"]) > 0 and "significant_fdr" in r4["subfamily_tests"] else 0

    node_ops = []
    for _, srow in r2["atlas"].iterrows():
        if srow.classification in ("LOCAL_SEQUENCE", "GLOBAL_SEQUENCE", "CONDITIONAL_SEQUENCE"):
            node_ops.append({"node": srow.seq_id, "operation": "NEW_NODE",
                             "strength": srow.classification, "source": "WS2",
                             "note": f"n={srow.n_effective}, lift={srow.lift}, q={srow.p_fdr}"})
    for _, er in q1.iterrows():
        node_ops.append({"node": f"BREADTH_DIVERGENCE_{er.coordinate}",
                         "operation": "NEW_NODE", "strength": "ROBUST",
                         "source": "WS3", "note": f"earliest at +{er.horizon_d}D"})
    node_ops.append({"node": "BREADTH_TRANSMISSION_STAGE", "operation": "NEW_NODE" if n_breadth_earliest >= 3 else "DESCRIPTIVE_ONLY",
                     "strength": f"{n_breadth_earliest}_earliest_coords", "source": "WS3"})
    node_ops.append({"node": "TWO_CLOCK_PROSPECTIVE", "operation": "NEW_NODE" if two_clock else "DESCRIPTIVE_ONLY",
                     "strength": f"CIF reentry={final_cif.get('REENTRY',0)}, prop={final_cif.get('PROPAGATION',0)}",
                     "source": "WS5"})
    node_ops.append({"node": "TERMINATION_MICROSEQUENCE", "operation": "DESCRIPTIVE_ONLY",
                     "strength": f"n_abrupt={n_abrupt}", "source": "WS6"})
    node_ops.append({"node": "RETEST_RELOAD", "operation": "DESCRIPTIVE_ONLY",
                     "strength": "MECH-5 WS3 null preserved", "source": "MECH-5"})
    node_ops.append({"node": "ACCUMULATION_LIKE", "operation": "MERGE",
                     "strength": "absorbed by breadth (MECH-4/5)", "source": "MECH-4"})
    node_ops.append({"node": "VOLATILITY_INCREMENTAL_GATE", "operation": "DISSOLVE",
                     "strength": "no incremental success/failure info (MECH-5)", "source": "MECH-5"})
    if n_motif_sig == 0:
        node_ops.append({"node": "MOTIF_SUBFAMILY", "operation": "NULL",
                         "strength": f"{n_motif_sig} significant subfamily splits", "source": "WS4"})
    pd.DataFrame(node_ops).to_csv(OUT / "19_NEW_NODE_MERGE_DISSOLVE.csv", index=False)

    # ---- 20_NULL_AND_FAILED_RESULTS ----
    nulls = []
    for _, srow in r2["atlas"].iterrows():
        if srow.classification in ("NULL", "LOW_SAMPLE_CURIOSITY"):
            nulls.append({"result": f"seq {srow.seq_id}", "classification": srow.classification,
                          "note": f"n_eff={srow.n_effective}, n_sub={srow.n_subperiods}, lift={srow.lift}, q={srow.p_fdr}"})
    if len(r4["subfamily_tests"]) > 0:
        for _, srow in r4["subfamily_tests"].iterrows():
            if not bool(srow.significant_fdr):
                nulls.append({"result": f"motif subfamily {srow.motif}/{srow.subfamily}/{srow.statistic}",
                              "classification": "NULL", "note": f"p_fdr={srow.p_fdr}"})
    if n_abrupt == len(r6["counts"]):
        nulls.append({"result": "termination precursor", "classification": "NULL",
                      "note": "all terminations ABRUPT (no early decline)"})
    if cond_sig == 0 and len(r7["audit"]) > 0:
        nulls.append({"result": "conditional local rules", "classification": "NULL",
                      "note": f"{cond_sig}/{len(r7['audit'])} condition cells significant"})
    pd.DataFrame(nulls).to_csv(OUT / "20_NULL_AND_FAILED_RESULTS.csv", index=False)

    # ---- 21 summary ----
    lines = ["# MECH-6 SUMMARY", "",
             f"## Micro-state event atlas (WS1)", f"- {len(r1['panel'])} event-horizon rows (125 events x 10 horizons)",
             f"- atoms: canonical state, composite micro-state, breadth/rank/conc/eth/btc axes",
             "", "## Local sequence discovery (WS2)",
             f"- Promoted LOCAL_SEQUENCE: {n_promoted}",
             f"- Event-anchored candidates: {len(r2['event_summary'])}; panel paths: {len(r2['panel_summary'])}"]
    for _, srow in r2["atlas"].iterrows():
        lines.append(f"  - [{srow.classification}] {srow.seq_id}: n_eff={srow.n_effective}, lift={srow.lift}, q={srow.p_fdr}, p_suc={srow.p_success}")
    lines += ["", "## Breadth transmission (WS3)",
              f"- Coordinates with earliest significant separation: {n_breadth_earliest}"]
    for _, er in q1.iterrows():
        lines.append(f"  - {er.coordinate}: earliest +{er.horizon_d}D (r={er.r_eff}, q={er.p_fdr})")
    lines += ["", "## Failure motif refinement (WS4)",
              f"- EARLY_SNAPBACK n={len(r4['early_snapback'])}, BREADTH_FADE n={len(r4['breadth_fade'])}",
              f"- Significant subfamily splits (FDR): {n_motif_sig}"]
    lines += ["", "## Two-clock prospective competing-risk (WS5)",
              f"- Final cumulative incidence: {final_cif}",
              f"- Two-clock (reentry CIF >> propagation CIF): {two_clock}",
              "", "## Termination microsequences (WS6)"]
    for _, wrow in r6["counts"].iterrows():
        lines.append(f"  - {wrow.signature}: {wrow.count} ({wrow.pct:.0%})")
    lines += ["", "## Conditional local rules (WS7)",
              f"- Significant condition cells (FDR): {cond_sig}/{len(r7['audit'])}",
              "", "## Alpha-role registry (WS8)", f"- {len(r8['registry'])} statistics tagged",
              "", "## Node graph (WS9)", f"- {len(r9['nodes'])} nodes, {len(r9['edges'])} edges"]
    with open(OUT / "21_MECH6_SUMMARY.md", "w") as f:
        f.write("\n".join(lines))

    # ---- 22 decision ----
    breadth_earned = n_breadth_earliest >= 3
    seq_earned = n_promoted >= 1
    if seq_earned and breadth_earned:
        verdict = "PASS_MECH6_MICROSTATE_SEQUENCE_ATLAS"
    elif breadth_earned or two_clock:
        verdict = "PASS_MECH6_WITH_LIMITATIONS"
    elif n_breadth_earliest > 0 or two_clock:
        verdict = "PASS_MECH6_WITH_LIMITATIONS"
    else:
        verdict = "FAIL_MECH6_NO_RECURRING_STRUCTURE"
    dlines = ["# MECH-6 DECISION", "", f"## VERDICT: {verdict}", "",
              "### Key findings:",
              f"- Promoted local sequences (>=50 eff, >=3 subperiods): {n_promoted}",
              f"- Breadth transmission earliest coordinates: {n_breadth_earliest}",
              f"- Prospective two-clock CIF: {final_cif}",
              f"- Termination microsequences: {r6['counts'].to_dict('records')}",
              f"- Conditional rule cells significant: {cond_sig}/{len(r7['audit'])}",
              f"- Motif subfamily splits significant: {n_motif_sig}",
              "", "### human_review_required = TRUE",
              "### next_checkpoint_authorized = FALSE", "",
              "No strategy. No PnL. No deployment."]
    with open(OUT / "22_MECH6_DECISION.md", "w") as f:
        f.write("\n".join(dlines))
    with open(OUT / "_verdicts.json", "w") as f:
        json.dump({"verdict": verdict, "n_promoted": int(n_promoted),
                   "n_breadth_earliest": int(n_breadth_earliest),
                   "two_clock": bool(two_clock), "n_cond_sig": int(cond_sig),
                   "n_motif_sig": int(n_motif_sig),
                   "final_cif": {k: float(v) for k, v in final_cif.items()}}, f, indent=2)
    print(f"\n[VERDICT] {verdict}")
    n_csv = len(list(OUT.glob("*.csv")))
    print(f"[DONE] {n_csv} CSV artifacts")


if __name__ == "__main__":
    main()
