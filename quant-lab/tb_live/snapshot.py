"""
TB-R2 — Synchronized Three-Leg Market-Data Layer
=================================================

The genuine greenfield layer of the TB forward engine.

PURPOSE
-------
Prove that the three legs (GBPAUD / GBPNZD / AUDNZD) represent the SAME closed
signal interval, and that execution quotes are fresh/synchronous enough to
translate a basket intent.

DESIGN RULES (from the frozen R2 contract):
  * SIGNAL generation stays CLOSED-M5-BAR based. Live ticks are used only for
    execution pricing / freshness / synchronization safety — never to change
    the strategy into a tick-entry model.
  * FAIL CLOSED: missing/stale/skewed/invalid data -> no strategy decision,
    no execution intent, zero broker orders.
  * No strategy math here (basis/z/entry/exit/weights live in the sealed
    research engine). This module only provides bars/quotes/snapshots.
  * No order functions exist in the adapter by construction (the MT5 adapter
    exposes ONLY data + symbol-info functions).
  * Timestamp semantics: MT5 bar timestamp = bar OPEN time in server time,
    used VERBATIM as the strategy key (canonical parity). close time is
    open + bar_seconds, used only for freshness.

Modules:
    market_data.py   -- typed contract + fail-closed validation + config
    snapshot.py      -- adapters, symbol resolution, synchronized feed
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Protocol

from tb_live.market_data import (
    TBMarketDataConfig,
    DEFAULT_MARKET_DATA_CONFIG,
    ClosedBar,
    LegQuote,
    TriangleSignalSnapshot,
    TriangleExecutionSnapshot,
    TriangleSnapshotHealth,
    FailureCode,
    HealthState,
    validate_closed_bar,
    validate_signal_snapshot,
    validate_execution_snapshot,
    utcnow,
    to_utc_aware,
)

try:
    import MetaTrader5 as _mt5
except ImportError:  # pragma: no cover - optional dependency
    _mt5 = None


# ─── CANONICAL SYMBOL SET ────────────────────────────────────────────────

CANONICAL_SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")

# Candidate broker suffixes probed at runtime (explicit, locked after resolve).
BROKER_SUFFIX_CANDIDATES = ("", ".PRO", "m", ".raw", ".stp", ".a")


# ─── ADAPTER INTERFACE ───────────────────────────────────────────────────

class MarketDataAdapter(Protocol):
    """Data-only broker adapter. MUST NOT expose any order functions."""

    def get_recent_bars(self, symbol: str, timeframe: str = "M5",
                        count: int = 500) -> Optional[List[ClosedBar]]:
        ...

    def get_tick(self, symbol: str) -> Optional[LegQuote]:
        ...

    def symbol_info(self, symbol: str) -> Optional[dict]:
        ...

    def server_time(self) -> Optional[datetime]:
        ...

    def shutdown(self) -> None:
        ...


# ─── MT5 ADAPTER (data + symbol-info only; NO order_send by construction) ─

_MT5_TIMEFRAME = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 16385}


class MT5MarketDataAdapter:
    """MetaTrader5 data adapter.

    Deliberately exposes ONLY: initialize, symbol_info, symbol_select,
    copy_rates_from_pos, symbol_info_tick, account_info, terminal_info,
    server_time, shutdown. There is NO order_send / order_send wrapper here.
    """

    def __init__(self, bar_seconds: int = 300):
        self._mt5 = _mt5
        self.bar_seconds = bar_seconds
        self._initialized = False

    def initialize(self, **kwargs) -> bool:
        if self._mt5 is None:
            return False
        try:
            self._initialized = bool(self._mt5.initialize(**kwargs))
        except Exception:
            self._initialized = False
        return self._initialized

    @property
    def connected(self) -> bool:
        return self._initialized and (self._mt5 is not None) \
            and self._mt5.terminal_info() is not None

    def server_time(self) -> Optional[datetime]:
        """MT5 has no direct server-time call; use the newest tick time across
        the triangle as the broker-time reference."""
        return None

    def _to_closed_bar(self, symbol: str, raw) -> ClosedBar:
        t = datetime.utcfromtimestamp(raw["time"]).replace(tzinfo=timezone.utc)
        return ClosedBar(
            symbol=symbol,
            bar_open_time=t,
            bar_close_time=t + timedelta(seconds=self.bar_seconds),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
            volume=float(raw.get("real_volume", raw.get("tick_volume", 0))),
            source_timestamp=t,
            is_closed=True,
            bar_id=f"{symbol}:{int(raw['time'])}",
        )

    def get_recent_bars(self, symbol: str, timeframe: str = "M5",
                        count: int = 500) -> Optional[List[ClosedBar]]:
        if self._mt5 is None or not self._initialized:
            return None
        tf = _MT5_TIMEFRAME.get(timeframe)
        if tf is None:
            return None
        try:
            raw = self._mt5.copy_rates_from_pos(symbol, tf, 0, count)
        except Exception:
            return None
        if raw is None or len(raw) == 0:
            return None
        bars = [self._to_closed_bar(symbol, r) for r in raw]
        bars.sort(key=lambda b: b.bar_open_time)
        return bars

    def get_tick(self, symbol: str) -> Optional[LegQuote]:
        if self._mt5 is None or not self._initialized:
            return None
        try:
            tk = self._mt5.symbol_info_tick(symbol)
        except Exception:
            return None
        if tk is None:
            return None
        t = datetime.utcfromtimestamp(tk.time).replace(tzinfo=timezone.utc)
        now = utcnow()
        age_ms = (now - t).total_seconds() * 1000.0
        return LegQuote(
            symbol=symbol, bid=float(tk.bid), ask=float(tk.ask),
            last=float(tk.last), tick_time=t, received_time=now,
            quote_age_ms=age_ms,
            spread_points=float(tk.bid - tk.ask),   # negative -> points below
            spread_price=float(tk.ask - tk.bid),
            valid=tk.bid > 0 and tk.ask > 0 and tk.ask >= tk.bid,
        )

    def symbol_info(self, symbol: str) -> Optional[dict]:
        if self._mt5 is None or not self._initialized:
            return None
        try:
            si = self._mt5.symbol_info(symbol)
        except Exception:
            return None
        if si is None:
            return None
        return {
            "symbol": symbol,
            "visible": bool(getattr(si, "visible", False)),
            "trade_mode": int(getattr(si, "trade_mode", 0)),
            "digits": int(getattr(si, "digits", 0)),
            "point": float(getattr(si, "point", 0.0)),
            "contract_size": float(getattr(si, "trade_contract_size", 0.0)),
            "volume_min": float(getattr(si, "volume_min", 0.0)),
            "volume_step": float(getattr(si, "volume_step", 0.0)),
            "volume_max": float(getattr(si, "volume_max", 0.0)),
            "trade_tick_size": float(getattr(si, "trade_tick_size", 0.0)),
            "trade_tick_value": float(getattr(si, "trade_tick_value", 0.0)),
            "trade_stops_level": int(getattr(si, "trade_stops_level", 0)),
            "filling_mode": int(getattr(si, "filling_mode", 0)),
        }

    def select_symbol(self, symbol: str) -> bool:
        if self._mt5 is None or not self._initialized:
            return False
        try:
            return bool(self._mt5.symbol_select(symbol, True))
        except Exception:
            return False

    def shutdown(self) -> None:
        if self._mt5 is not None and self._initialized:
            try:
                self._mt5.shutdown()
            except Exception:
                pass
            self._initialized = False


# ─── MOCK ADAPTER (deterministic; all R2 tests run against this) ──────────

@dataclass
class MockMarketDataAdapter:
    """Scriptable adapter for deterministic tests + historical replay.

    bars:     {canonical_symbol: [ClosedBar, ...]} ascending by open time.
    ticks:    {canonical_symbol: LegQuote}  (current tick per symbol)
    infos:    {canonical_symbol: dict}      (symbol metadata)
    forming:  {canonical_symbol: ClosedBar} optional forming (open) bar
              that MUST NEVER be emitted as a signal bar.
    """

    bars: Dict[str, List[ClosedBar]] = field(default_factory=dict)
    ticks: Dict[str, LegQuote] = field(default_factory=dict)
    infos: Dict[str, dict] = field(default_factory=dict)
    forming: Dict[str, ClosedBar] = field(default_factory=dict)
    disconnected: bool = False
    symbol_suffixes: Dict[str, str] = field(default_factory=dict)

    # -- deterministic shaping helpers ------------------------------------
    @classmethod
    def from_bars_dict(cls, raw: Dict[str, List[ClosedBar]]) -> "MockMarketDataAdapter":
        return cls(bars=raw)

    @classmethod
    def from_synced_frame(cls, df, bar_seconds: int = 300,
                          symbols: tuple = CANONICAL_SYMBOLS,
                          close_cols: tuple = ("close", "close", "close"),
                          high_cols: tuple = None, low_cols: tuple = None,
                          ) -> "MockMarketDataAdapter":
        """Build a mock adapter from a synchronized pandas frame whose index is
        the raw bar open time (same semantics as the canonical CSVs)."""
        high_cols = high_cols or ("ga_h", "gn_h", "an_h")
        low_cols = low_cols or ("ga_l", "gn_l", "an_l")
        prefix = {"GBPAUD": "ga", "GBPNZD": "gn", "AUDNZD": "an"}
        bars = {}
        for i, sym in enumerate(symbols):
            p = prefix[sym]
            sym_bars = []
            for ts, row in df.iterrows():
                t = pd_to_dt(ts)
                sym_bars.append(ClosedBar(
                    symbol=sym, bar_open_time=t,
                    bar_close_time=t + timedelta(seconds=bar_seconds),
                    open=float(row[f"{p}_o"]) if f"{p}_o" in row else float(row[close_cols[i]]),
                    high=float(row[high_cols[i]]),
                    low=float(row[low_cols[i]]),
                    close=float(row[close_cols[i]]),
                    volume=0.0,
                    is_closed=True,
                    bar_id=f"{sym}:{int(t.timestamp())}",
                ))
            bars[sym] = sym_bars
        return cls(bars=bars)

    # -- protocol ----------------------------------------------------------
    def get_recent_bars(self, symbol: str, timeframe: str = "M5",
                        count: int = 500) -> Optional[List[ClosedBar]]:
        if self.disconnected:
            return None
        b = self.bars.get(symbol)
        if not b:
            return None
        return b[-count:]

    def get_tick(self, symbol: str) -> Optional[LegQuote]:
        if self.disconnected:
            return None
        return self.ticks.get(symbol)

    def symbol_info(self, symbol: str) -> Optional[dict]:
        if self.disconnected:
            return None
        # No silent guessing: unknown symbols return None exactly like the real
        # MT5 adapter. Tests/examples must provision infos explicitly.
        return self.infos.get(symbol)

    def server_time(self) -> Optional[datetime]:
        return utcnow() if not self.disconnected else None

    def shutdown(self) -> None:
        pass


def pd_to_dt(ts) -> datetime:
    """Convert a pandas Timestamp (or str) to a UTC-aware datetime preserving
    the wall-clock hour (the strategy key semantics)."""
    import pandas as pd
    if isinstance(ts, datetime):
        dt = ts
    else:
        dt = pd.Timestamp(ts).to_pydatetime()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ─── SYMBOL RESOLUTION (explicit, runtime-verified, never assumed) ────────

@dataclass
class SymbolResolution:
    mapping: Dict[str, str] = field(default_factory=dict)      # canon -> broker
    metadata: Dict[str, dict] = field(default_factory=dict)    # canon -> info
    locked: bool = False

    def to_dict(self) -> dict:
        return {
            "mapping": self.mapping,
            "metadata": self.metadata,
            "locked": self.locked,
        }


class SymbolResolver:
    """Resolve canonical symbols (GBPAUD/GBPNZD/AUDNZD) to broker symbols at
    runtime by probing candidates and requiring valid metadata + trade mode.

    The resolution is explicit and locked: after the first successful resolve
    the mapping is frozen for the process lifetime (no silent re-mapping).
    """

    def __init__(self, adapter: MarketDataAdapter,
                 candidates: tuple = BROKER_SUFFIX_CANDIDATES,
                 canonical_symbols: tuple = CANONICAL_SYMBOLS):
        self.adapter = adapter
        self.candidates = candidates
        self.canonical_symbols = canonical_symbols
        self.resolution = SymbolResolution()

    def resolve(self, force: bool = False) -> SymbolResolution:
        if self.resolution.locked and not force:
            return self.resolution

        mapping, metadata = {}, {}
        for canon in self.canonical_symbols:
            found = None
            for suffix in self.candidates:
                probe = canon + suffix if suffix else canon
                info = self.adapter.symbol_info(probe)
                if info is None:
                    continue
                # trade_mode: 0 = disabled -> fail; require tradeable.
                trade_mode = info.get("trade_mode", 0)
                if trade_mode == 0:
                    continue
                if info.get("contract_size", 0) <= 0:
                    continue
                found = (probe, info)
                break
            if found is None:
                # Keep previously resolved mappings; mark this one unresolved.
                continue
            probe, info = found
            mapping[canon] = probe
            metadata[canon] = info

        self.resolution = SymbolResolution(
            mapping=mapping, metadata=metadata, locked=True)
        return self.resolution

    def require_resolved(self) -> SymbolResolution:
        r = self.resolve()
        missing = [c for c in self.canonical_symbols if c not in r.mapping]
        if missing:
            raise RuntimeError(f"Symbol resolution failed for: {missing}")
        return r


# ─── SYNCHRONIZED TRIANGLE FEED (the R2 core) ─────────────────────────────

class SynchronizedTriangleFeed:
    """Fail-closed synchronized three-leg market-data feed.

    Sequence (mirrors the R2 contract):
        1. fetch recent closed bars for all three legs
        2. discard forming bars, find the latest common CLOSED timestamp
        3. validate (same timestamp, OHLC sanity, staleness, dedup)
        4. -> TriangleSignalSnapshot (strategy input)
        5. separately, fresh bid/ask ticks -> TriangleExecutionSnapshot
    """

    def __init__(self, adapter: MarketDataAdapter,
                 config: TBMarketDataConfig = DEFAULT_MARKET_DATA_CONFIG,
                 resolver: SymbolResolver = None,
                 lookback_bars: int = 12):
        """lookback_bars: how many recent bars are fetched per leg to find the
        latest common closed interval. The strategy only needs the newest few
        closed bars; the lag gate rejects anything >1 bar behind anyway, so a
        small window is both sufficient and fail-closed (a stale leg that has
        fallen out of the window simply yields no common bar)."""
        self.adapter = adapter
        self.config = config
        self.resolver = resolver or SymbolResolver(adapter)
        self.lookback_bars = lookback_bars
        self.last_processed_signal_ts: Optional[datetime] = None
        self._last_tick_times: Dict[str, datetime] = {}
        self._stats = {
            "snapshots_emitted": 0,
            "signal_invalid": 0,
            "execution_invalid": 0,
            "stale_signal": 0,
            "stale_quote": 0,
            "cross_leg_skew": 0,
            "no_common_bar": 0,
            "forming_bar": 0,
            "dedup_skipped": 0,
        }

    # ── bar-level helpers ────────────────────────────────────────────────
    def _fetch_closed_bars(self, reference_time: datetime) -> Dict[str, List[ClosedBar]]:
        """Fetch recent bars for all legs, keeping only bars CLOSED by the
        reference time (bar_close_time <= reference). A bar is closed only
        when its M5 interval has ended; the forming bar is excluded by time,
        never by list position."""
        out: Dict[str, List[ClosedBar]] = {}
        try:
            resolution = self.resolver.require_resolved()
        except RuntimeError:
            self._stats["signal_invalid"] += 1
            return out
        for canon in self.config.required_symbols:
            broker = resolution.mapping.get(canon)
            if broker is None:
                self._stats["signal_invalid"] += 1
                return {}
            bars = self.adapter.get_recent_bars(broker, "M5", self.lookback_bars)
            if bars is None or len(bars) == 0:
                self._stats["signal_invalid"] += 1
                return {}
            closed = [b for b in bars if b.bar_close_time <= reference_time]
            if not closed:
                self._stats["signal_invalid"] += 1
                return {}
            # fail closed on per-leg duplicate timestamps in the fetched set
            opens = [b.bar_open_time for b in closed]
            if len(set(opens)) != len(opens):
                self._stats["signal_invalid"] += 1
                return {}
            out[canon] = closed
        return out

    # ── signal snapshot ──────────────────────────────────────────────────
    def get_synchronized_closed_triangle(
            self, reference_time: Optional[datetime] = None
    ) -> TriangleSignalSnapshot:
        """Latest common CLOSED M5 bar across all three legs, or an invalid
        snapshot carrying the machine-readable failure code."""
        ref = to_utc_aware(reference_time) or utcnow()
        closed = self._fetch_closed_bars(ref)
        if len(closed) != len(self.config.required_symbols):
            return self._invalid_signal(FailureCode.MISSING_LEG, ref)

        # Timestamp intersection: find the latest bar OPEN time present in ALL
        # legs (scan the union newest-first; never 'latest bar per leg' alone).
        per_leg_ts = {c: {b.bar_open_time for b in bars}
                      for c, bars in closed.items()}
        # Candidate set = union of all timestamps, walked newest-first.
        all_ts = sorted(set().union(*per_leg_ts.values()), reverse=True)
        selected = None
        for ts in all_ts:
            if all(ts in s for s in per_leg_ts.values()):
                selected = ts
                break
        if selected is None:
            self._stats["no_common_bar"] += 1
            return self._invalid_signal(FailureCode.NO_COMMON_CLOSED_BAR, ref)

        bars_at = {}
        for canon in self.config.required_symbols:
            by_ts = {b.bar_open_time: b for b in closed[canon]}
            bars_at[canon] = by_ts[selected]

        # Per-leg lag gate: the common bar must be within max_signal_bar_lag_bars
        # of the newest closed bar available for that leg.
        for canon in self.config.required_symbols:
            newest = closed[canon][-1].bar_open_time
            lag_bars = round((newest - selected).total_seconds()
                             / self.config.bar_seconds)
            if lag_bars > self.config.max_signal_bar_lag_bars:
                self._stats["no_common_bar"] += 1
                return self._invalid_signal(FailureCode.STALE_SIGNAL_BAR, ref)

        snap = TriangleSignalSnapshot(
            signal_bar_close_time=selected,
            gbpaud_bar=bars_at["GBPAUD"],
            gbpnzd_bar=bars_at["GBPNZD"],
            audnzd_bar=bars_at["AUDNZD"],
            all_same_bar_close=True,
            all_closed=True,
            signal_snapshot_valid=True,
            failure_code=FailureCode.OK,
            snapshot_id=self._snapshot_id(selected, bars_at),
            source_hashes={c: b.bar_id for c, b in bars_at.items()},
        )

        code = validate_signal_snapshot(snap, self.config, ref)
        if code != FailureCode.OK:
            if code == FailureCode.STALE_SIGNAL_BAR:
                self._stats["stale_signal"] += 1
            self._stats["signal_invalid"] += 1
            return self._invalid_signal(code, ref)

        # Dedup: one strategy evaluation per new synchronized closed bar.
        if (self.last_processed_signal_ts is not None
                and selected == self.last_processed_signal_ts):
            self._stats["dedup_skipped"] += 1
            return self._invalid_signal(FailureCode.NO_NEW_SIGNAL_BAR, ref,
                                        ts=selected)

        self.last_processed_signal_ts = selected
        self._stats["snapshots_emitted"] += 1
        return snap

    def _invalid_signal(self, code: FailureCode, ref: datetime,
                        ts: Optional[datetime] = None) -> TriangleSignalSnapshot:
        t = ts or ref
        bar = ClosedBar(symbol="", bar_open_time=t,
                        bar_close_time=t + timedelta(seconds=self.config.bar_seconds),
                        open=0.0, high=0.0, low=0.0, close=0.0, is_closed=True)
        return TriangleSignalSnapshot(
            signal_bar_close_time=t, gbpaud_bar=bar, gbpnzd_bar=bar,
            audnzd_bar=bar, all_same_bar_close=False, all_closed=False,
            signal_snapshot_valid=False, failure_code=code, snapshot_id="",
        )

    # ── execution quote snapshot ─────────────────────────────────────────
    def get_execution_quote_snapshot(
            self, signal_bar_close_time: Optional[datetime] = None,
            reference_time: Optional[datetime] = None,
    ) -> TriangleExecutionSnapshot:
        """Fresh three-leg bid/ask snapshot (execution translation only)."""
        ref = to_utc_aware(reference_time) or utcnow()
        try:
            resolution = self.resolver.require_resolved()
        except RuntimeError:
            return self._invalid_exec(FailureCode.SYMBOL_UNAVAILABLE, ref)

        quotes, times = {}, []
        for canon in self.config.required_symbols:
            broker = resolution.mapping.get(canon)
            if broker is None:
                return self._invalid_exec(FailureCode.SYMBOL_UNAVAILABLE, ref)
            q = self.adapter.get_tick(broker)
            if q is None or not q.valid:
                return self._invalid_exec(FailureCode.INVALID_QUOTE, ref)
            # normalize quote tick time
            t = to_utc_aware(q.tick_time)
            info = resolution.metadata.get(canon, {})
            point = float(info.get("point", 1e-5)) or 1e-5
            q = LegQuote(symbol=q.symbol, bid=q.bid, ask=q.ask, last=q.last,
                         tick_time=t, received_time=to_utc_aware(q.received_time),
                         quote_age_ms=(ref - t).total_seconds() * 1000.0,
                         spread_points=(q.ask - q.bid) / point,
                         spread_price=q.ask - q.bid, valid=True)
            # clock regression guard
            prev = self._last_tick_times.get(canon)
            if (prev is not None
                    and self.config.clock_regression_tolerance_ms > 0
                    and (prev - t).total_seconds() * 1000.0
                    > self.config.clock_regression_tolerance_ms):
                return self._invalid_exec(FailureCode.CLOCK_REGRESSION, ref)
            self._last_tick_times[canon] = t
            quotes[canon] = q
            times.append(t)

        skew_ms = (max(times) - min(times)).total_seconds() * 1000.0
        age_ms = max((ref - t).total_seconds() * 1000.0 for t in times)

        snap = TriangleExecutionSnapshot(
            signal_bar_close_time=signal_bar_close_time,
            gbpaud_quote=quotes["GBPAUD"],
            gbpnzd_quote=quotes["GBPNZD"],
            audnzd_quote=quotes["AUDNZD"],
            max_quote_age_ms=age_ms,
            max_cross_leg_skew_ms=skew_ms,
            execution_snapshot_valid=True,
            failure_code=FailureCode.OK,
            snapshot_id=self._exec_id(signal_bar_close_time),
        )
        code = validate_execution_snapshot(snap, self.config, ref)
        if code != FailureCode.OK:
            if code == FailureCode.STALE_EXECUTION_QUOTES:
                self._stats["stale_quote"] += 1
            if code == FailureCode.CROSS_LEG_SKEW:
                self._stats["cross_leg_skew"] += 1
            self._stats["execution_invalid"] += 1
            return self._invalid_exec(code, ref)
        return snap

    def _invalid_exec(self, code: FailureCode, ref: datetime,
                      ) -> TriangleExecutionSnapshot:
        q = LegQuote(symbol="", bid=0.0, ask=0.0, valid=False,
                     tick_time=ref, received_time=ref)
        return TriangleExecutionSnapshot(
            signal_bar_close_time=None, gbpaud_quote=q, gbpnzd_quote=q,
            audnzd_quote=q, max_quote_age_ms=-1.0, max_cross_leg_skew_ms=-1.0,
            execution_snapshot_valid=False, failure_code=code, snapshot_id="",
        )

    # ── health ───────────────────────────────────────────────────────────
    def get_health(self, reference_time: Optional[datetime] = None,
                   ) -> TriangleSnapshotHealth:
        ref = to_utc_aware(reference_time) or utcnow()
        sig = self.get_synchronized_closed_triangle(ref)
        exec_snap = None
        if sig.signal_snapshot_valid:
            exec_snap = self.get_execution_quote_snapshot(
                sig.signal_bar_close_time, ref)
        qa = {"ga": -1.0, "gn": -1.0, "an": -1.0}
        spread = {"ga": -1.0, "gn": -1.0, "an": -1.0}
        if exec_snap is not None and exec_snap.execution_snapshot_valid:
            qa = {"ga": exec_snap.gbpaud_quote.quote_age_ms,
                  "gn": exec_snap.gbpnzd_quote.quote_age_ms,
                  "an": exec_snap.audnzd_quote.quote_age_ms}
            spread = {"ga": exec_snap.gbpaud_quote.spread_price,
                      "gn": exec_snap.gbpnzd_quote.spread_price,
                      "an": exec_snap.audnzd_quote.spread_price}
        age = -1.0
        if sig.signal_snapshot_valid:
            age = (ref - sig.gbpaud_bar.bar_close_time).total_seconds()
        return TriangleSnapshotHealth(
            signal_valid=sig.signal_snapshot_valid,
            execution_valid=(exec_snap is not None
                             and exec_snap.execution_snapshot_valid),
            signal_reason=sig.failure_code.value,
            execution_reason=(exec_snap.failure_code.value
                              if exec_snap is not None else "NOT_TAKEN"),
            selected_bar_close_time=(sig.signal_bar_close_time
                                     if sig.signal_snapshot_valid else None),
            signal_age_sec=age,
            quote_age_ms_ga=qa["ga"], quote_age_ms_gn=qa["gn"],
            quote_age_ms_an=qa["an"],
            max_quote_age_ms=(exec_snap.max_quote_age_ms
                              if exec_snap is not None else -1.0),
            cross_leg_skew_ms=(exec_snap.max_cross_leg_skew_ms
                               if exec_snap is not None else -1.0),
            spread_ga=spread["ga"], spread_gn=spread["gn"], spread_an=spread["an"],
        )

    def get_stats(self) -> dict:
        return dict(self._stats)

    def reset_dedup(self):
        self.last_processed_signal_ts = None

    def shutdown(self) -> None:
        """Shut down the underlying adapter (data-only; never orders)."""
        self.adapter.shutdown()

    # ── ids ──────────────────────────────────────────────────────────────
    @staticmethod
    def _snapshot_id(ts: datetime, bars_at: Dict[str, ClosedBar]) -> str:
        h = hashlib.sha256(
            (ts.isoformat() + "|" + "|".join(
                b.bar_id for b in bars_at.values())).encode()
        ).hexdigest()[:16]
        return f"SIG_{ts.strftime('%Y%m%d_%H%M%S')}_{h}"

    @staticmethod
    def _exec_id(ts: Optional[datetime]) -> str:
        if ts is None:
            return "EXEC_"
        return f"EXEC_{ts.strftime('%Y%m%d_%H%M%S')}"
