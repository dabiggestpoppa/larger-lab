"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · DATA
===================================================

Independent raw-bar acquisition and completeness gating.

The auditor reconstructs signals from RAW COMPLETED M5 bars — never from
live worker decisions/z/state. Sources (in priority order for a requested
week):

  1. Repo broker CSV cache (quant-lab/data/GBPAUD_M5.csv etc.) — the
     historical development window used to freeze the 405/194 reference.
  2. Read-only MT5 pull (mt5.copy_rates_range) — the broker source itself,
     for recent/current weeks not covered by the cache. Pulling rates is a
     READ; it can never send an order.

Bars retain: raw source timestamp, OHLC, volume, source identity. No
interpolation, no forward-fill, no synthetic bars.

Before strategy replay the loader runs completeness gates (common-bar
alignment, missing/duplicate bars, timestamp gaps, week boundaries,
warmup sufficiency). If integrity fails the week is AUDIT_INVALID_DATA —
the auditor refuses to claim a missed signal on broken data (fail closed).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

CANONICAL_SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")

# CSV layout per symbol: (filename, timestamp column)
CSV_LAYOUT = {
    "GBPAUD": ("GBPAUD_M5.csv", "timestamp"),
    "GBPNZD": ("GBPNZD_M5.csv", "timestamp"),
    "AUDNZD": ("AUDNZD_PRO_M5.csv", "time"),
}


@dataclass
class RawBar:
    ts: datetime            # bar OPEN time, naive UTC
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    source: str = "csv"


@dataclass
class DataWindow:
    """A complete, aligned M5 series for the audit: warmup + window bars."""
    week_start: datetime            # Monday 00:00 UTC of the audited week
    week_end: datetime              # next Monday 00:00 UTC
    bars: List[RawBar]              # chronological, common-bar aligned
    per_symbol: Dict[str, List[RawBar]]
    warmup_bars: int = 0            # bars fed before window start
    window_bars: int = 0
    ok: bool = True
    reasons: List[str] = field(default_factory=list)

    def symbol_counts(self) -> Dict[str, int]:
        return {s: len(v) for s, v in self.per_symbol.items()}


class DataCompletenessError(Exception):
    """Raised when integrity gates fail -> AUDIT_INVALID_DATA (fail closed)."""


def _normalize(df: pd.DataFrame, ts_col: str, source: str) -> List[RawBar]:
    if df is None or df.empty:
        return []
    ts = pd.to_datetime(df[ts_col], utc=True)
    out: List[RawBar] = []
    for i in range(len(df)):
        t = ts.iloc[i].to_pydatetime()
        if t.tzinfo is not None:
            t = t.astimezone(timezone.utc).replace(tzinfo=None)
        out.append(RawBar(
            ts=t,
            open=float(df["open"].iloc[i]),
            high=float(df["high"].iloc[i]),
            low=float(df["low"].iloc[i]),
            close=float(df["close"].iloc[i]),
            volume=float(df["volume"].iloc[i]) if "volume" in df.columns else 0.0,
            source=source,
        ))
    out.sort(key=lambda b: b.ts)
    return out


def load_symbol_bars(data_dir: Path, symbol: str) -> List[RawBar]:
    """Load one symbol's full M5 history from the repo CSV cache."""
    fname, ts_col = CSV_LAYOUT[symbol]
    path = data_dir / fname
    if not path.exists():
        return []
    df = pd.read_csv(path)
    # AUDNZD uses 'time'; others 'timestamp' — rename defensively.
    if "time" in df.columns and "timestamp" not in df.columns:
        df = df.rename(columns={"time": "timestamp"})
    df = df[~df["timestamp"].duplicated(keep="first")]
    df = df.dropna(subset=["open", "high", "low", "close"])
    return _normalize(df, "timestamp", "csv")


def _pull_mt5(symbols: Tuple[str, ...], start: datetime, end: datetime,
              broker_map: Dict[str, str]) -> Dict[str, List[RawBar]]:
    """Read-only MT5 pull (copy_rates_range only — cannot send orders).

    Returns {} when the terminal is not reachable; callers treat that as
    "no live-observed data" (parity UNKNOWN), never as a signal.
    """
    try:
        import MetaTrader5 as mt5  # noqa: PLC0415 - lazy, optional
    except Exception:
        return {}
    if not mt5.initialize():
        return {}
    out: Dict[str, List[RawBar]] = {}
    try:
        for canon in symbols:
            broker = broker_map.get(canon, canon)
            rates = mt5.copy_rates_range(
                broker, mt5.TIMEFRAME_M5, start, end)
            if rates is None or len(rates) == 0:
                out[canon] = []
                continue
            rows = []
            for r in rates:
                t = datetime.fromtimestamp(int(r["time"]), tz=timezone.utc)
                rows.append(RawBar(
                    ts=t.replace(tzinfo=None), open=float(r["open"]),
                    high=float(r["high"]), low=float(r["low"]),
                    close=float(r["close"]), volume=float(r["tick_volume"]),
                    source="mt5"))
            out[canon] = rows
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    return out


class MarketDataLoader:
    """Acquires + gates raw bars for an audit week. Read-only by design."""

    WARMUP_DAYS = 60          # ample M5 context (>> 200 bars) before Monday

    def __init__(self, data_dir: Path,
                 broker_map: Optional[Dict[str, str]] = None):
        self.data_dir = Path(data_dir)
        self.broker_map = broker_map or {
            "GBPAUD": "GBPAUD.PRO", "GBPNZD": "GBPNZD.PRO",
            "AUDNZD": "AUDNZD.PRO"}

    def available_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Full common coverage of the CSV cache, or None if unavailable."""
        series = {s: load_symbol_bars(self.data_dir, s)
                  for s in CANONICAL_SYMBOLS}
        if any(len(v) == 0 for v in series.values()):
            return None
        starts = [v[0].ts for v in series.values()]
        ends = [v[-1].ts for v in series.values()]
        return max(starts), min(ends)

    def load_week(self, week_start: datetime, use_mt5: bool = True,
                  force_mt5: bool = False) -> DataWindow:
        """Load + gate one ISO week. Raises DataCompletenessError on failure.

        week_start: Monday 00:00 UTC of the target week (any day of the week
        is accepted and normalized to its Monday).
        """
        ws = week_start - timedelta(days=week_start.weekday())
        ws = ws.replace(hour=0, minute=0, second=0, microsecond=0)
        we = ws + timedelta(days=7)
        reasons: List[str] = []

        per_symbol: Dict[str, List[RawBar]] = {}
        # 1) repo CSV cache
        for s in CANONICAL_SYMBOLS:
            all_bars = load_symbol_bars(self.data_dir, s)
            per_symbol[s] = [b for b in all_bars
                             if ws - timedelta(days=self.WARMUP_DAYS) <= b.ts < we]
        covered = all(len(v) > 0 for v in per_symbol.values())
        if (not covered) and use_mt5:
            mt5_bars = _pull_mt5(CANONICAL_SYMBOLS, ws - timedelta(days=self.WARMUP_DAYS), we, self.broker_map)
            for s in CANONICAL_SYMBOLS:
                if len(per_symbol[s]) == 0 and len(mt5_bars.get(s, [])) > 0:
                    per_symbol[s] = mt5_bars[s]
            covered = all(len(v) > 0 for v in per_symbol.values())
        if not covered and not force_mt5:
            missing = [s for s, v in per_symbol.items() if len(v) == 0]
            raise DataCompletenessError(
                f"no data source for week {ws.date()}; missing symbols: "
                f"{missing} (cache covers {self._range_str()})")

        # 2) common-bar alignment (inner join on timestamp)
        ts_sets = [set(b.ts for b in v) for v in per_symbol.values()]
        common = set.intersection(*ts_sets)
        for s in CANONICAL_SYMBOLS:
            by_ts = {b.ts: b for b in per_symbol[s]}
            per_symbol[s] = [by_ts[t] for t in sorted(common)]

        # 3) split warmup / window
        warm = [b for b in per_symbol[CANONICAL_SYMBOLS[0]] if b.ts < ws]
        wind = [b for b in per_symbol[CANONICAL_SYMBOLS[0]] if ws <= b.ts < we]

        # 4) completeness gates (fail closed)
        if len(warm) < MIN_WARMUP_BARS:
            reasons.append(
                f"warmup insufficient: {len(warm)} bars < {MIN_WARMUP_BARS} "
                f"before {ws.date()} (z would start cold)")
        if len(wind) == 0:
            reasons.append(f"no bars in window {ws.date()}..{we.date()}")

        # duplicate / gap checks within the window
        for s in CANONICAL_SYMBOLS:
            tss = [b.ts for b in per_symbol[s] if ws <= b.ts < we]
            if len(tss) != len(set(tss)):
                reasons.append(f"duplicate timestamps in window for {s}")
        # gap check: longest run of MISSING weekday 5-min slots within the
        # window. Weekends reset the run (market-close intervals are normal);
        # a run > 8h of weekday coverage loss => AUDIT_INVALID_DATA.
        if len(wind) > 1:
            expect = wind[0].ts
            streak = 0
            max_streak = 0
            for b in wind:
                while b.ts > expect:
                    if expect.weekday() < 5:
                        streak += 1
                        max_streak = max(max_streak, streak)
                    else:
                        streak = 0
                    expect += timedelta(minutes=5)
                if b.ts == expect:
                    streak = 0
                    expect += timedelta(minutes=5)
            if max_streak > MAX_WEEKDAY_GAP_SLOTS:
                reasons.append(
                    f"weekday gap of {max_streak * 5} min in window "
                    f"(>{MAX_WEEKDAY_GAP_SLOTS * 5} min of weekday coverage "
                    f"lost; market-close intervals excluded)")
        if not reasons:
            return DataWindow(week_start=ws, week_end=we, bars=wind,
                              per_symbol=per_symbol,
                              warmup_bars=len(warm), window_bars=len(wind))
        raise DataCompletenessError("; ".join(reasons))

    def _range_str(self) -> str:
        r = self.available_range()
        return f"{r[0]}..{r[1]}" if r else "unavailable"


MIN_WARMUP_BARS = 201      # 200-bar z lookback + the current bar
MAX_WEEKDAY_GAP_SLOTS = 96  # > 8h of consecutive lost weekday M5 coverage


def load_full_history(data_dir: Path) -> DataWindow:
    """Aligned full common-coverage window over the CSV cache.

    Used for the frozen historical cadence / reference-count anchoring.
    Deliberately skips the per-week completeness gates (it is a dev
    reference, not an audited week); raises DataCompletenessError if any
    symbol is missing entirely.
    """
    per_symbol: Dict[str, List[RawBar]] = {}
    for s in CANONICAL_SYMBOLS:
        bars = load_symbol_bars(data_dir, s)
        if not bars:
            raise DataCompletenessError(f"no data for {s} in cache")
        per_symbol[s] = bars
    ts_sets = [set(b.ts for b in v) for v in per_symbol.values()]
    common = set.intersection(*ts_sets)
    aligned: Dict[str, List[RawBar]] = {}
    for s in CANONICAL_SYMBOLS:
        by_ts = {b.ts: b for b in per_symbol[s]}
        aligned[s] = [by_ts[t] for t in sorted(common)]
    bars = aligned[CANONICAL_SYMBOLS[0]]
    ws = bars[0].ts - timedelta(days=bars[0].ts.weekday())
    ws = ws.replace(hour=0, minute=0, second=0, microsecond=0)
    we = bars[-1].ts + timedelta(days=7 - bars[-1].ts.weekday())
    we = we.replace(hour=0, minute=0, second=0, microsecond=0)
    return DataWindow(week_start=ws, week_end=we, bars=bars,
                      per_symbol=aligned, warmup_bars=0,
                      window_bars=len(bars))
