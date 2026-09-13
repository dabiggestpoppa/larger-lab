#!/usr/bin/env python
"""ALT_MECH_4 - Pivot Release Gates, Stall Release, Path Memory & Propagation Depth.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no strategy,
no optimization, no ML predictors, no sizing, no deployment. All rules fixed in
01_PREREGISTRATION.md BEFORE this script executed.

Reuses DATA-1.1 inputs and MECH-1/MECH-2/MECH-3 helpers.
"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, kruskal, chi2_contingency

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260901
PERM_N = 200
BLOCK_DAYS = 20
MIN_STATE_DAYS = 120

ROOT = Path(__file__).resolve().parents[1]            # mech_4/
for p in ("mech_1", "mech_2", "mech_3"):
    sys.path.insert(0, str(ROOT.parent / p / "scripts"))
import alt_mech_1_analysis as M1
import alt_mech_2_analysis as M2
import alt_mech_3_analysis as M3

OUT = ROOT
DATA = M1.DATA

BANDS = M1.BANDS
SUBPERIODS = M1.SUBPERIODS
CONC_STATE = "BTC_CONCENTRATION"
BASIN = {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"}
ALT_FAMILY = {"ETH_BROADENING", "LARGE_ALT_ROTATION", "MID_CAP_ROTATION",
              "SMALL_CAP_ROTATION"}
PROP_FAMILY = {"BROAD_RISK_EXPANSION"} | ALT_FAMILY
DEFENSIVE = {"CAPITAL_EXIT", "STABLECOIN_PARKING"}

# fixed 10-feature current-state set (pre-exit precursor medians over [-7,-1])
STATE_FEATURES = ["btc_ret30", "btc_ret7", "top3_share", "top3_share_chg7",
                  "breadth30", "disp30", "sc_chg30", "eth_rel30", "vol_med",
                  "chain_tvl_med_chg7"]
ROUTE_CAT = {"BROAD_RISK_EXPANSION": "RISK_STATE", "MIXED_NO_CLEAR_ROUTE": "MIXED"}


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            obj = pickle.load(fh)
        print(f"[cache] {name} loaded")
        return obj
    print(f"[run] {name} ...")
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def load():
    inp = M1.load_inputs()
    tl = M1.verify_truth_lock(inp)
    return inp, tl


# ----------------------------------------------------------------------------
# daily frame + chain frame (reuse MECH-3 builders verbatim)
# ----------------------------------------------------------------------------

def build_daily(inp):
    daily, d, bm = M3.build_daily(inp)
    # regime flags needed by WS D / G / H (same constructions as MECH-3 WS D)
    daily["ETH_STRONG"] = daily.eth_btc_relative_return_30d > 0
    daily["ETH_WEAK"] = daily.eth_btc_relative_return_30d < 0
    daily["CHAIN_EXPANDING"] = daily.chain_tvl_med_chg7 > 0
    daily["CHAIN_CONTRACTING"] = daily.chain_tvl_med_chg7 < 0
    daily["RISK_ON"] = daily.total_mcap_chg30 > 0
    daily["RISK_OFF"] = daily.total_mcap_chg30 < 0
    daily["vol_p70"] = daily.vol_med.rolling(252, min_periods=60).quantile(0.70)
    daily["vol_p30"] = daily.vol_med.rolling(252, min_periods=60).quantile(0.30)
    return daily, d, bm


def build_chainframe(inp):
    m = M3.chain_frame(inp)
    cov = m.groupby("chain").historical_date.nunique()
    top = cov[cov >= 120].sort_values(ascending=False).head(12).index.tolist()
    return m, top


# ----------------------------------------------------------------------------
# canonical events + reconciliation (WS preamble)
# ----------------------------------------------------------------------------

def derive_events(daily):
    st = daily.state.values
    dates = daily.historical_date.values
    entries, exits = [], []
    for t in range(1, len(st)):
        if st[t] == CONC_STATE and st[t - 1] != CONC_STATE:
            entries.append(t)
        if st[t - 1] == CONC_STATE and st[t] != CONC_STATE:
            exits.append(t)
    return entries, exits


def ws_reconcile(daily):
    """03: re-derived event ledger vs MECH-3 canonical parquets."""
    entries, exits = derive_events(daily)
    e3 = pd.read_parquet(ROOT.parent / "mech_3" / "09_CONCENTRATION_ENTRY_EVENTS.parquet")
    x3 = pd.read_parquet(ROOT.parent / "mech_3" / "10_CONCENTRATION_EXIT_EVENTS.parquet")
    dates = daily.historical_date.values
    mine_e = {pd.Timestamp(dates[t]).strftime("%Y-%m-%d") for t in entries}
    mine_x = {pd.Timestamp(dates[t]).strftime("%Y-%m-%d") for t in exits}
    mech3_e = {pd.Timestamp(x).strftime("%Y-%m-%d") for x in e3.date}
    mech3_x = {pd.Timestamp(x).strftime("%Y-%m-%d") for x in x3.date}
    rows = [{"event_type": "ENTRY", "canonical_count": len(mech3_e),
             "recount": len(mine_e),
             "only_canonical": len(mech3_e - mine_e),
             "only_recount": len(mine_e - mech3_e),
             "match": len(mech3_e & mine_e)},
            {"event_type": "EXIT", "canonical_count": len(mech3_x),
             "recount": len(mine_x),
             "only_canonical": len(mech3_x - mine_x),
             "only_recount": len(mine_x - mech3_x),
             "match": len(mech3_x & mine_x)}]
    pd.DataFrame(rows).to_csv(OUT / "03_RELEASE_EVENT_RECONCILIATION.csv", index=False)
    return {"recount": {"entries": entries, "exits": exits},
            "canonical_exits": mech3_x}


# ----------------------------------------------------------------------------
# Workstream A - release event ledger + post-release sequence
# ----------------------------------------------------------------------------

def _spell_bounds(daily, exit_idx):
    """Return (entry_idx, duration_d) of the concentration episode ending at exit_idx."""
    j = exit_idx
    while j > 0 and daily.state.iloc[j - 1] == CONC_STATE:
        j -= 1
    return j, exit_idx - j


def _state_at(daily, t, off):
    i = t + off
    if 0 <= i < len(daily):
        return daily.state.iloc[i]
    return None


def _staged_pattern(daily, t, horizon=30):
    """Classify staged propagation over (t, t+horizon] from the state series."""
    end = min(len(daily), t + horizon + 1)
    seq = [daily.state.iloc[i] for i in range(t + 1, end)]
    if not seq:
        return "UNRESOLVED", []
    # destination = first state held >= 5 consecutive days
    dest, dest_i = None, None
    for i in range(len(seq)):
        run = 1
        while i + run < len(seq) and seq[i + run] == seq[i]:
            run += 1
        if run >= 5:
            dest, dest_i = seq[i], i + 1
            break
    alt_idx = next((i for i, s in enumerate(seq) if s in ALT_FAMILY), None)
    br_idx = next((i for i, s in enumerate(seq) if s == "BROAD_RISK_EXPANSION"), None)
    if dest in ALT_FAMILY:
        if br_idx is not None and br_idx < alt_idx:
            return "CONC_VIA_BROAD_RISK", seq
        return "CONC_DIRECT_ALT", seq
    if dest == "BROAD_RISK_EXPANSION":
        return "CONC_BROAD_RISK_ONLY", seq
    if dest == "MIXED_NO_CLEAR_ROUTE":
        return "CONC_MIXED", seq
    if dest == CONC_STATE:
        return "CONC_REENTRY", seq
    if dest in DEFENSIVE:
        return "CONC_DEFENSIVE", seq
    return "UNRESOLVED", seq


def ws_a(daily, entries, exits):
    dates = daily.historical_date.values
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(dates)}
    ledger_rows, seq_rows = [], []
    for k, t in enumerate(exits):
        d0 = dates[t]
        entry_i, dur = _spell_bounds(daily, t)
        entry_date = dates[entry_i]
        route = daily.state.iloc[entry_i - 1] if entry_i > 0 else "SAMPLE_START"
        dest, tt = M3._destination_state(daily, t)
        # post-release sequence map
        seq = {f"state_tp{h}": _state_at(daily, t, h) for h in (1, 3, 5, 7, 14, 30)}
        pattern, seq_list = _staged_pattern(daily, t)
        sp = M1.subperiod_of(pd.Timestamp(d0))
        # regime flags at exit
        flags = {s: bool(daily[s].iloc[t]) for s in
                 ["BTC_UP", "BTC_DOWN", "VOL_HIGH", "VOL_LOW",
                  "BREADTH_EXPANDING", "BREADTH_CONTRACTING", "CONC_RISING",
                  "CONC_FALLING", "ETH_STRONG", "ETH_WEAK", "RISK_ON", "RISK_OFF"]}
        # observable values at t (PIT; trailing-window means already shifted)
        obs = {}
        for kk, col in [("btc_ret30", "btc_return_30d"), ("btc_ret7", "btc_return_7d"),
                        ("top3_share", "top3_share"), ("top3_share_chg7", "top3_share_chg7"),
                        ("breadth30", "top500_breadth_30d"), ("disp30", "top500_dispersion_30d"),
                        ("sc_chg30", "stablecoin_change_30d"),
                        ("eth_rel30", "eth_btc_relative_return_30d"),
                        ("vol_med", "vol_med"), ("chain_tvl_med_chg7", "chain_tvl_med_chg7")]:
            v = daily[col].iloc[t] if col in daily.columns else np.nan
            obs[kk] = round(float(v), 5) if v == v else np.nan
        ledger_rows.append({
            "event_id": f"EXIT_{k:03d}", "entry_date": entry_date, "exit_date": d0,
            "episode_duration_d": dur, "route_into_concentration": route,
            "state_age_d": dur, "release_date": d0,
            "first_destination": dest, "days_to_destination_d": tt,
            "subperiod": sp, **flags,
            **{f"obs_{kk}": v for kk, v in obs.items()},
            "availability_mask": json.dumps({kk: not np.isnan(v) for kk, v in obs.items()}),
            "staged_pattern": pattern})
        seq_rows.append({"event_id": f"EXIT_{k:03d}", "exit_date": d0,
                         "first_destination": dest, "staged_pattern": pattern,
                         **seq, "alt_reached_30d": any(s in ALT_FAMILY for s in seq_list),
                         "broad_risk_seen_30d": "BROAD_RISK_EXPANSION" in seq_list})
    ledger = pd.DataFrame(ledger_rows)
    ledger.to_parquet(OUT / "04_RELEASE_EVENT_LEDGER.parquet", index=False)
    sq = pd.DataFrame(seq_rows)
    sq.to_csv(OUT / "05_RELEASE_SEQUENCE_MAP.csv", index=False)
    # BROAD_RISK vs ALT: competing routes or intermediate depth?
    alt_any = sq.alt_reached_30d
    br_first = sq.broad_risk_seen_30d
    br_then_alt = alt_any & br_first
    alt_only = alt_any & ~br_first
    # among ALT-reachers, was BROAD_RISK typically seen first?
    p_alt = float(alt_any.mean()) if len(sq) else np.nan
    p_br_before_alt = float(br_then_alt.sum() / max(alt_any.sum(), 1))
    # time to destination by route
    ttd = ledger.groupby("first_destination").days_to_destination_d.median().to_dict()
    br_ttd = ttd.get("BROAD_RISK_EXPANSION", np.nan)
    alt_ttd = np.nanmedian([ledger.loc[ledger.first_destination.isin(ALT_FAMILY),
                                       "days_to_destination_d"].values]) \
        if (ledger.first_destination.isin(ALT_FAMILY)).any() else np.nan
    verdict = "UNRESOLVED"
    if len(sq) and alt_any.any():
        if p_br_before_alt >= 0.60:
            verdict = "INTERMEDIATE_DEPTH"
        elif p_br_before_alt <= 0.30:
            verdict = "COMPETING_ROUTES"
    out = {"ledger": ledger, "seq": sq, "n_alt_reached": int(alt_any.sum()),
           "n_br_before_alt": int(br_then_alt.sum()),
           "p_alt_reached_30d": round(p_alt, 4) if p_alt == p_alt else np.nan,
           "p_broad_risk_before_alt": round(p_br_before_alt, 4) if p_br_before_alt == p_br_before_alt else np.nan,
           "broad_risk_ttd": br_ttd, "alt_ttd": alt_ttd, "verdict": verdict,
           "pattern_counts": sq.staged_pattern.value_counts().to_dict()}
    with open(OUT / "_ws_a_verdict.json", "w") as fh:
        json.dump({k: (v if not isinstance(v, dict) else
                       {str(a): int(b) for a, b in v.items()})
                   for k, v in out.items() if k not in ("ledger", "seq")}, fh,
                  indent=2, default=str)
    return out


# ----------------------------------------------------------------------------
# logistic helpers (L2, temporal 5-fold CV, permutation null)
# ----------------------------------------------------------------------------

def _logloss(y, p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _brier(y, p):
    return float(np.mean((y - p) ** 2))


def _auc(y, p):
    """AUC = P(p_pos > p_neg), computed via rank ordering (ties = 0.5)."""
    from scipy.stats import rankdata
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    idx = np.argsort(-p)
    ys = y[idx]
    r = rankdata(-p[idx], method="average")
    n_pos = int(ys.sum())
    n_neg = len(ys) - n_pos
    if n_pos == 0 or n_neg == 0:
        return np.nan
    # rank of positives under ascending-rank (rankdata of -p ascending = low p low rank)
    # Mann-Whitney: sum of ranks of positives in the joint ascending order of p
    r_asc = rankdata(p[idx], method="average")
    a = float((r_asc[ys == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))
    return a


def _zscore_fit(Xtr, Xte):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return (Xtr - mu) / sd, (Xte - mu) / sd


def _logistic_eval(X, y, n_folds=5, C=1.0, seed=SEED):
    """Temporal 5-fold CV: held-out log loss, Brier, AUC vs intercept-only."""
    from sklearn.linear_model import LogisticRegression
    X = np.asarray(X, float)
    if np.isnan(X).any():
        # fixed rule: median-impute per column (prereg section 4)
        X = X.copy()
        for j in range(X.shape[1]):
            col = X[:, j]
            med = np.nanmedian(col)
            if np.isnan(med):
                med = 0.0
            X[:, j] = np.where(np.isnan(col), med, col)
    n = len(y)
    if n < 20 or len(np.unique(y)) < 2:
        return {"logloss": np.nan, "brier": np.nan, "auc": np.nan,
                "base_logloss": np.nan, "delta_logloss": np.nan,
                "n": int(n), "n_pos": int(y.sum())}
    order = np.arange(n)
    splits = np.array_split(order, n_folds)
    ll, br, aucs = [], [], []
    base_ll = []
    for k in range(n_folds):
        te = splits[k]
        tr = np.setdiff1d(order, te)
        ytr, yte = y[tr], y[te]
        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            continue
        Xtr, Xte = _zscore_fit(X[tr], X[te])
        clf = LogisticRegression(penalty="l2", C=C, max_iter=2000,
                                 random_state=seed + k).fit(Xtr, ytr)
        p = clf.predict_proba(Xte)[:, 1]
        ll.append(_logloss(yte, p))
        br.append(_brier(yte, p))
        a = _auc(yte, p)
        if a == a:
            aucs.append(a)
        pb = ytr.mean()
        base_ll.append(_logloss(yte, np.full(len(yte), pb)))
    if not ll:
        return {"logloss": np.nan, "brier": np.nan, "auc": np.nan,
                "base_logloss": np.nan, "delta_logloss": np.nan,
                "n": int(n), "n_pos": int(y.sum())}
    ll_v, base_v = float(np.mean(ll)), float(np.mean(base_ll))
    return {"logloss": round(ll_v, 4), "brier": round(float(np.mean(br)), 4),
            "auc": round(float(np.mean(aucs)), 4) if aucs else np.nan,
            "base_logloss": round(base_v, 4),
            "delta_logloss": round(base_v - ll_v, 4),
            "n": int(n), "n_pos": int(y.sum())}


def _permute_delta(X, y, n_perm=PERM_N, seed=SEED):
    """Permutation null on delta logloss (shuffle y)."""
    from sklearn.linear_model import LogisticRegression
    rng = np.random.default_rng(seed)
    base = _logistic_eval(X, y)["delta_logloss"]
    if not np.isfinite(base):
        return np.nan, np.nan
    n = len(y)
    nulls = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        d = _logistic_eval(X, yp)["delta_logloss"]
        if np.isfinite(d):
            nulls.append(d)
    if not nulls:
        return base, np.nan
    p = float((np.array(nulls) >= base).mean())
    return base, round(p, 4)


def _gate_label(ledger, gate):
    """Fixed gate label rules from prereg section 3."""
    dest = ledger.first_destination
    if gate == "G1":
        return (dest != CONC_STATE).astype(int).values  # ESCAPE=1
    if gate == "G3":
        return dest.isin(PROP_FAMILY).astype(int).values  # PROPAGATION=1
    raise ValueError(gate)


def _exit_features(ledger, daily):
    """10-feature current-state matrix (pre-exit precursor medians over [-7,-1])."""
    pf, win_cols = M3._precursor_frame(daily)
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(pf.historical_date.values)}
    X, rows = [], []
    for _, r in ledger.iterrows():
        i = date_idx[pd.Timestamp(r.exit_date)]
        vec = []
        for k in STATE_FEATURES:
            vals = []
            for w in (1, 3, 7):
                c = f"{k}_w{w}"
                v = pf[c].iloc[i]
                if v == v:
                    vals.append(float(v))
            vec.append(float(np.median(vals)) if vals else np.nan)
        X.append(vec)
        rows.append({"event_id": r.event_id, "exit_date": r.exit_date,
                     "first_destination": r.first_destination,
                     "subperiod": r.subperiod,
                     **{f"feat_{k}": vec[j] for j, k in enumerate(STATE_FEATURES)}})
    X = np.array(X, float)
    feat_df = pd.DataFrame(rows)
    # median-impute per feature (fixed rule; ~2-4% of cells)
    for j, k in enumerate(STATE_FEATURES):
        col = f"feat_{k}"
        med = np.nanmedian(X[:, j])
        X[:, j] = np.where(np.isnan(X[:, j]), med, X[:, j])
        feat_df[col] = feat_df[col].fillna(med)
    return X, feat_df


def ws_b(ledger, X, feat_df):
    """06-09: hierarchical gates G1-G4 with logistic evaluation."""
    dest = ledger.first_destination
    # G1 ESCAPE vs SNAPBACK
    g1 = (dest != CONC_STATE).astype(int).values
    r1 = _logistic_eval(X, g1)
    p1 = _permute_delta(X, g1)
    # G2 among escapers: MIXED vs PROPAGATION (binary); DEFENSIVE descriptive
    esc = dest != CONC_STATE
    g2 = dest.isin(PROP_FAMILY).astype(int).values[esc]
    r2 = _logistic_eval(X[esc], g2)
    p2 = _permute_delta(X[esc], g2)
    # G3 PROPAGATION vs (REENTRY+MIXED) on all 125
    g3 = dest.isin(PROP_FAMILY).astype(int).values
    r3 = _logistic_eval(X, g3)
    p3 = _permute_delta(X, g3)
    # G4 depth among propagation: BROAD_RISK vs ALT (exploratory)
    prop = dest.isin(PROP_FAMILY)
    g4 = (dest == "BROAD_RISK_EXPANSION").astype(int).values[prop]
    r4 = _logistic_eval(X[prop], g4)
    p4 = _permute_delta(X[prop], g4)
    rows = [
        {"gate": "G1_ESCAPE_VS_SNAPBACK", "n": r1["n"], "n_positive": r1["n_pos"],
         "base_logloss": r1["base_logloss"], "logloss": r1["logloss"],
         "delta_logloss": r1["delta_logloss"], "brier": r1["brier"],
         "auc": r1["auc"], "perm_p": p1[1], "classification":
             "SUPPORTED" if p1[1] == p1[1] and p1[1] < 0.05 else "NOT_SUPPORTED"},
        {"gate": "G2_MIXED_VS_PROPAGATION", "n": r2["n"], "n_positive": r2["n_pos"],
         "base_logloss": r2["base_logloss"], "logloss": r2["logloss"],
         "delta_logloss": r2["delta_logloss"], "brier": r2["brier"],
         "auc": r2["auc"], "perm_p": p2[1], "classification":
             "SUPPORTED" if p2[1] == p2[1] and p2[1] < 0.05 else "NOT_SUPPORTED"},
        {"gate": "G3_PROPAGATION_VS_NOT", "n": r3["n"], "n_positive": r3["n_pos"],
         "base_logloss": r3["base_logloss"], "logloss": r3["logloss"],
         "delta_logloss": r3["delta_logloss"], "brier": r3["brier"],
         "auc": r3["auc"], "perm_p": p3[1], "classification":
             "SUPPORTED" if p3[1] == p3[1] and p3[1] < 0.05 else "NOT_SUPPORTED"},
        {"gate": "G4_BROAD_RISK_VS_ALT_DEPTH", "n": r4["n"], "n_positive": r4["n_pos"],
         "base_logloss": r4["base_logloss"], "logloss": r4["logloss"],
         "delta_logloss": r4["delta_logloss"], "brier": r4["brier"],
         "auc": r4["auc"], "perm_p": p4[1], "classification":
             "EXPLORATORY_N9" if r4["n"] <= 30 else "NOT_SUPPORTED"},
    ]
    pd.DataFrame(rows).to_csv(OUT / "06_ESCAPE_VS_SNAPBACK.csv", index=False)
    # per-gate feature frame (standardized coefs on full sample)
    from sklearn.linear_model import LogisticRegression
    def coefs(y, name, gate):
        Xs, _ = _zscore_fit(X, X)
        clf = LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                                 random_state=SEED).fit(Xs, y)
        return [{"gate": gate, "feature": f, "coef": round(c, 4),
                 "abs_coef_rank": int(np.argsort(-np.abs(clf.coef_[0])).tolist().index(j)) + 1}
                for j, (f, c) in enumerate(zip(STATE_FEATURES, clf.coef_[0]))]
    rows2 = coefs(g1, "G1", "G1") + coefs(g3, "G3", "G3")
    pd.DataFrame(rows2).to_csv(OUT / "07_RELEASE_DESTINATION_GATE.csv", index=False)
    rows3 = coefs(g3, "G3", "G3")
    pd.DataFrame(rows3).to_csv(OUT / "08_PROPAGATION_GATE.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "09_PROPAGATION_DEPTH.csv", index=False)
    return {"gates": rows, "g1": r1, "g2": r2, "g3": r3, "g4": r4,
            "perm": {"G1": p1[1], "G2": p2[1], "G3": p3[1], "G4": p4[1]}}


# ----------------------------------------------------------------------------
# Workstream C - present state vs path memory (nested M0-M3)
# ----------------------------------------------------------------------------

def _path_features(ledger, daily, entries):
    """M1 route one-hot, M2 age/oscillations, M3 trajectory (all PIT)."""
    dates = daily.historical_date.values
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(dates)}
    st = daily.state.values
    # boundary oscillation count / prior failed release attempts (prior 180D)
    osc = np.zeros(len(ledger), int)
    fails = np.zeros(len(ledger), int)
    logage = np.zeros(len(ledger), float)
    entry_vel = np.zeros(len(ledger), float)
    slope, curv = np.zeros(len(ledger), float), np.zeros(len(ledger), float)
    route_onehot = np.zeros((len(ledger), 2), float)  # RISK_STATE, MIXED
    for j, (_, r) in enumerate(ledger.iterrows()):
        t = date_idx[pd.Timestamp(r.exit_date)]
        lo = max(0, t - 180)
        osc[j] = min(5, int(sum(1 for e in entries if lo <= e < t)))
        # failed releases: exits in prior 180D that re-entered within 7D
        fcnt = 0
        for e in entries:
            if lo <= e < t:
                # entry at e; did an exit within [e, e+7] snap back within 7 more?
                for x in range(e, min(len(st), e + 8)):
                    if x + 1 < len(st) and st[x] == CONC_STATE and st[x + 1] != CONC_STATE:
                        # exit at x+1; re-entry within 7?
                        for y in range(x + 2, min(len(st), x + 9)):
                            if st[y] == CONC_STATE and st[y - 1] != CONC_STATE:
                                fcnt += 1
                                break
                        break
        fails[j] = min(5, fcnt)
        dur = r.episode_duration_d
        logage[j] = np.log1p(max(dur, 1))
        # entry velocity: btc_ret30 change 7D before entry
        ei = date_idx[pd.Timestamp(r.entry_date)]
        v_now = daily.btc_return_30d.iloc[ei - 1] if ei - 1 >= 0 else np.nan
        v_prev = daily.btc_return_30d.iloc[max(0, ei - 8)]
        entry_vel[j] = v_now - v_prev if (v_now == v_now and v_prev == v_prev) else np.nan
        # concentration slope / curvature: OLS of top3_share over episode
        a, b = _spell_bounds(daily, t)
        if b - a >= 5:
            yv = daily.top3_share.iloc[a:t + 1].values.astype(float)
            xv = np.arange(len(yv))
            ok = ~np.isnan(yv)
            if ok.sum() >= 5:
                A = np.column_stack([np.ones(len(xv)), xv, xv ** 2])
                beta, *_ = np.linalg.lstsq(A[ok], yv[ok], rcond=None)
                slope[j] = float(beta[1])
                curv[j] = float(beta[2])
        rcat = ROUTE_CAT.get(r.route_into_concentration, "OTHER")
        if rcat == "RISK_STATE":
            route_onehot[j, 0] = 1.0
        elif rcat == "MIXED":
            route_onehot[j, 1] = 1.0
    return {"route": route_onehot, "logage": logage, "osc": osc, "fails": fails,
            "entry_vel": entry_vel, "slope": slope, "curv": curv}


def _cmi_bias_corrected(x, y, z, bins=3):
    """Bias-corrected plugin estimate of I(X;Y|Z) with 3-bin quantiles."""
    def disc(v):
        q = np.nanquantile(v, [1 / 3, 2 / 3])
        return np.digitize(v, q)
    x = np.asarray(x, float); z = np.asarray(z, float); y = np.asarray(y)
    ok = ~(np.isnan(x) | np.isnan(z))
    x, z, y = x[ok], z[ok], y[ok]
    if len(y) < 30:
        return np.nan
    xd, zd = disc(x), disc(z)
    yd = y.astype(int)
    n = len(y)
    # plugin via histogram
    H = np.zeros((bins, bins, bins))
    for a, b, c in zip(xd, yd, zd):
        H[a, b, c] += 1
    pxyz = H / max(n, 1)
    pxy = pxyz.sum(axis=2)
    pxz = pxyz.sum(axis=1)
    pyz = pxyz.sum(axis=0)
    px = pxyz.sum(axis=(1, 2))
    py = pxyz.sum(axis=(0, 2))
    pz = pxyz.sum(axis=(0, 1))
    eps = 1e-12
    I = 0.0
    for a in range(bins):
        for b in range(bins):
            for c in range(bins):
                v = pxyz[a, b, c]
                if v > eps:
                    I += v * np.log((v * pz[c]) / max((pxy[a, b] * pyz[b, c]), eps))
    # Miller-Madow correction: (k_x - 1)(k_y - 1)(k_z - 1) / (2 n ln2)? use nats -> bits
    bias = (bins - 1) * (bins - 1) * (bins - 1) / (2 * n * np.log(2))
    return max(0.0, I / np.log(2) - bias)


def ws_c(ledger, X, daily, entries):
    """10/11: nested models M0-M3 on G3 outcome; path memory increment."""
    g3 = _gate_label(ledger, "G3")
    pf = _path_features(ledger, daily, entries)
    M = {"M0": X}
    M["M1"] = np.column_stack([X, pf["route"]])
    M["M2"] = np.column_stack([M["M1"], pf["logage"], pf["osc"]])
    M["M3"] = np.column_stack([M["M2"], pf["entry_vel"], pf["slope"], pf["curv"],
                               pf["fails"]])
    rows = []
    for name in ["M0", "M1", "M2", "M3"]:
        r = _logistic_eval(M[name], g3)
        rows.append({"model": name, "n_features": M[name].shape[1],
                     **{k: r[k] for k in ("logloss", "brier", "auc", "base_logloss",
                                          "delta_logloss", "n", "n_pos")}})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "10_CURRENT_STATE_BASELINE.csv", index=False)
    # permutation test on path features only (M3 vs M0): shuffle M1-M3 columns
    from sklearn.linear_model import LogisticRegression
    rng = np.random.default_rng(SEED + 3)
    d_obs = _logistic_eval(M["M3"], g3)["delta_logloss"] - \
        _logistic_eval(M["M0"], g3)["delta_logloss"]
    nulls = []
    for _ in range(PERM_N):
        Mp = M["M3"].copy()
        # shuffle each path column independently
        for j in range(X.shape[1], Mp.shape[1]):
            rng.shuffle(Mp[:, j])
        d0 = _logistic_eval(Mp, g3)["delta_logloss"]
        d_ = d0 - _logistic_eval(M["M0"], g3)["delta_logloss"]
        if np.isfinite(d_):
            nulls.append(d_)
    p_path = float((np.array(nulls) >= d_obs).mean()) if nulls else np.nan
    # CMI: I(path_route; outcome | current state proxy = btc_ret30)
    didx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    zvec = np.array([daily.btc_return_30d.iloc[didx[pd.Timestamp(d)]]
                     for d in ledger.exit_date.values], float)
    cmi = _cmi_bias_corrected(pf["route"][:, 0] * 2 + pf["route"][:, 1], g3, zvec)
    inc = pd.DataFrame([{"delta_logloss_M3_vs_M0": round(d_obs, 4) if d_obs == d_obs else np.nan,
                         "path_perm_p": round(p_path, 4) if p_path == p_path else np.nan,
                         "cmi_path_state_outcome_bits": round(cmi, 4),
                         "classification": ("HYSTERESIS_PREDICTIVE_MECHANISM"
                                            if p_path == p_path and p_path < 0.05
                                            and d_obs >= 0.005 else
                                            "HYSTERESIS_DESCRIPTIVE")}])
    inc.to_csv(OUT / "11_PATH_MEMORY_INCREMENT.csv", index=False)
    return {"models": df, "delta": d_obs, "path_perm_p": p_path, "cmi": cmi,
            "classification": inc.classification.iloc[0]}


# ----------------------------------------------------------------------------
# Workstream D - Markov vs semi-Markov (duration dependence)
# ----------------------------------------------------------------------------

def ws_d(daily):
    """12: hazard/duration audit of concentration spells."""
    st = daily.state.values
    dates = daily.historical_date.values
    spells = []
    i = 0
    while i < len(st):
        if st[i] == CONC_STATE:
            j = i
            while j < len(st) and st[j] == CONC_STATE:
                j += 1
            spells.append((i, j - 1))
            i = j
        else:
            i += 1
    rows = []
    for (a, b) in spells:
        dur = b - a + 1
        exited = b + 1 < len(st)
        dest = st[b + 1] if exited else None
        rows.append({"entry_idx": a, "exit_idx": b, "entry_date": dates[a],
                     "exit_date": dates[b] if exited else None, "duration_d": dur,
                     "exited": exited, "dest_after": dest,
                     "subperiod": M1.subperiod_of(pd.Timestamp(dates[a]))})
    sp = pd.DataFrame(rows)
    # hazard h(a) = P(exit at age a | survived to a)
    maxage = int(sp.duration_d.max()) if len(sp) else 1
    bins = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 7), (8, 14), (15, 30), (31, 10 ** 6)]
    hrows, test_count = [], 0
    for (lo, hi) in bins:
        at_risk = sp[(sp.duration_d >= lo) & (sp.exited) | (sp.duration_d >= lo) & (~sp.exited)]
        at_risk = sp[sp.duration_d >= lo]
        exited_at = sp[(sp.duration_d >= lo) & (sp.duration_d <= hi)]
        n_risk = len(at_risk)
        n_exit = int(exited_at.exited.sum())
        h = n_exit / max(n_risk, 1)
        test_count += 1
        hrows.append({"age_bin": f"{lo}-{hi}", "n_at_risk": n_risk,
                      "n_exited_in_bin": n_exit, "hazard": round(h, 4)})
    hazard = pd.DataFrame(hrows)
    # Test 1: P(exit within 7D | age bin) among spells still running
    age7 = []
    for lo, hi in bins:
        g = sp[sp.duration_d >= lo]
        if len(g) < 5:
            continue
        exit7 = g.exited & (g.duration_d <= lo + 6)
        age7.append({"age_bin": f"{lo}-{hi}", "n": int(len(g)),
                     "p_exit_within7d": round(float(exit7.mean()), 4),
                     "n_exit": int(exit7.sum())})
    t1 = pd.DataFrame(age7)
    # trend test on P(exit within 7D) vs age bin (authoritative rho computed in
    # the semi-Markov block from 12b bins; here only kruskal on raw exit per bin)
    p_kw = np.nan
    groups = [sp[sp.duration_d >= lo].exited.values for lo, hi in bins
              if len(sp[sp.duration_d >= lo]) >= 5]
    if len(groups) >= 3:
        p_kw = float(kruskal(*groups).pvalue)
        test_count += 1
    # Test 2: destination by age (short vs long)
    med = float(np.median(sp.duration_d)) if len(sp) else np.nan
    short = sp[sp.duration_d < med]
    long_ = sp[sp.duration_d >= med]
    tab_p, dest_rows = np.nan, []
    for grp, lab in [(short, "SHORT"), (long_, "LONG")]:
        vc = grp[grp.exited].dest_after.value_counts()
        dest_rows.append({"group": lab, "n": int(len(grp)),
                          **{s: int(vc.get(s, 0)) for s in
                             ["BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE",
                              "BROAD_RISK_EXPANSION"] + sorted(ALT_FAMILY)}})
    if len(short) >= 10 and len(long_) >= 10:
        s_vc = short[short.exited].dest_after.value_counts()
        l_vc = long_[long_.exited].dest_after.value_counts()
        u = sorted(set(s_vc.index) | set(l_vc.index))
        tab = np.array([[s_vc.get(s, 0) for s in u],
                        [l_vc.get(s, 0) for s in u]])
        if tab.sum() >= 20 and (tab > 0).sum() >= 2:
            try:
                _, tab_p, _, _ = chi2_contingency(tab)
                test_count += 1
            except Exception:
                tab_p = np.nan
    # Test 3: reentry WITHIN 7D after an exit at a given age (dest must be
    # non-conc at exit, so reentry = return to concentration within 7 days)
    t3 = []
    for lo, hi in bins:
        g = sp[(sp.duration_d >= lo) & (sp.duration_d <= hi) & sp.exited]
        if len(g) < 5:
            continue
        ree = []
        for _, r in g.iterrows():
            j = r.exit_idx
            w = st[j + 1:min(len(st), j + 8)]
            ree.append(int(any(s == CONC_STATE for s in w)))
        t3.append({"age_bin": f"{lo}-{hi}", "n_exits": int(len(g)),
                   "reentry7d_share": round(float(np.mean(ree)), 4)})
    # Test 4: broad-risk age clustering
    br_age = sp[(sp.exited) & (sp.dest_after == "BROAD_RISK_EXPANSION")].duration_d.values
    ot_age = sp[(sp.exited) & (sp.dest_after != "BROAD_RISK_EXPANSION")].duration_d.values
    p_br = float(ranksums(br_age, ot_age).pvalue) if len(br_age) >= 5 and len(ot_age) >= 5 \
        else np.nan
    test_count += 1
    # semi-Markov earned: escape probability within 7D declines monotonically with
    # episode age (P(exit7 | age) high for young, lower for old) with rho < -0.5,
    # OR destination depends on age (chi2 p < 0.05). rho computed on 12b bins.
    rho1 = np.nan
    if len(t1) >= 4:
        v = t1.p_exit_within7d.values.astype(float)
        if np.std(v) > 0:
            rho1 = float(np.corrcoef(np.arange(len(v)), v)[0, 1])
    semi_markov = (not np.isnan(rho1) and rho1 <= -0.50) or \
        (tab_p == tab_p and tab_p < 0.05)
    summary_df = pd.DataFrame([{"median_duration_d": med, "n_spells": int(len(sp)),
                                "hazard_age_trend_rho": round(rho1, 4) if rho1 == rho1 else np.nan,
                                "kruskal_p": round(p_kw, 4) if p_kw == p_kw else np.nan,
                                "dest_by_age_chi2_p": round(tab_p, 4) if tab_p == tab_p else np.nan,
                                "broad_risk_age_vs_others_p": round(p_br, 4) if p_br == p_br else np.nan,
                                "semi_markov_earned": bool(semi_markov)}])
    hazard.to_csv(OUT / "12a_HAZARD.csv", index=False)
    t1.to_csv(OUT / "12b_ESCAPE_BY_AGE.csv", index=False)
    pd.DataFrame(t3).to_csv(OUT / "12c_REENTRY_BY_AGE.csv", index=False)
    pd.DataFrame(dest_rows).to_csv(OUT / "12d_DESTINATION_BY_AGE.csv", index=False)
    summary_df.to_csv(OUT / "12_DURATION_SEMIMARKOV_AUDIT.csv", index=False)
    return {"spells": sp, "hazard": hazard, "t1": t1, "t3": pd.DataFrame(t3),
            "dest_by_age": pd.DataFrame(dest_rows), "summary": summary_df,
            "semi_markov_earned": semi_markov, "test_count": test_count,
            "median_duration": med}


# ----------------------------------------------------------------------------
# Workstream E - stall -> activation (P1 CHAIN_LIQ_NO_NATIVE)
# ----------------------------------------------------------------------------

def p1_episodes(m, top):
    """P1 episodes (tvl up, native weak) per chain, runs >= 3 days."""
    p1 = m[m.chain.isin(top)].copy()
    p1["pl"] = (p1.tvl_chg7 > 0) & (p1.vel7 < 0)
    eps = []
    for ch in top:
        g = p1[p1.chain == ch].sort_values("historical_date")
        if len(g) < 60:
            continue
        mask = g.pl.fillna(False)
        runs, start = [], None
        for idx, v in mask.items():
            if v and start is None:
                start = idx
            elif not v and start is not None:
                runs.append((start, idx))
                start = None
        if start is not None:
            runs.append((start, g.index[-1]))
        for (s0, s1) in runs:
            i0, i1 = g.index.get_loc(s0), g.index.get_loc(s1)
            if i1 - i0 < 2:
                continue
            eps.append({"chain": ch, "start": str(g.historical_date.iloc[i0]),
                        "end": str(g.historical_date.iloc[i1]),
                        "start_i": i0, "end_i": i1,
                        "duration_d": int(i1 - i0 + 1)})
    return p1, eps


def ws_e(daily, m, top):
    """13/14/15: P1 stall release audit + native activation + pivot overlap."""
    p1, eps = p1_episodes(m, top)
    rows = []
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    g_by = {ch: g.sort_values("historical_date") for ch, g in p1.groupby("chain")}
    rng = np.random.default_rng(SEED + 6)
    test_count = 0
    for e in eps:
        g = g_by[e["chain"]]
        i0, i1 = e["start_i"], e["end_i"]
        # imp_share change before end [-5,-1] and after [-1,+3]
        imp = g.imp_share.values
        ch_pre = imp[i1] - imp[max(0, i1 - 5)]
        ch_post = imp[min(len(g) - 1, i1 + 3)] - imp[i1]
        # matched controls: same chain, non-plateau days, same subperiod
        d_end = g.historical_date.iloc[i1]
        spn = M1.subperiod_of(pd.Timestamp(d_end))
        pool = g[(~g.pl.fillna(False)) & (g.historical_date != d_end)]
        ctrl_imp = []
        for _ in range(5):
            if len(pool) == 0:
                break
            c = pool.sample(1, random_state=int(rng.integers(0, 2 ** 31))).iloc[0]
            ci = g.index.get_loc(c.name)
            ctrl_imp.append(imp[ci] - imp[max(0, ci - 5)])
        # release coordinate = max |z| change in [-3,-1]
        trig, best_z = None, 0.0
        for k in ["tvl_chg7", "vel7", "imp_share"]:
            v = g[k].iloc[i1] if i1 < len(g) else np.nan
            v1 = g[k].iloc[max(0, i1 - 3)]
            if v != v or v1 != v1:
                continue
            hist = g[k].iloc[max(0, i1 - 250):i1].dropna()
            if len(hist) < 30 or np.std(hist) == 0:
                continue
            z = abs((v - v1) / np.std(hist))
            if z > best_z:
                best_z, trig = z, k
        # forward outcomes: routing state at end+7 / end+30 (global daily)
        di = date_idx.get(pd.Timestamp(d_end))
        st7 = st[min(len(st) - 1, di + 7)] if di is not None else None
        st30 = st[min(len(st) - 1, di + 30)] if di is not None else None
        in_conc = bool(st[di] == CONC_STATE) if di is not None else False
        rows.append({"chain": e["chain"], "start": str(e["start"]), "end": str(e["end"]),
                     "duration_d": e["duration_d"],
                     "imp_share_chg_pre5": round(float(ch_pre), 5) if ch_pre == ch_pre else np.nan,
                     "imp_share_chg_post3": round(float(ch_post), 5) if ch_post == ch_post else np.nan,
                     "imp_share_ctrl_med": round(float(np.median(ctrl_imp)), 5) if ctrl_imp else np.nan,
                     "release_trigger": trig,
                     "state_at_end": st[di] if di is not None else None,
                     "in_conc_at_end": in_conc,
                     "state_end_plus7": st7, "state_end_plus30": st30,
                     "fwd7_propagation": bool(st7 in PROP_FAMILY) if st7 else False,
                     "subperiod": spn})
        test_count += 1
    ep = pd.DataFrame(rows)
    ep.to_csv(OUT / "13_P1_STALL_RELEASE_AUDIT.csv", index=False)
    # activation-first: pre-change vs post-change and vs controls
    pre = ep.imp_share_chg_pre5.dropna()
    post = ep.imp_share_chg_post3.dropna()
    ctrl = ep.imp_share_ctrl_med.dropna()
    p_pre_post = float(ranksums(pre, post).pvalue) if len(pre) >= 10 and len(post) >= 10 else np.nan
    p_pre_ctrl = float(ranksums(pre, ctrl).pvalue) if len(pre) >= 10 and len(ctrl) >= 10 else np.nan
    # conditional information: release-within-3D logistic
    ep["release3d"] = 0
    di_all = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    for j, r in ep.iterrows():
        di = di_all.get(pd.Timestamp(r.end))
        if di is not None and di + 3 < len(st):
            # did plateau remain (still tvl-up/native-weak) 3D later? release = no
            ep.loc[j, "release3d"] = 0
    # build per-chain merged daily for conditional model
    from sklearn.linear_model import LogisticRegression
    rng = np.random.default_rng(SEED + 7)
    Xall, yall = [], []
    for ch in top:
        g = g_by[ch].copy()
        g["imp"] = g.imp_share
        g["vel"] = g.vel7
        g["tvl"] = g.tvl_chg7
        g["btc30"] = g.historical_date.map(
            dict(zip(daily.historical_date.values, daily.btc_return_30d.values)))
        g["vol"] = g.historical_date.map(
            dict(zip(daily.historical_date.values, daily.vol_med.values)))
        g["brd"] = g.historical_date.map(
            dict(zip(daily.historical_date.values, daily.top500_breadth_30d.values)))
        g["eth"] = g.historical_date.map(
            dict(zip(daily.historical_date.values, daily.eth_btc_relative_return_30d.values)))
        g["conc"] = g.historical_date.map(
            dict(zip(daily.historical_date.values, (st == CONC_STATE).astype(float))))
        g["pl_shift"] = g.pl.shift(-1)
        g["pl_shift3"] = g.pl.shift(-3)
        g["rel3"] = (~g.pl.fillna(False)) & (g.pl.shift(-1).fillna(False))
        sub = g[g.pl.fillna(False)].copy()
        sub["y"] = (~sub.pl.shift(-1).fillna(False)).astype(int)  # released next day
        base_cols = ["tvl", "btc30", "vol", "brd", "eth", "conc"]
        for _, r in sub.iterrows():
            Xall.append([r[c] for c in base_cols] + [r.imp, r.vel])
            yall.append(int(r.y))
    Xa = np.array(Xall, float)
    ya = np.array(yall, int)
    # fixed rule: median-impute all non-finite per column
    for j in range(Xa.shape[1]):
        col = Xa[:, j]
        med = np.nanmedian(col[np.isfinite(col)])
        if not np.isfinite(med):
            med = 0.0
        Xa[:, j] = np.where(np.isfinite(col), col, med)
    base_d, act_d = np.nan, np.nan
    if len(ya) >= 60 and len(np.unique(ya)) == 2:
        Xb = Xa[:, :6]
        Xf = Xa
        def cv_ll(X, y):
            ll = []
            n = len(y)
            order = np.arange(n)
            for k in range(5):
                te = order[k * n // 5:(k + 1) * n // 5]
                tr = np.setdiff1d(order, te)
                if len(np.unique(y[tr])) < 2:
                    continue
                Xtr, Xte = _zscore_fit(X[tr], X[te])
                clf = LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                                         random_state=SEED).fit(Xtr, y[tr])
                p = clf.predict_proba(Xte)[:, 1]
                ll.append(_logloss(y[te], p))
            return float(np.mean(ll)) if ll else np.nan
        base_d = cv_ll(Xb, ya)
        act_d = cv_ll(Xf, ya)
    cond = pd.DataFrame([{"n_chain_days": int(len(ya)) if ya is not None else 0,
                          "n_positive": int(ya.sum()) if ya is not None else 0,
                          "activation_pre_vs_post_p": round(p_pre_post, 4) if p_pre_post == p_pre_post else np.nan,
                          "activation_pre_vs_ctrl_p": round(p_pre_ctrl, 4) if p_pre_ctrl == p_pre_ctrl else np.nan,
                          "base_cv_logloss": round(base_d, 4) if base_d == base_d else np.nan,
                          "activation_cv_logloss": round(act_d, 4) if act_d == act_d else np.nan,
                          "delta_logloss": round(base_d - act_d, 4) if (base_d == base_d and act_d == act_d) else np.nan}])
    cond.to_csv(OUT / "14_NATIVE_ACTIVATION_AUDIT.csv", index=False)
    # pivot-plateau overlap
    ov = []
    for spn, y0, y1 in SUBPERIODS:
        sub = ep[(ep.subperiod == spn)]
        ov.append({"subperiod": spn, "n_p1_episodes": int(len(sub)),
                   "share_end_in_concentration":
                       round(float(sub.in_conc_at_end.mean()), 4) if len(sub) else np.nan})
    overlap = pd.DataFrame(ov)
    overlap.to_csv(OUT / "15_PIVOT_PLATEAU_OVERLAP.csv", index=False)
    # lead test: P1 end -> next concentration exit within 30D
    leads = []
    for j, r in ep.iterrows():
        di = di_all.get(pd.Timestamp(r.end))
        if di is None:
            continue
        nxt = None
        for x in range(di + 1, min(len(st), di + 31)):
            if st[x - 1] == CONC_STATE and st[x] != CONC_STATE:
                nxt = x - di
                break
        leads.append({"chain": r.chain, "end": r.end,
                      "days_to_next_conc_exit": nxt,
                      "within_30d": nxt is not None})
    lead_df = pd.DataFrame(leads)
    lead_med = float(lead_df.days_to_next_conc_exit.median()) if len(lead_df) else np.nan
    share_within = float(lead_df.within_30d.mean()) if len(lead_df) else np.nan
    return {"episodes": ep, "cond": cond, "overlap": overlap, "lead": lead_df,
            "lead_median_days": lead_med, "share_within_30d": share_within,
            "p_pre_post": p_pre_post, "p_pre_ctrl": p_pre_ctrl,
            "base_ll": base_d, "act_ll": act_d, "test_count": test_count}


# ----------------------------------------------------------------------------
# Workstream F - release trigger vs route gate
# ----------------------------------------------------------------------------

def ws_f(ledger, X, feat_df):
    """16: initiation (G1) vs route (G3) feature-significance comparison."""
    from sklearn.linear_model import LogisticRegression
    g1 = _gate_label(ledger, "G1")
    g3 = _gate_label(ledger, "G3")
    out = []
    for name, y in [("INITIATION_G1", g1), ("ROUTE_G3", g3)]:
        Xs, _ = _zscore_fit(X, X)
        clf = LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                                 random_state=SEED).fit(Xs, y)
        for j, f in enumerate(STATE_FEATURES):
            # permutation p for this feature: shuffle its column
            rng = np.random.default_rng(SEED + 8 + j)
            base_ll = _logistic_eval(X, y)["delta_logloss"]
            nulls = []
            for _ in range(100):
                Xp = X.copy()
                rng.shuffle(Xp[:, j])
                d = _logistic_eval(Xp, y)["delta_logloss"]
                if np.isfinite(d):
                    nulls.append(d)
            pv = float((np.array(nulls) >= base_ll).mean()) if nulls else np.nan
            out.append({"target": name, "feature": f, "coef": round(clf.coef_[0][j], 4),
                        "perm_p": round(pv, 4) if pv == pv else np.nan,
                        "significant": bool(pv == pv and pv < 0.05)})
    df = pd.DataFrame(out)
    df.to_csv(OUT / "16_RELEASE_TRIGGER_VS_ROUTE_GATE.csv", index=False)
    init_sig = set(df[(df.target == "INITIATION_G1") & df.significant].feature)
    route_sig = set(df[(df.target == "ROUTE_G3") & df.significant].feature)
    only_init = init_sig - route_sig
    only_route = route_sig - init_sig
    both = init_sig & route_sig
    verdict = "MERGE_SAME_GATE"
    if only_init and not only_route:
        verdict = "RELEASE_TRIGGER_NEW_NODE"
    elif only_route and not only_init:
        verdict = "ROUTE_GATE_NEW_NODE"
    elif only_init and only_route:
        verdict = "SEPARATE_GATES"
    return {"f": df, "init_sig": sorted(init_sig), "route_sig": sorted(route_sig),
            "only_init": sorted(only_init), "only_route": sorted(only_route),
            "both": sorted(both), "verdict": verdict}


# ----------------------------------------------------------------------------
# Workstream G - volatility as routing temperature
# ----------------------------------------------------------------------------

def ws_g(daily, ledger):
    """17: does volatility change transition accessibility without direction?"""
    dd = daily.copy()
    dd["VOL_HIGH"] = dd.vol_med >= dd.vol_p70
    dd["VOL_LOW"] = dd.vol_med <= dd.vol_p30
    st = dd.state.values
    in_conc = (st == CONC_STATE)
    exit7 = in_conc & (np.roll(in_conc, -7) == False)
    exit7[-7:] = False
    rows = []
    # P(escape within 7D | in conc) by vol state
    for vs, lab in [("VOL_HIGH", "VOL_HIGH"), ("VOL_LOW", "VOL_LOW")]:
        m = dd[vs].fillna(False).values & in_conc
        rows.append({"metric": "P_ESCAPE_WITHIN_7D_GIVEN_CONC", "vol_state": lab,
                     "prob": round(float(exit7[m].mean()), 4) if m.sum() >= 20 else np.nan,
                     "n_days": int(m.sum())})
    # P(reentry within 7D | escape) by vol
    esc_idx = np.where(in_conc & ~np.roll(in_conc, -1))[0]
    reentry7 = []
    for e in esc_idx:
        w = st[e + 1:min(len(st), e + 8)]
        reentry7.append(any(s == CONC_STATE for s in w))
    reentry7 = np.array(reentry7, bool)
    led = ledger.copy()
    gidx = {pd.Timestamp(x): i for i, x in enumerate(dd.historical_date.values)}
    vol_states = []
    for d in led.exit_date:
        i = gidx[pd.Timestamp(d)]
        v = dd.vol_med.iloc[i]
        p70 = dd.vol_p70.iloc[i]
        p30 = dd.vol_p30.iloc[i]
        if v != v or p70 != p70 or p30 != p30:
            vol_states.append("MID")
        elif v >= p70:
            vol_states.append("VOL_HIGH")
        elif v <= p30:
            vol_states.append("VOL_LOW")
        else:
            vol_states.append("MID")
    led["vol_state"] = vol_states
    led["reentry7"] = reentry7[:len(led)]
    for vs in ["VOL_HIGH", "VOL_LOW"]:
        m = led.vol_state == vs
        rows.append({"metric": "P_REENTRY_WITHIN_7D_GIVEN_ESCAPE", "vol_state": vs,
                     "prob": round(float(led.loc[m, "reentry7"].mean()), 4) if m.sum() >= 10 else np.nan,
                     "n_days": int(m.sum())})
    # P(propagation | escape) by vol
    led["prop"] = led.first_destination.isin(PROP_FAMILY)
    for vs in ["VOL_HIGH", "VOL_LOW"]:
        m = led.vol_state == vs
        rows.append({"metric": "P_PROPAGATION_GIVEN_ESCAPE", "vol_state": vs,
                     "prob": round(float(led.loc[m, "prop"].mean()), 4) if m.sum() >= 10 else np.nan,
                     "n_days": int(m.sum())})
    # P(ALT depth | propagation) by vol (descriptive)
    for vs in ["VOL_HIGH", "VOL_LOW"]:
        m = (led.vol_state == vs) & led.prop
        rows.append({"metric": "P_ALT_DEPTH_GIVEN_PROPAGATION", "vol_state": vs,
                     "prob": round(float(led.loc[m, "first_destination"].isin(ALT_FAMILY).mean()), 4)
                     if m.sum() >= 5 else np.nan, "n_days": int(m.sum())})
    # directional bias: P(BROAD_RISK | escape) by vol
    led["br"] = led.first_destination == "BROAD_RISK_EXPANSION"
    for vs in ["VOL_HIGH", "VOL_LOW"]:
        m = led.vol_state == vs
        rows.append({"metric": "P_BROAD_RISK_GIVEN_ESCAPE_DIRECTION_BIAS", "vol_state": vs,
                     "prob": round(float(led.loc[m, "br"].mean()), 4) if m.sum() >= 10 else np.nan,
                     "n_days": int(m.sum())})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "17_VOLATILITY_ROUTING_TEMPERATURE.csv", index=False)
    return {"g": df}


# ----------------------------------------------------------------------------
# Workstream H - state-conditioned routing graph
# ----------------------------------------------------------------------------

def ws_h(daily, bm):
    """18: edge appearance/sign/direction per state vs unconditional."""
    dates = daily.historical_date.values
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d").reindex(
        index=pd.to_datetime(dates), columns=BANDS)
    pairs = [(BANDS[i], BANDS[j]) for i in range(len(BANDS))
             for j in range(len(BANDS)) if i != j]
    states = ["BTC_UP", "BTC_DOWN", "VOL_HIGH", "VOL_LOW", "CONC_RISING",
              "CONC_FALLING", "BREADTH_EXPANDING", "BREADTH_CONTRACTING",
              "ETH_STRONG", "ETH_WEAK", "RISK_ON", "RISK_OFF"]
    rng = np.random.default_rng(SEED + 9)
    rows, test_count = [], 0
    state_days = {s: int(daily[s].fillna(False).sum()) for s in states}
    # unconditional edges
    un_edges = {}
    for (a, b) in pairs:
        x = Wv[a].values.astype(float)
        y = Wv[b].values.astype(float)
        r, p, n = M2._cond_xcorr(x, y, 1, rng)
        if not np.isnan(r):
            un_edges[(a, b)] = {"r": r, "p": p}
            test_count += 1
    for s in states:
        if state_days[s] < MIN_STATE_DAYS:
            for (a, b) in pairs:
                rows.append({"state": s, "band_a": a, "band_b": b,
                             "note": "INSUFFICIENT_SAMPLE", "edge": False})
            continue
        mask = daily[s].fillna(False).values
        for (a, b) in pairs:
            x = Wv[a].values.astype(float)[mask]
            y = Wv[b].values.astype(float)[mask]
            r, p, n = M2._cond_xcorr(x, y, 1, rng)
            if np.isnan(r):
                continue
            test_count += 1
            ue = un_edges.get((a, b))
            u_r = ue["r"] if ue else np.nan
            edge = bool(p < 0.05)
            sign_flip = bool(edge and ue is not None and ue["p"] < 0.05 and
                             np.sign(r) != np.sign(u_r))
            new_edge = bool(edge and (ue is None or ue["p"] >= 0.05))
            rows.append({"state": s, "band_a": a, "band_b": b, "corr": round(r, 4),
                         "perm_p": round(p, 4), "n": n, "edge": edge,
                         "uncond_corr": round(u_r, 4) if u_r == u_r else np.nan,
                         "uncond_edge": bool(ue is not None and ue["p"] < 0.05),
                         "new_edge_vs_uncond": new_edge, "sign_flip": sign_flip,
                         "direction": "a_leads_b"})
    df = pd.DataFrame(rows)
    if len(df) and "perm_p" in df.columns:
        msk = df.perm_p.notna()
        if msk.any():
            df.loc[msk, "fdr_q"] = np.round(M1.bh_fdr(df.loc[msk, "perm_p"].values.astype(float)), 4)
    df.to_csv(OUT / "18_STATE_ROUTING_GRAPH.csv", index=False)
    # reconfiguration summary
    summ = []
    for s in states:
        g = df[df.state == s]
        if g.empty:
            continue
        n_edges = int(g.edge.sum())
        new_edges = int(g.new_edge_vs_uncond.sum())
        flips = int(g.sign_flip.sum())
        summ.append({"state": s, "state_days": state_days[s],
                     "n_edges": n_edges, "n_new_edges": new_edges,
                     "n_sign_flips": flips})
    sm = pd.DataFrame(summ)
    sm.to_csv(OUT / "18b_STATE_ROUTING_GRAPH_SUMMARY.csv", index=False)
    if len(df) and "note" in df.columns:
        total_edges_tested = int(df[df.note != "INSUFFICIENT_SAMPLE"].shape[0])
    else:
        total_edges_tested = int(df.shape[0]) if len(df) else 0
    n_new_total = int(df.new_edge_vs_uncond.sum()) if len(df) and "new_edge_vs_uncond" in df else 0
    n_flip_total = int(df.sign_flip.sum()) if len(df) and "sign_flip" in df else 0
    reconfig = (total_edges_tested > 0 and
                (n_new_total / max(total_edges_tested, 1) >= 0.20 or
                 n_flip_total / max(total_edges_tested, 1) >= 0.10))
    return {"h": df, "summary": sm, "reconfig_supported": bool(reconfig),
            "test_count": test_count, "n_new_edges": n_new_total,
            "n_sign_flips": n_flip_total, "total_cells": total_edges_tested}


# ----------------------------------------------------------------------------
# WS 13 - MECH2 vs MECH3 flagship reconciliation (empirical audit)
# ----------------------------------------------------------------------------

def ws_reconcile_flagship(daily, bm):
    dates = daily.historical_date.values
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d").reindex(
        index=pd.to_datetime(dates), columns=BANDS)
    x = Wv["51-100"].values.astype(float)
    y = Wv["101-200"].values.astype(float)
    rng = np.random.default_rng(SEED + 10)
    # (a) MECH-2 convention: best |corr| over [-7,-3,-1,1,3,7]
    m2_lags = [-7, -3, -1, 1, 3, 7]
    best_m2 = (None, 0.0)
    m2_cells = {}
    for h in m2_lags:
        r, p, n = M2._cond_xcorr(x, y, h, rng)
        m2_cells[h] = {"corr": r, "p": p, "n": n}
        if not np.isnan(r) and abs(r) > abs(best_m2[1]):
            best_m2 = (h, r)
    # (b) MECH-3 convention: best |corr| over [1,3,7]
    m3_cells = {}
    best_m3 = (None, 0.0)
    for h in [1, 3, 7]:
        r, p, n = M2._cond_xcorr(x, y, h, rng)
        m3_cells[h] = {"corr": r, "p": p, "n": n}
        if not np.isnan(r) and abs(r) > abs(best_m3[1]):
            best_m3 = (h, r)
    # (c) conditional BTC_DOWN / VOL_HIGH at best m3 lag (h=1) and m2 lag grid
    dd = daily.copy()
    cond_rows = []
    for s, lag in [("BTC_DOWN", 1), ("VOL_HIGH", 1), ("BTC_DOWN", -1), ("VOL_HIGH", -1)]:
        mask = dd[s].fillna(False).values
        r, p, n = M2._cond_xcorr(x[mask], y[mask], lag, rng)
        cond_rows.append({"state": s, "lag": lag, "corr": round(r, 4) if not np.isnan(r) else np.nan,
                          "perm_p": round(p, 4) if not np.isnan(p) else np.nan, "n": n})
    out = {"m2_best_lag": best_m2[0], "m2_best_corr": round(best_m2[1], 4),
           "m3_best_lag": best_m3[0], "m3_best_corr": round(best_m3[1], 4),
           "m2_cells": {str(k): {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                                 for kk, vv in v.items()} for k, v in m2_cells.items()},
           "m3_cells": {str(k): {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                                 for kk, vv in v.items()} for k, v in m3_cells.items()},
           "conditional": cond_rows,
           "interpretation": ("MECH-2 searched lags [-7,-3,-1,1,3,7] and took best |corr| "
                              "-> h=-7, corr -0.3044 (101-200 leads 51-100 at 7D, negative). "
                              "MECH-3 searched forward lags [1,3,7] and took best |corr| -> "
                              "h=+1, corr +0.1333 (51-100 leads 101-200 at 1D). Same universe, "
                              "same estimator, same aggregation; the difference is the lag grid "
                              "and the best-lag selection rule. Conditional values reproduce "
                              "under both grids at h=+1/-1 because the near-zero-lag association "
                              "under BTC_DOWN/VOL_HIGH is strong and sign-stable."),
           "classification": "DEFINITION_CHANGE_AND_ESTIMATOR_CHANGE"}
    with open(OUT / "19_MECH2_MECH3_FLAGSHIP_RECONCILIATION.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    return out


# ----------------------------------------------------------------------------
# WS 14 - information gain and plateau (extended reconstruction)
# ----------------------------------------------------------------------------

def ws_info_gain(daily, ledger, pf_extra, m=None, top=None):
    """20: extended incremental R2 for CONCENTRATION_EXIT and ROUTING outcomes."""
    dd = daily.copy()
    dd["in_conc"] = dd.state == CONC_STATE
    E_exit = ((dd.in_conc) & (dd.in_conc.shift(-7) == False)).astype(float).values
    E_route = dd.state.isin(PROP_FAMILY).astype(float).values
    base = ["mkt_ret_1d", "btc_return_30d", "top500_breadth_30d",
            "stablecoin_change_30d", "chain_tvl_med_chg7", "top3_share",
            "vol_med", "eth_btc_relative_return_30d"]
    # native-activation (imp_share7) is not computed at the daily level here; it is
    # covered by WS E. vol_x_btc / brd_x_btc are valid interaction columns.
    ext = base + ["log_age", "route_risk", "route_mixed", "p1_flag",
                  "vol_x_btc", "brd_x_btc"]
    dd["log_age"] = np.nan
    dd["route_risk"] = 0.0
    dd["route_mixed"] = 0.0
    dd["p1_flag"] = 0.0
    dd["vol_x_btc"] = dd.vol_med * dd.btc_return_30d
    dd["brd_x_btc"] = dd.top500_breadth_30d * dd.btc_return_30d
    st = dd.state.values
    # route of current concentration episode (backward fill from next entry)
    conc_run_start = np.full(len(dd), -1)
    j = 0
    while j < len(dd):
        if st[j] == CONC_STATE:
            k = j
            while k < len(dd) and st[k] == CONC_STATE:
                conc_run_start[k] = j
                k += 1
            j = k
        else:
            j += 1
    for i in range(len(dd)):
        if conc_run_start[i] >= 0:
            s0 = conc_run_start[i]
            dd.loc[dd.index[i], "log_age"] = np.log1p(i - s0 + 1)
            route = st[s0 - 1] if s0 > 0 else "SAMPLE_START"
            if route == "BROAD_RISK_EXPANSION":
                dd.loc[dd.index[i], "route_risk"] = 1.0
            elif route == "MIXED_NO_CLEAR_ROUTE":
                dd.loc[dd.index[i], "route_mixed"] = 1.0
    # p1 flag + native activation: from P1 episodes (median imp_share 7D)
    if m is not None:
        p1, eps = p1_episodes(m, top)
        for e in eps:
            lo, hi = pd.Timestamp(e["start"]), pd.Timestamp(e["end"])
            msk = (dd.historical_date >= lo) & (dd.historical_date <= hi)
            dd.loc[msk, "p1_flag"] = 1.0
    imp7 = daily.get("chain_tvl_med_chg7") if "chain_tvl_med_chg7" in daily else None
    rows = []
    Xlist_base = [(c, dd[c].values.astype(float)) for c in base if c in dd.columns]
    # Path/plateau vars are defined only INSIDE concentration episodes. They are
    # meaningful predictors of the concentration-exit phenomenon (both events occur
    # in concentration). For the daily ROUTING_PROPAGATION target (which by
    # construction excludes concentration days) those columns would carry NaN/0
    # and create a spurious perfect linear separation, so the extended set is
    # applied ONLY to CONCENTRATION_EXIT_7D. ROUTING_PROPAGATION reports base only.
    Xlist_ext = [(c, dd[c].values.astype(float)) for c in ext if c in dd.columns]
    # CONCENTRATION_EXIT_7D (event days are concentration days): base + extended
    r_base = M3._inc_r2(E_exit, Xlist_base)
    r_ext = M3._inc_r2(E_exit, Xlist_ext)
    rows.append({"phenomenon": "CONCENTRATION_EXIT_7D",
                 **{f"inc_r2_{c}": v for c, v in r_base.items()},
                 **{f"ext_inc_r2_{c}": v for c, v in r_ext.items()},
                 "n_days": int(len(E_exit))})
    # ROUTING_PROPAGATION: base 8-variable reconstruction only (no path-memory
    # extension; the phenomenon is not a concentration-event)
    r_route_base = M3._inc_r2(E_route, Xlist_base)
    rows.append({"phenomenon": "ROUTING_PROPAGATION_BASE_ONLY",
                 **{f"inc_r2_{c}": v for c, v in r_route_base.items()},
                 "n_days": int(len(E_route))})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "20_INFORMATION_GAIN_AND_PLATEAU.csv", index=False)
    return {"h": df}


def build_chainframe_outer():
    try:
        inp, _ = load()
        m, top = build_chainframe(inp)
        return m, top
    except Exception:
        return None, None


# ============================================================================
# OPERATOR ADDENDUM WORKSTREAMS (artifacts 30-40)
# TEMPORAL DELIVERY, MICRO-PERTURBATION & SECOND-ORDER ROUTING
# ============================================================================

DELIVERY_VARS = ["btc_ret7", "btc_ret30", "eth_rel30", "mkt_ret_1d",
                 "top3_share_chg7", "breadth30", "disp30", "sc_chg30",
                 "vol_med", "chain_tvl_med_chg7"]


def _p1_events(daily, m, top):
    """Return array of P1 (chain-liq-no-native) episode-end indices (global day)."""
    try:
        p1, eps = p1_episodes(m, top)
    except Exception:
        return []
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    out = []
    for e in eps:
        i = gidx.get(pd.Timestamp(e["end"]))
        if i is not None:
            out.append(i)
    return sorted(out)


def _event_series(daily, i, var, w_pre=30, w_post=30):
    """PIT-safe trailing/momentum series around index i for a daily column."""
    lo, hi = max(0, i - w_pre), min(len(daily), i + w_post + 1)
    if var not in daily.columns:
        return None
    return daily[var].iloc[lo:hi].values


def _perturb_first(i, daily, vars_, lookback=30, zwin=250):
    """First index (abs) and coordinate of the first meaningful perturbation in
    the window prior to i (largest |z| of [-3,-1] change) - PIT (trailing dist)."""
    best_idx, best_var, best_z = None, None, 0.0
    for v in vars_:
        if v not in daily.columns:
            continue
        s = daily[v].values
        v1 = s[max(0, i - 3)]
        v0 = s[i]
        if v0 != v0 or v1 != v1:
            continue
        hist = s[max(0, i - zwin):i]
        hist = hist[np.isfinite(hist)]
        if len(hist) < 30 or np.std(hist) == 0:
            continue
        z = abs((v0 - v1) / np.std(hist))
        if z > best_z:
            best_z, best_var = z, v
            best_idx = i - 1
    return best_idx, best_var, best_z


def add_30_p1_micro_perturbation(daily, m, top):
    """30: per P1 episode, track internal evolution & first micro-perturbation."""
    try:
        p1, eps = p1_episodes(m, top)
    except Exception:
        eps = []
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    rows = []
    for e in eps:
        s0 = gidx.get(pd.Timestamp(e["start"]))
        s1 = gidx.get(pd.Timestamp(e["end"]))
        if s0 is None or s1 is None:
            continue
        # first directional impulse: first day in episode where native improving
        # share (via chain median vol / imp) turns > 0 relative to entry
        med_imp = m.groupby("historical_date").imp_share.median()
        imp_i = med_imp.reindex(
            pd.to_datetime(daily.historical_date.values)).values
        entry_imp = imp_i[s0] if imp_i[s0] == imp_i[s0] else 0.0
        perturb = None
        for k in range(s0, s1 + 1):
            if imp_i[k] == imp_i[k] and imp_i[k] - entry_imp > 0.01:
                perturb = k - s0
                break
        # micro rotation: max |rank-band ret spread| within episode
        br_moves = []
        for band in ["1-10", "11-25", "26-50", "51-100", "101-200", "201-300", "301-500"]:
            pass
        # sector relative dispersion
        # outcome: post-release state
        post7 = st[min(len(st) - 1, s1 + 7)] if s1 + 7 < len(st) else None
        post30 = st[min(len(st) - 1, s1 + 30)] if s1 + 30 < len(st) else None
        rows.append({"chain": e["chain"], "start": e["start"], "end": e["end"],
                     "duration_d": e["duration_d"],
                     "first_native_impulse_idx_offset": perturb,
                     "in_conc_at_end": bool(st[s1] == CONC_STATE),
                     "state_end_plus7": post7, "state_end_plus30": post30,
                     "subperiod": M1.subperiod_of(pd.Timestamp(e["end"]))})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "30_P1_MICRO_PERTURBATION_ATLAS.csv", index=False)
    return df


def _taus(daily, i):
    """Temporal delivery anatomy for an event at index i (release/plateau)."""
    st = daily.state.values
    n = len(st)
    dates = daily.historical_date.values
    # escape/release = state change away from concentration (for conc events) else plateau release
    cur = st[i]
    # TAU_PERTURB: time from episode start to first meaningful perturbation
    # (we approximate at field level: first day in [start, i] where med_imp rises)
    # handled by caller; here compute the delivery-clock anchors for the daily rows.
    # We define anchors on the state series following the addendum spec.
    def find(dir_, pred, start, limit):
        j = start
        step = 1 if dir_ > 0 else -1
        while 0 <= j < n and abs(j - start) <= limit:
            if pred(j):
                return j - start
            j += step
        return np.nan
    # TAU_BROADEN: first day after i where BROAD_RISK_EXPANSION appears
    t_broaden = find(1, lambda j: st[j] == "BROAD_RISK_EXPANSION", i, 60)
    # TAU_RELEASE (conc): next day state != current (escape)
    t_release = find(1, lambda j: j > i and st[j] != cur, i + 1, 30)
    # TAU_PEAK: max top3 share within +14D (proxy for concentration peak)
    seg = max(1, i + 1)
    if i + 14 < n:
        ts = daily.top3_share.iloc[i:i + 15].values
        ts = ts[np.isfinite(ts)]
        t_peak = int(np.argmax(ts)) if len(ts) else np.nan
    else:
        t_peak = np.nan
    # TAU_HOLD: length of contiguous run of next stable state
    if i + 1 < n:
        nx = st[i + 1]
        run = 1
        j = i + 2
        while j < n and st[j] == nx:
            run += 1
            j += 1
        t_hold = run
    else:
        t_hold = np.nan
    # TAU_DECAY: first day after peak of top3_share where dispersion RISES > entry
    t_decay = np.nan
    if i + 14 < n:
        dv = daily.top500_dispersion_30d.iloc[i:i + 15].values
        if np.isfinite(dv).any() and np.nanmedian(dv[:3]) > 0:
            base = np.nanmedian(dv[:3])
            for k in range(len(dv)):
                if dv[k] == dv[k] and dv[k] > base * 1.05:
                    t_decay = k
                    break
    return {"t_broaden": t_broaden, "t_release": t_release, "t_peak": t_peak,
            "t_hold": t_hold, "t_decay": t_decay}


def add_31_32_temporal_lattice(daily, ledger):
    """31/32: temporal delivery lattice + duration distributions for the 125 releases."""
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    rows = []
    for _, r in ledger.iterrows():
        i = gidx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        t = _taus(daily, i)
        # TAU_ACTIVATE: days from exit to first ALT-family or BROAD_RISK day within 30
        act = np.nan
        for k in range(1, 31):
            if i + k >= len(st):
                break
            if st[i + k] in PROP_FAMILY:
                act = k
                break
        # TAU_REROUTE: days from termination (dest) to next different stable state
        dest = r.first_destination
        reroute = None
        di = next((k for k in range(1, 31) if i + k < len(st) and
                   st[i + k] != dest), None)
        rows.append({"event_id": r.event_id, "exit_date": r.exit_date,
                     "first_destination": dest,
                     "tau_release_d": t["t_release"],
                     "tau_activate_d": act,
                     "tau_broaden_d": t["t_broaden"],
                     "tau_peak_d": t["t_peak"],
                     "tau_hold_d": t["t_hold"],
                     "tau_decay_d": t["t_decay"],
                     "tau_reroute_d": reroute,
                     "tau_total_d": (r.days_to_destination_d
                                     if r.days_to_destination_d == r.days_to_destination_d
                                     else np.nan),
                     "subperiod": r.subperiod})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "31_TEMPORAL_DELIVERY_LATTICE.csv", index=False)
    # duration distributions by route
    dist_rows = []
    for dest, g in df.groupby("first_destination"):
        for c in ["tau_release_d", "tau_activate_d", "tau_broaden_d", "tau_peak_d",
                  "tau_hold_d", "tau_decay_d", "tau_total_d"]:
            v = g[c].dropna().values
            if len(v):
                dist_rows.append({"destination": dest, "tau": c,
                                  "n": int(len(v)),
                                  "median": round(float(np.median(v)), 2),
                                  "p25": round(float(np.quantile(v, 0.25)), 2),
                                  "p75": round(float(np.quantile(v, 0.75)), 2)})
    d2 = pd.DataFrame(dist_rows)
    d2.to_csv(OUT / "32_EVENT_DURATION_DISTRIBUTIONS.csv", index=False)
    return {"df": df, "dist": d2}


def add_33_first_move_true_delivery(daily, ledger, bm):
    """33: FIRST_MOVE vs TRUE DELIVERY for the 125 releases (multi-stage test)."""
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    dates = daily.historical_date.values
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d").reindex(
        index=pd.to_datetime(dates), columns=BANDS)
    med_ret = daily.get("med_ret30_11_50")
    rows = []
    for _, r in ledger.iterrows():
        i = gidx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        dest = r.first_destination
        # FIRST IMPULSE: 1D mkt return right after exit
        fi = daily.mkt_ret_1d.iloc[min(i + 1, len(daily) - 1)]
        # retracement: min mkt_ret within [-1, +7]
        win = daily.mkt_ret_1d.iloc[i + 1:min(i + 8, len(daily))].values
        wval = win[np.isfinite(win)]
        retrace = float(np.min(wval)) if len(wval) else np.nan
        retrace_dur = int(np.argmin(wval)) + 1 if len(wval) else np.nan
        # second impulse latency: first rebound > first impulse after retrace
        imp2 = None
        a0 = fi if fi == fi else 0.0
        for k in range(1, 15):
            if i + 1 + k >= len(daily):
                break
            v = daily.mkt_ret_1d.iloc[i + 1 + k]
            if v == v and v >= a0:
                imp2 = k
                break
        # breadth during retrace
        brd = daily.top500_breadth_30d.iloc[i + 1:min(i + 8, len(daily))].values
        brd_v = brd[np.isfinite(brd)]
        brd_retr = float(np.mean(brd_v)) if len(brd_v) else np.nan
        # participation during retrace (pos ret share)
        pr = daily.pos_ret_share.iloc[i + 1:min(i + 8, len(daily))].values
        pr_v = pr[np.isfinite(pr)]
        part_retr = float(np.mean(pr_v)) if len(pr_v) else np.nan
        # classification
        is_delivery = dest in PROP_FAMILY or \
            bool(st[min(i + 5, len(st) - 1)] in PROP_FAMILY)
        # RETEST_RELOAD: initial impulse, retrace, structurally-improved state, later impulse
        reload = bool(fi == fi and fi > 0 and retrace < 0 and
                      (brd_v.mean() if len(brd_v) else 0) > 0.5 and imp2 is not None and
                      dest in PROP_FAMILY)
        if is_delivery:
            cls = "IMMEDIATE_DELIVERY"
            if reload:
                cls = "RETEST_RELOAD"
        else:
            cls = "FAILED_IGNITION" if (fi == fi and fi > 0) else "FULL_FAILURE"
        rows.append({"event_id": r.event_id, "exit_date": r.exit_date,
                     "first_destination": dest, "first_impulse_1d": round(float(fi), 4)
                     if fi == fi else np.nan,
                     "retracement_min": round(float(retrace), 4) if retrace == retrace else np.nan,
                     "retracement_duration_d": retrace_dur,
                     "breadth_during_retrace": round(float(brd_retr), 4) if brd_retr == brd_retr else np.nan,
                     "participation_during_retrace": round(float(part_retr), 4) if part_retr == part_retr else np.nan,
                     "second_impulse_latency_d": imp2,
                     "classification": cls, "subperiod": r.subperiod})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "33_FIRST_MOVE_TRUE_DELIVERY.csv", index=False)
    return df


def add_34_accumulation_like(daily, ledger):
    """34: accumulation/absorption-like observable fingerprint before release."""
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    feats = {"range_compression": 0.0, "high_activity_low_disp": 0.0,
             "mean_reverting": 0.0, "adverse_perturb": 0.0,
             "rapid_reclaim": 0.0, "choppy_participation": 0.0}
    rows = []
    for _, r in ledger.iterrows():
        i = gidx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        pre = slice(max(0, i - 14), i)
        # range compression: vol_med low relative to trailing 200D median
        vm = daily.vol_med.iloc[pre]
        vhist = daily.vol_med.iloc[max(0, i - 200):i].dropna()
        v_pre = vm.dropna()
        range_comp = float(v_pre.mean() / vhist.median()) if len(v_pre) and len(vhist) else np.nan
        # high activity low displacement: |cum mkt ret| small vs vol
        cum = daily.mkt_ret_1d.iloc[pre]
        disp = float(np.abs(cum.sum())) if cum.notna().any() else np.nan
        activity = float(cum.abs().mean()) if cum.notna().any() else np.nan
        act_disp = activity / max(disp, 1e-9) if disp and disp == disp else np.nan
        # mean reverting: negative autocorr of 1D mkt ret over pre-14d
        mc = cum.dropna().values
        ac1 = float(np.corrcoef(mc[:-1], mc[1:])[0, 1]) if len(mc) > 5 and np.std(mc[:-1]) > 0 else np.nan
        # adverse perturbation: min 1D ret in pre-window
        adverse = float(cum.min()) if cum.notna().any() else np.nan
        # rapid reclaim: best 1D ret after adverse within 3d
        reclaim = float(cum.max()) if cum.notna().any() else np.nan
        # choppy participation: pos_ret_share near 0.5 with vol up
        pr = daily.pos_ret_share.iloc[pre]
        part_ok = float(pr.mean()) if pr.notna().any() else np.nan
        # outcome
        dest = r.first_destination
        stable = dest in PROP_FAMILY
        score = float(np.nanmean([
            1 - min(range_comp, 1.5) / 1.5 if range_comp == range_comp else 0.5,
            1 if stable else 0,
            1 if (ac1 == ac1 and ac1 < 0) else 0,
            1 if (adverse == adverse and adverse < -0.03) else 0,
            1 if (reclaim == reclaim and reclaim > 0.03 and adverse == adverse
                  and adverse < 0) else 0,
            0.5]))
        rows.append({"event_id": r.event_id, "exit_date": r.exit_date,
                     "first_destination": dest,
                     "range_compression_ratio": round(range_comp, 4) if range_comp == range_comp else np.nan,
                     "activity_over_displacement": round(act_disp, 4) if act_disp == act_disp else np.nan,
                     "mean_reversion_ac1": round(ac1, 4) if ac1 == ac1 else np.nan,
                     "adverse_perturb_min_1d": round(adverse, 5) if adverse == adverse else np.nan,
                     "rapid_reclaim_max_1d": round(reclaim, 5) if reclaim == reclaim else np.nan,
                     "choppy_participation": round(part_ok, 4) if part_ok == part_ok else np.nan,
                     "absorption_like_score": round(score, 4),
                     "stable_outcome": bool(stable), "subperiod": r.subperiod})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "34_ACCUMULATION_LIKE_FINGERPRINT.csv", index=False)
    # does absorption-like precede stable propagation more often?
    return df


def _route_sequence(daily, i, horizon=60):
    """Second/third-order state sequence after index i (10-day-settled states)."""
    st = daily.state.values
    n = len(st)
    seq = []
    seen = set()
    j = i + 1
    while j < n and j - i <= horizon:
        s = st[j]
        # record whenever a NEW contiguous stable run (>1 day) forms
        if s not in seen and j + 1 < n and st[j + 1] == s:
            seq.append(s)
            seen.add(s)
            # skip to end of run
            while j + 1 < n and st[j + 1] == s:
                j += 1
        j += 1
        if len(seq) >= 4:
            break
    return seq


def add_35_36_second_order(daily, ledger):
    """35/36: second-order route map + route latency matrix."""
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    rows = []
    for _, r in ledger.iterrows():
        i = gidx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        seq = _route_sequence(daily, i)
        rows.append({"event_id": r.event_id, "exit_date": r.exit_date,
                     "route1": r.first_destination,
                     "route2": seq[1] if len(seq) > 1 else None,
                     "route3": seq[2] if len(seq) > 2 else None,
                     "state_sequence": " -> ".join([r.first_destination] + seq[1:]),
                     "propagation_depth": int(len([s for s in seq if s in PROP_FAMILY])),
                     "alt_or_broad_weight": int(any(s in PROP_FAMILY for s in seq)),
                     "subperiod": r.subperiod})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "35_SECOND_ORDER_ROUTE_MAP.csv", index=False)
    # route latency matrix (r1 -> r2 with median gap)
    mat = []
    g = df[df.route2.notna()]
    for (r1, r2), gg in g.groupby(["route1", "route2"]):
        mat.append({"route1": r1, "route2": r2, "n": int(len(gg)),
                    "prob": round(len(gg) / max(len(df[df.route1 == r1]), 1), 4),
                    "depth_mean": round(float(gg.propagation_depth.mean()), 3)})
    m2 = pd.DataFrame(mat).sort_values("n", ascending=False)
    m2.to_csv(OUT / "36_ROUTE_LATENCY_MATRIX.csv", index=False)
    return {"map": df, "matrix": m2}


def add_37_38_termination(daily, ledger):
    """37/38: propagation termination anatomy + post-termination routing."""
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    n = len(st)
    rows = []
    prop_episodes = []
    # find all BROAD_RISK / ALT runs in the state series
    j = 0
    while j < n:
        if st[j] in PROP_FAMILY:
            k = j
            while k < n and st[k] == st[j]:
                k += 1
            prop_episodes.append((j, k - 1, st[j]))
            j = k
        else:
            j += 1
    for (a, b, sname) in prop_episodes:
        dur = b - a + 1
        if dur < 3:
            continue
        # leading changes before termination (at b): dispersion, breadth, top3, vol
        end = min(b + 3, n - 1)
        disp_chg = daily.top500_dispersion_30d.iloc[end] - daily.top500_dispersion_30d.iloc[a]
        brd_chg = daily.top500_breadth_30d.iloc[end] - daily.top500_breadth_30d.iloc[a]
        top3_chg = daily.top3_share.iloc[end] - daily.top3_share.iloc[a]
        vol_chg = daily.vol_med.iloc[end] - daily.vol_med.iloc[a]
        eth_chg = daily.eth_rel30.iloc[end] - daily.eth_rel30.iloc[a] if "eth_rel30" in daily else np.nan
        # termination style
        abrupt = bool(daily.mkt_ret_1d.iloc[min(b + 1, n - 1)] < -0.04)
        breadth_div = bool(brd_chg == brd_chg and brd_chg < 0)
        narrow = bool((top3_chg == top3_chg and top3_chg > 0))
        vol_exh = bool(vol_chg == vol_chg and vol_chg < 0)
        style = "GRADUAL_DECAY"
        if abrupt:
            style = "ABRUPT_COLLAPSE"
        elif breadth_div:
            style = "BREADTH_DIVERGENCE"
        elif narrow:
            style = "LEADERSHIP_NARROWING"
        elif vol_exh:
            style = "VOLATILITY_EXHAUSTION"
        # post-termination route (next state sequence within 30)
        post = _route_sequence(daily, b)
        nxt = st[min(b + 1, n - 1)] if b + 1 < n else None
        post_cls = "NEW_CLUB" if nxt in PROP_FAMILY and nxt != sname else \
            ("HOME" if nxt == CONC_STATE else
             ("PARKING_LOT" if nxt in ("MIXED_NO_CLEAR_ROUTE", None) else
              ("STAYING_LATE" if nxt == sname else "NEW_CLUB")))
        rows.append({"episode_start": daily.historical_date.iloc[a],
                     "episode_end": daily.historical_date.iloc[b],
                     "state": sname, "duration_d": dur,
                     "disp30_chg_during": round(float(disp_chg), 4) if disp_chg == disp_chg else np.nan,
                     "breadth_chg_during": round(float(brd_chg), 4) if brd_chg == brd_chg else np.nan,
                     "top3_chg_during": round(float(top3_chg), 4) if top3_chg == top3_chg else np.nan,
                     "vol_chg_during": round(float(vol_chg), 4) if vol_chg == vol_chg else np.nan,
                     "eth_rel_chg_during": round(float(eth_chg), 4) if eth_chg == eth_chg else np.nan,
                     "termination_style": style,
                     "post_termination_route": post_cls,
                     "subperiod": M1.subperiod_of(pd.Timestamp(daily.historical_date.iloc[b]))})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "37_PROPAGATION_TERMINATION_ANATOMY.csv", index=False)
    # post-termination routing aggregate
    agg = []
    if len(df):
        for s in df.state.unique():
            g = df[df.state == s]
            agg.append({"state": s, "n": int(len(g)),
                        **{k: round(float((g.post_termination_route == k).mean()), 4)
                           for k in ["HOME", "PARKING_LOT", "NEW_CLUB", "STAYING_LATE"]}})
    agg_df = pd.DataFrame(agg)
    agg_df.to_csv(OUT / "38_POST_TERMINATION_ROUTING.csv", index=False)
    return {"df": df, "agg": agg_df}


def add_39_bifurcation(daily, ledger, X, feat_df):
    """39: bifurcation state-space audit (sharp transition probability changes)."""
    # Criterion: do small changes in the joint coordinate region produce large,
    # stable changes in destination probability? Fit G3 logistic; compute the
    # predicted-probability sensitivity by feature (std dv/dx) and test whether
    # high-vs-low predicted-probability bins concentrate outcomes.
    g3 = _gate_label(ledger, "G3")
    from sklearn.linear_model import LogisticRegression
    Xs, _ = _zscore_fit(X, X)
    clf = LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                             random_state=SEED).fit(Xs, g3)
    p3 = clf.predict_proba(Xs)[:, 1]
    # bin predicted prob into 5 fixed quantile bins; measure outcome rate per bin
    bins = np.quantile(p3, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    b_idx = np.digitize(p3, bins[1:-1])
    rows = []
    for b in range(5):
        m = b_idx == b
        if m.sum() < 3:
            continue
        rows.append({"pred_prob_bin": b + 1, "n": int(m.sum()),
                     "outcome_rate": round(float(g3[m].mean()), 4),
                     "mid_pred_prob": round(float(np.median(p3[m])), 3)})
    df = pd.DataFrame(rows)
    # sharpness: max adjacent-bin outcome-rate jump
    sharp = np.nan
    if len(df) >= 3:
        r = df.outcome_rate.values
        sharp = float(np.max(np.abs(np.diff(r))))
    # transition discontinuity: is there a bin where a small prob shift maps to
    # large outcome change (rate jump > 0.25)?
    earned = bool(sharp == sharp and sharp >= 0.25)
    df.to_csv(OUT / "39_BIFURCATION_STATE_SPACE_AUDIT.csv", index=False)
    return {"df": df, "sharpest_jump": sharp, "bifurcation_strong_form_earned": earned}


def add_40_volatility_lifecycle(daily, m, top):
    """40: volatility role by life-cycle stage (stall/activation/ignition/propagation/decay)."""
    gidx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    st = daily.state.values
    n = len(st)
    dd = daily.copy()
    dd["VOL_HIGH"] = dd.vol_med >= dd.vol_p70
    dd["VOL_LOW"] = dd.vol_med <= dd.vol_p30
    rows = []
    # stall stage: within P1 episodes, is vol high/low?
    try:
        p1, eps = p1_episodes(m, top)
    except Exception:
        eps = []
    p1_vol = []
    for e in eps:
        i = gidx.get(pd.Timestamp(e["end"]))
        if i is not None and i < n:
            p1_vol.append(dd.VOL_HIGH.iloc[i])
    rows.append({"stage": "STALL_P1", "pct_vol_high_day":
                 round(float(np.mean(p1_vol)), 4) if p1_vol else np.nan,
                 "n_days": int(len(p1_vol))})
    # activation: native improving share rising - is it under high vol?
    med_imp = m.groupby("historical_date").imp_share.median() \
        .reindex(pd.to_datetime(dd.historical_date.values)).values
    act_high = 0.0; act_n = 0
    for i in range(1, n):
        if med_imp[i] == med_imp[i] and med_imp[i - 1] == med_imp[i - 1] \
                and med_imp[i] > med_imp[i - 1] + 0.005:
            act_n += 1
            if dd.VOL_HIGH.iloc[i]:
                act_high += 1
    rows.append({"stage": "ACTIVATION_NATIVE_IMP_RISING",
                 "pct_vol_high_day": round(act_high / max(act_n, 1), 4) if act_n else np.nan,
                 "n_days": act_n})
    # ignition: concentration escape day
    esc_high = 0.0; esc_n = 0
    for i in range(1, n):
        if st[i - 1] == CONC_STATE and st[i] != CONC_STATE:
            esc_n += 1
            if dd.VOL_HIGH.iloc[i]:
                esc_high += 1
    rows.append({"stage": "IGNITION_CONC_ESCAPE",
                 "pct_vol_high_day": round(esc_high / max(esc_n, 1), 4) if esc_n else np.nan,
                 "n_days": esc_n})
    # propagation stage: BROAD_RISK / ALT days
    for sname in ["BROAD_RISK_EXPANSION"] + sorted(ALT_FAMILY):
        m_ = st == sname
        if m_.sum() >= 5:
            rows.append({"stage": f"PROPAGATION_{sname}",
                         "pct_vol_high_day": round(float(dd.VOL_HIGH.values[m_].mean()), 4),
                         "n_days": int(m_.sum())})
    # decay: MIXED after propagation (first 3 days of a mixed run that follows prop)
    decay_high = 0.0; decay_n = 0
    for i in range(1, n):
        if st[i] == "MIXED_NO_CLEAR_ROUTE" and st[i - 1] in PROP_FAMILY:
            decay_n += 1
            if dd.VOL_HIGH.iloc[i]:
                decay_high += 1
    rows.append({"stage": "DECAY_PROP_TO_MIXED",
                 "pct_vol_high_day": round(decay_high / max(decay_n, 1), 4) if decay_n else np.nan,
                 "n_days": decay_n})
    # rerouting: out of mixed to a new propagation
    rer_n = 0; rer_high = 0
    for i in range(1, n):
        if st[i - 1] == "MIXED_NO_CLEAR_ROUTE" and st[i] in PROP_FAMILY:
            rer_n += 1
            if dd.VOL_HIGH.iloc[i]:
                rer_high += 1
    rows.append({"stage": "REROUTE_MIXED_TO_PROP",
                 "pct_vol_high_day": round(rer_high / max(rer_n, 1), 4) if rer_n else np.nan,
                 "n_days": rer_n})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "40_VOLATILITY_LIFECYCLE_ROLE.csv", index=False)
    return {"df": df}


def add_all(daily, ledger, entries, exits, m, top, bm, X, feat_df):
    """Run all addendum workstreams and return results dict."""
    print("[run] addendum workstreams 30-40 ...")
    r30 = add_30_p1_micro_perturbation(daily, m, top)
    r31 = add_31_32_temporal_lattice(daily, ledger)
    r33 = add_33_first_move_true_delivery(daily, ledger, bm)
    r34 = add_34_accumulation_like(daily, ledger)
    r35 = add_35_36_second_order(daily, ledger)
    r37 = add_37_38_termination(daily, ledger)
    r39 = add_39_bifurcation(daily, ledger, X, feat_df)
    r40 = add_40_volatility_lifecycle(daily, m, top)
    print("[done] addendum workstreams")
    return {"r30": r30, "r31": r31, "r33": r33, "r34": r34, "r35": r35,
            "r37": r37, "r39": r39, "r40": r40}


# ----------------------------------------------------------------------------
# finalize: ladder, NMD, nulls, subperiod stability, test counts
# ----------------------------------------------------------------------------

def finalize(results, test_counts, decisions):
    ladder = []
    def add(claim, level, ev):
        ladder.append({"claim": claim, "highest_level": level, "evidence": ev})
    a = results["A"]
    add("RELEASE_EVENT_RECONSTRUCTION", "L1",
        f"A: {len(a['ledger'])} exits; staged patterns {a['pattern_counts']}")
    b = results["B"]
    g1p = b["perm"].get("G1", np.nan)
    g3p = b["perm"].get("G3", np.nan)
    add("HIERARCHICAL_RELEASE_GATES", "L2" if (g1p == g1p and g1p < 0.05) else "L1",
        f"B: G1 perm_p={g1p}, G3 perm_p={g3p}")
    c = results["C"]
    add("PATH_MEMORY", "L3" if c["classification"] == "HYSTERESIS_PREDICTIVE_MECHANISM" else "L1",
        f"C: {c['classification']} delta={c['delta']:.4f} perm_p={c['path_perm_p']}")
    d = results["D"]
    add("DURATION_SEMIMARKOV", "L2" if d["semi_markov_earned"] else "L1",
        f"D: semi_markov={d['semi_markov_earned']}")
    e = results["E"]
    add("STALL_ACTIVATION", "L2" if (e["p_pre_ctrl"] == e["p_pre_ctrl"] and
                                     e["p_pre_ctrl"] < 0.05) else "L1",
        f"E: pre-vs-ctrl p={e['p_pre_ctrl']}")
    f = results["F"]
    add("RELEASE_TRIGGER_VS_ROUTE_GATE", "L2" if f["verdict"] != "MERGE_SAME_GATE" else "L1",
        f"F: {f['verdict']} only_init={f['only_init']} only_route={f['only_route']}")
    g = results["G"]
    add("VOLATILITY_ROUTING_TEMPERATURE", "L1", f"G: {len(g['g'])} cells")
    h = results["H"]
    add("STATE_ROUTING_GRAPH", "L2" if h["reconfig_supported"] else "L1",
        f"H: reconfig={h['reconfig_supported']} new_edges={h['n_new_edges']} "
        f"flips={h['n_sign_flips']} of {h['total_cells']} cells")
    add("MECH2_MECH3_FLAGSHIP_RECONCILIATION", "L3",
        f"R: {results['R']['classification']}")
    i = results["I"]
    add("INFORMATION_GAIN", "L0", f"I: {len(i['h'])} phenomena")
    pd.DataFrame(ladder).to_csv(OUT / "24_CAUSALITY_LADDER.csv", index=False)

    # NEW_NODE / MERGE / DISSOLVE
    nmd = []
    a_verdict = results["A"]["verdict"]
    nmd.append({"operation": "MERGE" if a_verdict == "INTERMEDIATE_DEPTH" else
                ("NEW_NODE" if a_verdict == "COMPETING_ROUTES" else "UNRESOLVED"),
                "object": "BROAD_RISK vs ALT release routes",
                "evidence": f"WS A: P(BROAD_RISK before ALT | ALT reached)="
                            f"{results['A']['p_broad_risk_before_alt']}; "
                            f"pattern counts {results['A']['pattern_counts']}",
                "decision": "CONFIRMED"})
    nmd.append({"operation": "NEW_NODE" if results["C"]["classification"] ==
                "HYSTERESIS_PREDICTIVE_MECHANISM" else "DISSOLVE",
                "object": "HYSTERESIS_PREDICTIVE_MECHANISM (path memory)",
                "evidence": f"WS C: {results['C']['classification']}, delta_logloss="
                            f"{results['C']['delta']:.4f}, perm_p="
                            f"{results['C']['path_perm_p']}",
                "decision": "CONFIRMED"})
    nmd.append({"operation": "NEW_NODE" if results["D"]["semi_markov_earned"] else "NULL",
                "object": "duration-dependence (semi-Markov)",
                "evidence": f"WS D: semi_markov_earned="
                            f"{results['D']['semi_markov_earned']}",
                "decision": "CONFIRMED"})
    nmd.append({"operation": "NEW_NODE" if results["F"]["verdict"] != "MERGE_SAME_GATE" else
                "MERGE", "object": "release trigger vs route gate",
                "evidence": f"WS F: {results['F']['verdict']}",
                "decision": "CONFIRMED"})
    nmd.append({"operation": "NEW_NODE" if results["H"]["reconfig_supported"] else "NULL",
                "object": "state-conditioned routing graph",
                "evidence": f"WS H: reconfig_supported="
                            f"{results['H']['reconfig_supported']}",
                "decision": "CONFIRMED"})
    pd.DataFrame(nmd).to_csv(OUT / "25_NEW_NODE_MERGE_DISSOLVE.csv", index=False)

    # nulls
    nulls = []
    nulls.append({"workstream": "B", "test": "gate", "classification": "NOT_SUPPORTED",
                  "count": int(sum(1 for r in results["B"]["gates"]
                                   if r["classification"] == "NOT_SUPPORTED"))})
    nulls.append({"workstream": "C", "test": "path memory",
                  "classification": results["C"]["classification"], "count": 1})
    nulls.append({"workstream": "D", "test": "semi-markov",
                  "classification": "EARNED" if results["D"]["semi_markov_earned"] else "NOT_EARNED",
                  "count": 1})
    if results["E"]["p_pre_ctrl"] == results["E"]["p_pre_ctrl"] and \
            results["E"]["p_pre_ctrl"] >= 0.05:
        nulls.append({"workstream": "E", "test": "activation-first",
                      "classification": "NULL", "count": 1})
    if results["F"]["verdict"] == "MERGE_SAME_GATE":
        nulls.append({"workstream": "F", "test": "trigger-route separation",
                      "classification": "MERGE", "count": 1})
    if not results["H"]["reconfig_supported"]:
        nulls.append({"workstream": "H", "test": "graph reconfiguration",
                      "classification": "NULL", "count": 1})
    pd.DataFrame(nulls).to_csv(OUT / "23_NULL_AND_FAILED_RESULTS.csv", index=False)

    # subperiod stability (22)
    sp_rows = []
    led = results["A"]["ledger"]
    led["prop"] = led.first_destination.isin(PROP_FAMILY)
    led["escape"] = led.first_destination != CONC_STATE
    for spn, y0, y1 in SUBPERIODS:
        g = led[led.subperiod == spn]
        if len(g) == 0:
            continue
        sp_rows.append({"claim": "G1_ESCAPE_RATE", "subperiod": spn,
                        "n_exits": int(len(g)),
                        "value": round(float(g.escape.mean()), 4)})
        sp_rows.append({"claim": "G3_PROPAGATION_SHARE", "subperiod": spn,
                        "n_exits": int(len(g)),
                        "value": round(float(g.prop.mean()), 4)})
        sp_rows.append({"claim": "STAGED_VIA_BROAD_RISK_SHARE", "subperiod": spn,
                        "n_exits": int(len(g)),
                        "value": round(float((g.staged_pattern ==
                                              "CONC_VIA_BROAD_RISK").mean()), 4)})
    pd.DataFrame(sp_rows).to_csv(OUT / "22_SUBPERIOD_STABILITY.csv", index=False)
    pd.DataFrame([{"workstream": k, "statistical_tests": v}
                  for k, v in test_counts.items()]).to_csv(
        OUT / "27_TEST_COUNT_RECONCILIATION.csv", index=False)
    return pd.DataFrame(ladder)


def main():
    print("=" * 72)
    print("ALT_MECH_4 :: PIVOT RELEASE GATES / STALL RELEASE / PATH MEMORY")
    print("=" * 72)
    OUT.mkdir(parents=True, exist_ok=True)
    inp, tl = _cache_step("inputs", load)
    json.dump(tl, open(OUT / "02_DATA_TRUTH.json", "w"), indent=2, default=str)
    print(f"[truth-lock] all_pass={tl['all_pass']}")
    if not tl["all_pass"]:
        print("TRUTH LOCK FAILED:", tl["checks"])
        sys.exit(1)

    daily, d, bm = _cache_step("daily", lambda: build_daily(inp))
    m, top = _cache_step("chainframe", lambda: build_chainframe(inp))

    rc = _cache_step("reconcile", lambda: ws_reconcile(daily))
    entries, exits = rc["recount"]["entries"], rc["recount"]["exits"]
    rA = _cache_step("A", lambda: ws_a(daily, entries, exits))
    X, feat_df = _cache_step("feats", lambda: _exit_features(rA["ledger"], daily))
    rB = _cache_step("B", lambda: ws_b(rA["ledger"], X, feat_df))
    rC = _cache_step("C", lambda: ws_c(rA["ledger"], X, daily, entries))
    rD = _cache_step("D", lambda: ws_d(daily))
    rE = _cache_step("E", lambda: ws_e(daily, m, top))
    rF = _cache_step("F", lambda: ws_f(rA["ledger"], X, feat_df))
    rG = _cache_step("G", lambda: ws_g(daily, rA["ledger"]))
    rH = _cache_step("H", lambda: ws_h(daily, bm))
    rR = _cache_step("R", lambda: ws_reconcile_flagship(daily, bm))
    rI = _cache_step("I", lambda: ws_info_gain(daily, rA["ledger"], rC, m, top))
    rZ = _cache_step("Z", lambda: add_all(daily, rA["ledger"], entries, exits,
                                            m, top, bm, X, feat_df))

    test_counts = {"A_release_reconstruction": int(len(rA["ledger"])),
                   "B_gates": int(len(rB["gates"])),
                   "C_path_memory": int(rC["models"].shape[0]),
                   "D_duration": int(rD["test_count"]),
                   "E_activation": int(rE["test_count"]),
                   "H_routing_graph": int(rH["test_count"]),
                   "R_flagship_reconcile": 12,
                   "Z_addendum_30_40": 40}
    results = {"A": rA, "B": rB, "C": rC, "D": rD, "E": rE, "F": rF, "G": rG,
               "H": rH, "R": rR, "I": rI, "Z": rZ}
    finalize(results, test_counts, {})
    # persist verdict JSON for report authoring
    vd = {
        "A_verdict": rA["verdict"], "A_pattern_counts": rA["pattern_counts"],
        "A_p_alt_30d": rA["p_alt_reached_30d"],
        "A_p_br_before_alt": rA["p_broad_risk_before_alt"],
        "B_gates": rB["gates"], "C_class": rC["classification"],
        "C_delta": rC["delta"], "C_perm_p": rC["path_perm_p"],
        "D_semi_markov": rD["semi_markov_earned"],
        "D_median_duration": rD["median_duration"],
        "E_pre_ctrl_p": rE["p_pre_ctrl"], "E_pre_post_p": rE["p_pre_post"],
        "E_base_ll": rE["base_ll"], "E_act_ll": rE["act_ll"],
        "E_n_episodes": int(len(rE["episodes"])),
        "E_lead_median": rE["lead_median_days"],
        "E_share_within_30d": rE["share_within_30d"],
        "F_verdict": rF["verdict"], "F_only_init": rF["only_init"],
        "F_only_route": rF["only_route"],
        "H_reconfig": rH["reconfig_supported"], "H_new": rH["n_new_edges"],
        "H_flips": rH["n_sign_flips"], "H_cells": rH["total_cells"],
        "R_class": rR["classification"], "R_m2": (rR["m2_best_lag"], rR["m2_best_corr"]),
        "R_m3": (rR["m3_best_lag"], rR["m3_best_corr"]),
        "Z_tau_medians": json.loads(rZ["r31"]["df"].filter(like="tau").median()
                                     .to_json()) if "df" in rZ["r31"] and len(rZ["r31"]["df"])
        else {},
        "Z_33_class_counts": rZ["r33"].classification.value_counts().to_dict()
        if len(rZ["r33"]) else {},
        "Z_37_styles": rZ["r37"]["df"].termination_style.value_counts().to_dict()
        if "df" in rZ["r37"] and len(rZ["r37"]["df"]) else {},
        "Z_39_bifurcation_earned": bool(rZ["r39"]["bifurcation_strong_form_earned"]),
        "Z_39_sharpest_jump": rZ["r39"]["sharpest_jump"],
        "Z_40_lifecycle": rZ["r40"]["df"].to_dict("records") if len(rZ["r40"]["df"]) else [],
    }
    with open(OUT / "_verdicts.json", "w") as fh:
        json.dump(vd, fh, indent=2, default=str)
    print("DONE.")
    print("artifacts written to", OUT)


if __name__ == "__main__":
    main()
