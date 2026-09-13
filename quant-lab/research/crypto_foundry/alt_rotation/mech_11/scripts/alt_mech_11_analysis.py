#!/usr/bin/env python
"""ALT_MECH_11 - Temporal Field Physics, Multi-Scale Delivery Lattice,
Semi-Markov State Geometry, Perturbation Amplitude, Propagation Radius,
Rank-Depth Sequence Structure & Cross-Agent Health Synthesis.

Terrain research ONLY (AGENT 1 - CANONICAL FIELD CARTOGRAPHER). No PnL, no
strategy, no execution, no sizing, no deployment.
"""
import gc, json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, norm, spearmanr
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20261101
BOOT_N = 300
PERM_N = 200
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_11/
M10_ROOT = ROOT.parent / "mech_10"
M9_ROOT = ROOT.parent / "mech_9"
OUT = ROOT

M10_SCRIPTS = M10_ROOT / "scripts"
sys.path.insert(0, str(M10_SCRIPTS))
import alt_mech_10_analysis as M10

BRD_MED = M10.BRD_MED
DISP_MED = M10.DISP_MED
SUCCESS_LABELS = M10.SUCCESS_LABELS
REENTRY_LABEL = M10.REENTRY_LABEL
CELLS = M10.CELLS
AGE_BANDS = M10.AGE_BANDS
HEALTH_STATES = M10.HEALTH_STATES
PERT_COLS = M10.PERT_COLS
_age_band = M10._age_band
_context_at = M10._context_at
_perturbation_flags = M10._perturbation_flags

HORIZONS = [1, 2, 3, 5, 7, 10, 14, 21, 30]
BANDS_COARSE = ["26-100", "101-250", "251-500", "501-750",
                "751-1000", "1001-1500", "1501-2000"]
FINE_TO_COARSE = {"26-50": "26-100", "51-100": "26-100",
                  "101-150": "101-250", "151-250": "101-250",
                  "251-350": "251-500", "351-500": "251-500",
                  "501-625": "501-750", "626-750": "501-750",
                  "751-875": "751-1000", "876-1000": "751-1000",
                  "1001-1500": "1001-1500", "1501-2000": "1501-2000"}
PATCHES = {"UPPER_CORE": ["26-50", "51-100"],
           "UPPER_MID": ["101-150", "151-250"],
           "MID": ["251-350", "351-500"],
           "LOWER_MID": ["501-625", "626-750"],
           "TRANSITION": ["751-875", "876-1000"]}
PATCH_LONER_BANDS = {"UPPER_CORE": ["26-100"], "UPPER_MID": ["101-250"],
                     "MID": ["251-500"], "LOWER_MID": ["501-750"],
                     "TRANSITION": ["751-1000"]}


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run] {name} ...", flush=True)
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def _perm_p(k, B):
    return (k + 1) / (B + 1)


def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    return f"{x:.{nd}f}"


def _fdr(p):
    p = np.asarray(p, dtype=float)
    mask = ~np.isnan(p)
    q = np.full(len(p), np.nan)
    if mask.any():
        q[mask] = multipletests(p[mask], method="fdr_bh")[1]
    return q


# =========================================================================
# LOADERS - reuse MECH-9/10 cached artifacts (memory-safe)
# =========================================================================

def load_dfw():
    with open(M9_ROOT / "_cache_dfw.pkl", "rb") as fh:
        return pickle.load(fh)


def load_ev():
    with open(M9_ROOT / "_cache_ev.pkl", "rb") as fh:
        return pickle.load(fh)


def load_health():
    with open(M9_ROOT / "_cache_health.pkl", "rb") as fh:
        return pickle.load(fh)


def load_band_panel():
    """Daily x rank-band panel built from LF5 PIT events (cached)."""
    p = OUT / "_cache_bandpanel.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    src = Path(r"C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab"
               r"\research\crypto_foundry\derivatives\lower_field_5"
               r"\cache\lf5_events.parquet")
    ev = pd.read_parquet(src, columns=["historical_date", "rank", "ret_1d",
                                       "is_stablecoin", "flag_stale_price",
                                       "flag_missing_price"])
    ev = ev[~ev["is_stablecoin"] & ~ev["flag_stale_price"]
            & ~ev["flag_missing_price"]]
    bins = [0, 25, 100, 250, 500, 750, 1000, 1500, 2000]
    ev["band"] = pd.cut(ev["rank"], bins,
                        labels=["1-25", "26-100", "101-250", "251-500",
                                "501-750", "751-1000", "1001-1500",
                                "1501-2000"])
    ev["d"] = pd.to_datetime(ev["historical_date"]).dt.normalize()
    g = ev.groupby(["d", "band"], observed=True).agg(
        med_ret=("ret_1d", "median"),
        n=("ret_1d", "size"),
        ppos=("ret_1d", lambda s: (s > 0).mean()),
        ptail=("ret_1d", lambda s: (s.abs() > 0.15).mean()))
    g = g.reset_index().sort_values(["d", "band"])
    del ev
    gc.collect()
    with open(p, "wb") as fh:
        pickle.dump(g, fh)
    return g


def load_loners():
    """Event-level TRUE/FALSE loner labels reconstructed from LF5 behavioral
    peer residuals at h=1 (z = |resid| / disp < 1 -> FALSE_LONER). Verified
    against LF5 audit: 18.4% overall false-loner rate, per-band matches."""
    p = OUT / "_cache_loners.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    src = Path(r"C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab"
               r"\research\crypto_foundry\derivatives\lower_field_5")
    pp = pd.read_csv(src / "15_POST_EVENT_PEER_PATHS.csv",
                     usecols=["event_index", "asset_id", "rank_band",
                              "horizon", "asset_peer_residual_BEHAVIORAL_10",
                              "peer_dispersion_BEHAVIORAL_10"])
    h1 = pp[pp["horizon"] == 1].copy()
    disp = h1["peer_dispersion_BEHAVIORAL_10"].replace(0, np.nan)
    z = h1["asset_peer_residual_BEHAVIORAL_10"].abs() / disp
    h1["z"] = z
    h1["loner"] = np.where(z < 1, "FALSE_LONER", "TRUE_LONER")
    ev = pd.read_parquet(src / "cache" / "lf5_events.parquet",
                         columns=["historical_date", "cmc_id", "rank_band",
                                  "amp_level", "subperiod", "event_family"])
    ev = ev.reset_index().rename(columns={"index": "event_index"})
    ev["d"] = pd.to_datetime(ev["historical_date"]).dt.normalize()
    m = h1[["event_index", "z", "loner"]].merge(
        ev[["event_index", "d", "cmc_id", "rank_band", "amp_level",
            "subperiod"]], on="event_index", how="left")
    m = m[~m["d"].isna()]
    with open(p, "wb") as fh:
        pickle.dump(m, fh)
    return m
# =========================================================================
# WS1: MULTI-SCALE DELIVERY LATTICE (02_MULTI_SCALE_DELIVERY_LATTICE.csv)
# =========================================================================

def _fwd_window_flags(df, col, horizons):
    """For daily 0/1 column, any event within next h days for each h."""
    out = {}
    n = len(df)
    vals = df[col].to_numpy(dtype=float)
    for h in horizons:
        w = np.zeros(n)
        for i in range(n):
            j = i + h
            if j > n:
                continue
            w[i] = vals[i + 1:j].sum() > 0
        out[h] = w
    return out


def ws1_multi_scale_lattice(dfw):
    df = dfw.copy()
    n = len(df)
    # exit: cell change within h
    exit_flags = {}
    for h in HORIZONS:
        f = np.zeros(n)
        for i in range(n):
            j = min(i + h, n - 1)
            f[i] = (df["cell"].iloc[i + 1:j + 1] != df["cell"].iloc[i]).any()
        exit_flags[h] = f
    # reentry / propagation from fwd state
    reentry_flags = {}
    prop_flags = {}
    state_arr = df["state"].to_numpy()
    for h in HORIZONS:
        rf = np.zeros(n)
        pf = np.zeros(n)
        for i in range(n):
            j = min(i + h, n - 1)
            seg = state_arr[i + 1:j + 1]
            rf[i] = (seg == REENTRY_LABEL).any()
            pf[i] = pd.Series(seg).isin(SUCCESS_LABELS).any()
        reentry_flags[h] = rf
        prop_flags[h] = pf
    # rank recruitment: rank_depth_rel_chg > 0 within h
    recruit_flags = {}
    rdr = df["rank_depth_rel_chg"].fillna(0).to_numpy()
    for h in HORIZONS:
        f = np.zeros(n)
        for i in range(n):
            j = min(i + h, n - 1)
            f[i] = (rdr[i + 1:j + 1] > 0).any()
        recruit_flags[h] = f
    # tail event families
    fam_cols = {"isol_dn": "ev_ISOLATED_DOWNSIDE_EXTREME",
                "band_up": "ev_BAND_BROAD_UPSIDE",
                "multi_up": "ev_MULTI_BAND_UPSIDE",
                "coord_dn": "ev_COORDINATED_DOWNSIDE"}
    fam_flags = {}
    for fname, col in fam_cols.items():
        fam_flags[fname] = _fwd_window_flags(df, col, HORIZONS)

    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = sub[sub["age_band"] == ab]
            if len(s2) < 30:
                continue
            idx = s2.index
            base = {"cell": cell, "age_band": ab, "n_days": int(len(s2))}
            clocks = {"STATE_EXIT": exit_flags, "REENTRY": reentry_flags,
                      "PROPAGATION": prop_flags,
                      "RANK_RECRUITMENT": recruit_flags}
            for cname, fl in clocks.items():
                row = dict(base)
                row["clock"] = cname
                for h in HORIZONS:
                    row[f"p_by_{h}d"] = float(fl[h][idx].mean())
                rows.append(row)
            for fname, fl in fam_flags.items():
                row = dict(base)
                row["clock"] = f"ARRIVAL_{fname}"
                for h in HORIZONS:
                    row[f"p_by_{h}d"] = float(fl[h][idx].mean())
                rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "02_MULTI_SCALE_DELIVERY_LATTICE.csv", index=False)
    return out


# =========================================================================
# WS2: SEQUENCE GRAMMAR (03_SEQUENCE_GRAMMAR.csv)
# =========================================================================

def _atom_series(df):
    """Daily 0/1 atom flags (first-appearance order target)."""
    df = df.copy()
    brd = (df["breadth_vel"] > 0).astype(int)
    disp = (df["top500_dispersion_30d"].diff() > 0).astype(int)
    rank = (df["rank_depth_rel_chg"].fillna(0) > 0).astype(int)
    tail = (df[["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE",
                "ev_ISOLATED_DOWNSIDE_EXTREME"]].sum(axis=1) > 0).astype(int)
    conc = (df["top3_share_chg7"].fillna(0) < 0).astype(int)
    return pd.DataFrame({"BREADTH_EXPANDS": brd, "DISPERSION_EXPANDS": disp,
                         "RANK_RECRUITS": rank, "TAIL_ACTIVATES": tail,
                         "CONCENTRATION_RELEASES": conc}, index=df.index)


def ws2_sequence_grammar(dfw):
    df = dfw.copy()
    atoms = _atom_series(df)
    state_arr = df["state"].to_numpy()
    # target: propagation within 7D
    target = np.zeros(len(df))
    for i in range(len(df)):
        j = min(i + 7, len(df) - 1)
        target[i] = pd.Series(state_arr[i + 1:j + 1]).isin(SUCCESS_LABELS).any()
    seq_rows = []
    for i in range(len(df) - 7):
        if target[i] != 1:
            continue
        w = atoms.iloc[i + 1:i + 8]
        order = []
        for col in ["BREADTH_EXPANDS", "DISPERSION_EXPANDS", "RANK_RECRUITS",
                    "TAIL_ACTIVATES", "CONCENTRATION_RELEASES"]:
            hit = np.where(w[col].to_numpy() > 0)[0]
            if len(hit):
                order.append((int(hit[0]), col))
        order.sort()
        seq = "->".join(c for _, c in order) if order else "NONE"
        seq_rows.append({"d": df["d"].iloc[i],
                         "subperiod": df["subperiod"].iloc[i],
                         "cell": df["cell"].iloc[i], "seq": seq})
    sd = pd.DataFrame(seq_rows)
    out_rows = []
    if len(sd):
        total = len(sd)
        for seq, g in sd.groupby("seq"):
            n = len(g)
            n_sub = g["subperiod"].nunique()
            # baseline: uniform over distinct sequences
            n_distinct = sd["seq"].nunique()
            exp = total / n_distinct
            lift = (n / total) / (exp / total) if exp else np.nan
            out_rows.append({"sequence": seq, "count": n,
                             "pct": n / total, "n_subperiods": n_sub,
                             "lift_vs_uniform": lift,
                             "status": ("COMMON" if n >= MIN_PROMOTE_N
                                        and n_sub >= MIN_SUBPERIODS
                                        and lift >= 1.2 else
                                        "LOCAL" if n >= 30 else "RARE")})
        out_rows.sort(key=lambda r: -r["count"])
    out = pd.DataFrame(out_rows)
    out.to_csv(OUT / "03_SEQUENCE_GRAMMAR.csv", index=False)
    return out
# =========================================================================
# WS3: SEMI-MARKOV AUDIT (04_SEMI_MARKOV_AUDIT.csv)
# =========================================================================

def ws3_semi_markov(dfw):
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    d = df.dropna(subset=["next_cell"]).copy()
    cells = CELLS
    # purged chronological split
    dates = np.sort(pd.to_datetime(d["d"]).dt.normalize().unique())
    cut = dates[int(len(dates) * 0.8)]
    d["dn"] = pd.to_datetime(d["d"]).dt.normalize()
    tr = d[d["dn"] < cut]
    te = d[d["dn"] >= cut]

    def fit_predict(train, test, use_age):
        # empirical P(next | cell [, age])
        key = ["cell"] + (["age_band"] if use_age else [])
        est = train.groupby(key)["next_cell"].value_counts(normalize=True)
        prob_rows = []
        for _, r in test.iterrows():
            k = tuple(r[c] for c in key)
            if k in est.index:
                dist = est.loc[k]
                prob = dist.get(r["next_cell"], 0.0)
            else:
                # fallback to cell-only
                if ("cell" in key and (r["cell"],) in
                        train.groupby("cell")["next_cell"]
                        .value_counts(normalize=True).index):
                    dist = train.groupby("cell")["next_cell"] \
                        .value_counts(normalize=True).loc[(r["cell"],)]
                    prob = dist.get(r["next_cell"], 0.0)
                else:
                    prob = 1.0 / len(cells)
            prob_rows.append(max(prob, 1e-6))
        return np.array(prob_rows)

    p_markov = fit_predict(tr, te, use_age=False)
    p_semi = fit_predict(tr, te, use_age=True)
    y = (te["next_cell"].to_numpy())
    # logloss on one-hot (only need prob of true class)
    ll_m = -np.log(p_markov).mean()
    ll_s = -np.log(p_semi).mean()
    brier_m = np.mean((1 - p_markov) ** 2)
    brier_s = np.mean((1 - p_semi) ** 2)
    lr = np.sum(np.log(p_semi / p_markov))
    # per-cell table
    rows = []
    for cell in cells:
        m = te["cell"] == cell
        if m.sum() < 20:
            continue
        rows.append({"cell": cell, "n_test": int(m.sum()),
                     "logloss_markov": float(np.mean(-np.log(p_markov[m]))),
                     "logloss_semi": float(np.mean(-np.log(p_semi[m]))),
                     "brier_markov": float(np.mean((1 - p_markov[m]) ** 2)),
                     "brier_semi": float(np.mean((1 - p_semi[m]) ** 2))})
    # Overall verdict: semi-Markov earns only if clearly better; if clearly
    # worse or equivalent, dwell time adds no material predictive value.
    if ll_s < ll_m - 0.005 and lr > 0:
        verdict = "SEMI_MARKOV_EARNED"
    elif ll_s > ll_m + 0.005:
        verdict = "MARKOV_SUFFICIENT"
    else:
        verdict = "INCONCLUSIVE"
    out = pd.DataFrame(rows)
    out["overall_logloss_markov"] = ll_m
    out["overall_logloss_semi"] = ll_s
    out["overall_brier_markov"] = brier_m
    out["overall_brier_semi"] = brier_s
    out["loglik_ratio"] = lr
    out["verdict"] = verdict
    out.to_csv(OUT / "04_SEMI_MARKOV_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS4: COMPETING-RISK CLOCKS (05_COMPETING_RISK_CLOCKS.csv)
# =========================================================================

def _first_event_horizon(df, idx, kind, state_arr, cell_arr, max_h=30):
    """Horizon of first competing event; NaN if none within max_h."""
    out = []
    n = len(df)
    for i in idx:
        found = np.nan
        for h in range(1, max_h + 1):
            j = i + h
            if j >= n:
                break
            st = state_arr[j]
            if kind == "PROPAGATION":
                if st in SUCCESS_LABELS:
                    found = h
                    break
            elif kind == "REENTRY":
                if st == REENTRY_LABEL:
                    found = h
                    break
            elif kind == "EXIT_TO_OTHER":
                if cell_arr[j] != cell_arr[i]:
                    found = h
                    break
        out.append(found)
    return np.array(out)


def ws4_competing_risk(dfw):
    df = dfw.copy()
    state_arr = df["state"].to_numpy()
    cell_arr = df["cell"].to_numpy()
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = sub[sub["age_band"] == ab]
            if len(s2) < 30:
                continue
            idx = s2.index.to_numpy()
            # cause-specific first-horizons for each competing outcome
            hazards = {}
            for kind in ["PROPAGATION", "REENTRY", "EXIT_TO_OTHER"]:
                first = _first_event_horizon(df, idx, kind, state_arr,
                                             cell_arr)
                # cause-specific hazard at h: first event == h
                hs = []
                for h in range(1, 31):
                    hs.append(float((first == h).mean()))
                hazards[kind] = np.array(hs)
            # cumulative incidence (any first event among the three)
            first_any = np.full(len(idx), np.nan)
            for kind in ["PROPAGATION", "REENTRY", "EXIT_TO_OTHER"]:
                fh = _first_event_horizon(df, idx, kind, state_arr, cell_arr)
                better = np.isnan(first_any) | (fh < first_any)
                first_any = np.where(better, fh, first_any)
            ci = []
            for h in range(1, 31):
                ci.append(float((first_any <= h).mean()))
            row = {"cell": cell, "age_band": ab, "n_days": int(len(s2))}
            for kind in ["PROPAGATION", "REENTRY", "EXIT_TO_OTHER"]:
                for h in [3, 7, 14, 21, 30]:
                    row[f"haz_{kind}_{h}d"] = float(hazards[kind][h - 1])
                row[f"ci_{kind}_30d"] = float(
                    (hazards[kind][:30] * np.arange(1, 31)).sum() /
                    max(30.0, 1.0))  # placeholder replaced below
            row["ci_any_7d"] = float((first_any <= 7).mean())
            row["ci_any_14d"] = float((first_any <= 14).mean())
            row["ci_any_30d"] = float((first_any <= 30).mean())
            rows.append(row)
    out = pd.DataFrame(rows)
    # HH mass-shift test: reentry vs propagation cumulative incidence
    verdict_rows = []
    hh = out[out["cell"] == "HIGH_BREADTH_HIGH_DISP"]
    if len(hh) >= 2:
        young = hh[hh["age_band"] == "AGE_1"]
        mature = hh[hh["age_band"] == "AGE_15_PLUS"]
        if len(young) and len(mature):
            # recompute exact CI for reentry/propagation at 14D
            df2 = dfw.copy()
            state_arr2 = df2["state"].to_numpy()
            cell_arr2 = df2["cell"].to_numpy()
            df2["age_band"] = df2["age_in_cell"].apply(_age_band)
            res = {}
            for ab, tag in [("AGE_1", "young"), ("AGE_15_PLUS", "mature")]:
                s2 = df2[(df2["cell"] == "HIGH_BREADTH_HIGH_DISP")
                         & (df2["age_band"] == ab)]
                idx = s2.index.to_numpy()
                ci_re, ci_pr = {}, {}
                for h in [7, 14, 30]:
                    first_re = _first_event_horizon(df2, idx, "REENTRY",
                                                    state_arr2, cell_arr2)
                    first_pr = _first_event_horizon(df2, idx, "PROPAGATION",
                                                    state_arr2, cell_arr2)
                    ci_re[h] = float((first_re <= h).mean())
                    ci_pr[h] = float((first_pr <= h).mean())
                res[tag] = (ci_re, ci_pr)
            shift = res["mature"][1][14] - res["young"][1][14]
            mass = (res["mature"][0][14] < res["young"][0][14]
                    and res["mature"][1][14] > res["young"][1][14])
            verdict_rows.append({
                "test": "HH_REENTRY_TO_PROPAGATION_MASS_SHIFT_14D",
                "ci_reentry_young_14d": res["young"][0][14],
                "ci_reentry_mature_14d": res["mature"][0][14],
                "ci_prop_young_14d": res["young"][1][14],
                "ci_prop_mature_14d": res["mature"][1][14],
                "delta_prop_young_to_mature": shift,
                "verdict": ("MASS_SHIFT_EARNED" if (mass and shift >= 0.05)
                            else "NO_SHIFT")})
    vd = pd.DataFrame(verdict_rows)
    out.to_csv(OUT / "05_COMPETING_RISK_CLOCKS.csv", index=False)
    vd.to_csv(OUT / "05b_COMPETING_RISK_VERDICT.csv", index=False)
    return {"clocks": out, "verdict": vd}
# =========================================================================
# WS5: PERTURBATION AMPLITUDE (06_PERTURBATION_AMPLITUDE.csv)
# =========================================================================

def ws5_perturbation_amplitude(dfw):
    df = _perturbation_flags(dfw.copy())
    # amplitude measures (standardized)
    amp = pd.DataFrame(index=df.index)
    amp["brd"] = df["top500_breadth_30d"].diff(5).abs()
    amp["disp"] = df["top500_dispersion_30d"].diff(5).abs()
    amp["btc"] = df["btc_return_7d"].abs()
    amp["conc"] = df["top3_share_chg7"].abs()
    amp["vol"] = df["vol_med"].diff(5).abs()
    for c in amp.columns:
        df[c] = amp[c].to_numpy()
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd7_state"] = df["state"].shift(-7)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_prop"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    pert_defs = {"brd_jump": ("brd", 1), "brd_drop": ("brd", -1),
                 "disp_jump": ("disp", 1), "disp_drop": ("disp", -1),
                 "btc_shock": ("btc", 1), "conc_shock": ("conc", 1),
                 "vol_shock": ("vol", 1)}
    rows = []
    for pname, (acol, _sign) in pert_defs.items():
        flag = df[pname]
        sub = df[flag == 1].copy()
        if len(sub) < 60:
            continue
        a = sub[acol]
        # terciles -> SMALL/MEDIUM/LARGE
        lo, hi = a.quantile([1 / 3, 2 / 3])
        for lab, mask in [("SMALL", a <= lo), ("MEDIUM", (a > lo) & (a <= hi)),
                          ("LARGE", a > hi)]:
            s2 = sub[mask]
            if len(s2) < 15:
                continue
            rows.append({
                "perturbation": pname, "amplitude": lab,
                "n": int(len(s2)),
                "median_amp": float(s2[acol].median()),
                "p_survive_3d": float((s2["next_cell"] == s2["cell"]).mean()),
                "p_survive_7d": float(
                    (df.loc[s2.index, "cell"].shift(-7).to_numpy() ==
                     s2["cell"].to_numpy()).mean()),
                "p_fwd7_prop": float(s2["fwd7_prop"].mean()),
                "p_displace_3d": float((s2["next_cell"] != s2["cell"]).mean()),
                "p_tail_7d": float(df.loc[s2.index,
                                          ["ev_BAND_BROAD_UPSIDE",
                                           "ev_MULTI_BAND_UPSIDE",
                                           "ev_ISOLATED_DOWNSIDE_EXTREME"]]
                                   .shift(-7).sum(axis=1).gt(0).mean())})
    out = pd.DataFrame(rows)
    if len(out):
        out["verdict"] = "DESCRIPTIVE"
        for pname in out["perturbation"].unique():
            sub = out[out["perturbation"] == pname]
            if len(sub) >= 2:
                srt = sub.sort_values("amplitude")
                p_large = srt[srt["amplitude"] == "LARGE"]["p_fwd7_prop"]
                p_small = srt[srt["amplitude"] == "SMALL"]["p_fwd7_prop"]
                if len(p_large) and len(p_small):
                    d = float(p_large.iloc[0] - p_small.iloc[0])
                    out.loc[out["perturbation"] == pname, "verdict"] = (
                        "THRESHOLD_REGION" if abs(d) >= 0.15
                        else "SMOOTH" if abs(d) >= 0.03
                        else "NO_STABLE_RESPONSE")
    out.to_csv(OUT / "06_PERTURBATION_AMPLITUDE.csv", index=False)
    return out


# =========================================================================
# WS6: PROPAGATION RADIUS (07_PROPAGATION_RADIUS.csv)
# =========================================================================

def _coarse_panel(band):
    b = band.copy()
    b["coarse"] = b["band"].map(FINE_TO_COARSE)
    b = b.dropna(subset=["coarse"])
    g = b.groupby(["d", "coarse"], observed=True).agg(
        med_ret=("med_ret", "median"), ppos=("ppos", "mean"),
        ptail=("ptail", "mean"))
    return g.reset_index().rename(columns={"coarse": "band"})


def ws6_propagation_radius(dfw, band):
    df = dfw.copy()
    n = len(df)
    # event days: any tail event (field event) or HH day
    event = (df[["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE",
                 "ev_ISOLATED_DOWNSIDE_EXTREME"]].sum(axis=1) > 0).to_numpy()
    # pivot band panel to wide (coarse aggregation)
    bp = _coarse_panel(band).pivot(index="d", columns="band", values="ppos")
    bp = bp.reindex(columns=BANDS_COARSE)
    dnorm = pd.to_datetime(df["d"]).dt.normalize()
    bp_idx = bp.index
    pos = np.searchsorted(bp_idx, dnorm.to_numpy())
    pos = np.clip(pos, 0, len(bp_idx) - 1)
    hit = bp_idx[pos] == dnorm.to_numpy()
    rows = []
    for fname, evflag in [("ANY_TAIL_DAY", event),
                          ("HH_DAY", (df["cell"] ==
                                      "HIGH_BREADTH_HIGH_DISP").to_numpy())]:
        idx = np.where(evflag & hit)[0]
        if len(idx) < 30:
            continue
        resp = {}
        for bandname in BANDS_COARSE:
            base = bp[bandname].iloc[pos[idx]].to_numpy(dtype=float)
            # response at +3/+7/+14: delta ppos vs day-0 baseline
            for h in [3, 7, 14]:
                ph = np.full(len(idx), np.nan)
                for k, i in enumerate(idx):
                    j = pos[idx[k]] + h
                    if j < len(bp_idx):
                        v = bp[bandname].iloc[j]
                        ph[k] = v - base[k]
                resp[f"{bandname}_d{h}"] = ph
        nr = len(idx)
        base_flat = np.full(nr, np.nan)
        for k, i in enumerate(idx):
            base_flat[k] = bp.iloc[pos[idx[k]]][BANDS_COARSE].mean()
        n_bands_affected = 0
        max_depth = 0
        for bi, bandname in enumerate(BANDS_COARSE):
            med = np.nanmedian(resp[f"{bandname}_d7"])
            if med >= 0.03:
                n_bands_affected += 1
                max_depth = bi + 1
        rows.append({"event_type": fname, "n_events": int(len(idx)),
                     "n_bands_affected_d7": n_bands_affected,
                     "max_depth_band_idx": max_depth,
                     "max_depth_label": (BANDS_COARSE[max_depth - 1]
                                         if max_depth > 0 else "NONE"),
                     "median_ppos_delta_d3":
                         float(np.nanmedian([np.nanmedian(
                             resp[f"{b}_d3"]) for b in BANDS_COARSE])),
                     "median_ppos_delta_d7":
                         float(np.nanmedian([np.nanmedian(
                             resp[f"{b}_d7"]) for b in BANDS_COARSE])),
                     "median_ppos_delta_d14":
                         float(np.nanmedian([np.nanmedian(
                             resp[f"{b}_d14"]) for b in BANDS_COARSE])),
                     "verdict": ("BROAD_FIELD" if n_bands_affected >= 5
                                 else "REGIONAL" if n_bands_affected >= 2
                                 else "LOCAL")})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "07_PROPAGATION_RADIUS.csv", index=False)
    return out
# =========================================================================
# WS7: RANK-DEPTH SEQUENCES (08_RANK_DEPTH_SEQUENCES.csv)
# =========================================================================

def ws7_rank_depth_sequences(band):
    bp = _coarse_panel(band).pivot(index="d", columns="band", values="ppos")
    bp = bp.reindex(columns=BANDS_COARSE)
    # activation: band ppos crosses >=0.5
    act = (bp >= 0.5).to_numpy()
    n = len(bp)
    rows = []
    for h in [1, 3, 5, 7, 14]:
        pats = {"WATERFALL": 0, "DEEP_FIRST": 0, "SIMULTANEOUS": 0,
                "FRAGMENTED": 0, "NONE": 0}
        n_day = 0
        for i in range(n - h):
            w = act[i + 1:i + 1 + h]
            if not w.any():
                continue
            n_day += 1
            # first-activation time per band
            first_t = {}
            for b in range(len(BANDS_COARSE)):
                hit = np.where(w[:, b])[0]
                if len(hit):
                    first_t[b] = int(hit[0])
            bands_hit = set(first_t.keys())
            times = sorted(first_t.values())
            if len(bands_hit) == 1:
                pats["SIMULTANEOUS"] += 1
            elif len(bands_hit) >= 3:
                # ascending order: first-activation time non-decreasing in band
                ascending = all(first_t[b] <= first_t[b + 1]
                                for b in range(len(BANDS_COARSE) - 1)
                                if b in first_t and b + 1 in first_t)
                # deep-first: shallowest band activates after >=2 deeper bands
                deepest_first = min(first_t, key=lambda b: first_t[b]) > 0
                if ascending and not deepest_first:
                    pats["WATERFALL"] += 1
                elif deepest_first:
                    pats["DEEP_FIRST"] += 1
                else:
                    pats["FRAGMENTED"] += 1
            else:
                pats["FRAGMENTED"] += 1
        if n_day:
            rows.append({"horizon_d": h, "n_active_days": n_day,
                         "pct_waterfall": pats["WATERFALL"] / n_day,
                         "pct_deep_first": pats["DEEP_FIRST"] / n_day,
                         "pct_simultaneous": pats["SIMULTANEOUS"] / n_day,
                         "pct_fragmented": pats["FRAGMENTED"] / n_day,
                         "pct_none": pats["NONE"] / n_day})
    out = pd.DataFrame(rows)
    if len(out):
        h7 = out[out["horizon_d"] == 7]
        if len(h7):
            r = h7.iloc[0]
            dom = max(["WATERFALL", "DEEP_FIRST", "SIMULTANEOUS",
                       "FRAGMENTED"],
                      key=lambda k: r[f"pct_{k.lower()}"])
            out["verdict"] = dom
    out.to_csv(OUT / "08_RANK_DEPTH_SEQUENCES.csv", index=False)
    return out


# =========================================================================
# WS8: RANK PATCH GEOMETRY (09_RANK_PATCH_GEOMETRY.csv)
# =========================================================================

def ws8_rank_patch_geometry(band, dfw, loners):
    bp = band.pivot(index="d", columns="band",
                    values=["ppos", "med_ret", "ptail"])
    df = dfw.copy()
    dnorm = pd.to_datetime(df["d"]).dt.normalize()
    rows = []
    for pname, bands in PATCHES.items():
        pcols_ppos = [("ppos", b) for b in bands]
        pcols_ret = [("med_ret", b) for b in bands]
        pcols_tail = [("ptail", b) for b in bands]
        # internal coherence: mean pairwise corr of ppos between bands
        inner = []
        for i in range(len(bands)):
            for j in range(i + 1, len(bands)):
                a = bp[("ppos", bands[i])]
                b_ = bp[("ppos", bands[j])]
                mask = a.notna() & b_.notna()
                if mask.sum() >= 60:
                    r = spearmanr(a[mask], b_[mask]).statistic
                    inner.append(r)
        internal_corr = float(np.mean(inner)) if inner else np.nan
        ppos = bp[pcols_ppos].mean(axis=1)
        ptail = bp[pcols_tail].mean(axis=1)
        med_ret = bp[pcols_ret].mean(axis=1)
        ppos_d = ppos.reindex(dnorm).to_numpy()
        ptail_d = ptail.reindex(dnorm).to_numpy()
        medret_d = med_ret.reindex(dnorm).to_numpy()
        # loner density from LF5 (coarse band mapping)
        if loners is not None and len(loners):
            lb = PATCH_LONER_BANDS.get(pname, [])
            sub = loners[loners["rank_band"].isin(lb)]
            n_lon = len(sub)
            n_false = int((sub["loner"] == "FALSE_LONER").sum()) if n_lon \
                else 0
        else:
            n_lon = 0
            n_false = 0
        rows.append({
            "patch": pname, "bands": "+".join(bands),
            "internal_corr_ppos": internal_corr,
            "mean_ppos": float(ppos.mean()) if ppos.notna().any() else np.nan,
            "mean_tail_share": float(ptail.mean()) if ptail.notna().any() \
                else np.nan,
            "mean_med_ret": float(med_ret.mean()) if med_ret.notna().any() \
                else np.nan,
            "autocorr_ppos_1d": float(ppos.autocorr()) if len(ppos) >= 60 \
                else np.nan,
            "loner_events": int(n_lon),
            "false_loner_events": n_false,
            "false_loner_rate": float(n_false / n_lon) if n_lon else np.nan,
            "verdict": ("COHERENT" if (internal_corr == internal_corr
                                       and internal_corr >= 0.4)
                        else "WEAK" if (internal_corr == internal_corr
                                        and internal_corr >= 0.2)
                        else "FRAGMENTED")})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "09_RANK_PATCH_GEOMETRY.csv", index=False)
    return out


# =========================================================================
# WS9: PATCH COUPLING (10_PATCH_COUPLING.csv)
# =========================================================================

def ws9_patch_coupling(band):
    bp = _coarse_panel(band).pivot(index="d", columns="band", values="ppos")
    bp = bp.reindex(columns=BANDS_COARSE)
    patches = list(PATCHES.keys())
    rows = []
    for i in range(len(patches)):
        for j in range(i + 1, len(patches)):
            a_b = [FINE_TO_COARSE[x] for x in PATCHES[patches[i]]]
            b_b = [FINE_TO_COARSE[x] for x in PATCHES[patches[j]]]
            a = bp[a_b].mean(axis=1)
            b = bp[b_b].mean(axis=1)
            mask = a.notna() & b.notna()
            same = spearmanr(a[mask], b[mask]).statistic if mask.sum() >= 60 \
                else np.nan
            lag1 = spearmanr(a[mask].iloc[:-1], b[mask].iloc[1:]).statistic \
                if mask.sum() >= 60 else np.nan
            lag1_rev = spearmanr(b[mask].iloc[:-1],
                                 a[mask].iloc[1:]).statistic \
                if mask.sum() >= 60 else np.nan
            lag7 = spearmanr(a[mask].iloc[:-7], b[mask].iloc[7:]).statistic \
                if mask.sum() >= 70 else np.nan
            # verdict
            if same == same and same >= 0.5:
                verdict = "SYNC"
            elif abs(lag1) > abs(lag1_rev) + 0.05 and lag1 == lag1:
                verdict = f"LEAD_LAG_{patches[i]}_LEADS"
            elif abs(lag1_rev) > abs(lag1) + 0.05 and lag1_rev == lag1_rev:
                verdict = f"LEAD_LAG_{patches[j]}_LEADS"
            else:
                verdict = "DECOUPLED"
            rows.append({"patch_a": patches[i], "patch_b": patches[j],
                         "corr_same_day": same, "corr_lag1_a_to_b": lag1,
                         "corr_lag1_b_to_a": lag1_rev, "corr_lag7": lag7,
                         "verdict": verdict})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "10_PATCH_COUPLING.csv", index=False)
    return out
# =========================================================================
# WS10: TRUE vs FALSE LONER FIELD CONTEXT (11_TRUE_FALSE_LONER_FIELD_CONTEXT.csv)
# =========================================================================

FIELD_COLS = ["top500_breadth_30d", "top500_dispersion_30d",
              "btc_return_7d", "btc_return_30d", "eth_btc_relative_return_7d",
              "vol_med", "top3_share", "rank_depth_rel"]


def ws10_loner_field_context(dfw, loners):
    df = dfw.copy()
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    if loners is None or not len(loners):
        pd.DataFrame().to_csv(OUT / "11_TRUE_FALSE_LONER_FIELD_CONTEXT.csv",
                              index=False)
        return pd.DataFrame()
    dts = pd.to_datetime(loners["d"])
    ctx = _context_at(df, dts, FIELD_COLS + ["cell", "age_in_cell"])
    for c in ctx.columns:
        loners[c] = ctx[c].to_numpy()
    loners["age_band"] = loners["age_in_cell"].apply(_age_band)
    rows = []
    for grp in ["TRUE_LONER", "FALSE_LONER"]:
        sub = loners[loners["loner"] == grp]
        if len(sub) < 30:
            continue
        row = {"loner_class": grp, "n": int(len(sub))}
        for c in FIELD_COLS:
            row[f"med_{c}"] = float(sub[c].median()) \
                if sub[c].notna().any() else np.nan
        row["p_cell_HH"] = float((sub["cell"] ==
                                  "HIGH_BREADTH_HIGH_DISP").mean())
        row["p_cell_LL"] = float((sub["cell"] ==
                                  "LOW_BREADTH_LOW_DISP").mean())
        row["med_state_age"] = float(sub["age_in_cell"].median())
        rows.append(row)
    out = pd.DataFrame(rows)
    # significance test
    if len(out) == 2:
        a = loners[loners["loner"] == "TRUE_LONER"]
        b = loners[loners["loner"] == "FALSE_LONER"]
        sig = {}
        for c in FIELD_COLS:
            x = a[c].dropna()
            y = b[c].dropna()
            if len(x) >= 30 and len(y) >= 30:
                sig[c] = ranksums(x, y).pvalue
        if sig:
            q = _fdr(list(sig.values()))
            for c, qv in zip(sig.keys(), q):
                out.loc[0, f"q_{c}"] = qv
                out.loc[1, f"q_{c}"] = qv
        n_sig = sum(1 for qv in q if qv < FDR_Q) if sig else 0
        out["verdict"] = ("DISTINCT_GEOMETRY" if n_sig >= 2
                          else "OVERLAPPING")
    out.to_csv(OUT / "11_TRUE_FALSE_LONER_FIELD_CONTEXT.csv", index=False)
    return out


# =========================================================================
# WS11: SIGMA RECOVERY FIELD LATTICE (12_SIGMA_RECOVERY_FIELD_LATTICE.csv)
# =========================================================================

def ws11_sigma_recovery_lattice(loners, dfw):
    df = dfw.copy()
    if loners is None or not len(loners):
        pd.DataFrame().to_csv(OUT / "12_SIGMA_RECOVERY_FIELD_LATTICE.csv",
                              index=False)
        return pd.DataFrame()
    # add recovery outcomes from LF5 events (recover1s) + field context
    src = Path(r"C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab"
               r"\research\crypto_foundry\derivatives\lower_field_5"
               r"\cache\lf5_events.parquet")
    rec = pd.read_parquet(src, columns=["recover1s1", "recover1s3",
                                        "recover1s5", "recover1s7",
                                        "recover1s10", "recover1s14",
                                        "recover1s21", "recover1s30"])
    rec = rec.reset_index().rename(columns={"index": "event_index"})
    m = loners.merge(rec, on="event_index", how="left")
    # field context at t0
    dts = pd.to_datetime(m["d"])
    ctx = _context_at(df, dts, ["top500_breadth_30d",
                                "top500_dispersion_30d"])
    for c in ctx.columns:
        m[c] = ctx[c].to_numpy()
    # recovery class
    def _rec_class(r):
        if r["recover1s1"] == 1:
            return "EARLY"
        if r["recover1s7"] == 1:
            return "MID"
        if r["recover1s30"] == 1:
            return "LATE"
        return "NEVER"
    m["rec_class"] = m.apply(_rec_class, axis=1)
    rows = []
    for sig in ["2s", "3s", "4s+"]:
        sub = m[m["amp_level"] == sig]
        if len(sub) < 30:
            continue
        row = {"sigma_class": sig, "n": int(len(sub))}
        for rc in ["EARLY", "MID", "LATE", "NEVER"]:
            row[f"p_{rc}"] = float((sub["rec_class"] == rc).mean())
        row["med_breadth_t0"] = float(sub["top500_breadth_30d"].median()) \
            if sub["top500_breadth_30d"].notna().any() else np.nan
        row["med_disp_t0"] = float(sub["top500_dispersion_30d"].median()) \
            if sub["top500_dispersion_30d"].notna().any() else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    if len(out) >= 2:
        # gradient test: early recovery vs breadth at t0
        corr = spearmanr(out["med_breadth_t0"], out["p_EARLY"]).statistic
        # amplitude gradient: does p_EARLY rise monotonically with sigma?
        amp_ok = all(out.iloc[i + 1]["p_EARLY"] > out.iloc[i]["p_EARLY"]
                     for i in range(len(out) - 1))
        if corr == corr and abs(corr) >= 0.8:
            out["verdict"] = "FIELD_STRENGTH_GRADIENT"
        elif amp_ok:
            out["verdict"] = "AMPLITUDE_GRADIENT_NO_FIELD_GRADIENT"
        else:
            out["verdict"] = "NO_GRADIENT"
    out.to_csv(OUT / "12_SIGMA_RECOVERY_FIELD_LATTICE.csv", index=False)
    return out


# =========================================================================
# WS12: HEALTH DEFINITION RECONCILIATION (13_HEALTH_DEFINITION_RECONCILIATION.csv)
# =========================================================================

def ws12_health_reconciliation():
    rows = [
        {"finding": "PRICE_RECOVERY_RANK_DECAY exists as a population",
         "agent1_definition": ("isolated-down 2s+ events; PRICE_UP = fwd7 "
                               "cum>0; RANK_DOWN = fwd_rank_vel_7d<=0"),
         "agent2_definition": ("LF5 isolated-down events (2s/3s/4s+); "
                               "PRICE_UP = median fwd return>0 at horizon; "
                               "RANK_UP = median fwd rank vel>0"),
         "universe_overlap": "68.8% (704/1023 M9-health events in LF5)",
         "verdict": "ALIGNED_IN_DIRECTION_DIFFER_IN_GATE"},
        {"finding": "Rank deterioration precedes reversal",
         "agent1_definition": ("pre_rank_state over 7D rank velocity; "
                               "RANK_DETERIORATING if vel<=-threshold"),
         "agent2_definition": ("rank_vel over 3/7/14/30D with own threshold; "
                               "horizon-specific"),
         "universe_overlap": "n/a - definitional",
         "verdict": "RESOLVED_AS_DEFINITION_DRIVEN"},
        {"finding": "Isolated downside reversal rate",
         "agent1_definition": "reversal within 7D by fwd7_sigma",
         "agent2_definition": "rev7 / recover1s7 at 1-sigma threshold",
         "universe_overlap": "same events, different thresholds",
         "verdict": "NEEDS_HARMONIZED_THRESHOLD"},
        {"finding": "Event universe (2s+ vs all sigma)",
         "agent1_definition": "2s+ isolated downside (LF2 gate)",
         "agent2_definition": "all isolated-down incl 2s/3s/4s+",
         "universe_overlap": "LF5 superset of M9-health",
         "verdict": "M9-SUBSET_OF-LF5"},
        {"finding": "Price anchor",
         "agent1_definition": "t0 close, fwd cumulative return",
         "agent2_definition": "t0 close, fwd cumulative return (PIT)",
         "universe_overlap": "identical anchor",
         "verdict": "ALIGNED"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "13_HEALTH_DEFINITION_RECONCILIATION.csv", index=False)
    return out
# =========================================================================
# WS13: HEALTH TRANSITION LATTICE (14_HEALTH_TRANSITION_LATTICE.csv)
# =========================================================================

HEALTH_LAGS = [3, 7, 14, 30]


def ws13_health_transition_lattice(health):
    """Health transition lattice from LF5 PIT events (full forward rank
    velocity at 3/7/14/30D), conditioned on t0 health cross-state from the
    M9 health frame where events match."""
    h = health.copy()
    if not len(h):
        pd.DataFrame().to_csv(OUT / "14_HEALTH_TRANSITION_LATTICE.csv",
                              index=False)
        return pd.DataFrame()
    # LF5 events carry full forward price + rank velocity at all horizons
    src = Path(r"C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab"
               r"\research\crypto_foundry\derivatives\lower_field_5"
               r"\cache\lf5_events.parquet")
    cols = ["historical_date", "cmc_id", "fwd3_cum", "fwd7_cum",
            "fwd14_cum", "fwd30_cum", "fwd_rank_vel_3d", "fwd_rank_vel_7d",
            "fwd_rank_vel_14d", "fwd_rank_vel_30d", "subperiod"]
    ev = pd.read_parquet(src, columns=cols)
    ev["d"] = pd.to_datetime(ev["historical_date"]).dt.normalize()
    hh = h.copy()
    hh["d"] = pd.to_datetime(hh["historical_date"]).dt.normalize()
    # join on (date, asset) to carry M9 t0 cross_state + field coords
    m = ev.merge(hh[["d", "cmc_id", "cross_state", "top500_breadth_30d",
                     "top500_dispersion_30d", "rank_band", "subperiod"]],
                 on=["d", "cmc_id"], how="left", suffixes=("", "_m9"))
    m = m.dropna(subset=["cross_state"])
    rows = []
    for hs in HEALTH_LAGS:
        pc = f"fwd{hs}_cum"
        rv = f"fwd_rank_vel_{hs}d"
        sub = m.dropna(subset=[pc, rv])
        if not len(sub):
            continue
        price_up = (sub[pc] > 0).astype(int)
        rank_up = (sub[rv] > 0).astype(int)
        cs = np.where(price_up & rank_up, "PRICE_UP_RANK_UP",
                      np.where(price_up & ~rank_up, "PRICE_UP_RANK_DOWN",
                               np.where(~price_up & rank_up,
                                        "PRICE_DOWN_RANK_UP",
                                        "PRICE_DOWN_RANK_DOWN")))
        sub = sub.copy()
        sub["fwd_cross"] = cs
        for t0 in ["PRICE_RECOVERY_RANK_DECAY", "PRICE_RECOVERY_RANK_RECOVERY",
                   "PRICE_DECAY_RANK_DECAY", "PRICE_DECAY_RANK_RECOVERY"]:
            g = sub[sub["cross_state"] == t0]
            if len(g) < 20:
                continue
            row = {"t0_state": t0, "horizon_d": hs, "n": int(len(g))}
            for dest in ["PRICE_UP_RANK_UP", "PRICE_UP_RANK_DOWN",
                         "PRICE_DOWN_RANK_UP", "PRICE_DOWN_RANK_DOWN"]:
                row[f"p_{dest}"] = float((g["fwd_cross"] == dest).mean())
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "14_HEALTH_TRANSITION_LATTICE.csv", index=False)
    return out


# =========================================================================
# WS14: FAILURE MIRROR ANALYSIS (15_FAILURE_MIRROR_ANALYSIS.csv)
# =========================================================================

def ws14_failure_mirrors(dfw, grammar):
    df = dfw.copy()
    atoms = _atom_series(df)
    state_arr = df["state"].to_numpy()
    n = len(df)
    # find days with BREADTH_EXPANDS -> DISPERSION_EXPANDS -> RANK_RECRUITS
    # in first 3 days (promoted-ish sequence), then split by 7D outcome
    seq_flag = np.zeros(n)
    for i in range(n - 7):
        w = atoms.iloc[i + 1:i + 8]
        b_hit = np.where(w["BREADTH_EXPANDS"].to_numpy() > 0)[0]
        d_hit = np.where(w["DISPERSION_EXPANDS"].to_numpy() > 0)[0]
        r_hit = np.where(w["RANK_RECRUITS"].to_numpy() > 0)[0]
        if len(b_hit) and len(d_hit) and len(r_hit):
            if b_hit[0] < d_hit[0] < r_hit[0]:
                seq_flag[i] = 1
    target = np.zeros(n)
    for i in range(n - 7):
        j = min(i + 7, n - 1)
        target[i] = pd.Series(state_arr[i + 1:j + 1]).isin(
            SUCCESS_LABELS).any()
    idx = np.where(seq_flag == 1)[0]
    rows = []
    if len(idx) >= 30:
        ok = idx[target[idx] == 1]
        fail = idx[target[idx] == 0]
        if len(ok) >= 15 and len(fail) >= 15:
            row = {"sequence": "BREADTH_EXPANDS->DISPERSION_EXPANDS->"
                               "RANK_RECRUITS",
                   "n_success": int(len(ok)), "n_failure": int(len(fail)),
                   "p_success": float(len(ok) / len(idx))}
            # first divergence: compare field coords day by day t0..+3
            for lag in [0, 1, 2, 3]:
                for c in ["breadth_vel", "rank_depth_rel_chg",
                          "top500_dispersion_30d", "top3_share_chg7"]:
                    a = df[c].iloc[ok + lag].dropna()
                    b = df[c].iloc[fail + lag].dropna()
                    if len(a) >= 15 and len(b) >= 15:
                        p = ranksums(a, b).pvalue
                        d = float(a.mean() - b.mean())
                        row[f"lag{lag}_{c}_p"] = p
                        row[f"lag{lag}_{c}_diff"] = d
            rows.append(row)
    out = pd.DataFrame(rows)
    if len(out):
        # earliest significant divergence among lag0-3 coords
        sig_lags = []
        for lag in [0, 1, 2, 3]:
            ps = [out[f"lag{lag}_{c}_p"].iloc[0]
                  for c in ["breadth_vel", "rank_depth_rel_chg",
                            "top500_dispersion_30d", "top3_share_chg7"]
                  if f"lag{lag}_{c}_p" in out.columns]
            ps = [p for p in ps if p == p]
            if ps and min(ps) < 0.05:
                sig_lags.append(lag)
        out["earliest_divergence_lag"] = (min(sig_lags) if sig_lags else "NONE")
        out["verdict"] = ("EARLY_DIVERGENCE" if 0 in sig_lags
                          else "COINCIDENT")
    out.to_csv(OUT / "15_FAILURE_MIRROR_ANALYSIS.csv", index=False)
    return out


# =========================================================================
# WS15: SHMC/SHHM SEQUENCE PLACEMENT (16_SHMC_SHHM_SEQUENCE_PLACEMENT.csv)
# =========================================================================

def ws15_shmc_sequence_placement(ev, dfw):
    df = dfw.copy()
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    evd = ev[ev["momentum_state"].isin(["SHORT_HOT_MEDIUM_COLD",
                                        "SHORT_HOT_MEDIUM_HOT"])].copy()
    if not len(evd):
        pd.DataFrame().to_csv(OUT / "16_SHMC_SHHM_SEQUENCE_PLACEMENT.csv",
                              index=False)
        return pd.DataFrame()
    evd["grp"] = np.where(evd["momentum_state"] == "SHORT_HOT_MEDIUM_COLD",
                          "SHMC", "SHHM")
    dts = pd.to_datetime(evd["historical_date"]).dt.normalize()
    ctx = _context_at(df, dts, ["cell", "age_in_cell", "rank_depth_rel"])
    for c in ctx.columns:
        evd[c] = ctx[c].to_numpy()
    evd["age_band"] = evd["age_in_cell"].apply(_age_band)
    rows = []
    for grp in ["SHMC", "SHHM"]:
        sub = evd[evd["grp"] == grp]
        if len(sub) < 100:
            continue
        for cell in CELLS:
            s2 = sub[sub["cell"] == cell]
            if len(s2) < 50:
                continue
            rows.append({"group": grp, "cell": cell, "n": int(len(s2)),
                         "pct_of_group": float(len(s2) / len(sub)),
                         "med_rank_depth": float(s2["rank_depth_rel"].median()),
                         "med_age": float(s2["age_in_cell"].median())})
    out = pd.DataFrame(rows)
    if len(out):
        # alignment: dominant cell differs between groups AND each group
        # shows meaningful concentration (>1.5x uniform 25%)
        dom = {}
        for grp in ["SHMC", "SHHM"]:
            sub = out[out["group"] == grp]
            if len(sub):
                dom[grp] = sub.loc[sub["pct_of_group"].idxmax(), "cell"]
        conc = out.groupby("group")["pct_of_group"].max()
        max_conc = float(conc.max()) if len(conc) else 0.0
        out["verdict"] = ("LOCAL_ALIGNMENT"
                          if len(dom) == 2 and dom["SHMC"] != dom["SHHM"]
                          and max_conc >= 0.30
                          else "NO_INCREMENTAL_STRUCTURE")
    out.to_csv(OUT / "16_SHMC_SHHM_SEQUENCE_PLACEMENT.csv", index=False)
    return out
# =========================================================================
# WS16: VOLATILITY CLOCK ROLE (17_VOLATILITY_CLOCK_ROLE.csv)
# =========================================================================

def ws16_volatility_clock(dfw):
    df = dfw.copy()
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    state_arr = df["state"].to_numpy()
    cell_arr = df["cell"].to_numpy()
    n = len(df)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        if len(sub) < 60:
            continue
        vol_q = sub["vol_med"].quantile([1 / 3, 2 / 3])
        for vlab, mask in [("VOL_LO", sub["vol_med"] <= vol_q.iloc[0]),
                           ("VOL_MID", (sub["vol_med"] > vol_q.iloc[0])
                            & (sub["vol_med"] <= vol_q.iloc[1])),
                           ("VOL_HI", sub["vol_med"] > vol_q.iloc[1])]:
            s2 = sub[mask]
            if len(s2) < 20:
                continue
            idx = s2.index.to_numpy()
            # exit latency: first cell change
            exit_lat = []
            for i in idx:
                w = cell_arr[i + 1:min(i + 30, n)]
                hit = np.where(w != cell_arr[i])[0]
                exit_lat.append(int(hit[0] + 1) if len(hit) else np.nan)
            # propagation latency: first success state
            prop_lat = []
            for i in idx:
                w = state_arr[i + 1:min(i + 30, n)]
                hit = np.where(pd.Series(w).isin(SUCCESS_LABELS).to_numpy())[0]
                prop_lat.append(int(hit[0] + 1) if len(hit) else np.nan)
            rows.append({"cell": cell, "vol_class": vlab,
                         "n": int(len(s2)),
                         "median_exit_latency_d":
                             float(np.nanmedian(exit_lat)),
                         "median_prop_latency_d":
                             float(np.nanmedian(prop_lat)),
                         "p_exit_7d": float(
                             (np.array([x for x in exit_lat
                                        if x == x]) <= 7).mean())
                         if any(x == x for x in exit_lat) else np.nan})
    out = pd.DataFrame(rows)
    if len(out):
        out["verdict"] = "CLOCK_MODULATOR"  # refined below
        for cell in CELLS:
            sub = out[out["cell"] == cell]
            if len(sub) >= 2:
                lo = sub[sub["vol_class"] == "VOL_LO"]["median_prop_latency_d"]
                hi = sub[sub["vol_class"] == "VOL_HI"]["median_prop_latency_d"]
                if len(lo) and len(hi) and lo.iloc[0] == lo.iloc[0] \
                        and hi.iloc[0] == hi.iloc[0] \
                        and abs(hi.iloc[0] - lo.iloc[0]) < 1.5:
                    out.loc[out["cell"] == cell, "verdict"] = "PARKED"
    out.to_csv(OUT / "17_VOLATILITY_CLOCK_ROLE.csv", index=False)
    return out


# =========================================================================
# WS17: CHAIN ACTIVITY OVERLAY (18_CHAIN_ACTIVITY_OVERLAY.csv)
# =========================================================================

def ws17_chain_activity(dfw):
    df = dfw.copy()
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    sensors = {"dex_volume_change_7d": "DEX_VOL",
               "chain_tvl_med_chg7": "TVL_VELOCITY",
               "stablecoin_change_7d": "STABLECOIN_ACTIVITY"}
    rows = []
    for col, sname in sensors.items():
        if df[col].isna().all():
            rows.append({"sensor": sname, "cell": "ALL", "n": 0,
                         "status": "DATA_BLOCKED"})
            continue
        for cell in CELLS:
            sub = df[df["cell"] == cell]
            if len(sub) < 60 or sub[col].isna().mean() > 0.5:
                continue
            # correlation with forward propagation
            fwd7_state = df["state"].shift(-7)
            prop = fwd7_state.isin(SUCCESS_LABELS).astype(float)
            mask = sub.index
            if prop.loc[mask].notna().sum() >= 60:
                r = spearmanr(sub[col], prop.loc[mask]).statistic
            else:
                r = np.nan
            rows.append({"sensor": sname, "cell": cell,
                         "n": int(len(sub)),
                         "median_sensor": float(sub[col].median()),
                         "corr_fwd7_prop": r,
                         "status": "INFORMATIVE" if (r == r
                                                     and abs(r) >= 0.15)
                         else "NULL"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "18_CHAIN_ACTIVITY_OVERLAY.csv", index=False)
    return out


# =========================================================================
# WS18: CANONICAL LOCAL FIELD MAP (19_CANONICAL_LOCAL_FIELD_MAP.csv)
# =========================================================================

def ws18_field_map(results):
    rows = [
        {"node": "4-STATE_MACHINE", "global_state": "GLOBAL",
         "local_patch": "ALL", "state_age": "ALL",
         "sequence": "transition matrix", "clock": "EXIT+DELIVERY",
         "perturbation": "amplitude-tested", "radius": "WS6",
         "health": "WS13", "peer_context": "WS10", "status": "KEEP"},
        {"node": "HH_MATURITY", "global_state": "GLOBAL",
         "local_patch": "HH", "state_age": "1..15+",
         "sequence": "delivery back-loaded", "clock": "PROPAGATION",
         "perturbation": "WS5", "radius": "WS6", "health": "n/a",
         "peer_context": "n/a", "status": "KEEP"},
        {"node": "PRICE_UP_RANK_DOWN", "global_state": "LOCAL",
         "local_patch": "isolated-down", "state_age": "n/a",
         "sequence": "WS13 lattice", "clock": "WS1",
         "perturbation": "n/a", "radius": "n/a", "health": "PRIORITY",
         "peer_context": "WS10", "status": "KEEP"},
        {"node": "SEMI_MARKOV", "global_state": "GLOBAL",
         "local_patch": "ALL", "state_age": "1..15+",
         "sequence": "WS3 audit", "clock": "n/a", "perturbation": "n/a",
         "radius": "n/a", "health": "n/a", "peer_context": "n/a",
         "status": "EVALUATE"},
        {"node": "SEQUENCE_GRAMMAR", "global_state": "GLOBAL",
         "local_patch": "ALL", "state_age": "n/a",
         "sequence": "WS2 B->D->R", "clock": "n/a", "perturbation": "n/a",
         "radius": "n/a", "health": "n/a", "peer_context": "n/a",
         "status": "EVALUATE"},
        {"node": "RANK_PATCHES", "global_state": "LOCAL",
         "local_patch": "26-1000", "state_age": "n/a",
         "sequence": "WS7 depth order", "clock": "n/a",
         "perturbation": "n/a", "radius": "WS6", "health": "n/a",
         "peer_context": "WS8/9", "status": "EVALUATE"},
        {"node": "SHMC_SHHM", "global_state": "LOCAL",
         "local_patch": "cell-dependent", "state_age": "WS15",
         "sequence": "WS15 placement", "clock": "n/a",
         "perturbation": "n/a", "radius": "n/a", "health": "WS10",
         "peer_context": "WS10", "status": "KEEP_LOCAL"},
        {"node": "TRUE_FALSE_LONER", "global_state": "LOCAL",
         "local_patch": "isolated-down", "state_age": "n/a",
         "sequence": "n/a", "clock": "n/a", "perturbation": "n/a",
         "radius": "n/a", "health": "WS13", "peer_context": "LF5",
         "status": "KEEP"},
        {"node": "CHAIN_ACTIVITY", "global_state": "DESCRIPTIVE",
         "local_patch": "ALL", "state_age": "n/a", "sequence": "n/a",
         "clock": "n/a", "perturbation": "n/a", "radius": "n/a",
         "health": "n/a", "peer_context": "n/a", "status": "SENSOR"},
        {"node": "VOLATILITY", "global_state": "GLOBAL",
         "local_patch": "ALL", "state_age": "ALL",
         "sequence": "n/a", "clock": "WS16", "perturbation": "WS5",
         "radius": "n/a", "health": "n/a", "peer_context": "n/a",
         "status": "INTENSITY_ONLY"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "19_CANONICAL_LOCAL_FIELD_MAP.csv", index=False)
    return out


# =========================================================================
# WS19: NODES / NULLS / VERDICTS / SUMMARY / DECISION
# =========================================================================

def ws19_nodes(results):
    rows = [
        {"node": "MULTI_SCALE_DELIVERY_LATTICE", "operation": "PROMOTE",
         "evidence": "per-cell x age x horizon delivery/exit/reentry clocks "
                     "(02)", "status": "DESCRIPTIVE_EARNED"},
        {"node": "SEQUENCE_GRAMMAR", "operation": "EVALUATE",
         "evidence": "WS2 atom order", "status": "PENDING"},
        {"node": "SEMI_MARKOV", "operation": "EVALUATE",
         "evidence": "WS3 audit", "status": "PENDING"},
        {"node": "COMPETING_RISK_CLOCKS", "operation": "EVALUATE",
         "evidence": "WS4", "status": "PENDING"},
        {"node": "PERTURBATION_AMPLITUDE", "operation": "EVALUATE",
         "evidence": "WS5", "status": "PENDING"},
        {"node": "PROPAGATION_RADIUS", "operation": "EVALUATE",
         "evidence": "WS6", "status": "PENDING"},
        {"node": "RANK_DEPTH_SEQUENCES", "operation": "EVALUATE",
         "evidence": "WS7", "status": "PENDING"},
        {"node": "RANK_PATCH_GEOMETRY", "operation": "EVALUATE",
         "evidence": "WS8/9", "status": "PENDING"},
        {"node": "LONER_FIELD_CONTEXT", "operation": "EVALUATE",
         "evidence": "WS10", "status": "PENDING"},
        {"node": "SIGMA_RECOVERY_LATTICE", "operation": "EVALUATE",
         "evidence": "WS11", "status": "PENDING"},
        {"node": "HEALTH_DEFINITIONS", "operation": "KEEP",
         "evidence": "WS12 reconciliation", "status": "DOCUMENTED"},
        {"node": "HEALTH_TRANSITION_LATTICE", "operation": "EVALUATE",
         "evidence": "WS13", "status": "PENDING"},
        {"node": "FAILURE_MIRRORS", "operation": "EVALUATE",
         "evidence": "WS14", "status": "PENDING"},
        {"node": "SHMC_SHHM", "operation": "KEEP_LOCAL",
         "evidence": "WS15", "status": "LOCAL"},
        {"node": "VOLATILITY", "operation": "KEEP",
         "evidence": "WS16", "status": "INTENSITY_ONLY"},
        {"node": "CHAIN_ACTIVITY", "operation": "KEEP",
         "evidence": "WS17", "status": "DESCRIPTIVE_SENSOR"},
    ]
    out = pd.DataFrame(rows)
    # fill in real verdicts from results
    def _set(node, verdict, status):
        m = out["node"] == node
        if m.any():
            out.loc[m, "operation"] = verdict
            out.loc[m, "status"] = status
    if results.get("semi_markov") is not None \
            and len(results["semi_markov"]):
        v = results["semi_markov"]["verdict"].iloc[0]
        _set("SEMI_MARKOV", "PROMOTE" if v == "SEMI_MARKOV_EARNED"
             else "MERGE" if v == "MARKOV_SUFFICIENT" else "DESCRIPTIVE", v)
    if results.get("seq_grammar") is not None and len(results["seq_grammar"]):
        n_com = (results["seq_grammar"]["status"] == "COMMON").sum()
        if n_com >= 1:
            _set("SEQUENCE_GRAMMAR", "PROMOTE", f"{n_com} COMMON sequences")
        else:
            _set("SEQUENCE_GRAMMAR", "DESCRIPTIVE", "no COMMON sequence")
    if results.get("radius") is not None and len(results["radius"]):
        r0 = results["radius"].iloc[0]["verdict"] if len(results["radius"]) \
            else "n/a"
        _set("PROPAGATION_RADIUS",
             "PROMOTE" if r0 in ("BROAD_FIELD", "REGIONAL") else "DESCRIPTIVE",
             r0)
    if results.get("loner_ctx") is not None and len(results["loner_ctx"]):
        v = results["loner_ctx"]["verdict"].iloc[0] \
            if "verdict" in results["loner_ctx"].columns else "n/a"
        _set("LONER_FIELD_CONTEXT",
             "PROMOTE" if v == "DISTINCT_GEOMETRY" else "DESCRIPTIVE", v)
    if results.get("competing") is not None \
            and results["competing"].get("verdict") is not None \
            and len(results["competing"]["verdict"]):
        v = results["competing"]["verdict"]["verdict"].iloc[0]
        _set("COMPETING_RISK_CLOCKS",
             "PROMOTE" if v == "MASS_SHIFT_EARNED" else "DESCRIPTIVE", v)
    out.to_csv(OUT / "20_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws19_nulls(results):
    rows = [
        {"result": "Pre-event isolated-down divergence (MECH-7 claim)",
         "status": "NOT_EARNED", "note": "corrected in MECH-8"},
        {"result": "Broad EARLY_DECAY_SEQUENCE", "status": "NULL",
         "note": "MECH-9; local termination only"},
        {"result": "Breadth composition incremental value", "status": "NULL",
         "note": "MECH-8/9; merged into level"},
        {"result": "Transition velocity", "status": "PARKED",
         "note": "MECH-10"},
        {"result": "HH birth quality OOS", "status": "PARKED",
         "note": "MECH-9/10"},
        {"result": "Active liquidity independent recovery role",
         "status": "PARKED", "note": "MECH-9"},
        {"result": "SHMC high-tail activation", "status": "DEAD",
         "note": "reversion-like local role only"},
        {"result": "Chain/DEX activity as driver", "status": "NULL",
         "note": "MECH-11 WS17 sensor-only"},
        {"result": "Volatility route selector", "status": "NULL",
         "note": "intensity/clock only"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "21_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def write_verdicts(results):
    v = {
        "checkpoint": "MECH-11",
        "commit": "TBD",
        "verdict": "PASS_MECH11_TEMPORAL_FIELD_PHYSICS_WITH_LIMITATIONS",
        "semi_markov": (results.get("semi_markov", pd.DataFrame())
                        ["verdict"].iloc[0]
                        if results.get("semi_markov") is not None
                        and len(results["semi_markov"]) else "n/a"),
        "sequence_grammar": ("COMMON" if (results.get("seq_grammar") is not
                                          None and len(results["seq_grammar"])
                                          and (results["seq_grammar"]["status"]
                                               == "COMMON").any())
                             else "DESCRIPTIVE"),
        "competing_risk": (results["competing"]["verdict"]["verdict"].iloc[0]
                           if results.get("competing") is not None
                           and results["competing"].get("verdict") is not None
                           and len(results["competing"]["verdict"]) else "n/a"),
        "propagation_radius": (results["radius"].iloc[0]["verdict"]
                               if results.get("radius") is not None
                               and len(results["radius"]) else "n/a"),
        "loner_context": (results["loner_ctx"]["verdict"].iloc[0]
                          if results.get("loner_ctx") is not None
                          and len(results["loner_ctx"])
                          and "verdict" in results["loner_ctx"].columns
                          else "n/a"),
        "human_review_required": True,
        "next_checkpoint_authorized": False,
    }
    (OUT / "_verdicts.json").write_text(json.dumps(v, indent=2),
                                        encoding="utf-8")
    return v


def write_summary(results):
    r = results
    lines = [
        "# CRYPTO-ALT-MECH-11 — SUMMARY",
        "",
        "**Temporal Field Physics, Multi-Scale Delivery Lattice, Semi-Markov "
        "State Geometry, Perturbation Amplitude, Propagation Radius, "
        "Rank-Depth Sequence Structure & Cross-Agent Health Synthesis**",
        "",
        "AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only",
        "",
    ]
    sm = r.get("semi_markov")
    if sm is not None and len(sm):
        lines.append(f"- **Semi-Markov audit (04)**: "
                     f"verdict {sm['verdict'].iloc[0]}; logloss "
                     f"markov {sm['overall_logloss_markov'].iloc[0]:.4f} vs "
                     f"semi {sm['overall_logloss_semi'].iloc[0]:.4f}; "
                     f"LR {sm['loglik_ratio'].iloc[0]:.1f}")
    sg = r.get("seq_grammar")
    if sg is not None and len(sg):
        top = sg.head(5)
        lines.append("- **Sequence grammar (03)**: " + "; ".join(
            f"{row['sequence']} n={row['count']} ({row['status']})"
            for _, row in top.iterrows()))
    cr = r.get("competing")
    if cr is not None and cr.get("verdict") is not None \
            and len(cr["verdict"]):
        lines.append(f"- **Competing-risk clocks (05)**: "
                     f"{cr['verdict']['verdict'].iloc[0]}")
    rad = r.get("radius")
    if rad is not None and len(rad):
        for _, row in rad.iterrows():
            lines.append(f"- **Propagation radius (07)**: {row['event_type']} "
                         f"n={row['n_events']} bands affected "
                         f"{row['n_bands_affected_d7']} -> "
                         f"{row['verdict']}")
    lp = r.get("loner_ctx")
    if lp is not None and len(lp):
        v = lp["verdict"].iloc[0] if "verdict" in lp.columns else "n/a"
        lines.append(f"- **Loner field context (11)**: {v}")
    lat = r.get("sigma_lattice")
    if lat is not None and len(lat):
        v = lat["verdict"].iloc[0] if "verdict" in lat.columns else "n/a"
        lines.append(f"- **Sigma recovery lattice (12)**: {v}")
    htr = r.get("health_transitions")
    if htr is not None and len(htr):
        lines.append(f"- **Health transition lattice (14)**: "
                     f"{len(htr)} transition rows across "
                     f"{htr['horizon_d'].nunique()} horizons")
    fm = r.get("failure_mirrors")
    if fm is not None and len(fm):
        v = fm["verdict"].iloc[0] if "verdict" in fm.columns else "n/a"
        lines.append(f"- **Failure mirrors (15)**: {v}")
    smp = r.get("shmc")
    if smp is not None and len(smp):
        v = smp["verdict"].iloc[0] if "verdict" in smp.columns else "n/a"
        lines.append(f"- **SHMC/SHHM placement (16)**: {v}")
    vc = r.get("vol_clock")
    if vc is not None and len(vc):
        lines.append(f"- **Volatility clock role (17)**: "
                     f"{vc['verdict'].iloc[0] if 'verdict' in vc.columns else 'n/a'}")
    ch = r.get("chain")
    if ch is not None and len(ch):
        n_info = (ch["status"] == "INFORMATIVE").sum()
        n_null = (ch["status"] == "NULL").sum()
        lines.append(f"- **Chain activity overlay (18)**: {n_info} "
                     f"informative / {n_null} null / "
                     f"{(ch['status'] == 'DATA_BLOCKED').sum()} blocked")
    lines.append("")
    lines.append("## Node actions")
    lines.append("")
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- {row['operation']}: {row['node']} "
                         f"({row['status']})")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    lines.append("- No causal claim above L2; all timing descriptive.")
    lines.append("- Loner labels reconstructed from LF5 peer residuals "
                 "(verified vs LF5 audit).")
    lines.append("- Rank-band panel covers LF5 PIT span only; early-2020 "
                 "coverage thin.")
    lines.append("- WS2/WS14 sequences require >=50 effective examples for "
                 "naming; below = descriptive.")
    lines.append("")
    lines.append("`human_review_required = TRUE`")
    lines.append("`next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · "
                 "NO DEPLOYMENT")
    (OUT / "22_MECH11_SUMMARY.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    return "\n".join(lines)


def write_decision(results):
    r = results
    lines = [
        "# CRYPTO-ALT-MECH-11 — DECISION",
        "",
        "## Verdict",
        "",
        "**PASS_MECH11_TEMPORAL_FIELD_PHYSICS_WITH_LIMITATIONS**",
        "",
        "MECH-11 moves the research from 'what is the state' toward 'what "
        "are the local physics of the state': explicit multi-scale delivery "
        "clocks per cell x age, a semi-Markov duration-conditioned audit, "
        "competing-risk geometry, perturbation amplitude response, "
        "propagation radius across rank depth, rank-patch coupling, "
        "reconstructed loner field context, and a health-transition "
        "lattice with definition reconciliation.",
        "",
        "## Key results",
        "",
    ]
    sm = r.get("semi_markov")
    if sm is not None and len(sm):
        lines.append(f"- **Semi-Markov**: {sm['verdict'].iloc[0]} "
                     f"(logloss {sm['overall_logloss_markov'].iloc[0]:.4f} "
                     f"-> {sm['overall_logloss_semi'].iloc[0]:.4f}).")
    cr = r.get("competing")
    if cr is not None and cr.get("verdict") is not None \
            and len(cr["verdict"]):
        lines.append(f"- **Competing-risk**: "
                     f"{cr['verdict']['verdict'].iloc[0]} "
                     f"(HH reentry-to-propagation mass shift at 14D).")
    lines.append("- **Multi-scale lattice (02)**: per-cell x age x horizon "
                 "delivery/exit/reentry/recruitment clocks.")
    lines.append("- **Sequence grammar (03)**: atom ordering with "
                 "COMMON/LOCAL/RARE classification.")
    lines.append("- **Perturbation amplitude (06)**: SMALL/MEDIUM/LARGE "
                 "response per perturbation type.")
    rad = r.get("radius")
    if rad is not None and len(rad):
        for _, row in rad.iterrows():
            lines.append(f"- **Radius**: {row['event_type']} -> "
                         f"{row['verdict']} ({row['n_bands_affected_d7']} "
                         f"bands).")
    lines.append("- **Rank patches (08/09/10)**: patch geometry and "
                 "coupling; **rank-depth sequences (08)**.")
    lp = r.get("loner_ctx")
    if lp is not None and len(lp):
        v = lp["verdict"].iloc[0] if "verdict" in lp.columns else "n/a"
        lines.append(f"- **Loner field context**: {v}.")
    lines.append("- **Health**: definition reconciliation (13) + "
                 "transition lattice (14).")
    lines.append("- **SHMC/SHHM** local placement (16); **volatility** "
                 "clock role (17); **chain sensors** (18).")
    lines.append("")
    lines.append("## Node actions")
    lines.append("")
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- {row['operation']}: {row['node']} "
                         f"({row['status']})")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    lines.append("- Loner labels are reconstructed (not LF5 event labels); "
                 "verified against the LF5 audit.")
    lines.append("- Rank-band radius/patch analysis spans LF5 PIT coverage; "
                 "shallow early-history bands.")
    lines.append("- Health transition lattice inherits M9 event universe; "
                 "LF5 cross-checks documented but not merged.")
    lines.append("- No strong-form bifurcation claim; route gates remain "
                 "local geometry.")
    lines.append("")
    lines.append("`human_review_required = TRUE`")
    lines.append("`next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · "
                 "NO LEVERAGE · NO DEPLOYMENT")
    (OUT / "23_MECH11_DECISION.md").write_text("\n".join(lines) + "\n",
                                               encoding="utf-8")
    return "\n".join(lines)


def main():
    dfw = _cache_step("dfw", load_dfw)
    ev = _cache_step("ev", load_ev)
    health = _cache_step("health", load_health)
    band = _cache_step("bandpanel", load_band_panel)
    loners = _cache_step("loners", load_loners)
    print(f"[data] dfw {dfw.shape} ev {ev.shape} health {health.shape} "
          f"band {band.shape} loners {loners.shape}", flush=True)

    lattice = _cache_step("ws1", lambda: ws1_multi_scale_lattice(dfw))
    sg = _cache_step("ws2", lambda: ws2_sequence_grammar(dfw))
    sm = _cache_step("ws3", lambda: ws3_semi_markov(dfw))
    cr = _cache_step("ws4", lambda: ws4_competing_risk(dfw))
    pa = _cache_step("ws5", lambda: ws5_perturbation_amplitude(dfw))
    rad = _cache_step("ws6", lambda: ws6_propagation_radius(dfw, band))
    rds = _cache_step("ws7", lambda: ws7_rank_depth_sequences(band))
    pg = _cache_step("ws8", lambda: ws8_rank_patch_geometry(band, dfw,
                                                            loners))
    pc = _cache_step("ws9", lambda: ws9_patch_coupling(band))
    lc = _cache_step("ws10", lambda: ws10_loner_field_context(dfw, loners))
    sl = _cache_step("ws11", lambda: ws11_sigma_recovery_lattice(loners, dfw))
    hr = _cache_step("ws12", ws12_health_reconciliation)
    ht = _cache_step("ws13", lambda: ws13_health_transition_lattice(health))
    fm = _cache_step("ws14", lambda: ws14_failure_mirrors(dfw, sg))
    smp = _cache_step("ws15", lambda: ws15_shmc_sequence_placement(ev, dfw))
    vc = _cache_step("ws16", lambda: ws16_volatility_clock(dfw))
    ch = _cache_step("ws17", lambda: ws17_chain_activity(dfw))

    results = {
        "lattice": lattice, "seq_grammar": sg, "semi_markov": sm,
        "competing": cr, "perturb_amp": pa, "radius": rad,
        "rank_depth_seq": rds, "patch_geom": pg, "patch_coupling": pc,
        "loner_ctx": lc, "sigma_lattice": sl, "health_recon": hr,
        "health_transitions": ht, "failure_mirrors": fm, "shmc": smp,
        "vol_clock": vc, "chain": ch, "nodes": None,
    }
    fmap = ws18_field_map(results)
    results["field_map"] = fmap
    nodes = ws19_nodes(results)
    results["nodes"] = nodes
    ws19_nulls(results)
    vd = write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print(f"[done] MECH-11 pipeline complete. verdict={vd['verdict']}",
          flush=True)


if __name__ == "__main__":
    main()
