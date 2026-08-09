"""
Phase 3 - Canonical Common Market Panel builder.

Consumes only accepted Phase 2 normalized datasets (per the Phase 2 audit
CR-P2-MARKET-CALENDAR-AUDIT-06) and constructs a timestamp-indexed,
calendar-aware, cross-market H1/H4/D1 panel with masks, transforms and QC.

This module NEVER forward-fills OHLC. Missing observations stay missing.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..quality.fx_trading_calendar import (
    SessionGroup,
    get_session_schedule,
    generate_expected_timestamps,
)


# The accepted Phase 2 universe (Batch A, 10 FX pairs).
PHASE2_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURGBP",
    "EURJPY", "GBPJPY", "CHFJPY", "EURCHF", "GBPCHF",
]

# Asset class classification (all FX for the accepted universe).
ASSET_CLASS = {sym: "fx" for sym in PHASE2_SYMBOLS}

# Canonical quote orientation. A positive return means base-curve strength.
# base_quote : positive => base strong / quote weak
CURRENCY_ORIENTATION = {
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
    "USDCHF": ("USD", "CHF"),
    "EURGBP": ("EUR", "GBP"),
    "EURJPY": ("EUR", "JPY"),
    "GBPJPY": ("GBP", "JPY"),
    "CHFJPY": ("CHF", "JPY"),
    "EURCHF": ("EUR", "CHF"),
    "GBPCHF": ("GBP", "CHF"),
}

# Cross-rate identities to validate synchronization:
# target ≈ product/pair of two other members of the panel.
CROSS_RATE_IDENTITIES = [
    # (output, numerator, denominator) => output ≈ numerator / denominator
    ("EURGBP", "EURUSD", "GBPUSD"),
    ("GBPCHF", "GBPUSD", "USDCHF"),
    ("EURCHF", "EURUSD", "USDCHF"),
    ("EURJPY", "EURUSD", "USDJPY"),
    ("GBPJPY", "GBPUSD", "USDJPY"),
    ("CHFJPY", "USDCHF", "USDJPY"),
]


@dataclass
class PanelInput:
    """Metadata for one accepted Phase 2 dataset used as Phase 3 input."""
    symbol: str
    asset_class: str
    provider: str
    timeframe: str
    start: str
    end: str
    timezone: str
    row_count: int
    sha256: str
    phase2_qc_status: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_input_manifest(
    normalized_h1_dir: Path,
    symbols: Optional[List[str]] = None,
) -> Dict:
    """
    Build the Phase 3 input manifest from accepted normalized H1 parquet files.

    Only files matching the accepted Phase 2 universe are consumed.
    """
    symbols = symbols or PHASE2_SYMBOLS
    records = []
    for sym in symbols:
        path = normalized_h1_dir / f"{sym}_H1.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing accepted Phase 2 dataset: {path}")
        df = pd.read_parquet(path, columns=["timestamp_utc"])
        ts = pd.to_datetime(df["timestamp_utc"], utc=True)
        records.append(PanelInput(
            symbol=sym,
            asset_class=ASSET_CLASS.get(sym, "fx"),
            provider="mt5_pro",
            timeframe="H1",
            start=str(ts.min()),
            end=str(ts.max()),
            timezone="UTC",
            row_count=int(len(df)),
            sha256=sha256_file(path),
            phase2_qc_status="accepted",
        ))
    return {
        "phase": "3",
        "gate_source": "CR-P2-MARKET-CALENDAR-AUDIT-06",
        "rule": "Phase 3 consumes accepted normalized Phase 2 outputs only",
        "symbols": symbols,
        "inputs": [asdict(r) for r in records],
    }


def load_accepted_h1(symbol: str, normalized_h1_dir: Path) -> pd.DataFrame:
    """Load one accepted normalized H1 parquet and normalize timestamp to UTC index."""
    path = normalized_h1_dir / f"{symbol}_H1.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing accepted Phase 2 dataset: {path}")
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["timestamp_utc"], utc=True)
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("UTC")
    else:
        ts = ts.dt.tz_convert("UTC")
    df = df.copy()
    df["timestamp_utc"] = ts
    df = df.drop_duplicates(subset=["timestamp_utc"], keep="first")
    df = df.sort_values("timestamp_utc").set_index("timestamp_utc")
    return df


def build_h1_master_panel(
    normalized_h1_dir: Path,
    symbols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Build the union timestamp master H1 panel.

    Returns:
        - master_panel: timestamp-indexed wide DataFrame, columns like
          EURUSD_open, EURUSD_high, ... (one OHLC block per symbol).
        - per_symbol_frames: {symbol: source H1 DataFrame}
    """
    symbols = symbols or PHASE2_SYMBOLS
    per_symbol = {}
    for sym in symbols:
        per_symbol[sym] = load_accepted_h1(sym, normalized_h1_dir)

    # Union of all timestamps
    all_ts = set()
    for sym, df in per_symbol.items():
        all_ts.update(df.index)
    master_index = pd.DatetimeIndex(sorted(all_ts), tz="UTC")

    panel = pd.DataFrame(index=master_index)
    for sym in symbols:
        df = per_symbol[sym]
        # Reindex to master index (missing stay NaN - NO forward fill)
        aligned = df.reindex(master_index)
        for ohlc in ["open", "high", "low", "close"]:
            panel[f"{sym}_{ohlc}"] = aligned[ohlc].values
    return panel, per_symbol


def build_availability_masks(master_panel, symbols=None) -> pd.DataFrame:
    """Boolean availability: timestamp has a valid(H1) observation for the symbol."""
    symbols = symbols or PHASE2_SYMBOLS
    mask = pd.DataFrame(index=master_panel.index)
    for sym in symbols:
        mask[sym] = master_panel[f"{sym}_close"].notna().values
    return mask


def build_market_open_masks(master_panel, symbols=None) -> pd.DataFrame:
    """
    Boolean market-open per symbol from the Phase 2 empirical calendar.

    True where the market is EXPECTED to be open (per session group),
    regardless of whether data exists. Used to distinguish legitimate
    closure from unexpected missingness.
    """
    symbols = symbols or PHASE2_SYMBOLS
    mask = pd.DataFrame(index=master_panel.index)
    for sym in symbols:
        schedule = get_session_schedule(sym)
        expected = generate_expected_timestamps(
            sym, master_panel.index.min(), master_panel.index.max()
        )
        expected_set = set(expected)
        mask[sym] = [ts in expected_set for ts in master_panel.index]
    return mask


def missingness_mask(availability, market_open) -> pd.DataFrame:
    """
    Unexpected missing = market was open but the observation is absent.
    Values: 'present', 'closed', 'unexpected_missing'
    """
    out = pd.DataFrame(index=availability.index)
    for sym in availability.columns:
        out[sym] = np.where(
            availability[sym].values,
            "present",
            np.where(market_open[sym].values, "unexpected_missing", "closed"),
        )
    return out


def build_h4_panel(master_h1_panel, symbols=None, label="H4") -> pd.DataFrame:
    """
    Derive H4 from canonical H1 using fixed UTC 4-hour boundaries.
    Bind each H1 to its H4 bucket, aggregate OHLC, count constituents.
    Incomplete H4 buckets (fewer than expected constituents) are flagged.
    """
    symbols = symbols or PHASE2_SYMBOLS
    # 4-hour buckets aligned to UTC multiples of 4h (00,04,08,12,16,20)
    idx = master_h1_panel.index
    bucket = pd.Timestamp.ceil(idx, "4h") if False else idx.floor("4h")
    bucket = idx.floor("4h")
    rows = {"timestamp": [], "constituents": []}
    # We'll gather per-symbol H4 frames then concat
    h4_frames = {}
    for sym in symbols:
        cols = [f"{sym}_open", f"{sym}_high", f"{sym}_low", f"{sym}_close"]
        sub = master_h1_panel[cols].copy()
        sub["bucket"] = bucket
        obs = sub.dropna(subset=[f"{sym}_close"])
        if obs.empty:
            h4_frames[sym] = pd.DataFrame(columns=[f"{sym}_open", f"{sym}_high", f"{sym}_low", f"{sym}_close", f"{sym}_h1_count", f"{sym}_incomplete"])
            continue
        g = obs.groupby("bucket")
        open_ = g[f"{sym}_open"].first()
        high = g[f"{sym}_high"].max()
        low = g[f"{sym}_low"].min()
        close = g[f"{sym}_close"].last()
        count = g.size()
        h4 = pd.DataFrame({
            f"{sym}_open": open_,
            f"{sym}_high": high,
            f"{sym}_low": low,
            f"{sym}_close": close,
            f"{sym}_h1_count": count,
        })
        # Flag incomplete: for FX expected ~4 H1 per H4 bucket when open.
        h4[f"{sym}_incomplete"] = h4[f"{sym}_h1_count"] < 4
        h4_frames[sym] = h4

    # Union index
    all_idx = set()
    for f in h4_frames.values():
        all_idx.update(f.index)
    h4_index = pd.DatetimeIndex(sorted(all_idx), tz="UTC")
    panel = pd.DataFrame(index=h4_index)
    for sym, f in h4_frames.items():
        f_aligned = f.reindex(h4_index)
        for c in f.columns:
            panel[c] = f_aligned[c].values
    return panel


def build_d1_panel(master_h1_panel, symbols=None, boundary_hour: int = 0) -> pd.DataFrame:
    """
    Derive canonical D1 from normalized H1.
    Daily boundary is defined as UTC midnight (hour boundary_hour).
    Documented in report. No broker daily candles used.
    """
    symbols = symbols or PHASE2_SYMBOLS
    idx = master_h1_panel.index
    # Daily bucket anchored at boundary_hour UTC
    day = idx.floor("D") + pd.Timedelta(hours=boundary_hour)
    # For timestamps before boundary, they belong to previous day bucket.
    # floor('D') keeps calendar day; we shift so hours < boundary map to prior day.
    day = day.where(idx.hour >= boundary_hour, day - pd.Timedelta(days=1))

    d1_frames = {}
    for sym in symbols:
        cols = [f"{sym}_open", f"{sym}_high", f"{sym}_low", f"{sym}_close"]
        sub = master_h1_panel[cols].copy()
        sub["day"] = day
        obs = sub.dropna(subset=[f"{sym}_close"])
        if obs.empty:
            d1_frames[sym] = pd.DataFrame(columns=[f"{sym}_open", f"{sym}_high", f"{sym}_low", f"{sym}_close", f"{sym}_h1_count", f"{sym}_coverage_ratio", f"{sym}_open_hours"])
            continue
        g = obs.groupby("day")
        open_ = g[f"{sym}_open"].first()
        high = g[f"{sym}_high"].max()
        low = g[f"{sym}_low"].min()
        close = g[f"{sym}_close"].last()
        count = g.size()
        d1 = pd.DataFrame({
            f"{sym}_open": open_,
            f"{sym}_high": high,
            f"{sym}_low": low,
            f"{sym}_close": close,
            f"{sym}_h1_count": count,
        })
        # coverage ratio = observed H1 / (expected open H1 for that day)
        schedule = get_session_schedule(sym)
        ratios = {}
        open_hours = {}
        for ts in count.index:
            exp = len(generate_expected_timestamps(sym, ts, ts + pd.Timedelta(hours=23, minutes=59)))
            ratios[ts] = (count[ts] / exp) if exp > 0 else 0.0
            expected_for_day = schedule.get_expected_hours_in_range(
                ts, ts + pd.Timedelta(hours=23, minutes=59))
            open_hours[ts] = expected_for_day
        d1[f"{sym}_coverage_ratio"] = pd.Series(ratios)
        d1[f"{sym}_open_hours"] = pd.Series(open_hours)
        d1_frames[sym] = d1

    all_idx = set()
    for f in d1_frames.values():
        all_idx.update(f.index)
    d1_index = pd.DatetimeIndex(sorted(all_idx), tz="UTC")
    panel = pd.DataFrame(index=d1_index)
    for sym, f in d1_frames.items():
        f_aligned = f.reindex(d1_index)
        for c in f.columns:
            panel[c] = f_aligned[c].values
    return panel


def build_price_transforms(h1_close, risk_free: float = 0.0) -> pd.DataFrame:
    """
    Build returns/range/volatility columns from a close-only DataFrame.

    Input: timestamp x symbol DataFrame of raw close prices.
    Output: transforms share index with input. Raw close untouched.
    """
    t = h1_close.copy()
    simple = t.pct_change(fill_method=None)
    logr = np.log(t / t.shift(1))
    out = pd.DataFrame(index=t.index)
    for sym in t.columns:
        out[f"{sym}_simple_ret"] = simple[sym]
        out[f"{sym}_log_ret"] = logr[sym]
    return out


def pair_returns_orientation(h1_close, symbols=None) -> pd.DataFrame:
    """
    Return log-return columns per pair, tagged with base/quote orientation.
    """
    symbols = symbols or PHASE2_SYMBOLS
    logr = np.log(h1_close / h1_close.shift(1))
    meta = {}
    for sym in symbols:
        base, quote = CURRENCY_ORIENTATION.get(sym, (sym[:3], sym[3:]))
        meta[sym] = {"base": base, "quote": quote}
    return logr, meta


def cross_rate_residuals(h1_close, identities=None) -> Dict:
    """
    For each identity output ≈ numerator / denominator, compute the log-return
    residual: log_ret(output) - (log_ret(numerator) - log_ret(denominator)).

    Returns dict identity -> DataFrame[timestamp, predicted_log_ret, actual_log_ret, residual]
    """
    ids = identities or CROSS_RATE_IDENTITIES
    logr = np.log(h1_close / h1_close.shift(1))
    result = {}
    for out, num, den in ids:
        pred = logr[num] - logr[den]
        actual = logr[out]
        resid = actual - pred
        fr = pd.DataFrame({
            "predicted_log_ret": pred,
            "actual_log_ret": actual,
            "residual": resid,
        })
        result[(out, num, den)] = fr
    return result


def staleness_flag(h1_master_panel, symbols=None, tolerance: float = 1e-12) -> pd.DataFrame:
    """
    Flag suspicious repeated OHLC/close values during expected trading hours.
    stale_candidate=True where close == previous close within tolerance AND
    market was open (per market_open mask).
    """
    symbols = symbols or PHASE2_SYMBOLS
    market_open = build_market_open_masks(h1_master_panel, symbols)
    out = pd.DataFrame(index=h1_master_panel.index)
    for sym in symbols:
        close = h1_master_panel[f"{sym}_close"]
        same = close.diff().abs() <= tolerance
        stale = same & market_open[sym]
        out[sym] = stale.fillna(False)
    return out


def outlier_report(h1_master_panel, symbols=None, z_threshold: float = 8.0) -> pd.DataFrame:
    """
    Flag impossible OHLC, nonpositive price, duplicate ts (n/a here), extreme return,
    timestamp reversal (n/a with sorted index). Flag first; do not drop.
    """
    symbols = symbols or PHASE2_SYMBOLS
    idx = h1_master_panel.index
    out = pd.DataFrame(index=idx)
    for sym in symbols:
        o = h1_master_panel[f"{sym}_open"]
        h = h1_master_panel[f"{sym}_high"]
        l = h1_master_panel[f"{sym}_low"]
        c = h1_master_panel[f"{sym}_close"]
        present = c.notna()
        impossible = present & ~((h >= l) & (h >= o) & (h >= c) & (l <= o) & (l <= c))
        nonpos = present & ((c <= 0) | (o <= 0))
        logr = np.log(c / c.shift(1))
        mean = logr.mean()
        std = logr.std()
        extreme = present & (std > 0) & (logr.sub(mean).abs() > z_threshold * std)
        out[f"{sym}_impossible_ohlc"] = impossible.fillna(False)
        out[f"{sym}_nonpositive"] = nonpos.fillna(False)
        out[f"{sym}_extreme_return"] = extreme.fillna(False)
    return out


def coverage_matrix(master_index, availability, market_open, symbols=None) -> pd.DataFrame:
    """
    instrument x (year-month) matrix:
    expected_bars, observed_bars, valid_bars (present), missing_bars,
    unexpected_missing_pct, coverage_pct.
    """
    symbols = symbols or PHASE2_SYMBOLS
    period = master_index.to_period("M")
    rows = []
    for sym in symbols:
        av = availability[sym]
        mo = market_open[sym]
        for period_label, grp in pd.Series(period).groupby(period):
            sel = (period == period_label)
            expected = int(mo[sel].sum())
            present = int(av[sel].sum())
            missing = expected - present
            unexpected = int((mo[sel] & ~av[sel]).sum())
            rows.append({
                "symbol": sym,
                "year_month": str(period_label),
                "expected_bars": expected,
                "observed_bars": int(len(mo[sel])),
                "valid_bars": present,
                "missing_bars": missing,
                "unexpected_missing_pct": round(100.0 * unexpected / expected, 2) if expected else 0.0,
                "coverage_pct": round(100.0 * present / expected, 2) if expected else 0.0,
            })
    return pd.DataFrame(rows)


def common_overlap(availability, market_open, symbols=None) -> Dict:
    """
    Determine exact common research windows over the intersection universe.
    Only timestamps where all symbols are market-open and present count.
    """
    symbols = symbols or PHASE2_SYMBOLS
    all_present = pd.Series(True, index=availability.index)
    for sym in symbols:
        all_present &= availability[sym] & market_open[sym]

    present_idx = availability.index[all_present.values]
    info = {
        "universe": symbols,
        "universe_size": len(symbols),
        "intersection_valid_hours": int(len(present_idx)),
        "earliest_common_ts": str(present_idx.min()) if len(present_idx) else None,
        "latest_common_ts": str(present_idx.max()) if len(present_idx) else None,
        "per_symbol_valid_hours": {
            s: int((availability[s] & market_open[s]).sum()) for s in symbols
        },
    }
    return info