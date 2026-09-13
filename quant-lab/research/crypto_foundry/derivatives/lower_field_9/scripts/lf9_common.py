"""LOWER-FIELD-9 shared configuration, loaders and the continuous
relational-state panel builder.

LF9 extends LF8 from event-anchored snapshots to a continuous PIT-safe daily
relational-state panel (carry-forward of the most recent snapshot state per
asset, with explicit coverage/freshness flags), overlays the MECH-15 global
field surface (16-cell exact + 6-cell candidate + 8-cell reference), and asks
how physical disturbance reorganizes local network structure as a function of
global field state.

SAMPLING DESIGN (PIT-safe, frozen substrate):
The LF5 peer maps are event-anchored. LF9 does NOT re-derive daily
behavioral/correlation peer maps (out of scope, would reinvent LF5). Instead
the relational-state object is carried forward: on each asset-day, the asset's
state is the state assigned at its most recent snapshot (<= that day). Days
before the first snapshot are NO_COVERAGE and never forced. Every row carries
days_since_snapshot + freshness so stale carry days can be conditioned on.

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_8" / "scripts"))
import lf8_common as C  # noqa: E402
import lf8_analyze as A  # noqa: E402  (reuse _purged_auc, _future_lookup, _abs_class, ...)

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent          # lower_field_9/
LF8 = ROOT.parent / "lower_field_8"
M15 = ROOT.parent.parent / "alt_rotation" / "mech_15"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

PRIMARY = C.PRIMARY_FAMILY          # HYBRID_10
FAMILY_ORDER = C.DEEP_FAMILIES
STATE_ORDER = C.STATE_ORDER_EXT
DEPTH_BANDS = C.DEPTH_BANDS
MIN_SUPPORT = C.MIN_SUPPORT

WINDOWS = [1, 3, 7, 14, 30, 60]

ABS_CLASSES = [("<2%", 0.0, 0.02), ("2-5%", 0.02, 0.05), ("5-10%", 0.05, 0.10),
               ("10-20%", 0.10, 0.20), ("20%+", 0.20, np.inf)]
SIGMA_CLASSES = [("<2σ", 0.0, 2.0), ("2-3σ", 2.0, 3.0), ("3-4σ", 3.0, 4.0),
                 ("4σ+", 4.0, np.inf)]

RANK_DEPTH = {"SHALLOW": ["26-100", "101-250"],
              "MID": ["251-500", "501-750"],
              "DEEP": ["751-1000", "1001-1500", "1501-2000"]}

# ---------------------------------------------------------------------------
# MECH-15 global field surfaces
# ---------------------------------------------------------------------------
# Deterministic partitions from mech_15/06_COLLAPSE_MERGE_TREE.csv
# (average-linkage dendrogram on 16 cells; cut levels 8 and 6).

M8_MAP = {
    "HH_HA_LE": "M8_A", "HH_LA_LE": "M8_A",
    "HL_LA_HE": "M8_B", "HL_LA_LE": "M8_B",
    "HH_HA_HE": "M8_C", "HH_LA_HE": "M8_C",
    "LL_HA_HE": "M8_D", "LL_LA_HE": "M8_D",
    "LH_HA_HE": "M8_E", "LH_HA_LE": "M8_E", "LH_LA_HE": "M8_E",
    "LL_HA_LE": "M8_F", "LL_LA_LE": "M8_F",
    "HL_HA_HE": "M8_G", "HL_HA_LE": "M8_G",
    "LH_LA_LE": "M8_H",
}
M6_MAP = {
    "HH_HA_LE": "M6_A", "HH_LA_LE": "M6_A",
    "HH_HA_HE": "M6_B", "HH_LA_HE": "M6_B",
    "LL_HA_LE": "M6_C", "LL_LA_LE": "M6_C",
    "HL_HA_HE": "M6_D", "HL_HA_LE": "M6_D",
    "HL_LA_HE": "M6_E", "HL_LA_LE": "M6_E",
    "LL_HA_HE": "M6_E", "LL_LA_HE": "M6_E",
    "LH_HA_HE": "M6_F", "LH_HA_LE": "M6_F",
    "LH_LA_HE": "M6_F", "LH_LA_LE": "M6_F",
}

MCELL_FILE = CACHE / "mcell15_daily.parquet"


def load_mcell_frame() -> pd.DataFrame:
    """Per-day MECH-15 16-cell frame (exact construction, reproduced from the
    cached daily field frame; 16-cell mcell + constraint axes + forcing)."""
    p = CACHE / "mcell15_daily.parquet"
    if not p.exists():
        sys.path.insert(0, str(M15 / "scripts"))
        import pickle
        from _m15base import build_matrix_frame
        with open(M15 / "_cache_dfw15.pkl", "rb") as fh:
            dfw = pickle.load(fh)
        with open(M15 / "_cache_band15.pkl", "rb") as fh:
            band = pickle.load(fh)
        df = build_matrix_frame(dfw, band)
        keep = ["historical_date", "d", "cell", "state", "subperiod", "age_in_cell",
                "spatial_activation", "ent_resid", "spatial_ax", "temporal_ax",
                "constraint", "mcell", "forcing", "rank_depth_rel", "archetype"]
        df[keep].to_parquet(p, index=False)
    return pd.read_parquet(p)


def _mcell_partitions():
    mc = load_mcell_frame()
    mc["mcell6"] = mc["mcell"].map(M6_MAP)
    mc["mcell8"] = mc["mcell"].map(M8_MAP)
    mc["cell4"] = mc["mcell"].str[:2]
    mc["d"] = pd.to_datetime(mc["d"]).dt.normalize()
    return mc


# ---------------------------------------------------------------------------
# Continuous relational-state panel (primary family)
# ---------------------------------------------------------------------------

CARRY_COLS = [
    "rel_state", "membership_class", "roll_turnover_30d", "entropy_30d",
    "peer_std_ret", "peer_abs_med", "peer_count", "is_true_loner",
    "is_false_loner", "final_class", "state_age_d", "state_changed",
    "event_index", "days_since_prev", "prev_res_z", "res_z",
    "out_rejoin", "out_contagion", "out_decouple", "out_relapse",
    "out_price_repair", "out_rank_repair", "st4_7", "st4_30",
    "price_up_30", "rank_up_30", "recover1s30", "z1", "event_sign",
    "abs_ret_snap", "peer_corr",
]

SUB_COLS = [
    "cmc_id", "historical_date", "ret_1d", "sigma_t0", "vol_30d", "rank",
    "rank_band", "rank_vel_7d", "liq_proxy", "mcap_q_within_date",
    "top500_breadth_30d", "top500_dispersion_30d", "field_cell", "turnover",
    "volume_24h_usd", "vol_prev7_med", "log10_mcap",
    "flag_any_quality", "flag_stale_price", "flag_zero_volume",
]


def _panel_snaps():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    s = snap.copy()
    s["abs_ret_snap"] = s["abs_ret"]
    return s


def build_continuous_panel(use_cache: bool = True) -> pd.DataFrame:
    """Per asset-day panel: carried relational state + membership metrics +
    regime outcome flags, joined to daily substrate features + MECH-15 cells."""
    cache_p = CACHE / "lf9_continuous_panel.parquet"
    if use_cache and cache_p.exists():
        return pd.read_parquet(cache_p)

    snap = _panel_snaps()
    assets = snap["cmc_id"].unique()
    sub = pd.read_parquet(C.SUBSTRATE, columns=SUB_COLS)
    sub = sub[sub["cmc_id"].isin(assets)]
    sub = sub.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sub["abs_ret"] = sub["ret_1d"].abs()
    sub["sigma"] = sub["sigma_t0"].clip(lower=0.0)
    sub["vol_amp"] = np.log1p(sub["volume_24h_usd"] / sub["vol_prev7_med"].replace(0, np.nan))

    left = sub[["cmc_id", "historical_date", "abs_ret", "sigma", "vol_30d", "rank",
                "rank_band", "rank_vel_7d", "liq_proxy", "mcap_q_within_date",
                "top500_breadth_30d", "top500_dispersion_30d", "field_cell",
                "turnover", "volume_24h_usd", "vol_amp", "log10_mcap",
                "flag_any_quality", "flag_stale_price", "flag_zero_volume"]].copy()

    carry = snap[["cmc_id", "historical_date"] + CARRY_COLS].rename(
        columns={"historical_date": "snapshot_date"})
    p = pd.merge_asof(left.sort_values("historical_date"),
                      carry.sort_values("snapshot_date"),
                      left_on="historical_date", right_on="snapshot_date",
                      by="cmc_id", direction="backward")
    p["has_snapshot"] = (p["snapshot_date"] == p["historical_date"]).astype(int)
    p["days_since_snapshot"] = (p["historical_date"] - p["snapshot_date"]).dt.days
    p.loc[p["snapshot_date"].isna(), "days_since_snapshot"] = np.nan
    p["coverage"] = np.where(p["rel_state"].isna(), "NO_COVERAGE", "COVERED")
    p["freshness"] = np.select(
        [p["days_since_snapshot"] <= 7, p["days_since_snapshot"] <= 30,
         p["days_since_snapshot"] <= 60],
        ["FRESH_0_7", "STALE_8_30", "STALE_31_60"], default="STALE_60_PLUS")
    p.loc[p["coverage"] == "NO_COVERAGE", "freshness"] = np.nan

    # continuous state-change: only observable on snapshot days (carry is flat)
    prev_state = p.groupby("cmc_id")["rel_state"].shift(1)
    p["state_changed_daily"] = (
        (p["rel_state"] != prev_state) & p["rel_state"].notna()
        & prev_state.notna() & (p["has_snapshot"] == 1)).astype(int)

    # MECH-15 field surface join (by date)
    mc = _mcell_partitions()
    j = mc[["d", "mcell", "mcell6", "mcell8", "cell4", "spatial_activation",
            "ent_resid", "constraint", "forcing", "subperiod", "age_in_cell"]].copy()
    j["d"] = pd.to_datetime(j["d"]).dt.normalize()
    p["d"] = pd.to_datetime(p["historical_date"]).dt.normalize()
    p = p.merge(j, on="d", how="left").drop(columns=["d"])

    # carried-state day count from panel start (per asset)
    first = snap.groupby("cmc_id")["historical_date"].min()
    p = p.merge(first.rename("first_snapshot_date"), on="cmc_id", how="left")
    p["days_since_first_snapshot"] = (p["historical_date"] - p["first_snapshot_date"]).dt.days

    p.to_parquet(cache_p, index=False)
    return p


def _sigma_class_full(x):
    """Full-range sigma class incl. the <2 band (LF8's classifier fell through
    to 4+ for anything under 2, fine on event panels, wrong on continuous)."""
    for name, lo, hi in SIGMA_CLASSES:
        if lo <= x < hi:
            return name
    return "4σ+"


def continuous_sig_abs(df):
    df = df.copy()
    df["abs_class"] = df["abs_ret"].map(A._abs_class)
    df["sigma_class"] = df["sigma"].map(_sigma_class_full)
    return df


def _rank_depth_band(x):
    for name, bands in RANK_DEPTH.items():
        if x in bands:
            return name
    return "OUT_OF_SCOPE"


def add_rank_depth(df):
    df = df.copy()
    df["rank_depth"] = df["rank_band"].map(_rank_depth_band)
    return df


def _med(s):
    s = pd.Series(s).dropna()
    return float(s.median()) if len(s) else np.nan


def _mean(s):
    s = pd.Series(s).dropna()
    return float(s.mean()) if len(s) else np.nan
