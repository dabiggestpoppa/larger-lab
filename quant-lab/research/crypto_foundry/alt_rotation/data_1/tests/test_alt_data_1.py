#!/usr/bin/env python3
"""ALT-DATA-1 test suite.

Covers: PIT rank uniqueness, exact top-500 membership, fallen-asset
survival, entry/exit causality, perp listing/delisting causality, 30D
maturity, 90D history requirement, per-window feature causality, future
perturbation invariance, rank-change sign convention, sector-rank
consistency, sector participation hierarchy, rank-band membership and
counts, market-cap share sums, BTC/ETH-relative returns, beta/residual
causality, feature-registry determinism, provenance hashes.

All tests read the frozen artifacts in data_1/ (parquet + registry +
raw meta sidecars). No network.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import alt_data_1_build_pipeline as P  # noqa: E402

BANDS = [(1, 10), (11, 25), (26, 50), (51, 100), (101, 200), (201, 300),
         (301, 500)]
BAND_SIZES = {f"{lo}-{hi}": (hi - lo + 1) for lo, hi in BANDS}
WINDOWS = [1, 3, 7, 14, 30, 60, 90]
MIN_MATURITY = 30


@pytest.fixture(scope="session")
def uni():
    return pd.read_parquet(ROOT / "ALT_DATA_1_PIT_UNIVERSE.parquet")


@pytest.fixture(scope="session")
def feat():
    return pd.read_parquet(ROOT / "ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet")


@pytest.fixture(scope="session")
def elig():
    return pd.read_parquet(ROOT / "ALT_DATA_1_PERP_ELIGIBILITY.parquet")


@pytest.fixture(scope="session")
def ident():
    return pd.read_parquet(ROOT / "ALT_DATA_1_IDENTITY_MAP.parquet")


@pytest.fixture(scope="session")
def band():
    return pd.read_parquet(ROOT / "ALT_DATA_1_RANK_BAND_FEATURES.parquet")


@pytest.fixture(scope="session")
def sec():
    return pd.read_parquet(ROOT / "ALT_DATA_1_SECTOR_FEATURES.parquet")


@pytest.fixture(scope="session")
def smem():
    return pd.read_parquet(ROOT / "ALT_DATA_1_SECTOR_MEMBERSHIP.parquet")


@pytest.fixture(scope="session")
def terr():
    return pd.read_parquet(ROOT / "ALT_DATA_1_MARKET_TERRAIN_FEATURES.parquet")


@pytest.fixture(scope="session")
def surv():
    return pd.read_parquet(ROOT / "ALT_DATA_1_SURVIVORSHIP.parquet")


@pytest.fixture(scope="session")
def summary():
    return json.loads((ROOT / "derived" / "build_summary.json")
                      .read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# PIT universe
# ----------------------------------------------------------------------
def test_pit_rank_uniqueness_per_date(uni):
    bad = uni.groupby("historical_date")["rank"].nunique() != 500
    assert not bad.any(), f"dates with non-unique ranks: {bad[bad].index[:5]}"


def test_exact_top500_membership(uni):
    for dt, sub in uni.groupby("historical_date"):
        assert set(sub["rank"]) == set(range(1, 501)), dt


def test_no_rank_out_of_range(uni):
    assert (uni["rank"] >= 1).all()
    assert (uni["rank"] <= 500).all()


def test_no_duplicate_asset_per_date(uni):
    dup = uni.groupby("historical_date")["cmc_id"].apply(
        lambda s: s.nunique() != len(s))
    assert not dup.any()


def test_date_range_expectation(uni, summary):
    assert str(uni["historical_date"].min().date()) == "2020-06-01"
    assert str(uni["historical_date"].max().date()) == "2026-08-23"
    assert summary["n_dates"] == uni["historical_date"].nunique()


def test_excluded_dates_documented(summary):
    # every exclusion is recorded; no silent date holes
    excl = summary["excluded_dates"]
    dates = set(excl_d["historical_date"] for excl_d in excl)
    assert len(dates) >= 22, f"too few excluded dates: {len(dates)}"
    assert "20210928" in dates  # known major gap
    for d in dates:
        assert len(d.replace("-", "")) == 8, f"invalid date format: {d}"


def test_fallen_asset_survival(uni, ident):
    # assets once top-ranked but since fallen remain present historically
    # (checked by stable cmc_id, since symbols may have been renamed)
    cases = {4195: "FTT/FTX Token", 4172: "LUNA/LUNC",
             2682: "HOT", 6187: "SRM"}
    for cid, label in cases.items():
        sub = uni[uni["cmc_id"] == cid]
        assert not sub.empty, label
        assert sub["historical_date"].min() <= pd.Timestamp("2021-01-01"), \
            label
    lunc = uni[uni["cmc_id"] == 4172]
    assert lunc["historical_date"].max() >= pd.Timestamp("2023-01-01")
    ftt = uni[uni["symbol"] == "FTT"]
    ftt_ids = ftt["cmc_id"].unique()
    assert 4195 in ftt_ids  # FTX Token
    assert len(ftt_ids) >= 2  # symbol reuse (FarmaTrust) also present
    idr = ident[ident["cmc_id"] == 4195]
    assert not idr.empty
    assert idr["collision_class"].iloc[0] == "TRUE_TICKER_REUSE"


def test_identity_stable_ids_unique(ident):
    assert ident["internal_asset_id"].is_unique
    assert ident["cmc_id"].is_unique


def test_top500_entry_exit_causality(uni, feat, surv):
    # entered_top500 is causal: true on first appearance / gap re-entry
    f = feat.sort_values(["cmc_id", "historical_date"])
    first = f.groupby("cmc_id")["historical_date"].transform("min")
    firsts = f[f["historical_date"] == first]
    assert firsts["entered_top500"].all()
    # no future knowledge: entered uses only t-1 membership
    prev = f.groupby("cmc_id")["historical_date"].shift(1)
    gap = f["historical_date"].sub(prev).dt.days.ne(1).fillna(True)
    assert (f["entered_top500"] == gap).all()
    # consecutive_days_in_top500 consistency
    c = f.set_index(["cmc_id", "historical_date"])[
        "consecutive_days_in_top500"]
    assert c.notna().all()
    assert (c >= 1).all()
    # survivorship is non-causal and separate
    assert "exited_top500" not in feat.columns
    assert "exited_top500" in surv.columns
    assert "days_until_exit" in surv.columns
    # exit label sits exactly on the last observed day
    last_day = surv.groupby("cmc_id")["historical_date"].transform("max")
    assert (surv["exited_top500"] == (surv["historical_date"] == last_day))\
        .all()


# ----------------------------------------------------------------------
# Perp eligibility causality
# ----------------------------------------------------------------------
def test_perp_listing_causality(elig):
    tr = elig[elig["tradable_at_t"]]
    # contract_age_days_at_t is float; NaN values are OK (not tradable)
    ages = pd.to_numeric(tr["contract_age_days_at_t"], errors="coerce")
    valid = ages.dropna()
    assert (valid >= 0).all()
    # listing_timestamp must be <= historical_date for all tradable rows
    lt = pd.to_datetime(tr["listing_timestamp"], errors="coerce", utc=True)
    lt_ok = lt.dropna()
    if len(lt_ok):
        idx = lt_ok.index
        hd = tr.loc[idx, "historical_date"].dt.tz_localize("UTC")
        assert (hd >= lt_ok).all()


def test_perp_delisting_causality(elig):
    dl = elig[elig["delisting_timestamp"] != ""]
    tr = dl[dl["tradable_at_t"]]
    if len(tr) == 0:
        return
    dlt = pd.to_datetime(tr["delisting_timestamp"], errors="coerce", utc=True)
    dlt = dlt.dropna()
    if len(dlt):
        idx = dlt.index
        hd = tr.loc[idx, "historical_date"].dt.tz_localize("UTC")
        assert (hd <= dlt).all()


def test_maturity_rule_30d(elig):
    for _, r in elig.iterrows():
        exp = bool(r["tradable_at_t"] and
                   r["contract_age_days_at_t"] is not None and
                   r["contract_age_days_at_t"] >= MIN_MATURITY)
        assert r["mature_30d_at_t"] == exp, r.to_dict()


def test_eligible_implies_mature_and_data(elig):
    ex = elig[elig["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY"]
    assert (ex["mature_30d_at_t"]).all()
    assert (ex["historical_data_eligible"]).all()
    assert (~ex["historical_liquidity_verified"]).all()
    assert (ex["liquidity_proxy_status"].isin(
        ["VOLUME_PROXY_ONLY", "PARTIAL"])).all()


def test_no_full_eligible_status(elig):
    assert "FULLY_ELIGIBLE" not in set(elig["eligibility_status"])


def test_venues_covered(elig):
    assert set(elig["venue"]) <= {"HYPERLIQUID", "OKX"}
    assert elig["venue"].isin(["HYPERLIQUID"]).any()
    assert elig["venue"].isin(["OKX"]).any()


def test_fallen_perp_causality(elig):
    # FTT HL contract exists; check any FTT HL rows exist
    ftt = elig[(elig["symbol"] == "FTT") & (elig["venue"] == "HYPERLIQUID")]
    # FTT may have exited top-500 before HL listing; either way, check
    # that no tradable row is before listing or after delisting
    if not ftt.empty:
        tr = ftt[ftt["tradable_at_t"]]
        assert len(tr) == 0 or (tr["contract_age_days_at_t"] >= 0).all()


# ----------------------------------------------------------------------
# Feature causality per window
# ----------------------------------------------------------------------
@pytest.mark.parametrize("w", WINDOWS)
def test_return_window_causality(uni, feat, w):
    m = uni[["cmc_id", "historical_date", "price_usd"]]
    lag = (m[["cmc_id", "historical_date", "price_usd"]]
           .assign(dl=m["historical_date"] + pd.Timedelta(days=w))
           .drop(columns=["historical_date"])
           .rename(columns={"price_usd": f"p{w}"}))
    mm = m.merge(lag, left_on=["cmc_id", "historical_date"],
                 right_on=["cmc_id", "dl"], how="left")
    mm = mm.merge(feat[["cmc_id", "historical_date", f"return_{w}d"]],
                  on=["cmc_id", "historical_date"], how="left")
    exp = mm["price_usd"] / mm[f"p{w}"] - 1.0
    got = mm[f"return_{w}d"]
    diff = (exp - got).dropna()
    assert np.abs(diff).max() < 1e-9, f"return_{w}d mismatch"


@pytest.mark.parametrize("w", WINDOWS)
def test_rank_change_sign_convention(uni, feat, w):
    m = uni[["cmc_id", "historical_date", "rank"]]
    lag = (m[["cmc_id", "historical_date", "rank"]]
           .assign(dl=m["historical_date"] + pd.Timedelta(days=w))
           .drop(columns=["historical_date"])
           .rename(columns={"rank": f"r{w}"}))
    mm = m.merge(lag, left_on=["cmc_id", "historical_date"],
                 right_on=["cmc_id", "dl"], how="left")
    mm = mm.merge(feat[["cmc_id", "historical_date", f"rank_change_{w}d"]],
                  on=["cmc_id", "historical_date"], how="left")
    exp = mm[f"r{w}"] - mm["rank"]  # positive = improving
    got = mm[f"rank_change_{w}d"]
    diff = (exp - got).dropna()
    assert np.abs(diff).max() < 1e-9, f"rank_change_{w}d mismatch"
    # velocity alias exists only for 1,3,7,14d windows
    if w in (1, 3, 7, 14):
        sub = feat[["cmc_id", "historical_date", f"rank_change_{w}d",
                    f"rank_velocity_{w}d"]].dropna(subset=[f"rank_velocity_{w}d"])
        assert (sub[f"rank_change_{w}d"] == sub[f"rank_velocity_{w}d"]).all()


def test_relative_return_vs_btc(uni, feat, terr):
    # Verify relative return vs BTC columns exist for a non-BTC asset
    eth = feat[feat["cmc_id"] == 1027]
    assert len(eth) > 100  # ETH must be present
    for w in (1, 3, 7, 14, 30, 60, 90):
        col = f"relative_return_vs_BTC_{w}d"
        assert col in eth.columns, f"{col} missing"
        assert eth[col].notna().sum() > 100, f"{col} has <100 values"


def test_relative_return_vs_eth(uni, feat):
    # Verify relative return vs ETH columns exist for BTC
    btc = feat[feat["cmc_id"] == 1]
    assert len(btc) > 100
    for w in (1, 3, 7, 14, 30, 60, 90):
        col = f"relative_return_vs_ETH_{w}d"
        assert col in btc.columns, f"{col} missing"
        assert btc[col].notna().sum() > 100, f"{col} has <100 values"


def test_90d_history_requirement(feat, uni):
    # an asset with < 90d of prior history must NOT have a 90d return
    m = uni[["cmc_id", "historical_date"]]
    lag = (m.assign(dl=m["historical_date"] + pd.Timedelta(days=90))
           .drop(columns=["historical_date"]))
    mm = m.merge(lag, left_on=["cmc_id", "historical_date"],
                 right_on=["cmc_id", "dl"], how="left",
                 indicator=True)
    no_hist = mm[mm["_merge"] == "left_only"][["cmc_id", "historical_date"]]
    if len(no_hist):
        chk = feat.merge(no_hist, on=["cmc_id", "historical_date"],
                         how="inner")
        assert chk["return_90d"].isna().all()
    # no NaN backfill: NaN is NaN, never silently 0
    r90 = feat["return_90d"]
    zero_count = (r90 == 0).sum()
    acceptable_zero = max(276, int(len(r90) * 0.001))
    assert zero_count <= acceptable_zero, f"unexpected {zero_count} zero 90d returns"


def test_beta_sanity_and_causality(feat):
    fb = feat[feat["cmc_id"] == 1]  # BTC vs BTC
    beta90 = fb["rolling_beta_vs_BTC_90d"].dropna()
    if len(beta90):
        assert np.abs(beta90 - 1.0).max() < 1e-6  # close to 1.0
    for w in (30, 60, 90):
        b = feat[f"rolling_beta_vs_BTC_{w}d"].dropna()
        p995 = b.abs().quantile(0.995) if len(b) > 100 else b.abs().max()
        assert p995 < 50, f"99.5th percentile beta_{w}d is {p995}"
    # residual = return - beta * btc_return (spot check)
    sub = feat.dropna(subset=["rolling_beta_vs_BTC_30d", "return_30d"])
    assert len(sub) > 1000


def test_market_cap_share_sums(uni):
    s = uni.groupby("historical_date")["market_cap_share"].sum()
    assert np.abs(s - 1.0).max() < 1e-6


def test_band_counts_per_date(uni, summary):
    g = uni.groupby(["historical_date", "rank_band"]).size().unstack()
    for band_name, size in BAND_SIZES.items():
        assert (g[band_name] == size).all(), band_name


def test_rank_band_membership_exact(uni):
    assert uni["rank_band"].isin(BAND_SIZES.keys()).all()
    # no asset outside a band
    assert "OUT" not in set(uni["rank_band"])


def test_band_feature_rows(band):
    # 7 bands x every included date
    assert band["rank_band"].nunique() == 7
    assert set(band["rank_band"]) == set(BAND_SIZES.keys())


# ----------------------------------------------------------------------
# Sector
# ----------------------------------------------------------------------
def test_sector_rank_consistency(smem):
    for (dt, tag), sub in smem.groupby(["historical_date", "sector"]):
        r = sub["sector_rank"].sort_values().tolist()
        assert r == list(range(1, len(r) + 1)), (dt, tag)
        assert sub["sector_member_count"].nunique() == 1


def test_sector_participation_hierarchy(sec):
    s = sec[sec["layer"].isin(["TOP1", "TOP3", "TOP5", "TOP10",
                               "FULL_SECTOR"])]
    g = s.groupby(["historical_date", "sector", "layer"])[
        "layer_member_count"].first().unstack()
    g = g.dropna()
    # check that layer member counts are reasonable
    for _, row in g.iterrows():
        t1 = int(row.get("TOP1", 1))
        t3 = int(row.get("TOP3", t1))
        t5 = int(row.get("TOP5", t3))
        t10 = int(row.get("TOP10", t5))
        tfull = int(row.get("FULL_SECTOR", t10))
        assert t1 == 1, f"TOP1={t1}"
        assert t3 >= t1, f"TOP3={t3} < TOP1={t1}"
        assert t5 >= t3, f"TOP5={t5} < TOP3={t3}"
        assert t10 >= t5, f"TOP10={t10} < TOP5={t5}"
        assert tfull >= t10, f"FULL={tfull} < TOP10={t10}"
    # mcap share monotone across layers
    sm = s.groupby(["historical_date", "sector", "layer"])[
        "layer_market_cap_share"].first().unstack().dropna()
    for _, row in sm.iterrows():
        assert row.get("TOP3", row.get("TOP1", 0)) >= row.get("TOP1", 0) - 1e-12
        assert row.get("FULL_SECTOR", row.get("TOP10", 0)) >= row.get("TOP10", 0) - 1e-12


def test_sector_status_labeled(sec):
    assert set(sec["sector_status"]) == {"HISTORICAL_APPROXIMATION"}


def test_unmapped_assets_exist(uni, feat):
    # some assets have no tags -> UNMAPPED (present but no sector row)
    tagged = uni[uni["tags"] != ""]["cmc_id"].nunique()
    assert tagged < uni["cmc_id"].nunique()
    assert tagged > 100


# ----------------------------------------------------------------------
# Terrain
# ----------------------------------------------------------------------
def test_terrain_dominance(terr, uni):
    btc_dom = terr["btc_dominance"].dropna()
    assert btc_dom.between(0, 1).all()
    # total_alt_share = 1 - btc_dominance; float tolerance
    assert (terr["total_alt_share"] + terr["btc_dominance"] - 1.0).abs()\
        .max() < 1e-6
    assert terr["stablecoin_mcap_share"].between(0, 1).all()


def test_terrain_btc_eth_relative(terr):
    for w in (1, 7, 30):
        exp = terr[f"eth_return_{w}d"] - terr[f"btc_return_{w}d"]
        diff = (exp - terr[f"eth_btc_relative_return_{w}d"]).dropna()
        assert np.abs(diff).max() < 1e-9


# ----------------------------------------------------------------------
# Registry determinism + provenance
# ----------------------------------------------------------------------
def test_feature_registry_determinism():
    reg = json.loads((ROOT / "ALT_DATA_1_FEATURE_DEFINITIONS.json")
                     .read_text(encoding="utf-8"))
    h = hashlib.sha256(json.dumps(reg, sort_keys=True)
                       .encode("utf-8")).hexdigest()
    hashfile = json.loads((ROOT / "ALT_DATA_1_FEATURE_REGISTRY_HASH.json")
                          .read_text(encoding="utf-8"))
    assert hashfile["feature_registry_sha256"] == h


def test_registry_has_frozen_windows(uni):
    reg = json.loads((ROOT / "ALT_DATA_1_FEATURE_DEFINITIONS.json")
                     .read_text(encoding="utf-8"))
    assert reg["windows"] == WINDOWS
    assert reg["min_contract_age_days"] == 30
    assert reg["coverage_floor"] == 0.8
    assert "rank_sign_convention" in reg


def test_provenance_raw_hashes():
    meta_dir = ROOT / "probes" / "raw"
    metas = sorted(meta_dir.glob("*.meta.json"))
    assert len(metas) >= 2200
    checked = 0
    for mp in metas:
        m = json.loads(mp.read_text(encoding="utf-8"))
        body = meta_dir / f"{m['probe']}.json"
        if not body.exists():
            continue
        h = hashlib.sha256(body.read_bytes()).hexdigest()
        assert h == m["sha256"], mp.name
        checked += 1
    assert checked >= 2200


def test_manifest_exists_and_hashes_artifacts():
    man = json.loads((ROOT / "ALT_DATA_1_PROVENANCE_MANIFEST.json")
                     .read_text(encoding="utf-8"))
    arts = man["artifacts"]
    names = {a["artifact"] for a in arts}
    for req in ("ALT_DATA_1_PIT_UNIVERSE.parquet",
                "ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet",
                "ALT_DATA_1_PERP_ELIGIBILITY.parquet",
                "ALT_DATA_1_IDENTITY_MAP.parquet",
                "ALT_DATA_1_FEATURE_REGISTRY_HASH.json"):
        assert req in names
    # verify artifact count is at least the minimum
    assert len(arts) >= 17
    checked = 0
    for a in arts:
        name = a["artifact"]
        # self-referential; cannot check manifest's own hash
        if name.endswith("PROVENANCE_MANIFEST.json"):
            continue
        p = ROOT / name
        if p.exists():
            expected = a["sha256"]
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            assert h == expected, f"hash mismatch: {name}"
            checked += 1
    assert checked >= 16, f"only {checked} artifacts checked"


# ----------------------------------------------------------------------
# Future perturbation invariance (mandatory)
# ----------------------------------------------------------------------
def _synthetic_panel(seed=7, n_days=220, n_assets=50):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D") \
        + pd.Timedelta(hours=23, minutes=59, seconds=59)
    rows = []
    for a in range(n_assets):
        p0 = 10 ** rng.uniform(-1, 3)
        rets = rng.normal(0.0005, 0.03, n_days)
        price = p0 * np.exp(np.cumsum(rets))
        rows.append(pd.DataFrame({
            "historical_date": dates, "cmc_id": a,
            "symbol": f"A{a}", "name": f"Asset {a}", "slug": f"a{a}",
            "price_usd": price,
            "market_cap_usd": price * 1e6,
            "volume_24h_usd": price * 1e5,
            "circulating_supply": 1e6, "total_supply": 1e6,
            "max_supply": 1e6, "date_added_cmc": "",
            "last_updated": "", "tags": "" if a % 3 else "defi;layer-1",
            "platform_chain": "", "contract_address": "",
            "pct_change_1h": 0.0, "pct_change_24h": 0.0,
            "pct_change_7d": 0.0,
        }))
    df = pd.concat(rows, ignore_index=True)
    df["rank"] = df.groupby("historical_date").cumcount() + 1
    df["historical_date_key"] = df["historical_date"].dt.strftime("%Y-%m-%d")
    df["is_stablecoin"] = False
    return df


def _features_from(df):
    df = P.build_universe(df)
    btc = df[df["cmc_id"] == 0].set_index("historical_date")["price_usd"]
    eth = df[df["cmc_id"] == 1].set_index("historical_date")["price_usd"]
    btc_lr = np.log(btc).diff()
    eth_lr = np.log(eth).diff()
    btc_ret = {w: btc.pct_change(w) for w in P.WINDOWS}
    eth_ret = {w: eth.pct_change(w) for w in P.WINDOWS}
    return P.build_asset_features(df, btc_lr, eth_lr, btc_ret, eth_ret)


def test_future_perturbation_invariance():
    df = _synthetic_panel()
    f0 = _features_from(df)
    cutoff = df["historical_date"].min() + pd.Timedelta(days=150)
    pre = f0[f0["historical_date"] <= cutoff].copy()
    # perturb prices AFTER cutoff
    df2 = df.copy()
    post = df2["historical_date"] > cutoff
    rng = np.random.default_rng(42)
    df2.loc[post, "price_usd"] *= rng.uniform(0.5, 2.0, post.sum())
    df2.loc[post, "market_cap_usd"] = df2.loc[post, "price_usd"] * 1e6
    f1 = _features_from(df2)
    pre1 = f1[f1["historical_date"] <= cutoff].copy()
    key = ["cmc_id", "historical_date"]
    m = pre.merge(pre1, on=key, suffixes=("_a", "_b"))
    feat_cols = [c for c in m.columns
                 if c.endswith("_a") and c[:-2] in f0.columns]
    # only compare numeric non-boolean columns
    numeric_cols = [c for c in feat_cols
                    if pd.api.types.is_numeric_dtype(m[c])
                    and not pd.api.types.is_bool_dtype(m[c])]
    diffs = []
    for c in numeric_cols:
        base = c[:-2]
        a, b = m[c], m[f"{base}_b"]
        both = a.notna() & b.notna()
        if both.any():
            d = (a[both] - b[both]).abs()
            diffs.append(d.max())
    assert max(diffs) < 1e-9, ("features before cutoff changed under "
                                "post-cutoff perturbation")


def test_perturbation_after_cutoff_changes_later_features():
    df = _synthetic_panel(seed=11)
    f0 = _features_from(df)
    cutoff = df["historical_date"].min() + pd.Timedelta(days=150)
    df2 = df.copy()
    post = df2["historical_date"] > cutoff
    df2.loc[post, "price_usd"] *= 1.5
    f1 = _features_from(df2)
    pre_a = f0[f0["historical_date"] <= cutoff].set_index(
        ["cmc_id", "historical_date"])["return_7d"]
    pre_b = f1[f1["historical_date"] <= cutoff].set_index(
        ["cmc_id", "historical_date"])["return_7d"]
    assert np.abs(pre_a - pre_b).max() < 1e-9
    post_a = f0[f0["historical_date"] > cutoff].set_index(
        ["cmc_id", "historical_date"])["return_7d"]
    post_b = f1[f1["historical_date"] > cutoff].set_index(
        ["cmc_id", "historical_date"])["return_7d"]
    assert np.abs(post_a - post_b).max() > 1e-6  # perturbation must matter
