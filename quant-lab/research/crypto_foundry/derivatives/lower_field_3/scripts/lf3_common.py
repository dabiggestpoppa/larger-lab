"""Shared LF3 paths and causal event helpers."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LF2 = ROOT.parent / "lower_field_2"
RESULTS = ROOT / "RESULTS"
RESULTS.mkdir(exist_ok=True)
LF2_CACHE = LF2 / "RESULTS" / "lf2_feature_frame.parquet"
LF2_PANEL = LF2.parent / "lower_field" / "RESULTS" / "lower_field_panel.parquet"
PRIMARY_BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]
COMPARE_BANDS = ["26-100", "101-250", "251-500"]
H = [1, 2, 3, 5, 7, 10, 14, 21, 30]
FWD = {h: f"fwd{h}_cum" for h in H}


def load_panel() -> pd.DataFrame:
    """Load LF2 cache, falling back to its panel only if cache absent.

    The cache includes continuous forward returns and sigma. The fallback is
    intentionally conservative: it raises, rather than silently rebuilding a
    large feature frame with an alternate algorithm.
    """
    if LF2_CACHE.exists():
        return pd.read_parquet(LF2_CACHE)
    raise FileNotFoundError(
        f"LF2 feature cache missing: {LF2_CACHE}. Run lower_field_2/scripts/lf2_load.py first."
    )


def z1(df):
    return df["ret_1d"].abs() / df["sigma_t0"]


def sign_reverse(fwd, event_sign):
    return (np.sign(fwd) != event_sign) & fwd.notna() & (event_sign != 0)


def signed_forward(df, h):
    return np.sign(df["ret_1d"].to_numpy(float)) * df[FWD[h]].to_numpy(float)


def add_basic_event_features(df: pd.DataFrame) -> pd.DataFrame:
    # Mutate the loaded feature frame in place to avoid duplicating a ~700MB
    # parquet in memory. Callers do not reuse an unmodified copy.
    d = df
    d["z1"] = z1(d)
    d["event_sign"] = np.sign(d["ret_1d"].to_numpy(float))
    d["event_sign_label"] = np.where(d["event_sign"] > 0, "UP", "DOWN")
    d["is_2s"] = d["z1"] >= 2
    d["is_3s"] = d["z1"] >= 3
    d["is_4s"] = d["z1"] >= 4
    d["raw10"] = d["ret_1d"].abs() >= .10
    d["raw15"] = d["ret_1d"].abs() >= .15
    d["raw20"] = d["ret_1d"].abs() >= .20
    return d


def rank_window_context(df: pd.DataFrame, width: int = 50) -> pd.DataFrame:
    """Same-date rank neighborhood summary, with no future values."""
    # This explicit implementation is used on event dates only; it does not
    # fill missing neighbors and preserves PIT rank.
    d = df.sort_values(["historical_date", "rank"]).copy()
    out = []
    for date, g in d.groupby("historical_date", sort=False):
        ranks = g["rank"].to_numpy(float)
        ret = g["ret_1d"].to_numpy(float)
        z = g["z1"].to_numpy(float)
        for idx, r in zip(g.index, ranks):
            m = (np.abs(ranks - r) <= width) & (ranks != r)
            rr = ret[m]
            zz = z[m]
            rr = rr[np.isfinite(rr)]
            zz = zz[np.isfinite(zz)]
            row = {
                "_idx": idx,
                f"rank{width}_n": int(len(rr)),
                f"rank{width}_median_ret": float(np.median(rr)) if len(rr) else np.nan,
                f"rank{width}_p10_ret": float(np.quantile(rr, .10)) if len(rr) else np.nan,
                f"rank{width}_p90_ret": float(np.quantile(rr, .90)) if len(rr) else np.nan,
                f"rank{width}_same_sign": float((np.sign(rr) == np.sign(ret[g.index.get_loc(idx)])).mean()) if len(rr) else np.nan,
                f"rank{width}_tail_share": float((zz >= 2).mean()) if len(zz) else np.nan,
            }
            out.append(row)
    return pd.DataFrame(out).set_index("_idx")


def fdr_bh(p):
    p = np.asarray(p, float)
    out = np.zeros(len(p), dtype=bool)
    good = np.isfinite(p)
    ix = np.where(good)[0]
    if not len(ix):
        return out
    order = ix[np.argsort(p[ix], kind="stable")]
    q = p[order] * len(order) / np.arange(1, len(order) + 1)
    ok = q <= .05
    if ok.any():
        out[order[: np.max(np.where(ok)[0]) + 1]] = True
    return out


def periods(dates):
    return pd.to_datetime(dates).dt.to_period("Q").astype(str)
