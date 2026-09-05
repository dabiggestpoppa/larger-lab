"""LOWER-FIELD-6 shared configuration and loaders.

Built on top of the LF5 PIT substrate, event cache and the five true peer
families. All peer definitions are outcome-free and PIT-safe (same-date /
t-1 windows); LF6 deepens validation, classifies loners by consensus, and
maps recovery ladders, peer rejoin/catchdown geometry and rank-patch
structure. Research only: no strategy, no PnL, no execution.
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
MECH8 = C5.MECH8
MECH10 = ROOT.parent.parent / "alt_rotation" / "mech_10"
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
LF5_PRICE_RANK = LF5 / "22_PRICE_RANK_HEALTH_MATRIX.csv"
MECH8_HEALTH = MECH8 / "13b_PRICE_RANK_HEALTH_EVENTS.parquet"
MECH10_PRD = MECH10 / "08_PRICE_UP_RANK_DOWN_FIELD_MATRIX.csv"

EVENT_BANDS = C5.PRIMARY_BANDS + C5.COMPARE_BANDS
PRIMARY_BANDS = C5.PRIMARY_BANDS
COMPARE_BANDS = C5.COMPARE_BANDS

# Peer families used for the deep validation / consensus classification.
DEEP_FAMILIES = ["BEHAVIORAL_10", "CORR_60_10", "CORR_120_10", "STATE", "HYBRID_10"]

H = [1, 2, 3, 5, 7, 10, 14, 21, 30]
MIN_EVENTS = 50

# Age bands (MECH-8/10 convention).
AGE_BANDS = [(1, 1, "AGE_1"), (2, 3, "AGE_2_3"), (4, 7, "AGE_4_7"),
             (8, 14, "AGE_8_14"), (15, 10 ** 9, "AGE_15_PLUS")]


def age_band(age):
    for lo, hi, name in AGE_BANDS:
        if lo <= age <= hi:
            return name
    return "AGE_15_PLUS"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_events() -> pd.DataFrame:
    """Full LF5 event table with index preserved as event_index."""
    ev = pd.read_parquet(EVENTS)
    ev["historical_date"] = pd.to_datetime(ev["historical_date"])
    ev["event_index"] = ev.index
    return ev


def loner_universe(ev: pd.DataFrame, amp="2s") -> pd.DataFrame:
    """Isolated downside events in the peer-map EVENT_BANDS (26-2000)."""
    mask = (ev["participation"] == "ISOLATED") & (ev["event_sign"] < 0) \
        & (ev["rank_band"].isin(EVENT_BANDS))
    if amp == "3s":
        mask = mask & (ev["z1"] >= 3)
    return ev[mask].copy()


def load_substrate_slim() -> pd.DataFrame:
    """Substrate rows needed for peer forward returns."""
    cols = ["cmc_id", "historical_date", "ret_1d"] + [f"fwd{h}_cum" for h in H]
    df = pd.read_parquet(SUBSTRATE, columns=cols)
    df["historical_date"] = pd.to_datetime(df["historical_date"])
    return df


def load_peer_map(family: str) -> pd.DataFrame:
    """Peer map rows for one exact family string (e.g. BEHAVIORAL_10)."""
    prefix = family.split("_")[0]
    f = PEER_FILES[prefix]
    pm = pd.read_parquet(f)
    pm = pm[pm["peer_family"] == family]
    return pm.reset_index(drop=True)


def load_age_in_cell() -> pd.DataFrame:
    """Consecutive-day run length of the same field cell per asset."""
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


def merge_age(ev: pd.DataFrame) -> pd.DataFrame:
    age = load_age_in_cell()
    ev = ev.merge(age, on=["cmc_id", "historical_date"], how="left")
    ev["age_band"] = ev["age_in_cell"].map(age_band)
    return ev
