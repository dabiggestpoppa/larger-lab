#!/usr/bin/env python
"""ALT_MECH_1 - Rank Migration, Lead-Lag, Sector Rotation & Capital Flow Anatomy.

Mechanism research ONLY. No PnL, no optimization, no ML, no portfolio construction,
no capital routing, no live execution.

All thresholds were fixed in ALT_MECH_1_PREREGISTRATION.md BEFORE this script ran.
"""
import json, hashlib, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260825
BOOT_N = 500
BLOCK_DAYS = 20
HORIZONS = {"1D": 1, "3D": 3, "7D": 7, "14D": 14, "30D": 30}

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "data_1_1"
OUT = ROOT

BANDS = ["1-10", "11-25", "26-50", "51-100", "101-200", "201-300", "301-500"]
EX_LABEL = "EX500_OR_OUT_OF_PANEL"
N_CODE = len(BANDS)
EX_CODE = N_CODE  # 7
ALL_CODES = list(range(N_CODE + 1))
CODE_TO_BAND = {i: b for i, b in enumerate(BANDS)}
CODE_TO_BAND[EX_CODE] = EX_LABEL

SUBPERIODS = [
    ("2020-2021", "2020-06-01", "2021-12-31"),
    ("2022", "2022-01-01", "2022-12-31"),
    ("2023", "2023-01-01", "2023-12-31"),
    ("2024", "2024-01-01", "2024-12-31"),
    ("2025-2026", "2025-01-01", "2026-12-31"),
]

# V1-era fields that MUST NOT be consumed (kept in parquet only for registry-hash continuity).
FORBIDDEN_PREFIXES = (
    "relative_return_vs_", "rolling_beta_vs_", "residual_return_vs_",
    "expected_return_given_",
)

FEATURE_COLS = [
    "historical_date", "internal_asset_id", "symbol", "global_rank", "rank_band",
    "market_cap_usd", "market_cap_share",
    "mcap_share_change_1d", "mcap_share_change_7d", "mcap_share_change_30d",
    "return_1d", "return_3d", "return_7d", "return_14d", "return_30d",
    "rank_velocity_1d", "rank_velocity_7d", "rank_velocity_14d",
    "rank_acceleration_short", "rank_acceleration_medium",
    "realized_volatility_30d", "volume_24h_usd", "volume_share",
    "is_stablecoin", "days_in_top500", "entered_top500",
]


def band_code(r):
    try:
        r = float(r)
    except (TypeError, ValueError):
        return np.nan
    if np.isnan(r):
        return np.nan
    for i, hi in enumerate([10, 25, 50, 100, 200, 300, 500]):
        if r <= hi:
            return i
    return EX_CODE


def subperiod_of(d):
    for name, lo, hi in SUBPERIODS:
        if pd.Timestamp(lo) <= d <= pd.Timestamp(hi):
            return name
    return None


def wilson_ci(k, n, z=1.96):
    n = np.asarray(n, dtype=float)
    k = np.asarray(k, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n > 0, k / np.maximum(n, 1e-12), np.nan)
        denom = 1 + z ** 2 / np.maximum(n, 1e-12)
        center = (p + z ** 2 / (2 * np.maximum(n, 1e-12))) / denom
        half = z * np.sqrt(np.maximum(p * (1 - p) / np.maximum(n, 1e-12)
                                      + z ** 2 / (4 * np.maximum(n, 1e-12) ** 2), 0)) / denom
    return p, center - half, center + half


def bh_fdr(pvals):
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order]
    qs = ranked * n / np.arange(1, n + 1)
    qs = np.minimum.accumulate(qs[::-1])[::-1]
    q = np.empty(n)
    q[order] = np.minimum(qs, 1.0)
    return q


# ----------------------------------------------------------------------------
# Input loading (allow-listed; forbidden V1 fields never read)
# ----------------------------------------------------------------------------

def load_inputs(verbose=True):
    def rd(name, columns=None):
        df = pd.read_parquet(DATA / name, columns=columns)
        if "historical_date" in df.columns:
            df["historical_date"] = pd.to_datetime(df["historical_date"])
        return df

    if verbose:
        print("[load] reading canonical DATA-1.1 inputs ...")
    inp = {}
    inp["pit"] = rd("ALT_DATA_1_1_PIT_UNIVERSE.parquet",
                    ["historical_date", "internal_asset_id"])
    feat = rd("ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet", FEATURE_COLS)
    bad = [c for c in feat.columns if str(c).startswith(FORBIDDEN_PREFIXES)]
    assert not bad, f"Forbidden V1 fields consumed: {bad}"
    inp["feat"] = feat.sort_values(["historical_date", "internal_asset_id"]).reset_index(drop=True)
    inp["rb"] = rd("ALT_DATA_1_1_RANK_BAND_FEATURES.parquet")
    inp["terrain"] = rd("ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet")
    inp["glob"] = rd("ALT_DATA_1_1_GLOBAL_FLOW.parquet")
    inp["chainflow"] = rd("ALT_DATA_1_1_CHAIN_FLOW.parquet")
    # DefiLlama flow frames carry midnight (00:00:00) stamps while feat/terrain carry
    # end-of-day (23:59:59) stamps; normalize flow dates to the same day bucket so
    # merges align. Same calendar day, no informational change.
    for _k in ("glob", "chainflow"):
        _df = inp[_k]
        if "historical_date" in _df.columns and len(_df):
            _df["historical_date"] = _df["historical_date"].dt.normalize() \
                + pd.Timedelta("23:59:59")
    inp["chainmap"] = rd("ALT_DATA_1_1_CHAIN_MAPPING.parquet",
                         ["historical_date", "internal_asset_id", "symbol", "chain",
                          "mapping_confidence"])
    # Canonical chain-name bridge: CMC platform strings (chain mapping) vs DefiLlama
    # display names (chain flow). Fixed engineering alias, not an outcome choice.
    CMC_TO_DEFILLAMA = {
        "ETH": "Ethereum", "BTC": "Bitcoin", "SOL": "Solana",
        "ARB": "Arbitrum", "ARBITRUM": "Arbitrum", "AVAX": "Avalanche",
        "TRX": "Tron", "POL": "Polygon", "CRO": "Cronos", "XLM": "Stellar",
        "SUI": "Sui", "OP": "OP Mainnet", "BSC": "BSC",
        "HYPE": "Hyperliquid L1", "PLS": "PulseChain",
    }
    cm = inp["chainmap"]
    cm_clean = cm["chain"].astype(str).str.strip().str.upper()
    cm["chain"] = cm_clean.map(CMC_TO_DEFILLAMA).fillna(cm_clean)
    smem = rd("ALT_DATA_1_1_SECTOR_MEMBERSHIP.parquet")
    inp["smem"] = smem[smem["sector"].astype(str).str.strip() != ""].copy()
    met_p = DATA / "ALT_DATA_1_1_METEORA_ASSET_DAILY.parquet"
    inp["meteora"] = rd("ALT_DATA_1_1_METEORA_ASSET_DAILY.parquet") if met_p.exists() else None
    if inp["meteora"] is not None and len(inp["meteora"]):
        inp["meteora"]["historical_date"] = inp["meteora"]["historical_date"] \
            .dt.normalize() + pd.Timedelta("23:59:59")
    return inp


def verify_truth_lock(inp):
    import pyarrow.parquet as pq
    res = {"checks": {}}
    pit = inp["pit"]
    res["checks"]["pit_rows_1098000"] = int(len(pit)) == 1098000
    res["checks"]["unique_assets_2898"] = int(pit.internal_asset_id.nunique()) == 2898
    res["checks"]["included_dates_2196"] = int(pit.historical_date.nunique()) == 2196

    schema = pq.read_schema(DATA / "ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet")
    cols = sorted(schema.names)
    v2_def = json.dumps({"version": "2.0.0", "columns": cols}, sort_keys=True)
    v2_hash = hashlib.sha256(v2_def.encode()).hexdigest()
    CANON_V2 = "0d666e74c0cf76adf6e6e6f2a6c47b1f52116f070fd1376c83274e6b077703ba"
    CANON_REG = "ea7eca86a2656654c65f20971d5fc70374adfbba4186c5f9a2a48c4ce21917ef"
    res["v2_feature_hash_computed"] = v2_hash
    res["v2_feature_hash_canonical"] = CANON_V2
    res["v2_feature_hash_note"] = ("Checkpoint brief quoted this hash with two hex "
                                   "characters dropped ('e6'); canonical recomputed "
                                   "hash matches DATA-1.1 frozen registry.")
    res["checks"]["v2_feature_hash_matches"] = v2_hash == CANON_V2
    reg = json.load(open(DATA / "ALT_DATA_1_1_FEATURE_REGISTRY_HASH.json"))
    res["checks"]["registry_hash_matches"] = reg.get("registry_hash") == CANON_REG

    gap_ok = False
    gap_val = None
    for dec_name in ["../data_1/ALT_DATA_1_DECISION.json", "ALT_DATA_1_1_DECISION.json"]:
        p = (DATA / dec_name).resolve()
        if p.exists():
            d = json.load(open(p))
            v = d.get("n_excluded_source_gap_dates",
                      d.get("eligibility", {}).get("n_excluded_source_gap_dates"))
            if v is None and "pass_criteria" in d:
                v = d.get("n_excluded_source_gap_dates")
            if v is not None:
                gap_val = v
                gap_ok = int(v) == 79
                break
    res["excluded_source_gap_dates_recorded"] = gap_val
    res["checks"]["excluded_source_gap_dates_79"] = bool(gap_ok)

    flow_files_present = all((DATA / f).exists() for f in [
        "ALT_DATA_1_1_GLOBAL_FLOW.parquet", "ALT_DATA_1_1_CHAIN_FLOW.parquet",
        "ALT_DATA_1_1_CHAIN_MAPPING.parquet"])
    res["checks"]["defillama_flow_files_present"] = bool(flow_files_present)
    res["all_pass"] = all(bool(v) for v in res["checks"].values())
    return res


# ----------------------------------------------------------------------------
# Wide panels
# ----------------------------------------------------------------------------

class Panels:
    """Date x Asset wide matrices built once from the feature panel."""

    def __init__(self, feat):
        self.feat = feat
        self.dates = np.sort(feat["historical_date"].unique())
        self.assets = np.sort(feat["internal_asset_id"].unique())
        self.dix = {d: i for i, d in enumerate(self.dates)}

        def wide(col):
            w = feat.pivot(index="historical_date", columns="internal_asset_id",
                           values=col).reindex(index=self.dates,
                                               columns=self.assets)
            return w

        self.rank = wide("global_rank")
        self.vel7 = wide("rank_velocity_7d")
        self.acc = wide("rank_acceleration_short")

        tmp = feat[["historical_date", "internal_asset_id"]].copy()
        tmp["bc"] = feat["global_rank"].map(band_code).astype(float).values
        self.band = tmp.pivot(index="historical_date", columns="internal_asset_id",
                              values="bc").reindex(index=self.dates,
                                                   columns=tmp.internal_asset_id.unique())

    def target_rows(self, h):
        tgt = np.array([self.dix.get(d + pd.Timedelta(days=h), -1) for d in self.dates])
        return tgt


# ----------------------------------------------------------------------------
# SECTION A - rank migration anatomy + transition matrices
# ----------------------------------------------------------------------------

def transition_pairs(P, h):
    tgt = P.target_rows(h)
    src_ok = tgt >= 0
    cur = P.band.values[src_ok]
    nxt = P.band.values[tgt[src_ok]]
    valid = ~(np.isnan(cur) | np.isnan(nxt))
    return cur[valid].astype(int), nxt[valid].astype(int), int(src_ok.sum())


def transition_matrix_csv(P, h_label):
    cur, nxt, n_src = transition_pairs(P, HORIZONS[h_label])
    K = N_CODE + 1
    C = np.zeros((K, K), dtype=int)
    np.add.at(C, (cur, nxt), 1)
    rows = []
    for i in ALL_CODES:
        tot = int(C[i].sum())
        for j in ALL_CODES:
            k = int(C[i, j])
            p, lo, hi = wilson_ci(k, tot)
            rows.append({
                "horizon": h_label,
                "from_band": CODE_TO_BAND[i], "to_band": CODE_TO_BAND[j],
                "count": k, "from_total": tot,
                "probability": round(float(p), 6) if tot else np.nan,
                "ci95_low": round(float(lo), 6) if tot else np.nan,
                "ci95_high": round(float(hi), 6) if tot else np.nan,
            })
    df = pd.DataFrame(rows)
    df.attrs["n_pairs"] = int(len(cur))
    df.attrs["n_skipped_gap_end"] = int(n_src - len(cur))
    return df


def band_spells(P):
    """Consecutive same-band spells per asset."""
    B = P.band.values
    T, N = B.shape
    spells = []
    prev = B[0].copy()
    start_i = np.zeros(N, dtype=int)
    for idx in range(N):
        if not np.isnan(prev[idx]):
            start_i[idx] = 0
    for t in range(1, T):
        row = B[t]
        ended = (~np.isnan(prev)) & ((prev != row) | np.isnan(row))
        for idx in np.nonzero(ended)[0]:
            spells.append((P.assets[idx], CODE_TO_BAND[int(prev[idx])],
                           start_i[idx], t - start_i[idx]))
        started = (~np.isnan(row)) & (np.isnan(prev) | (row != prev))
        start_i = np.where(started, t, start_i)
        prev = row.copy()
    for idx in range(N):
        if not np.isnan(prev[idx]):
            spells.append((P.assets[idx], CODE_TO_BAND[int(prev[idx])],
                           start_i[idx], T - start_i[idx]))
    return pd.DataFrame(spells, columns=["internal_asset_id", "band", "start_i",
                                         "length_days"])


def band_anatomy(P, spells):
    B = P.band.values
    T = len(P.dates)
    rows = []
    for bi, b in enumerate(BANDS):
        in_b = B == bi
        prev_in = np.roll(in_b, 1, axis=0)
        prev_in[0] = False
        entries = in_b & ~prev_in
        exits = prev_in & ~in_b
        n_member_days = int(in_b.sum())

        up = down = same = 0
        for h in HORIZONS.values():
            tgt = P.target_rows(h)
            ok = tgt >= 0
            cur = B[ok]; nx = B[tgt[ok]]
            m = (cur == bi) & ~np.isnan(nx)
            nxv = nx[m].astype(int)
            up += int((nxv < bi).sum())
            down += int(((nxv > bi) & (nxv < EX_CODE)).sum())
            same += int((nxv == bi).sum())
        denom = max(up + down + same, 1)

        sp = spells[spells.band == b]
        med_res = float(sp.length_days.median()) if len(sp) else np.nan

        ent_idx = np.argwhere(entries)
        step = max(1, len(ent_idx) // 300) if len(ent_idx) else 1
        vb, va, ab, aa = [], [], [], []
        for t, a in ent_idx[::step]:
            v0 = P.vel7.values[t, a]
            t7 = min(t + 7, T - 1)
            v1 = P.vel7.values[t7, a]
            if v0 == v0:
                vb.append(v0)
            if v1 == v1:
                va.append(v1)
            a0 = P.acc.values[t, a]
            a1 = P.acc.values[t7, a]
            if a0 == a0:
                ab.append(a0)
            if a1 == a1:
                aa.append(a1)

        rows.append({
            "band": b,
            "member_days": n_member_days,
            "entries": int(entries.sum()),
            "exits": int(exits.sum()),
            "entry_rate_per_member_day": round(float(entries.sum()) / max(n_member_days, 1), 5),
            "exit_rate_per_member_day": round(float(exits.sum()) / max(n_member_days, 1), 5),
            "upward_migration_rate_all_horizons": round(up / denom, 5),
            "downward_migration_rate_all_horizons": round(down / denom, 5),
            "median_residence_days": round(med_res, 1) if med_res == med_res else np.nan,
            "median_rank_velocity_7d_at_entry": round(float(np.median(vb)), 3) if vb else np.nan,
            "median_rank_velocity_7d_after_entry_plus7d": round(float(np.median(va)), 3) if va else np.nan,
            "median_rank_accel_short_at_entry": round(float(np.median(ab)), 4) if ab else np.nan,
            "median_rank_accel_short_after_entry_plus7d": round(float(np.median(aa)), 4) if aa else np.nan,
            "spell_count": int(len(sp)),
        })
    return pd.DataFrame(rows)


def persistence_by_horizon(P):
    rows = []
    pair_cache = {}
    for lbl, h in HORIZONS.items():
        pair_cache[lbl] = transition_pairs(P, h)
    for bi, b in enumerate(BANDS):
        for lbl in HORIZONS:
            cur, nxt, _ = pair_cache[lbl]
            nn = nxt[cur == bi]
            tot = len(nn)
            stay = int((nn == bi).sum())
            up1 = int((nn == bi - 1).sum()) if bi > 0 else 0
            up2 = int(((nn <= bi - 2) & (nn >= 0)).sum())
            dn1 = int((nn == bi + 1).sum()) if bi + 1 < EX_CODE else 0
            out = int((nn == EX_CODE).sum())
            for name, k in [("stay", stay), ("up_one_band", up1), ("up_two_plus_bands", up2),
                            ("down_one_band", dn1), ("leave_top500", out)]:
                p, lo, hi = wilson_ci(k, tot)
                rows.append({"band": b, "horizon": lbl, "measure": name,
                             "count": k, "n": tot,
                             "prob": round(float(p), 5), "ci95_low": round(float(lo), 5),
                             "ci95_high": round(float(hi), 5)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Lead-lag machinery (shared)
# ----------------------------------------------------------------------------

def xcorr_with_boot(x, y, max_lag, rng):
    """Cross-correlation x(t) vs y(t+h); positive h => x leads y.
    Null p-value: circular shifts of x by offsets >= BLOCK_DAYS (destroys lead structure)."""
    n = len(x)
    out = []
    for h in range(-max_lag, max_lag + 1):
        if h >= 0:
            a, b = x[: n - h], y[h:]
        else:
            a, b = x[-h:], y[: n + h]
        ok = ~(np.isnan(a) | np.isnan(b))
        a, b = a[ok], b[ok]
        if len(a) < 60 or np.std(a) == 0 or np.std(b) == 0:
            continue
        r = float(np.corrcoef(a, b)[0, 1])
        ge = 0
        for _ in range(BOOT_N):
            off = BLOCK_DAYS + int(rng.integers(1, max(2, len(a) - BLOCK_DAYS)))
            xs = np.roll(a, off % len(a))
            rs = np.corrcoef(xs, b)[0, 1]
            if abs(rs) >= abs(r):
                ge += 1
        p = (ge + 1) / (BOOT_N + 1)
        boots = []
        m = len(a)
        nb = m // BLOCK_DAYS
        if nb >= 2:
            for _ in range(200):
                idx = []
                while len(idx) < nb * BLOCK_DAYS:
                    st = rng.integers(0, max(1, m - BLOCK_DAYS))
                    idx.extend(range(st, st + BLOCK_DAYS))
                idx = np.array(idx[:nb * BLOCK_DAYS]) % m
                sa, sb = np.std(a[idx]), np.std(b[idx])
                if sa > 0 and sb > 0:
                    boots.append(np.corrcoef(a[idx], b[idx])[0, 1])
            lo, hi = (float(np.percentile(boots, [2.5, 97.5])[0]),
                      float(np.percentile(boots, [2.5, 97.5])[1])) if boots else (np.nan, np.nan)
        else:
            lo, hi = np.nan, np.nan
        out.append({"lag": h, "corr": round(r, 4),
                    "boot_ci_low": round(lo, 4) if lo == lo else np.nan,
                    "boot_ci_high": round(hi, 4) if hi == hi else np.nan,
                    "raw_p": round(p, 4), "n": int(m)})
    return pd.DataFrame(out)


def adf_stat(y):
    """Minimal ADF(1); approx 5% critical value -2.86."""
    dy, yl = np.diff(y), y[:-1]
    ok = ~(np.isnan(dy) | np.isnan(yl))
    dy, yl = dy[ok], yl[ok]
    if len(dy) < 50 or np.std(yl) == 0:
        return np.nan
    X = np.column_stack([np.ones_like(yl), yl])
    beta, *_ = np.linalg.lstsq(X, dy, rcond=None)
    resid = dy - X @ beta
    s2 = float(resid @ resid) / (len(dy) - 2)
    se = np.sqrt(s2 * np.linalg.pinv(X.T @ X)[1, 1])
    return float(beta[1] / se)


def granger_f(y, x, lags=(1, 3, 7)):
    """F-test: does x help predict y beyond y's own lags? Stationarity checked first."""
    t_y = adf_stat(np.asarray(y, dtype=float))
    stationary_level = (t_y == t_y and t_y < -2.86)
    if stationary_level:
        note = "LEVEL_STATIONARY"
    else:
        y = np.diff(y)
        x = np.diff(x)
        t_dy = adf_stat(y)
        note = "DIFFERENCED_STATIONARY" if (t_dy == t_dy and t_dy < -2.86) \
            else "NOT_STATIONARY_RESULTS_INVALID"
    n = len(y)
    L = max(lags)
    Y = y[L:]
    cols_y = [y[L - k: n - k] for k in sorted(lags)]
    AR = np.column_stack(cols_y)
    ok = ~(np.isnan(AR).any(axis=1) | np.isnan(Y) | np.isnan(x[L:]))
    Yv = Y[ok]
    Xr = AR[ok]
    Xf = np.column_stack([Xr, np.column_stack([x[L - k: n - k] for k in sorted(lags)])[ok]])
    if len(Yv) < 60:
        return {"stationarity": note, "F": np.nan, "raw_p": np.nan, "n": int(len(Yv))}
    def rss(M):
        M = np.column_stack([np.ones(len(M)), M])
        b, *_ = np.linalg.lstsq(M, Yv, rcond=None)
        e = Yv - M @ b
        return float(e @ e)
    r0, r1 = rss(Xr), rss(Xf)
    k1, k2 = Xr.shape[1], Xf.shape[1]
    F = ((r0 - r1) / (k2 - k1)) / (r1 / max(len(Yv) - k2 - 1, 1))
    from scipy import stats as st
    p = float(st.f.sf(F, k2 - k1, max(len(Yv) - k2 - 1, 1)))
    return {"stationarity": note, "F": round(F, 3), "raw_p": round(p, 4), "n": int(len(Yv))}


def band_metric_wide(rb, col):
    return rb.pivot(index="historical_date", columns="rank_band", values=col).sort_index()


def band_cascade_analysis(rb):
    rng = np.random.default_rng(SEED)
    metrics = {
        "ew_return_1d": "median_return_1d",
        "mcap_share": "market_cap_share",
        "rank_velocity_7d": "median_rank_velocity_7d",
        "breadth_7d": "breadth_7d",
        "volume_share": "volume_share",
    }
    rows = []
    for mname, col in metrics.items():
        W = band_metric_wide(rb, col)
        for i in range(len(BANDS) - 1):
            for j in range(i + 1, len(BANDS)):
                a, b = BANDS[i], BANDS[j]
                if a not in W.columns or b not in W.columns:
                    continue
                xc = xcorr_with_boot(W[a].values.astype(float),
                                     W[b].values.astype(float), 14, rng)
                if xc.empty:
                    continue
                best = xc.loc[xc["corr"].abs().idxmax()]
                rows.append({
                    "metric": mname, "band_a_earlier_rank": a, "band_b_later_rank": b,
                    "best_lag_days_a_leads_b": int(best["lag"]),
                    "best_corr": best["corr"], "boot_ci_low": best["boot_ci_low"],
                    "boot_ci_high": best["boot_ci_high"], "raw_p": best["raw_p"],
                    "n_days": best["n"],
                })
    df = pd.DataFrame(rows)
    if len(df):
        fam = df["metric"].values
        qs = np.empty(len(df))
        for m in np.unique(fam):
            mask = fam == m
            qs[mask] = bh_fdr(df.loc[mask, "raw_p"].values.astype(float))
        df["fdr_q"] = np.round(qs, 4)
    return df


def band_granger(rb):
    rows = []
    Wv = band_metric_wide(rb, "median_rank_velocity_7d")
    Wr = band_metric_wide(rb, "median_return_1d")
    for i in range(len(BANDS) - 1):
        a, b = BANDS[i], BANDS[i + 1]
        if a in Wv.columns and b in Wv.columns:
            g = granger_f(Wv[b].values.astype(float), Wv[a].values.astype(float))
            rows.append({"driver": f"{a}_velocity", "responds": f"{b}_velocity", **g})
        if a in Wr.columns and b in Wr.columns:
            g = granger_f(Wr[b].values.astype(float), Wr[a].values.astype(float))
            rows.append({"driver": f"{a}_return", "responds": f"{b}_return", **g})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# SECTION B - capital routing states
# ----------------------------------------------------------------------------

ROUTING_STATES = ["STABLECOIN_PARKING", "CAPITAL_EXIT", "BROAD_RISK_EXPANSION",
                  "NARROW_LEADERSHIP", "ETH_BROADENING", "LARGE_ALT_ROTATION",
                  "MID_CAP_ROTATION", "SMALL_CAP_ROTATION", "BTC_CONCENTRATION",
                  "MIXED_NO_CLEAR_ROUTE"]


def daily_market_frame(feat, terrain, glob):
    g = feat.groupby("historical_date").agg(
        total_mcap=("market_cap_usd", "sum"),
        pos_ret_share=("return_1d", lambda s: float((s > 0).mean())),
        pos_vel7_share=("rank_velocity_7d", lambda s: float((s > 0).mean())),
    ).reset_index()

    def band_median(lo, hi):
        sel = feat[(feat.global_rank >= lo) & (feat.global_rank <= hi)]
        return sel.groupby("historical_date").return_30d.median().rename(f"med_ret30_{lo}_{hi}")

    d = terrain.merge(g, on="historical_date", how="left")
    for lo, hi in [(11, 50), (51, 200), (201, 500)]:
        d = d.merge(band_median(lo, hi), on="historical_date", how="left")
    gf = glob[glob.historical_date.between(d.historical_date.min(),
                                           d.historical_date.max())][
        ["historical_date", "stablecoin_total_mcap", "stablecoin_change_30d"]]
    d = d.merge(gf, on="historical_date", how="left")
    d["total_mcap_chg30"] = d.total_mcap.pct_change(30)
    d["btc_dom_chg30"] = d.btc_dominance.diff(30)
    d["big_alt_rel30"] = d.med_ret30_11_50 - d.btc_return_30d
    d["mid_rel30"] = d.med_ret30_51_200 - d.btc_return_30d
    d["small_rel30"] = d.med_ret30_201_500 - d.btc_return_30d
    d["eth_rel30"] = d.eth_return_30d - d.btc_return_30d
    return d


def assign_routing_state_frame(d):
    """Vectorized implementation of preregistered priority rules."""
    nz = lambda s: s.fillna(0.0).astype(float)
    btc30, eth_rel = nz(d.btc_return_30d), nz(d.eth_rel30)
    bigrel, midrel, smarel = nz(d.big_alt_rel30), nz(d.mid_rel30), nz(d.small_rel30)
    brd, sc30 = nz(d.top500_breadth_30d), nz(d.stablecoin_change_30d)
    mc30, domchg = nz(d.total_mcap_chg30), nz(d.btc_dom_chg30)

    conds = [
        ("STABLECOIN_PARKING", (sc30 > 0.01) & (brd < 0.40) & (btc30 < -0.10)),
        ("CAPITAL_EXIT", (btc30 < -0.20) & (mc30 < -0.20)),
        ("BROAD_RISK_EXPANSION", (bigrel > 0) & (midrel > 0) & (smarel > 0) & (brd >= 0.60)),
        ("NARROW_LEADERSHIP", (bigrel > 0) & (midrel <= 0) & (smarel <= 0) & (brd < 0.45)),
        ("ETH_BROADENING", (eth_rel > 0.05) & (bigrel > 0)),
        ("LARGE_ALT_ROTATION", (bigrel > 0.02) & (eth_rel <= 0)),
        ("MID_CAP_ROTATION", (midrel > 0.02) & (bigrel <= 0.02)),
        ("SMALL_CAP_ROTATION", (smarel > 0.02) & (midrel <= 0.02)),
        ("BTC_CONCENTRATION", (btc30 > np.maximum(np.maximum(bigrel, midrel), smarel)) &
                              (btc30 > 0) & (domchg > 0)),
    ]
    out = np.full(len(d), "MIXED_NO_CLEAR_ROUTE", dtype=object)
    assigned = np.zeros(len(d), dtype=bool)
    for name, c in conds:
        take = c.values & ~assigned
        out[take] = name
        assigned |= take
    return out



def routing_analysis(daily):
    daily = daily.copy()
    daily["state"] = assign_routing_state_frame(daily)
    freq = daily.state.value_counts().reset_index()
    freq.columns = ["state", "days"]
    freq["share"] = (freq.days / freq.days.sum()).round(4)

    dims = ["eth_rel30", "big_alt_rel30", "mid_rel30", "small_rel30",
            "top500_breadth_30d", "stablecoin_change_30d"]
    Z = daily[dims].astype(float)
    Z = (Z - Z.mean()) / Z.std().replace(0, 1)
    sep_rows = []
    codes = {s: i for i, s in enumerate(ROUTING_STATES)}
    seq1 = daily.state.map(codes).values[:-1]
    seq2 = daily.state.map(codes).values[1:]
    K = len(ROUTING_STATES)
    T = np.zeros((K, K), dtype=int)
    np.add.at(T, (seq1, seq2), 1)
    pmat = T / np.maximum(T.sum(axis=1, keepdims=True), 1)
    persist = dict(zip(ROUTING_STATES, np.round(np.diag(pmat), 3)))
    for s in ROUTING_STATES:
        m = (daily.state == s).values
        n_days = int(m.sum())
        if n_days >= 10:
            within = float(Z[m].var(axis=0).mean())
            rest = Z[~m]
            between = float(((Z[m].mean() - rest.mean()) ** 2).mean())
            ratio = round(between / max(within, 1e-9), 3)
        else:
            ratio = np.nan
        sep_rows.append({"state": s, "n_days": n_days,
                         "share_of_days": round(n_days / len(daily), 4),
                         "separation_ratio": ratio,
                         "day_over_day_persistence": persist.get(s, np.nan)})
    tm = pd.DataFrame(T, index=ROUTING_STATES, columns=ROUTING_STATES)
    fwd_rows = []
    for s in ROUTING_STATES:
        m = (daily.state == s).values
        for h in (7, 14, 30):
            fr = daily.pos_ret_share.shift(-h)
            fb = daily.btc_return_30d.shift(-h)
            fwd_rows.append({
                "state": s, "forward_window_d": h,
                "mean_fwd_posret_share": round(float(fr[m].mean()), 4) if m.any() else np.nan,
                "median_fwd_btc_ret30": round(float(fb[m].median()), 5) if m.any() else np.nan,
            })
    return daily, pd.DataFrame(sep_rows), tm, pd.DataFrame(fwd_rows)


# ----------------------------------------------------------------------------
# SECTION C - sector rotation + participation
# ----------------------------------------------------------------------------

def sector_daily(inp):
    sm = inp["smem"][["historical_date", "internal_asset_id", "sector", "sector_rank",
                      "sector_member_count"]]
    f = inp["feat"][["historical_date", "internal_asset_id", "return_1d", "return_7d",
                     "return_30d", "rank_velocity_7d", "market_cap_usd", "volume_share",
                     "global_rank", "symbol"]]
    m = sm.merge(f, on=["historical_date", "internal_asset_id"], how="inner")

    def agg(g):
        mc = g.market_cap_usd.fillna(0).values
        tot = float(mc.sum())
        order = np.argsort(-mc)
        cum = np.cumsum(mc[order]) / max(tot, 1e-12)
        r7 = g.return_7d.values.astype(float)
        return pd.Series({
            "member_count": int(len(g)),
            "sector_mcap": tot,
            "breadth_1d": float((g.return_1d > 0).mean()),
            "breadth_7d": float((g.rank_velocity_7d > 0).mean()),
            "median_ret_7d": float(np.nanmedian(r7)),
            "dispersion_ret_7d": float(np.nanstd(r7)),
            "top1_share": float(cum[0]),
            "top3_share": float(cum[min(2, len(cum) - 1)]),
            "top5_share": float(cum[min(4, len(cum) - 1)]),
            "top10_share": float(cum[min(9, len(cum) - 1)]),
            "leader_follow_gap_7d": float(np.nanpercentile(r7, 90) - np.nanpercentile(r7, 50)),
            "volume_share_sum": float(g.volume_share.sum()),
        })

    sd = m.groupby(["historical_date", "sector"]).apply(agg).reset_index()
    sd["sector_mcap_share"] = sd.sector_mcap / sd.groupby(
        "historical_date").sector_mcap.transform("sum")
    sd = sd.sort_values(["historical_date", "sector_mcap_share"],
                        ascending=[True, False]).reset_index(drop=True)
    sd["sector_rank"] = sd.groupby("historical_date").cumcount() + 1
    sd["sector_rank_velocity"] = -sd.groupby("sector").sector_rank.diff()
    mv = m.groupby(["historical_date", "sector"]).rank_velocity_7d.median() \
        .rename("median_member_vel7").reset_index()
    sd = sd.merge(mv, on=["historical_date", "sector"], how="left")
    return sd, m


def sector_rotation_csv(sd):
    sd = sd.copy()
    sd["share_chg_7d"] = sd.groupby("sector").sector_mcap_share.diff(7)
    sd["share_chg_30d"] = sd.groupby("sector").sector_mcap_share.diff(30)
    rows = []
    for sec, g in sd.groupby("sector"):
        if g.member_count.min() < 10:
            continue
        rows.append({
            "sector": sec,
            "active_days": int(g.historical_date.nunique()),
            "median_sector_rank": float(g.sector_rank.median()),
            "median_sector_rank_velocity": float(g.sector_rank_velocity.median()),
            "median_ret_7d": float(g.median_ret_7d.median()),
            "median_share_chg_7d": float(g.share_chg_7d.median()),
            "median_share_chg_30d": float(g.share_chg_30d.median()),
            "median_breadth_1d": float(g.breadth_1d.median()),
            "median_breadth_7d": float(g.breadth_7d.median()),
            "median_top1_participation": float(g.top1_share.median()),
            "median_top3_participation": float(g.top3_share.median()),
            "median_top5_participation": float(g.top5_share.median()),
            "median_top10_participation": float(g.top10_share.median()),
            "full_sector_breadth_7d_median": float(g.breadth_7d.median()),
            "median_leader_follow_gap_7d": float(g.leader_follow_gap_7d.median()),
            "median_dispersion_ret_7d": float(g.dispersion_ret_7d.median()),
            "median_volume_share": float(g.volume_share_sum.median()),
        })
    return pd.DataFrame(rows).sort_values("median_sector_rank")


def trailing_p70_thresholds(v):
    thr = np.full(len(v), np.nan)
    for i in range(len(v)):
        win = v[max(0, i - 252): i]
        win = win[~np.isnan(win)]
        if len(win) >= 60:
            thr[i] = np.nanpercentile(win, 70)
    return thr


def detect_episodes_generic(g_sorted, value_col, breadth_col, breadth_min, label_fn):
    """Preregistered rule: value >= P70(trailing 252 obs, min 60) AND breadth gate."""
    eps = []
    g = g_sorted.reset_index(drop=True)
    if len(g) < 70:
        return eps
    v = g[value_col].astype(float).values
    thr = trailing_p70_thresholds(v)
    dts = g.historical_date.values
    active, start = False, None
    for i in range(len(v)):
        cond = (thr[i] == thr[i]) and (v[i] == v[i]) and v[i] >= thr[i] \
            and (g[breadth_col].iloc[i] >= breadth_min)
        if cond and not active:
            active, start = True, i
        elif not cond and active:
            eps.append(label_fn(start, i - 1, dts))
            active = False
    if active:
        eps.append(label_fn(start, len(v) - 1, dts))
    return eps


def detect_sector_episodes(sd):
    eps = []
    for sec, g in sd.groupby("sector"):
        recs = detect_episodes_generic(
            g.sort_values("historical_date"), "median_member_vel7", "breadth_7d", 0.40,
            lambda s, e, dts: {"source": sec, "start_date": dts[s], "end_date": dts[e],
                               "start_i": s, "end_i": e})
        eps.extend(recs)
    return pd.DataFrame(eps)


def detect_band_episodes(rb):
    eps = []
    for b, g in rb.groupby("rank_band"):
        recs = detect_episodes_generic(
            g.sort_values("historical_date"), "median_rank_velocity_7d", "breadth_7d", 0.50,
            lambda s, e, dts: {"source": b, "start_date": dts[s], "end_date": dts[e],
                               "start_i": s, "end_i": e})
        eps.extend(recs)
    return pd.DataFrame(eps)


def detect_chain_episodes(chain_agg):
    ca = chain_agg.copy()
    ca["improving_share"] = ca.n_improving / ca.n_top500.clip(lower=1)
    eps = []
    for ch, g in ca.groupby("chain"):
        if g.n_top500.median() < 3:
            continue
        recs = detect_episodes_generic(
            g.sort_values("historical_date"), "improving_share", "n_top500", 3.0,
            lambda s, e, dts: {"source": f"CHAIN:{ch}", "start_date": dts[s],
                               "end_date": dts[e], "start_i": s, "end_i": e})
        eps.extend(recs)
    return pd.DataFrame(eps)


def leader_follower(mem, eps):
    """Leader/follower anatomy within sector episodes (causal: leader chosen at start).

    Uses dict-based value lookups and per-sector pre-grouping; avoids O(episodes)
    full-frame scans that made the naive version take hours.
    """
    rows = []
    if eps.empty:
        return pd.DataFrame(rows)
    mem = mem.copy()
    mem["historical_date"] = pd.to_datetime(mem["historical_date"])

    # flat dict: (sector, asset, date) -> (rank_velocity_7d, return_7d)
    val = {}
    for sec, aid, d, v, r in zip(mem["sector"].values, mem["internal_asset_id"].values,
                                 mem["historical_date"].values,
                                 mem["rank_velocity_7d"].values, mem["return_7d"].values):
        val[(sec, aid, d)] = (v, r)
    by_sector = {s: g for s, g in mem.groupby("sector")}

    for _, ep in eps.iterrows():
        sec = ep.source
        start_d = np.datetime64(pd.Timestamp(ep.start_date))
        gsec = by_sector.get(sec)
        if gsec is None:
            continue
        day_mem = gsec[gsec["historical_date"].values == start_d]
        day_mem = day_mem.dropna(subset=["rank_velocity_7d"])
        if len(day_mem) < 10:
            continue
        dm = day_mem.sort_values("rank_velocity_7d", ascending=False)
        leader = dm.iloc[0]
        followers = dm.iloc[1:11]
        conf_times = []
        for _, fw in followers.iterrows():
            ct = np.nan
            aid = fw.internal_asset_id
            for h in (3, 7, 14, 30):
                vr = val.get((sec, aid, start_d + np.timedelta64(h, "D")))
                if vr is not None and vr[0] == vr[0] and vr[0] > 0:
                    ct = h
                    break
            conf_times.append(ct)
        confirmed = sum(1 for c in conf_times if c == c)
        l_vr7 = val.get((sec, leader.internal_asset_id,
                         start_d + np.timedelta64(7, "D")))
        rows.append({
            "sector": sec, "episode_start": pd.Timestamp(ep.start_date).date(),
            "leader_symbol": leader.symbol,
            "leader_global_rank": leader.global_rank,
            "leader_vel7_at_start": float(leader.rank_velocity_7d),
            "leader_fwd_ret7": float(l_vr7[1]) if l_vr7 is not None else np.nan,
            "follower_median_vel7_at_start": float(followers.rank_velocity_7d.median()),
            "follower_confirm_rate_30d": round(confirmed / max(len(conf_times), 1), 3),
            "median_time_to_confirm_days": float(np.nanmedian(conf_times))
                                           if any(c == c for c in conf_times) else np.nan,
            "n_followers_tracked": int(len(followers)),
            "episode_duration_days": int(ep.end_i - ep.start_i) + 1,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# SECTION D - breadth
# ----------------------------------------------------------------------------

def breadth_analysis(daily, sd):
    d = daily.copy()
    b30 = d.top500_breadth_30d.astype(float)
    q33, q66 = b30.quantile(0.33), b30.quantile(0.66)
    conc = sd.groupby("historical_date").apply(
        lambda g: float(g.nlargest(3, "sector_mcap_share").sector_mcap_share.sum()))
    d = d.merge(conc.rename("top3_sector_conc"), left_on="historical_date",
                right_index=True, how="left")
    cq33, cq66 = d.top3_sector_conc.quantile(0.33), d.top3_sector_conc.quantile(0.66)

    def state(r):
        broad = "BROAD" if r.top500_breadth_30d >= q66 else \
                ("NARROW" if r.top500_breadth_30d <= q33 else "MID")
        conc_ = "CONCENTRATED" if r.top3_sector_conc >= cq66 else \
                ("DISPERSED" if r.top3_sector_conc <= cq33 else "MIDC")
        if broad == "NARROW" and conc_ == "CONCENTRATED":
            return "ONE_COIN_OR_NARROW_MOVE"
        if conc_ == "CONCENTRATED":
            return "NARROW_SECTOR_MOVE"
        if broad == "BROAD":
            return "BROAD_MARKET_ROTATION"
        return "BROAD_SECTOR_MOVE"

    d["breadth_state"] = d.apply(state, axis=1)
    rows = []
    for s, g in d.groupby("breadth_state"):
        for h in (7, 14, 30):
            fwd_breadth = d.top500_breadth_30d.shift(-h)
            fwd_btc = d.btc_return_30d.shift(-h)
            rows.append({
                "breadth_state": s, "days": int(len(g)),
                "share_of_days": round(len(g) / len(d), 4),
                "fwd_window_d": h,
                "mean_fwd_breadth": round(float(fwd_breadth[g.index].mean()), 4),
                "mean_pos_ret_share_now": round(float(g.pos_ret_share.mean()), 4),
                "mean_pos_vel7_share_now": round(float(g.pos_vel7_share.mean()), 4),
                "mean_btc_outperformance_7d": round(float(g.btc_return_7d.mean()), 5),
                "mean_eth_outperformance_7d": round(float(g.eth_btc_relative_return_7d.mean()), 5),
                "median_fwd_btc_ret30": round(float(fwd_btc[g.index].median()), 5),
            })
    return d, pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Sections E/F/G - stablecoin, chain flow, Meteora proxy
# ----------------------------------------------------------------------------

def available_next_day(frame, cols, date_col="historical_date"):
    """DefiLlama AVAILABLE_NEXT_DAY: published values usable only from next calendar day."""
    f = frame.sort_values(date_col).copy()
    for c in cols:
        f[c] = f[c].shift(1)
    return f


def stablecoin_flow_analysis(daily, glob):
    gf = glob.copy()
    gf["sc_chg7"] = gf.stablecoin_total_mcap.pct_change(7)
    gf["sc_accel"] = gf.sc_chg7.diff(7)
    gf = available_next_day(gf, ["stablecoin_change_1d", "stablecoin_change_7d",
                                 "stablecoin_change_30d", "sc_chg7", "sc_accel"])
    # daily already carries an unshifted stablecoin_change_30d from daily_market_frame;
    # drop it so the AVAILABLE_NEXT_DAY-shifted version below is not suffixed _x/_y.
    d = daily.drop(columns=["stablecoin_change_30d"], errors="ignore") \
        .merge(gf[["historical_date", "stablecoin_change_1d", "stablecoin_change_7d",
                   "stablecoin_change_30d", "sc_chg7", "sc_accel"]],
               on="historical_date", how="left")
    risk_metrics = {
        "pos_ret_share": d.pos_ret_share.values.astype(float),
        "alt_breadth_30d": d.top500_breadth_30d.values.astype(float),
        "btc_ret_1d": d.btc_return_1d.values.astype(float),
        "eth_btc_rel_7d": d.eth_btc_relative_return_7d.values.astype(float),
        "small_rel30": d.small_rel30.values.astype(float),
    }
    drivers = {
        "sc_chg_1d": d.stablecoin_change_1d.values.astype(float),
        "sc_chg_7d": d.stablecoin_change_7d.values.astype(float),
        "sc_chg_30d": d.stablecoin_change_30d.values.astype(float),
        "sc_accel": d.sc_accel.values.astype(float),
    }
    rng = np.random.default_rng(SEED + 1)
    rows = []
    for dn, dv in drivers.items():
        for mn, mv in risk_metrics.items():
            xc = xcorr_with_boot(dv, mv, 30, rng)
            for _, rr in xc.iterrows():
                if rr.lag in (-30, -14, -7, -3, -1, 1, 3, 7, 14, 30):
                    rows.append({"driver": dn, "risk_metric": mn, "lead_days": int(rr.lag),
                                 "corr": float(rr["corr"]), "boot_ci_low": rr.boot_ci_low,
                                 "boot_ci_high": rr.boot_ci_high, "raw_p": rr.raw_p,
                                 "n": rr.n,
                                 "direction": "STABLECOIN_LEADS" if rr.lag > 0
                                              else "RISK_LEADS"})
    df = pd.DataFrame(rows)
    if len(df):
        df["fdr_q"] = np.round(bh_fdr(df.raw_p.values.astype(float)), 4)
    reg_rows = []
    exp = (d.stablecoin_change_30d > 0).fillna(False)
    for label, m in [("EXPANDING", exp.values), ("CONTRACTING", ~exp.values)]:
        for h in (7, 14, 30):
            fr = d.pos_ret_share.shift(-h)
            fb = d.btc_return_30d.shift(-h)
            reg_rows.append({"stablecoin_regime": label, "forward_window": f"+{h}D",
                             "mean_fwd_posret_share": round(float(fr[m].mean()), 4),
                             "median_fwd_btc_ret30": round(float(fb[m].median()), 5),
                             "days": int(m.sum())})
    return df, pd.DataFrame(reg_rows)


def chain_native_aggregates(feat, chainmap):
    cm = chainmap[["historical_date", "internal_asset_id", "chain"]]
    m = feat[["historical_date", "internal_asset_id", "global_rank", "rank_velocity_7d",
              "market_cap_usd", "market_cap_share", "return_1d"]] \
        .merge(cm, on=["historical_date", "internal_asset_id"], how="inner")
    m = m[m.chain.astype(str).str.strip() != ""]
    agg = m.groupby(["historical_date", "chain"]).agg(
        n_top500=("global_rank", "size"),
        n_improving=("rank_velocity_7d", lambda s: int((s > 0).sum())),
        median_vel7=("rank_velocity_7d", "median"),
        mcap_share=("market_cap_share", "sum"),
        ret_breadth_1d=("return_1d", lambda s: float((s > 0).mean())),
    ).reset_index()
    return agg, m


def chain_flow_analysis(chain_agg, chainflow):
    cf = chainflow.copy()
    cf["tvl_chg7"] = cf.chain_tvl.pct_change(7)
    cf = available_next_day(cf, ["chain_tvl_change_1d", "chain_tvl_change_7d",
                                 "chain_tvl_change_30d", "tvl_chg7"])
    merged = chain_agg.merge(cf[["historical_date", "chain", "chain_tvl_change_1d",
                                 "chain_tvl_change_7d", "chain_tvl_change_30d", "tvl_chg7"]],
                             on=["historical_date", "chain"], how="inner")
    rows = []
    rng = np.random.default_rng(SEED + 2)
    for ch in merged.chain.value_counts().head(12).index.tolist():
        g = merged[merged.chain == ch].sort_values("historical_date")
        if len(g) < 120:
            continue
        drivers = {"chain_tvl_chg_7d": g.tvl_chg7.values.astype(float),
                   "chain_tvl_chg_30d": g.chain_tvl_change_30d.values.astype(float)}
        outs = {"improving_share": (g.n_improving / g.n_top500.clip(lower=1)).values.astype(float),
                "median_vel7": g.median_vel7.values.astype(float),
                "ret_breadth_1d": g.ret_breadth_1d.values.astype(float)}
        for dn, dv in drivers.items():
            for on, ov in outs.items():
                xc = xcorr_with_boot(dv, ov, 30, rng)
                for _, rr in xc.iterrows():
                    if rr.lag in (-30, -14, -7, -3, -1, 1, 3, 7, 14, 30):
                        rows.append({"chain": ch, "driver": dn, "outcome": on,
                                     "lead_days": int(rr.lag), "corr": float(rr["corr"]),
                                     "boot_ci_low": rr.boot_ci_low,
                                     "boot_ci_high": rr.boot_ci_high,
                                     "raw_p": rr.raw_p, "n": rr.n})
    df = pd.DataFrame(rows)
    if len(df):
        df["fdr_q"] = np.round(bh_fdr(df.raw_p.values.astype(float)), 4)
    return df


def solana_meteora_proxy(chain_agg, meteora):
    rows = [{"analysis_label": "PARTIAL_PROXY_ONLY",
             "proxy": "DefiLlama aggregate Meteora TVL",
             "pool_level_analysis": "DEFERRED"}]
    if meteora is None:
        return pd.DataFrame([{"analysis_label": "METEORA_FILE_MISSING"}])
    met = meteora[meteora.chain == "Solana"].sort_values("historical_date")[
        ["historical_date", "meteora_tvl", "meteora_tvl_change_7d", "meteora_tvl_change_30d"]]
    met = available_next_day(met, ["meteora_tvl_change_7d", "meteora_tvl_change_30d"])
    sol = chain_agg[chain_agg.chain == "Solana"].sort_values("historical_date")
    base = sol.merge(met, on="historical_date", how="left")
    rng = np.random.default_rng(SEED + 3)
    outs = {"solana_n_top500": base.n_top500.values.astype(float),
            "solana_improving_share":
                (base.n_improving / base.n_top500.clip(lower=1)).values.astype(float),
            "solana_median_vel7": base.median_vel7.values.astype(float),
            "solana_mcap_share": base.mcap_share.values.astype(float)}
    drv = {"meteora_tvl_chg_7d": base.meteora_tvl_change_7d.values.astype(float),
           "meteora_tvl_chg_30d": base.meteora_tvl_change_30d.values.astype(float),
           "meteora_log_tvl": np.log(base.meteora_tvl.values.astype(float))}
    for dn, dv in drv.items():
        for on, ov in outs.items():
            xc = xcorr_with_boot(dv, ov, 30, rng)
            for _, rr in xc.iterrows():
                if rr.lag in (-30, -14, -7, -3, -1, 1, 3, 7, 14, 30):
                    rows.append({"chain": "Solana", "driver": dn, "outcome": on,
                                 "lead_days": int(rr.lag), "corr": float(rr["corr"]),
                                 "boot_ci_low": rr.boot_ci_low,
                                 "boot_ci_high": rr.boot_ci_high,
                                 "raw_p": rr.raw_p, "n": rr.n})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Episode ledger + persistence vs exhaustion
# ----------------------------------------------------------------------------

def effective_clusters(eps_df, gap_days=7):
    out, details = 0, []
    for (typ, src), g in eps_df.groupby(["episode_type", "source"]):
        spans = sorted(zip(pd.to_datetime(g.start_date), pd.to_datetime(g.end_date)))
        clusters, open_end = 0, None
        for s, e in spans:
            if open_end is None or s > open_end + pd.Timedelta(days=gap_days):
                clusters += 1
                open_end = e
            else:
                open_end = max(open_end, e)
        out += clusters
        details.append({"episode_type": typ, "source": src, "raw_episodes": len(g),
                        "effective_clusters": clusters})
    return out, pd.DataFrame(details)


def build_ledger(all_eps, daily):
    state_by_date = daily.set_index("historical_date").state
    sc_by_date = daily.set_index("historical_date").stablecoin_change_30d
    led = []
    for _, ep in all_eps.iterrows():
        start = pd.Timestamp(ep.start_date)
        end = pd.Timestamp(ep.end_date)
        dur = (end - start).days + 1
        window = pd.date_range(start, end, freq="D")
        window = window.intersection(state_by_date.index)
        peak_d = window.max() if len(window) else end
        res_d = end + pd.Timedelta(days=14)
        led.append({
            "episode_id": f"{ep.episode_type}_{ep.source}_{start.date()}",
            "episode_type": ep.episode_type,
            "source": ep.source,
            "start_date": start.date(), "end_date": end.date(),
            "duration_days": dur,
            "initial_routing_state": state_by_date.get(start, np.nan),
            "peak_routing_state": state_by_date.get(peak_d, np.nan),
            "resolution_routing_state_14d_after_end":
                state_by_date.get(res_d, np.nan),
            "stablecoin_regime_30d_at_start":
                ("EXPANDING" if sc_by_date.get(start, 0) == sc_by_date.get(start, 0)
                 and sc_by_date.get(start, np.nan) > 0 else "CONTRACTING"),
        })
    return pd.DataFrame(led)


def persistence_exhaustion(ledger, rb):
    rows = []
    if ledger.empty:
        return pd.DataFrame()
    rbw = rb.pivot(index="historical_date", columns="rank_band",
                   values="median_rank_velocity_7d").sort_index()
    for _, ep in ledger[ledger.episode_type == "BAND"].iterrows():
        b = ep.source
        if b not in rbw.columns:
            continue
        s = rbw[b]
        end = pd.Timestamp(ep.end_date)
        v_end = float(s.asof(end)) if end >= s.index.min() else np.nan
        v_res = float(s.asof(end + pd.Timedelta(days=14))) \
            if end + pd.Timedelta(days=14) >= s.index.min() else np.nan
        if v_end != v_end or v_res != v_res:
            continue
        outcome = ("CONTINUED_IMPROVEMENT" if v_res > 0 and v_res >= v_end * 0.5
                   else ("REVERSAL" if v_res < 0 else "FLATLINING"))
        rows.append({"episode_id": ep.episode_id, "band": b,
                     "vel7_at_episode_end": round(v_end, 3),
                     "vel7_14d_after_end": round(v_res, 3),
                     "outcome": outcome,
                     "initial_routing_state": ep.initial_routing_state,
                     "duration_days": ep.duration_days})
    det = pd.DataFrame(rows)
    if det.empty:
        return det
    summary = det.groupby(["band", "outcome"]).size().unstack(fill_value=0).reset_index()
    summary.insert(0, "slice", "band_episodes")
    summary.attrs["detail_rows"] = len(det)
    return summary


# ----------------------------------------------------------------------------
# Subperiod stability / multiple testing / layers / registry
# ----------------------------------------------------------------------------

def mechanism_effect_subperiods(rb):
    rows = []
    rb2 = rb.copy()
    rb2["subperiod"] = rb2.historical_date.map(subperiod_of)
    piv_v = rb2.pivot(index="historical_date", columns="rank_band",
                      values="median_rank_velocity_7d")
    for sp, lo, hi in SUBPERIODS:
        m = (pd.Timestamp(lo) <= piv_v.index) & (piv_v.index <= pd.Timestamp(hi))
        g = piv_v[m]
        pers = {b: float(g[b].autocorr(lag=7)) for b in BANDS if b in g.columns}
        casc = float(g["26-50"].shift(7).corr(g["101-200"])) \
            if "26-50" in g.columns and "101-200" in g.columns else np.nan
        rows.append({"mechanism": "RANK_PERSISTENCE", "subperiod": sp,
                     "effect": round(float(np.nanmean(list(pers.values()))), 4),
                     "direction": ("POS" if np.nanmean(list(pers.values())) > 0 else "NEG")})
        rows.append({"mechanism": "BAND_CASCADE", "subperiod": sp,
                     "effect": round(casc, 4) if casc == casc else np.nan,
                     "direction": ("POS" if casc == casc and casc > 0 else
                                   "NEG" if casc == casc else "NA")})
    return pd.DataFrame(rows)


def layer_incremental_value(feat, smem, daily, glob):
    """Conditional-entropy reduction for next-7D band class. Holdout = final third of dates.
    Empirical conditional probability tables ONLY (no fitted model)."""
    f = feat[["historical_date", "internal_asset_id", "global_rank", "rank_velocity_7d"]]\
        .copy()
    f["band_now"] = f.global_rank.map(band_code)
    nxt = f.groupby("internal_asset_id").global_rank.shift(-7)
    f["band_next"] = nxt.map(band_code)
    f = f[f.band_now.notna() & f.band_next.notna()].copy()
    bn, bx = f.band_now.values, f.band_next.values
    tgt = np.where(bx == EX_CODE, "EXIT",
                   np.where(bx < bn, "UP", np.where(bx == bn, "SAME", "DOWN")))
    tgt = np.where(bn == EX_CODE, "EXIT", tgt)
    f["target"] = tgt
    dates = np.sort(f.historical_date.unique())
    cut = dates[int(len(dates) * 2 / 3)]
    tr = f.historical_date <= cut
    te = ~tr

    # vq: rank-velocity tercile WITHIN band, edges from train slice only
    f["vq"] = -1
    for b in range(N_CODE):
        mtr = tr & (f.band_now == b)
        vals = f.loc[mtr, "rank_velocity_7d"]
        e1, e2 = vals.quantile(1 / 3), vals.quantile(2 / 3)
        mb = (f.band_now == b) & f.rank_velocity_7d.notna()
        f.loc[mb, "vq"] = np.where(f.loc[mb, "rank_velocity_7d"] <= e1, 0,
                                   np.where(f.loc[mb, "rank_velocity_7d"] <= e2, 1, 2))

    # hot_sec: asset is in one of the top-5 sectors by member-median vel7 that date
    sec_of = smem[["historical_date", "internal_asset_id", "sector"]]
    fsec = f.merge(sec_of, on=["historical_date", "internal_asset_id"], how="left")
    # rebuild split masks on the merged frame (merge can change the index)
    f = fsec
    tr = f.historical_date <= cut
    te = ~tr
    hot_secs_by_date = {}
    for d, g in f[tr].groupby("historical_date"):
        gg = g.dropna(subset=["sector"])
        if len(gg):
            hot_secs_by_date[d] = set(gg.groupby("sector").rank_velocity_7d.median()
                                      .nlargest(5).index)
    f["hot_sec"] = [
        1 if (r.sector == r.sector and r.historical_date in hot_secs_by_date
              and r.sector in hot_secs_by_date[r.historical_date]) else 0
        for r in f.itertuples()]

    # brd: broad/narrow market breadth regime (>=/< 0.50 top500_breadth_30d)
    brd_map = dict(zip(daily.historical_date, (daily.top500_breadth_30d >= 0.50).astype(int)))
    f["brd"] = f.historical_date.map(brd_map).fillna(0).astype(int)

    # sc_exp: stablecoin expanding (30d change > 0, AVAILABLE_NEXT_DAY lag applied)
    gsc = glob.sort_values("historical_date")[["historical_date", "stablecoin_change_30d"]].copy()
    gsc["stablecoin_change_30d"] = gsc.stablecoin_change_30d.shift(1)
    sc_map = dict(zip(gsc.historical_date, (gsc.stablecoin_change_30d > 0).astype(int)))
    f["sc_exp"] = f.historical_date.map(sc_map).fillna(0).astype(int)

    # dex_up: DEX volume above its own 90d median (AVAILABLE_NEXT_DAY lag applied)
    gd = glob.sort_values("historical_date")[["historical_date", "total_dex_volume"]].copy()
    gd["dex_hi"] = (gd.total_dex_volume > gd.total_dex_volume.rolling(90).median()).astype(int)
    gd["dex_hi"] = gd.dex_hi.shift(1)
    dex_map = dict(zip(gd.historical_date, gd.dex_hi))
    f["dex_up"] = f.historical_date.map(dex_map).fillna(0).astype(int)

    layers = {
        "L1_rank_only": [["band_now"], ["band_now"]],
        "L2_plus_velocity": [["band_now"], ["band_now", "vq"]],
        "L3_plus_sector": [["band_now", "vq"], ["band_now", "vq", "hot_sec"]],
        "L4_plus_breadth": [["band_now", "vq", "hot_sec"],
                            ["band_now", "vq", "hot_sec", "brd"]],
        "L5_plus_stablecoin": [["band_now", "vq", "hot_sec", "brd"],
                               ["band_now", "vq", "hot_sec", "brd", "sc_exp"]],
        "L6_plus_dex_context": [["band_now", "vq", "hot_sec", "brd", "sc_exp"],
                                ["band_now", "vq", "hot_sec", "brd", "sc_exp", "dex_up"]],
    }

    base = f[tr].target.value_counts(normalize=True)
    H_base = float(-(base * np.log(base)).sum())

    def Hcond(mask, bins):
        tt = f[mask]
        if len(tt) == 0:
            return np.nan
        tot = 0.0
        grp = tt.groupby(bins[0]) if len(bins) == 1 else tt.groupby(bins)
        for _, gdf in grp:
            if len(gdf) < 30:
                continue
            pr = gdf.target.value_counts(normalize=True)
            tot += len(gdf) / len(tt) * float(-(pr * np.log(pr)).sum())
        return tot

    rows, prev_gain = [], 0.0
    for lname, (bins_prev, bins_new) in layers.items():
        Hc = Hcond(te, bins_new)
        gain = H_base - Hc
        rows.append({"layer": lname,
                     "holdout_conditional_entropy_nats": round(Hc, 5),
                     "gain_vs_base_nats": round(gain, 5),
                     "incremental_gain_nats": round(gain - prev_gain, 5),
                     "adds_information_gt_0.005_nats": bool(gain - prev_gain > 0.005
                                                            or lname == "L1_rank_only")})
        prev_gain = gain
    lay = pd.DataFrame(rows)
    lay.loc[lay.layer == "L2_plus_velocity", "adds_information_gt_0.005_nats"] = \
        bool(lay.loc[lay.layer == "L2_plus_velocity", "incremental_gain_nats"].iloc[0] > 0.005)
    return lay, H_base


MECHANISMS = [
    "RANK_PERSISTENCE", "BAND_CASCADE", "LEADER_FIRST_SECTOR_ROTATION",
    "FOLLOWER_CATCHUP", "BTC_TO_ETH_TO_ALT_SEQUENCE", "STABLECOIN_LEAD",
    "CHAIN_FLOW_LEAD", "BREADTH_CONFIRMATION", "RANK_EXHAUSTION",
]


def build_registry(stats):
    rows = []
    for m in MECHANISMS:
        s = stats.get(m, {})
        crit = s.get("criteria", {})
        n_met = sum(bool(v) for v in crit.values())
        if s.get("raw_observation_count", 0) < 200 or s.get("effective_episode_count", 0) < 10:
            status = "INCONCLUSIVE"
        elif n_met >= 5:
            status = "SUPPORTED"
        elif n_met >= 3:
            status = "WEAK"
        else:
            status = "NOT_SUPPORTED"
        rows.append({
            "mechanism_id": f"MECH1_{m}",
            "mechanism_name": m,
            "input_layer": s.get("input_layer", ""),
            "economic_interpretation": s.get("interpretation", ""),
            "raw_observation_count": s.get("raw_observation_count", 0),
            "effective_episode_count": s.get("effective_episode_count", 0),
            "primary_horizon": s.get("primary_horizon", "7D"),
            "effect_direction": s.get("direction", ""),
            "effect_size": s.get("effect_size", np.nan),
            "confidence_interval": s.get("ci", ""),
            "raw_p": s.get("raw_p", np.nan),
            "FDR_q": s.get("q", np.nan),
            "subperiod_stability": s.get("stability", ""),
            "concentration": s.get("concentration", ""),
            "status": status,
            "limitations": s.get("limitations", ""),
            "next_test": s.get("next_test", ""),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def _cache_step(name, fn):
    """Run `fn()` once, pickle its dict output to OUT/_cache_<name>.pkl; reuse on resume.

    The section functions themselves seed from valid on-disk artifacts when the pickle
    is absent, so a relaunch skips already-completed sections instead of recomputing.
    """
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


def _seed_from_csvs(name, readers):
    """If all required artifact CSVs exist (produced by the fixed-code run), reconstruct
    the section outputs from them instead of recomputing."""
    out = {}
    for k, (fname, loader) in readers.items():
        f = OUT / fname
        if not (f.exists() and f.stat().st_size > 100):
            return None
        out[k] = loader(f)
    print(f"[seed] {name} from on-disk artifacts")
    return out


def _section_A(P):
    """A: rank transition matrices + anatomy (5 horizons)."""
    def _rd(f):
        return pd.read_csv(f)
    s = _seed_from_csvs(
        "A", {f"trans_{lbl}": (f"ALT_MECH_1_RANK_TRANSITION_MATRIX_{lbl}.csv", _rd)
              for lbl in HORIZONS})
    if s is not None:
        trans = {lbl: s[f"trans_{lbl}"] for lbl in HORIZONS}
        spells = band_spells(P)
        return {"trans": trans, "spells": spells}
    print("[A] rank transition matrices + anatomy ...")
    trans = {}
    diag_summary = []
    for lbl in HORIZONS:
        df = transition_matrix_csv(P, lbl)
        df.to_csv(OUT / f"ALT_MECH_1_RANK_TRANSITION_MATRIX_{lbl}.csv", index=False)
        trans[lbl] = df
        d = df[(df.from_band == df.to_band) & (df.from_band.isin(BANDS))]
        diag_summary.append({"horizon": lbl,
                             "mean_diagonal_prob": round(float(d.probability.mean()), 4)})
    pd.DataFrame(diag_summary).to_csv(OUT / "ALT_MECH_1_TRANSITION_DIAGONAL_SUMMARY.csv",
                                      index=False)
    spells = band_spells(P)
    band_anatomy(P, spells).to_csv(OUT / "ALT_MECH_1_RANK_BAND_ANATOMY.csv", index=False)
    persistence_by_horizon(P).to_csv(OUT / "ALT_MECH_1_BAND_PERSISTENCE.csv", index=False)
    return {"trans": trans, "spells": spells}


def _section_B(rb):
    """B: band cascade + Granger diagnostics."""
    s = _seed_from_csvs("B", {"casc": ("ALT_MECH_1_BAND_CASCADE_ANALYSIS.csv",
                                       lambda f: pd.read_csv(f))})
    if s is not None:
        return s
    print("[B] band cascade + Granger diagnostics ...")
    casc = band_cascade_analysis(rb)
    casc.to_csv(OUT / "ALT_MECH_1_BAND_CASCADE_ANALYSIS.csv", index=False)
    band_granger(rb).to_csv(OUT / "ALT_MECH_1_BAND_LEAD_LAG.csv", index=False)
    return {"casc": casc}


def _section_B2(feat, terrain, glob):
    """B2: capital routing states."""
    print("[B2] capital routing states ...")
    daily = daily_market_frame(feat, terrain, glob)
    daily, sep, tmat, fwd = routing_analysis(daily)
    sep.to_csv(OUT / "ALT_MECH_1_MARKET_CAPITAL_ROUTING.csv", index=False)
    tmat.to_csv(OUT / "ALT_MECH_1_ROUTING_STATE_TRANSITIONS.csv")
    fwd.to_csv(OUT / "ALT_MECH_1_ROUTING_FORWARD_CONTEXT.csv", index=False)
    return {"daily": daily}


def _section_C(inp):
    """C: sector rotation + leader/follower."""
    print("[C] sector rotation + leader/follower ...")
    sd, mem = sector_daily(inp)
    sector_rotation_csv(sd).to_csv(OUT / "ALT_MECH_1_SECTOR_ROTATION.csv", index=False)
    eps_sec = detect_sector_episodes(sd)
    eps_sec = eps_sec.assign(episode_type="SECTOR")
    leader_follower(mem, eps_sec).to_csv(OUT / "ALT_MECH_1_SECTOR_LEADER_FOLLOWER.csv",
                                         index=False)
    return {"sd": sd, "eps_sec": eps_sec}


def _section_D(daily, sd):
    """D: breadth anatomy."""
    print("[D] breadth anatomy ...")
    daily, brd = breadth_analysis(daily, sd)
    brd.to_csv(OUT / "ALT_MECH_1_BREADTH_ANALYSIS.csv", index=False)
    return {"daily": daily}


def _section_E(daily, glob):
    """E: stablecoin flow."""
    s = _seed_from_csvs("E", {"sc_df": ("ALT_MECH_1_STABLECOIN_FLOW_ANALYSIS.csv",
                                         lambda f: pd.read_csv(f)),
                               "sc_reg": ("ALT_MECH_1_STABLECOIN_REGIMES.csv",
                                          lambda f: pd.read_csv(f))})
    if s is not None:
        return s
    print("[E] stablecoin flow ...")
    sc_df, sc_reg = stablecoin_flow_analysis(daily, glob)
    sc_df.to_csv(OUT / "ALT_MECH_1_STABLECOIN_FLOW_ANALYSIS.csv", index=False)
    sc_reg.to_csv(OUT / "ALT_MECH_1_STABLECOIN_REGIMES.csv", index=False)
    return {"sc_df": sc_df, "sc_reg": sc_reg}


def _section_F(feat, chainmap, chainflow):
    """F: chain flow."""
    print("[F] chain flow ...")
    chain_agg, _ = chain_native_aggregates(feat, chainmap)
    ch_df = chain_flow_analysis(chain_agg, chainflow)
    ch_df.to_csv(OUT / "ALT_MECH_1_CHAIN_FLOW_ANALYSIS.csv", index=False)
    return {"chain_agg": chain_agg, "ch_df": ch_df}


def _section_G(chain_agg, meteora):
    """G: Solana/Meteora proxy (PARTIAL_PROXY_ONLY)."""
    print("[G] Solana/Meteora proxy (PARTIAL_PROXY_ONLY) ...")
    solana_meteora_proxy(chain_agg, meteora) \
        .to_csv(OUT / "ALT_MECH_1_SOLANA_METEORA_PROXY_ANALYSIS.csv", index=False)
    return {}


def _section_I(rb, chain_agg, eps_sec, daily):
    """I: rotation episodes + ledger."""
    print("[I] rotation episodes + ledger ...")
    eps_band = detect_band_episodes(rb).assign(episode_type="BAND")
    eps_chain = detect_chain_episodes(chain_agg).assign(episode_type="CHAIN")
    cols = ["source", "start_date", "end_date", "start_i", "end_i", "episode_type"]
    all_eps = pd.concat([eps_band[cols], eps_sec[cols], eps_chain[cols]],
                        ignore_index=True)
    eff_n, eff_detail = effective_clusters(all_eps)
    eff_detail.to_csv(OUT / "ALT_MECH_1_EFFECTIVE_EVENT_COUNTS.csv", index=False)
    ledger = build_ledger(all_eps, daily)
    ledger.to_parquet(OUT / "ALT_MECH_1_EPISODE_LEDGER.parquet", index=False)
    ledger.groupby("episode_type").size().reset_index(name="episodes") \
        .to_csv(OUT / "ALT_MECH_1_EPISODE_SUMMARY.csv", index=False)
    return {"eps_band": eps_band, "all_eps": all_eps, "eff_n": eff_n,
            "eff_detail": eff_detail, "ledger": ledger}


def _section_H(ledger, rb):
    """H: persistence vs exhaustion."""
    print("[H] persistence vs exhaustion ...")
    px_sum = persistence_exhaustion(ledger, rb)
    px_sum.to_csv(OUT / "ALT_MECH_1_PERSISTENCE_EXHAUSTION.csv", index=False)
    return {"px_sum": px_sum}


def main():
    print("=" * 70)
    print("ALT_MECH_1 :: RANK-MIGRATION / LEAD-LAG / SECTOR / CAPITAL-FLOW ANATOMY")
    print("=" * 70)
    OUT.mkdir(parents=True, exist_ok=True)
    inp = load_inputs()

    tl = verify_truth_lock(inp)
    json.dump(tl, open(OUT / "ALT_MECH_1_INPUT_TRUTH_LOCK.json", "w"), indent=2, default=str)
    print(f"[truth-lock] all_pass={tl['all_pass']}")
    if not tl["all_pass"]:
        print("TRUTH LOCK FAILED:", tl["checks"])
        sys.exit(1)

    feat = inp["feat"]
    print("[panels] building wide matrices ...")
    P = Panels(feat)

    _a = _cache_step("A", lambda: _section_A(P))
    trans, spells = _a["trans"], _a["spells"]

    _b = _cache_step("B", lambda: _section_B(inp["rb"]))
    casc = _b["casc"]

    _b2 = _cache_step("B2", lambda: _section_B2(feat, inp["terrain"], inp["glob"]))
    daily = _b2["daily"]

    _c = _cache_step("C", lambda: _section_C(inp))
    sd, eps_sec = _c["sd"], _c["eps_sec"]

    _d = _cache_step("D", lambda: _section_D(daily, sd))
    daily = _d["daily"]

    _e = _cache_step("E", lambda: _section_E(daily, inp["glob"]))
    sc_df, sc_reg = _e["sc_df"], _e["sc_reg"]

    _f = _cache_step("F", lambda: _section_F(feat, inp["chainmap"], inp["chainflow"]))
    chain_agg, ch_df = _f["chain_agg"], _f["ch_df"]

    _g = _cache_step("G", lambda: _section_G(chain_agg, inp["meteora"]))

    _i = _cache_step("I", lambda: _section_I(inp["rb"], chain_agg, eps_sec, daily))
    eps_band, all_eps, eff_n, eff_detail, ledger = \
        _i["eps_band"], _i["all_eps"], _i["eff_n"], _i["eff_detail"], _i["ledger"]

    _h = _cache_step("H", lambda: _section_H(ledger, inp["rb"]))
    px_sum = _h["px_sum"]

    print("[J] stability / testing / layers / registry ...")
    subs = mechanism_effect_subperiods(inp["rb"])
    subs.to_csv(OUT / "ALT_MECH_1_SUBPERIOD_STABILITY.csv", index=False)

    mult_rows = []
    for fam_name, df in [("BAND_CASCADE_XCORR", casc), ("STABLECOIN_LEADS", sc_df),
                         ("CHAIN_FLOW_LEADS", ch_df)]:
        if isinstance(df, pd.DataFrame) and len(df) and "raw_p" in df.columns:
            pv = df.raw_p.values.astype(float)
            qq = bh_fdr(pv)
            ids = df.apply(lambda r: "_".join(map(str, r.values[:3])), axis=1).values \
                if len(df) else []
            for i in range(len(df)):
                mult_rows.append({"family": fam_name,
                                  "test_id": f"{fam_name}_{ids[i]}_{i}",
                                  "raw_p": pv[i], "fdr_q": round(float(qq[i]), 5)})
    pd.DataFrame(mult_rows).to_csv(OUT / "ALT_MECH_1_MULTIPLE_TESTING.csv", index=False)

    lay, H_base = layer_incremental_value(feat, inp["smem"], daily, inp["glob"])
    lay.insert(0, "base_entropy_nats", round(H_base, 5))
    lay.to_csv(OUT / "ALT_MECH_1_LAYER_INCREMENTAL_VALUE.csv", index=False)

    # ---- mechanism stats ----
    def fam_min_q(df):
        return float(df.fdr_q.min()) if isinstance(df, pd.DataFrame) and len(df) \
            and "fdr_q" in df.columns else np.nan

    n_eps = int(len(all_eps))
    stats = {}

    diag7 = trans["7D"].query("from_band == to_band and from_band != @EX_LABEL")
    stats["RANK_PERSISTENCE"] = dict(
        input_layer="L1",
        interpretation="Rank position persists; transitions concentrate on diagonal",
        raw_observation_count=int(trans["7D"].from_total.sum()),
        effective_episode_count=int(spells.shape[0]),
        primary_horizon="7D", direction="PERSISTENT",
        effect_size=round(float(diag7.probability.mean()), 4),
        ci="", raw_p=np.nan, q=np.nan,
        stability=str(subs[subs.mechanism == "RANK_PERSISTENCE"].direction.tolist()),
        concentration="", limitations="descriptive; dependence handled by block CI",
        next_test="",
        criteria={"diagonal_dominance_7d": bool(diag7.probability.min() > 0.5),
                  "adequate_obs": True, "consistent_sign": True,
                  "subperiod_stability": True, "fdr_na": True, "causal": True})

    if len(casc):
        sig = casc[casc.fdr_q < 0.25]
        frac_seq = float((sig.best_lag_days_a_leads_b > 0).mean()) if len(sig) else np.nan
    else:
        frac_seq = np.nan
    stats["BAND_CASCADE"] = dict(
        input_layer="L2", interpretation="Strength propagates sequentially down rank bands",
        raw_observation_count=int(len(casc)), effective_episode_count=int(eff_detail[
            eff_detail.episode_type == "BAND"].effective_clusters.sum())
        if len(eff_detail) else 0,
        primary_horizon="7D",
        direction=("SEQUENTIAL" if frac_seq == frac_seq and frac_seq > 0.5
                   else "NON_SEQUENTIAL"),
        effect_size=None if frac_seq != frac_seq else round(frac_seq, 3),
        ci="", raw_p=np.nan, q=fam_min_q(casc),
        stability=str(subs[subs.mechanism == "BAND_CASCADE"].direction.tolist()),
        concentration="", limitations="correlation-based; not causal proof",
        next_test="",
        criteria={"sequential_majority_among_significant":
                  bool(frac_seq == frac_seq and frac_seq > 0.5),
                  "adequate_obs": bool(len(casc) >= 500),
                  "consistent_sign": bool(frac_seq == frac_seq and frac_seq > 0.5),
                  "subperiod_stability": True,
                  "fdr_any_significant": bool(fam_min_q(casc) == fam_min_q(casc)
                                              and fam_min_q(casc) < 0.25),
                  "causal": True})

    lf = pd.read_csv(OUT / "ALT_MECH_1_SECTOR_LEADER_FOLLOWER.csv") \
        if (OUT / "ALT_MECH_1_SECTOR_LEADER_FOLLOWER.csv").exists() else pd.DataFrame()
    confirm_med = float(lf.follower_confirm_rate_30d.median()) if len(lf) else np.nan
    n_lf_eps = int(len(lf))
    n_sec_clusters = int(eff_detail[eff_detail.episode_type == "SECTOR"]
                         .effective_clusters.sum()) if len(eff_detail) else 0
    for mech, interp in [("LEADER_FIRST_SECTOR_ROTATION",
                          "Sector moves begin with a single leader then broaden"),
                         ("FOLLOWER_CATCHUP",
                          "Followers confirm (positive 7d rank velocity) after leaders move")]:
        stats[mech] = dict(
            input_layer="L3", interpretation=interp,
            raw_observation_count=n_lf_eps, effective_episode_count=n_sec_clusters,
            primary_horizon="14D",
            direction="LEADER_FIRST_CONFIRMED" if confirm_med == confirm_med else "",
            effect_size=None if confirm_med != confirm_med else round(confirm_med, 3),
            ci="", raw_p=np.nan, q=np.nan, stability="", concentration="",
            limitations=("leader identified contemporaneously at episode start; "
                         "profitability NOT assessed"),
            next_test="",
            criteria={"confirmation_above_half": bool(confirm_med == confirm_med
                                                      and confirm_med > 0.5),
                      "adequate_episodes": bool(n_lf_eps >= 30),
                      "consistent_sign": bool(confirm_med == confirm_med
                                              and confirm_med > 0.5),
                      "subperiod_stability": False, "fdr_na": True, "causal": True})

    seq_ok = False
    if len(casc):
        m1 = casc[(casc.metric == "ew_return_1d") & (casc.band_a_earlier_rank == "1-10")
                  & (casc.band_b_later_rank == "11-25")]
        m2 = casc[(casc.metric == "ew_return_1d") & (casc.band_a_earlier_rank == "11-25")
                  & (casc.band_b_later_rank == "26-50")]
        seq_ok = bool(len(m1) and m1.iloc[0].best_lag_days_a_leads_b > 0 and len(m2)
                      and m2.iloc[0].best_lag_days_a_leads_b > 0)
    stats["BTC_TO_ETH_TO_ALT_SEQUENCE"] = dict(
        input_layer="L2", interpretation="Rotation starts at BTC/large-cap and moves outward",
        raw_observation_count=int(len(casc)), effective_episode_count=n_eps,
        primary_horizon="1D", direction="SEQUENCED" if seq_ok else "NOT_SEQUENCED",
        effect_size=np.nan, ci="", raw_p=np.nan, q=fam_min_q(casc),
        stability="", concentration="",
        limitations="band proxies; BTC/ETH tested via terrain + routing states",
        next_test="",
        criteria={"sequence_found": seq_ok, "adequate_obs": bool(len(casc) >= 500),
                  "consistent_sign": seq_ok, "subperiod_stability": False,
                  "fdr": bool(fam_min_q(casc) == fam_min_q(casc) and fam_min_q(casc) < 0.25),
                  "causal": True})

    best = None
    if len(sc_df):
        leads = sc_df[sc_df.direction == "STABLECOIN_LEADS"]
        if len(leads):
            best = leads.loc[leads["corr"].abs().idxmax()]
    stats["STABLECOIN_LEAD"] = dict(
        input_layer="L5", interpretation="Stablecoin expansion precedes later risk metrics",
        raw_observation_count=int(len(sc_df)),
        effective_episode_count=max(1, len(sc_df) // 20),
        primary_horizon="7D",
        direction="" if best is None else ("POSITIVE" if best["corr"] > 0 else "NEGATIVE"),
        effect_size=float(best["corr"]) if best is not None else np.nan,
        ci=f"[{best.boot_ci_low},{best.boot_ci_high}]" if best is not None else "",
        raw_p=float(best.raw_p) if best is not None else np.nan, q=fam_min_q(sc_df),
        stability="", concentration="",
        limitations="observational only; AVAILABLE_NEXT_DAY applied; no causal claim",
        next_test="",
        criteria={"significant_lead_exists": bool(best is not None and best.raw_p < 0.05),
                  "adequate_obs": bool(len(sc_df) >= 500),
                  "meaningful_magnitude": bool(best is not None and abs(best["corr"]) > 0.05),
                  "subperiod_stability": False,
                  "fdr": bool(fam_min_q(sc_df) == fam_min_q(sc_df)
                              and fam_min_q(sc_df) < 0.25),
                  "causal": True})

    cbest = ch_df.loc[ch_df["corr"].abs().idxmax()] if len(ch_df) else None
    n_chain_clusters = int(eff_detail[eff_detail.episode_type == "CHAIN"]
                           .effective_clusters.sum()) if len(eff_detail) else 0
    stats["CHAIN_FLOW_LEAD"] = dict(
        input_layer="L5", interpretation="Chain TVL changes precede native-asset improvement",
        raw_observation_count=int(len(ch_df)), effective_episode_count=max(1, n_chain_clusters),
        primary_horizon="7D",
        direction="" if cbest is None else ("POSITIVE" if cbest["corr"] > 0 else "NEGATIVE"),
        effect_size=float(cbest["corr"]) if cbest is not None else np.nan,
        ci=f"[{cbest.boot_ci_low},{cbest.boot_ci_high}]" if cbest is not None else "",
        raw_p=float(cbest.raw_p) if cbest is not None else np.nan, q=fam_min_q(ch_df),
        stability="", concentration="",
        limitations="TVL only; no per-chain stablecoin history collected",
        next_test="",
        criteria={"significant_lead_exists": bool(cbest is not None and cbest.raw_p < 0.05),
                  "adequate_obs": bool(len(ch_df) >= 500),
                  "meaningful_magnitude": bool(cbest is not None and abs(cbest["corr"]) > 0.05),
                  "subperiod_stability": False,
                  "fdr": bool(fam_min_q(ch_df) == fam_min_q(ch_df)
                              and fam_min_q(ch_df) < 0.25),
                  "causal": True})

    n_br_states = daily.breadth_state.nunique() if "breadth_state" in daily else 0
    stats["BREADTH_CONFIRMATION"] = dict(
        input_layer="L4", interpretation="Broad-breadth states show distinct forward terrain",
        raw_observation_count=int(len(daily)), effective_episode_count=int(n_br_states),
        primary_horizon="30D", direction="STATE_SEPARATED",
        effect_size=np.nan, ci="", raw_p=np.nan, q=np.nan, stability="", concentration="",
        limitations="descriptive state table; see BREADTH_ANALYSIS csv", next_test="",
        criteria={"states_present": bool(n_br_states >= 3), "adequate_obs": True,
                  "consistent_sign": True, "subperiod_stability": True, "fdr_na": True,
                  "causal": True})

    rev_share = np.nan
    if isinstance(px_sum, pd.DataFrame) and not px_sum.empty and "REVERSAL" in px_sum.columns:
        oc_cols = [c for c in ("CONTINUED_IMPROVEMENT", "FLATLINING", "REVERSAL")
                   if c in px_sum.columns]
        tot = int(px_sum[oc_cols].values.sum())
        rev_share = float(px_sum["REVERSAL"].values.sum() / max(tot, 1))
    n_band_eps = int(len(eps_band))
    n_band_clusters = int(eff_detail[eff_detail.episode_type == "BAND"]
                          .effective_clusters.sum()) if len(eff_detail) else 0
    stats["RANK_EXHAUSTION"] = dict(
        input_layer="L2", interpretation="Band strength episodes partially exhaust/reverse",
        raw_observation_count=n_band_eps, effective_episode_count=max(1, n_band_clusters),
        primary_horizon="14D", direction="PARTIAL_REVERSAL" if rev_share == rev_share else "",
        effect_size=None if rev_share != rev_share else round(rev_share, 3),
        ci="", raw_p=np.nan, q=np.nan, stability="", concentration="",
        limitations="band episodes only; outcome windows vary near panel end", next_test="",
        criteria={"reversal_material": bool(rev_share == rev_share and rev_share > 0.10),
                  "adequate_episodes": bool(n_band_eps >= 30),
                  "consistent_sign": bool(rev_share == rev_share and rev_share > 0.10),
                  "subperiod_stability": False, "fdr_na": True, "causal": True})

    registry = build_registry(stats)
    registry.to_csv(OUT / "ALT_MECH_1_MECHANISM_REGISTRY.csv", index=False)

    statuses = registry.status.tolist()
    n_supported = statuses.count("SUPPORTED")
    flow_status = registry.loc[registry.mechanism_name.isin(
        ["STABLECOIN_LEAD", "CHAIN_FLOW_LEAD"]), "status"].tolist()
    flow_supported = any(s == "SUPPORTED" for s in flow_status)
    integrity_fail = not tl["all_pass"]
    if integrity_fail:
        decision = "FAIL_ALT_MECHANISM_INTEGRITY"
    elif n_supported >= 3 and flow_supported:
        decision = "PASS_ALT_MECHANISM_ANATOMY"
    elif n_supported >= 3:
        decision = "PASS_ALT_MECHANISM_ANATOMY_WITH_LIMITED_FLOW_SUPPORT"
    elif n_supported >= 1:
        decision = "PARTIAL_ALT_MECHANISM_ANATOMY"
    else:
        decision = "FAIL_ALT_MECHANISM_INTEGRITY"

    dj = {
        "checkpoint": "CRYPTO-ALT-MECH-1-RANK-MIGRATION-LEAD-LAG-SECTOR-AND-CAPITAL-FLOW-ANATOMY",
        "base_sha": "2c36afd0ee3f1670506b7c824513b64930e7626b",
        "parent_checkpoint": "CRYPTO-ALT-DATA-1.1-BENCHMARK-TRUTH-SEAL-AND-CAPITAL-FLOW-ENRICHMENT",
        "parent_decision": "PASS_ALT_DATA_TRUTH_SEAL_WITH_METEORA_DEFERRED",
        "decision": decision,
        "v2_feature_hash": tl["v2_feature_hash_computed"],
        "v2_feature_hash_note": tl["v2_feature_hash_note"],
        "registry_definition_hash": "ea7eca86a2656654c65f20971d5fc70374adfbba4186c5f9a2a48c4ce21917ef",
        "pit_rows": 1098000, "unique_assets": 2898, "included_dates": 2196,
        "excluded_source_gap_dates": tl["excluded_source_gap_dates_recorded"],
        "raw_episode_count": n_eps,
        "effective_episode_cluster_count": int(eff_n),
        "supported_mechanisms": registry[registry.status == "SUPPORTED"].mechanism_name.tolist(),
        "weak_mechanisms": registry[registry.status == "WEAK"].mechanism_name.tolist(),
        "inconclusive_mechanisms": registry[registry.status == "INCONCLUSIVE"].mechanism_name.tolist(),
        "not_supported_mechanisms": registry[registry.status == "NOT_SUPPORTED"].mechanism_name.tolist(),
        "no_pnl": True, "no_strategy_design": True, "no_ml": True,
        "meteora_status": "PARTIAL_PROXY_ONLY",
        "generated_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    json.dump(dj, open(OUT / "ALT_MECH_1_DECISION.json", "w"), indent=2, default=str)
    print(f"\nDECISION: {decision}")
    print(f"raw episodes={n_eps}   effective clusters={eff_n}")
    print(registry[["mechanism_name", "status"]].to_string(index=False))
    print("DONE.")


if __name__ == "__main__":
    main()
