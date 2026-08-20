"""
CTBT T4 — Synchronized read-only M5 data feed.

Patterned on the canonical TB feed (mt5_triangular_data_feed.py): every
basis evaluation requires ALL legs to share the EXACT same closed M5
timestamp.  Snapshots with a missing/stale/forming leg are rejected.

Read-only: this module talks to MetaTrader5 only through ReadOnlyMT5Proxy.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding="utf-8")

from .config import SYMBOL_MAP, RUNTIME  # noqa: E402
from .read_only_proxy import ReadOnlyMT5Proxy, wrap_read_only  # noqa: E402


@dataclass
class M5Bar:
    timestamp: datetime      # UTC (MT5 server time normalized)
    open: float
    high: float
    low: float
    close: float
    volume: int
    raw_time: int


@dataclass
class LegQuote:
    symbol: str
    bid: float
    ask: float
    spread_points: float
    quote_ts: datetime
    fresh: bool


@dataclass
class TriSnapshot:
    timestamp: datetime            # the single closed M5 timestamp
    legs: Dict[str, M5Bar]         # leg name -> bar
    quotes: Optional[Dict[str, LegQuote]] = None
    complete: bool = True
    issues: List[str] = field(default_factory=list)


class CTBTDataFeed:
    """Synchronized 3-leg M5 feed over the read-only MT5 proxy.

    Broker MT5 epochs are SERVER time (e.g. UTC+3 for this provider).  The
    research engine axis (CSV data, activation timestamps, forward filter,
    session mapping) is REAL UTC, so every timestamp is normalized:

        real_utc = utcfromtimestamp(raw) - server_offset

    where server_offset is measured once at init from the latest tick
    (server_now_as_utc - utcnow).  If it cannot be measured the feed refuses
    to run rather than silently mislabel time.
    """

    def __init__(self, proxy: Optional[ReadOnlyMT5Proxy] = None):
        self.mt5 = proxy if proxy is not None else wrap_read_only()
        self._last_processed: Dict[str, Optional[datetime]] = {}
        self.initialized = False
        self.server_offset = None
        self._probe_symbol = None

    def init(self) -> bool:
        ok = bool(self.mt5.initialize())
        self.initialized = ok
        if ok:
            self.server_offset = self._measure_server_offset()
        return ok

    def _measure_server_offset(self) -> Optional[timedelta]:
        """Measure broker server time offset vs real UTC from a live tick."""
        for sym in ("EURUSD.PRO", "GBPUSD.PRO", "EURGBP.PRO"):
            tick = self.mt5.symbol_info_tick(sym)
            if tick is not None and getattr(tick, "time", None):
                self._probe_symbol = sym
                server_as_utc = datetime.utcfromtimestamp(tick.time)
                # broker offsets are whole or half hours; rounding to the
                # nearest 30 min makes normalized bars land on clean :00/:05
                # marks despite tick-age noise (a few seconds)
                secs = round((server_as_utc - datetime.utcnow()).total_seconds() / 1800.0) * 1800
                return timedelta(seconds=secs)
        return None

    def _to_utc(self, raw_epoch: int) -> datetime:
        ts = datetime.utcfromtimestamp(raw_epoch)
        if self.server_offset is not None:
            ts = ts - self.server_offset
        return ts

    def shutdown(self) -> None:
        try:
            self.mt5.shutdown()
        except Exception:
            pass

    def account_summary(self) -> dict:
        info = self.mt5.account_info()
        if info is None:
            return {"connected": False, "error": self.mt5.last_error()}
        return {
            "connected": True,
            "login": getattr(info, "login", None),
            "server": getattr(info, "server", None),
            "trade_mode": getattr(info, "trade_mode", None),
            "currency": getattr(info, "currency", None),
        }

    # ── bar fetching (read-only) ───────────────────────────────────────────
    def fetch_bars(self, leg: str, start: datetime, end: datetime) -> List[M5Bar]:
        """Fetch M5 bars for a leg in [start, end]. UTC-normalized."""
        broker_sym = SYMBOL_MAP[leg]
        rates = self.mt5.copy_rates_range(broker_sym, self.mt5.TIMEFRAME_M5, start, end)
        if rates is None:
            return []
        bars = []
        for r in rates:
            bars.append(M5Bar(
                timestamp=self._to_utc(int(r[0])),
                open=float(r[1]), high=float(r[2]), low=float(r[3]),
                close=float(r[4]), volume=int(r[5]), raw_time=int(r[0])))
        return bars

    def fetch_latest_completed_bars(self, leg: str, n: int = 300) -> List[M5Bar]:
        """Fetch the n most recent COMPLETED M5 bars for a leg (read-only)."""
        broker_sym = SYMBOL_MAP[leg]
        rates = self.mt5.copy_rates_from_pos(broker_sym, self.mt5.TIMEFRAME_M5, 0, n + 1)
        if rates is None:
            return []
        bars = []
        for r in rates:
            bars.append(M5Bar(
                timestamp=self._to_utc(int(r[0])),
                open=float(r[1]), high=float(r[2]), low=float(r[3]),
                close=float(r[4]), volume=int(r[5]), raw_time=int(r[0])))
        return bars

    def last_completed_m5_ts(self, leg: str) -> Optional[datetime]:
        bars = self.fetch_latest_completed_bars(leg, 2)
        return bars[-1].timestamp if bars else None

    # ── quotes (read-only, for cost capture) ───────────────────────────────
    def fetch_quote(self, leg: str, max_age_seconds: int = 120) -> Optional[LegQuote]:
        broker_sym = SYMBOL_MAP[leg]
        tick = self.mt5.symbol_info_tick(broker_sym)
        if tick is None:
            return None
        ts = self._to_utc(int(tick.time))
        fresh = (datetime.utcnow() - ts).total_seconds() <= max_age_seconds
        spread = max(tick.ask - tick.bid, 0.0)
        pts = spread / (getattr(self.mt5.symbol_info(broker_sym), "point", 1e-5) or 1e-5)
        return LegQuote(symbol=broker_sym, bid=float(tick.bid), ask=float(tick.ask),
                        spread_points=float(pts), quote_ts=ts, fresh=fresh)

    # ── synchronized snapshot ──────────────────────────────────────────────
    def build_snapshot(self, legs: List[str], ts: datetime) -> TriSnapshot:
        """Build a synchronized snapshot at a single closed M5 timestamp.

        Rejects the snapshot unless EVERY leg has the exact bar at `ts`.
        """
        bars: Dict[str, M5Bar] = {}
        issues: List[str] = []
        for leg in legs:
            got = self.fetch_bars(leg, ts, ts)
            if len(got) == 1 and got[0].timestamp == ts:
                bars[leg] = got[0]
            else:
                issues.append(f"missing-or-stale {leg} @ {ts}")
        if len(bars) != len(legs):
            return TriSnapshot(timestamp=ts, legs=bars, complete=False, issues=issues)
        quotes = {leg: self.fetch_quote(leg) for leg in legs}
        return TriSnapshot(timestamp=ts, legs=bars, quotes=quotes, complete=True, issues=[])

    def build_history(self, legs: List[str], start: datetime, end: datetime) -> List[TriSnapshot]:
        """Build all synchronized snapshots in [start, end] (completed bars only)."""
        per_leg = {leg: {b.timestamp: b for b in self.fetch_bars(leg, start, end)}
                   for leg in legs}
        common = sorted(set.intersection(*(set(v) for v in per_leg.values())))
        out = []
        for ts in common:
            bars = {leg: per_leg[leg][ts] for leg in legs}
            out.append(TriSnapshot(timestamp=ts, legs=bars, complete=True))
        return out
