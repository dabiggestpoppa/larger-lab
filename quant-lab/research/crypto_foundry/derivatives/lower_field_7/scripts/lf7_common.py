"""LOWER-FIELD-7 shared configuration and loaders.

LF7 moves from "who are the peers?" to "how do local peer neighborhoods form,
dissolve, respond and transmit shock?", and expands loner anatomy beyond the
downside-only body to full up/down, true/false, rejoin/contagion/decoupling,
built on the LF5 PIT substrate + five true peer families (which already cover
both sign directions). Added here: the sign-symmetric loner universes that
LF6 filtered to downside only.

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

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent
LF5 = ROOT.parent / "lower_field_5"
LF6 = ROOT.parent / "lower_field_6"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

EVENTS = LF5 / "cache" / "lf5_events.parquet"
SUBSTRATE = LF5 / "04_PIT_ASSET_DATE_FEATURES.parquet"
PEER_FILES = {
    "RANK": LF5 / "07_RANK_PEERS.parquet",
    "BEHAVIORAL": LF5 / "08_BEHAVIORAL_PEERS.parquet",
    "CORR": LF5 / "09_CORRELATION_PEERS.parquet",
    "STATE": LF5 / "10_STATE_PEERS.parquet",
    "HYBRID": LF5 / "11_HYBRID_LOCAL_BASKETS.parquet",
}
LF5_QUALITY = LF5 / "06_PEER_MAP_QUALITY.csv"
LF6_CLS = LF6 / "03_CONSENSUS_LONER_CLASSIFICATION.csv"
LF6_PATH = LF6 / "10_PEER_REJOIN_CATCHDOWN.csv"

EVENT_BANDS = C5.PRIMARY_BANDS + C5.COMPARE_BANDS
PRIMARY_BANDS = C5.PRIMARY_BANDS
COMPARE_BANDS = C5.COMPARE_BANDS

# Peer families used for true-peer analysis (same as LF6).
DEEP_FAMILIES = ["BEHAVIORAL_10", "CORR_60_10", "CORR_120_10", "STATE", "HYBRID_10"]
# The five peer "families" tracked for reclassification / dependence.
FAMILY_GROUPS = ["BEHAVIORAL", "CORR_60", "CORR_120", "STATE", "HYBRID"]

H = [1, 2, 3, 5, 7, 10, 14, 21, 30]
MIN_EVENTS = 50

# Rank depth buckets for map / patch analysis.
DEPTH_BANDS = ["26-100", "101-250", "251-500", "501-750", "751-1000",
               "1001-1500", "1501-2000"]


def age_band(age):
    for lo, hi, name in [(1, 1, "AGE_1"), (2, 3, "AGE_2_3"), (4, 7, "AGE_4_7"),
                         (8, 14, "AGE_8_14"), (15, 10 ** 9, "AGE_15_PLUS")]:
        if lo <= age <= hi:
            return name
    return "AGE_15_PLUS"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_events() -> pd.DataFrame:
    ev = pd.read_parquet(EVENTS)
    ev["historical_date"] = pd.to_datetime(ev["historical_date"])
    ev["event_index"] = ev.index
    return ev


def loner_universe(ev: pd.DataFrame, sign: int, amp="2s", bands=None) -> pd.DataFrame:
    """Isolated extreme events of a given sign in the peer EVENT_BANDS.

    sign>0 = upside, sign<0 = downside. amp '2s' or '3s'. Sign-symmetric
    PIT-safe construction mirrors LF5/LF6.
    """
    b = bands if bands is not None else EVENT_BANDS
    if sign > 0:
        mask = (ev["participation"] == "ISOLATED") & (ev["event_sign"] > 0) \
            & (ev["rank_band"].isin(b))
        if amp == "3s":
            mask = mask & (ev["z1"] >= 3)
    else:
        mask = (ev["participation"] == "ISOLATED") & (ev["event_sign"] < 0) \
            & (ev["rank_band"].isin(b))
        if amp == "3s":
            mask = mask & (ev["z1"] >= 3)
    return ev[mask].copy()


def load_substrate_slim() -> pd.DataFrame:
    cols = ["cmc_id", "historical_date", "ret_1d", "log10_mcap", "log10_vol",
            "turnover", "listing_age_days", "vol_63d", "vol_30d", "vol_20d",
            "rank_vel_7d", "rank_vel_30d", "field_cell", "market_cap_usd",
            "volume_24h_usd"] + [f"fwd{h}_cum" for h in C5.H]
    avail = list(pd.read_parquet(SUBSTRATE, columns=None).columns)
    cols = [c for c in cols if c in avail]
    df = pd.read_parquet(SUBSTRATE, columns=cols)
    df["historical_date"] = pd.to_datetime(df["historical_date"])
    return df


def load_market_state() -> pd.DataFrame:
    """Daily field context used for peer formation / driver conditioning."""
    cols = ["historical_date", "btc_ret_1d", "btc_return_30d", "top500_breadth_30d",
            "top500_dispersion_30d", "stablecoin_mcap_share", "field_cell"]
    ev = pd.read_parquet(EVENTS)
    ev["historical_date"] = pd.to_datetime(ev["historical_date"])
    sub = ev[cols].drop_duplicates("historical_date").copy()
    sub["cell4"] = sub["field_cell"].map(
        {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
         "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"})
    return sub


def load_peer_map(family: str) -> pd.DataFrame:
    """Peer map rows for one exact family string (e.g. BEHAVIORAL_10)."""
    prefix = family.split("_")[0]
    f = PEER_FILES[prefix]
    pm = pd.read_parquet(f)
    pm = pm[pm["peer_family"] == family]
    return pm.reset_index(drop=True)


def load_event_index_meta(ev):
    """Minimal per-event identity + outcome columns for merges."""
    cols = ["event_index", "historical_date", "cmc_id", "rank_band", "ret_1d",
            "z1", "sigma_t0", "amp_level", "subperiod", "event_sign"]
    return ev[cols]


def load_age_in_cell() -> pd.DataFrame:
    cache = CACHE / "age_in_cell.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = pd.read_parquet(SUBSTRATE, columns=["cmc_id", "historical_date", "field_cell"])
    df["historical_date"] = pd.to_datetime(df["historical_date"])
    df = df.sort_values(["cmc_id", "historical_date"], kind="stable")
    prev = df.groupby("cmc_id")["field_cell"].shift()
    new_run = (df["field_cell"] != prev) | prev.isna()
    run_id = new_run.groupby(df["cmc_id"]).cumsum()
    df["age_in_cell"] = df.groupby(["cmc_id", run_id]).cumcount() + 1
    out = df[["cmc_id", "historical_date", "age_in_cell"]]
    out.to_parquet(cache, index=False)
    return out