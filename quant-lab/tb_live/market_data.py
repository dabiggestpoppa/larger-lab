"""
TB-R2 — Synchronized Market-Data Contract
===========================================

Typed, FAIL-CLOSED market-data contract for the TB forward engine.

Two snapshots are NEVER conflated:

    TriangleSignalSnapshot     -- three CLOSED M5 bars at the SAME signal
                                  timestamp (strategy input; basis/z math).
    TriangleExecutionSnapshot  -- three live bid/ask ticks taken immediately
                                  before order translation (execution pricing,
                                  freshness, synchronization safety).

CRITICAL TIMESTAMP SEMANTICS (frozen, parity-preserving):

    MT5 ``copy_rates*`` returns bar timestamps in SERVER time and the timestamp
    is the bar OPEN time (not close). The sealed research CSVs
    (GBPAUD_M5.csv / GBPNZD_M5.csv / AUDNZD_PRO_M5.csv) carry exactly those
    raw open-time timestamps, and the sealed pipeline applies the canonical
    session rule  est_hour = (hour - 5) % 24  DIRECTLY to them (never +5 min).
    The R1.1 parity harness proved this verbatim handling reproduces
    265,809 bars, 194 primary / 405 control events, 0 mismatches.

    Therefore the STRATEGY KEY is the raw MT5 bar open time, used verbatim.
    ``bar_close_time = bar_open_time + bar_seconds`` is computed ONLY for
    freshness/age math. R2 does NOT add +5min to the strategy key — doing so
    would shift session classification and break the sealed parity.

SCIENTIFIC INVARIANTS: this module contains NO basis/z/entry/exit/weight math.
All execution-safety thresholds are centralized in TBMarketDataConfig and are
PROVISIONAL_EXECUTION_SAFETY_LIMITS (engineering defaults, not PnL-optimized).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional


# ─── FAILURE / HEALTH CODES ───────────────────────────────────────────────

class FailureCode(str, Enum):
    """Machine-readable fail-closed reason codes for snapshots."""

    MISSING_LEG = "MISSING_LEG"
    NO_COMMON_CLOSED_BAR = "NO_COMMON_CLOSED_BAR"
    FORMING_BAR = "FORMING_BAR"
    STALE_SIGNAL_BAR = "STALE_SIGNAL_BAR"
    INVALID_OHLC = "INVALID_OHLC"
    TIMESTAMP_MISMATCH = "TIMESTAMP_MISMATCH"
    DUPLICATE_BAR = "DUPLICATE_BAR"
    STALE_EXECUTION_QUOTES = "STALE_EXECUTION_QUOTES"
    CROSS_LEG_SKEW = "CROSS_LEG_SKEW"
    INVALID_QUOTE = "INVALID_QUOTE"
    SYMBOL_UNAVAILABLE = "SYMBOL_UNAVAILABLE"
    NOT_TRADEABLE = "NOT_TRADEABLE"
    BROKER_DISCONNECTED = "BROKER_DISCONNECTED"
    CLOCK_REGRESSION = "CLOCK_REGRESSION"
    NO_NEW_SIGNAL_BAR = "NO_NEW_SIGNAL_BAR"   # dedup: bar already processed
    OK = "OK"


class HealthState(str, Enum):
    """Overall market-data health for shadow logging."""

    HEALTHY = "HEALTHY"
    WAITING_FOR_BAR_SYNC = "WAITING_FOR_BAR_SYNC"
    STALE_SIGNAL_DATA = "STALE_SIGNAL_DATA"
    STALE_EXECUTION_QUOTES = "STALE_EXECUTION_QUOTES"
    BROKER_DISCONNECTED = "BROKER_DISCONNECTED"
    SYMBOL_UNAVAILABLE = "SYMBOL_UNAVAILABLE"
    INVALID_MARKET_DATA = "INVALID_MARKET_DATA"


# ─── CONFIG (single source of execution-safety thresholds) ───────────────

@dataclass(frozen=True)
class TBMarketDataConfig:
    """Centralized market-data configuration.

    All thresholds here are INFRASTRUCTURE / EXECUTION-SAFETY parameters.
    They are NOT alpha parameters and MUST NOT be tuned against PnL.
    """

    timeframe: str = "M5"
    bar_seconds: int = 300
    required_symbols: tuple = ("GBPAUD", "GBPNZD", "AUDNZD")
    # Signal-bar synchronization gates.
    max_signal_bar_lag_bars: int = 1   # common bar must be within 1 bar of
                                       # the newest bar available per leg.
    max_signal_bar_age_s: float = 600.0   # provisional: 2 M5 bars.
    # Execution-quote gates (provisional engineering defaults).
    max_quote_age_ms: float = 2000.0   # PROVISIONAL_EXECUTION_SAFETY_LIMIT
    max_cross_leg_skew_ms: float = 1000.0  # PROVISIONAL_EXECUTION_SAFETY_LIMIT
    spread_gate_mode: str = "spread_monitor_only"  # do not invent optimal limits
    max_spread_points_per_leg: float = 0.0  # 0 => disabled (monitor only)
    canonical_timezone_semantics: str = "FIXED_UTC_MINUS_5"
    # Clock regression guard: a tick older than the previous tick by more than
    # this delta is treated as a clock regression (0 disables the check).
    clock_regression_tolerance_ms: float = 5000.0

    @property
    def quote_age_tol(self) -> timedelta:
        return timedelta(milliseconds=self.max_quote_age_ms)

    @property
    def skew_tol(self) -> timedelta:
        return timedelta(milliseconds=self.max_cross_leg_skew_ms)


DEFAULT_MARKET_DATA_CONFIG = TBMarketDataConfig()


# ─── BAR / QUOTE TYPES ────────────────────────────────────────────────────

@dataclass(frozen=True)
class ClosedBar:
    """One fully closed M5 bar.

    bar_open_time  -- raw MT5 bar OPEN time (server time), the strategy key,
                      used verbatim per canonical parity semantics.
    bar_close_time -- bar_open_time + bar_seconds (freshness math only).
    is_closed      -- True when the bar is complete (never the forming bar).
    """

    symbol: str
    bar_open_time: datetime
    bar_close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    source_timestamp: Optional[datetime] = None
    is_closed: bool = True
    bar_id: str = ""

    @property
    def timestamp(self) -> datetime:
        """Alias for the strategy key (raw open time)."""
        return self.bar_open_time


@dataclass(frozen=True)
class LegQuote:
    """One leg's live execution quote."""

    symbol: str
    bid: float
    ask: float
    last: float = 0.0
    tick_time: Optional[datetime] = None       # broker tick time (UTC-normalized)
    received_time: Optional[datetime] = None   # local receipt time (UTC)
    quote_age_ms: float = -1.0                 # vs snapshot reference time
    spread_points: float = -1.0
    spread_price: float = -1.0
    valid: bool = True

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0


# ─── SIGNAL SNAPSHOT ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class TriangleSignalSnapshot:
    """Three closed M5 bars at the SAME signal timestamp (strategy input)."""

    signal_bar_close_time: datetime   # canonical strategy key (raw open time)
    gbpaud_bar: ClosedBar
    gbpnzd_bar: ClosedBar
    audnzd_bar: ClosedBar
    all_same_bar_close: bool = True
    all_closed: bool = True
    signal_snapshot_valid: bool = True
    failure_code: FailureCode = FailureCode.OK
    snapshot_id: str = ""
    source_hashes: Dict[str, str] = field(default_factory=dict)

    # Duck-typed aliases consumed by TriangularBasisLiveEngine.process_snapshot.
    @property
    def timestamp(self) -> datetime:
        return self.signal_bar_close_time

    @property
    def bars(self) -> Dict[str, ClosedBar]:
        return {"GBPAUD": self.gbpaud_bar, "GBPNZD": self.gbpnzd_bar,
                "AUDNZD": self.audnzd_bar}


# ─── EXECUTION SNAPSHOT ───────────────────────────────────────────────────

@dataclass(frozen=True)
class TriangleExecutionSnapshot:
    """Fresh three-leg bid/ask snapshot taken immediately before execution
    translation. NEVER used for signal regeneration."""

    signal_bar_close_time: datetime
    gbpaud_quote: LegQuote
    gbpnzd_quote: LegQuote
    audnzd_quote: LegQuote
    max_quote_age_ms: float = -1.0
    max_cross_leg_skew_ms: float = -1.0
    execution_snapshot_valid: bool = True
    failure_code: FailureCode = FailureCode.OK
    snapshot_id: str = ""

    @property
    def quotes(self) -> Dict[str, LegQuote]:
        return {"GBPAUD": self.gbpaud_quote, "GBPNZD": self.gbpnzd_quote,
                "AUDNZD": self.audnzd_quote}


# ─── HEALTH ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TriangleSnapshotHealth:
    """Structured health state written to shadow logs."""

    signal_valid: bool
    execution_valid: bool
    signal_reason: str
    execution_reason: str
    selected_bar_close_time: Optional[datetime] = None
    signal_age_sec: float = -1.0
    quote_age_ms_ga: float = -1.0
    quote_age_ms_gn: float = -1.0
    quote_age_ms_an: float = -1.0
    max_quote_age_ms: float = -1.0
    cross_leg_skew_ms: float = -1.0
    spread_ga: float = -1.0
    spread_gn: float = -1.0
    spread_an: float = -1.0

    def overall_state(self) -> HealthState:
        if self.signal_valid and self.execution_valid:
            return HealthState.HEALTHY
        if not self.signal_valid:
            if self.signal_reason in (FailureCode.STALE_SIGNAL_BAR,):
                return HealthState.STALE_SIGNAL_DATA
            if self.signal_reason in (FailureCode.BROKER_DISCONNECTED,):
                return HealthState.BROKER_DISCONNECTED
            if self.signal_reason in (FailureCode.SYMBOL_UNAVAILABLE,):
                return HealthState.SYMBOL_UNAVAILABLE
            if self.signal_reason in (FailureCode.MISSING_LEG,
                                      FailureCode.NO_COMMON_CLOSED_BAR,
                                      FailureCode.FORMING_BAR,
                                      FailureCode.NO_NEW_SIGNAL_BAR):
                return HealthState.WAITING_FOR_BAR_SYNC
            return HealthState.INVALID_MARKET_DATA
        return HealthState.STALE_EXECUTION_QUOTES


# ─── VALIDATION HELPERS (fail closed, no strategy math) ───────────────────

def _is_finite(v: float) -> bool:
    import math
    return isinstance(v, (int, float)) and math.isfinite(v)


def validate_closed_bar(bar: ClosedBar) -> FailureCode:
    """Validate one closed bar's OHLC sanity. Returns FailureCode.OK if valid."""
    if bar is None:
        return FailureCode.MISSING_LEG
    if not bar.is_closed:
        return FailureCode.FORMING_BAR
    o, h, l, c = bar.open, bar.high, bar.low, bar.close
    if not all(_is_finite(x) for x in (o, h, l, c)):
        return FailureCode.INVALID_OHLC
    if o <= 0 or h <= 0 or l <= 0 or c <= 0:
        return FailureCode.INVALID_OHLC
    if h < l:
        return FailureCode.INVALID_OHLC
    # close must lie within [low, high] (allow tiny float tolerance).
    eps = 1e-12
    if c < l - eps or c > h + eps:
        return FailureCode.INVALID_OHLC
    if o < l - eps or o > h + eps:
        return FailureCode.INVALID_OHLC
    return FailureCode.OK


def validate_signal_snapshot(snap: TriangleSignalSnapshot,
                             cfg: TBMarketDataConfig = DEFAULT_MARKET_DATA_CONFIG,
                             reference_time: Optional[datetime] = None,
                             ) -> FailureCode:
    """Fail-closed validation of a synchronized signal snapshot.

    Returns FailureCode.OK if every gate passes, else the first failing code.
    """
    if snap is None:
        return FailureCode.MISSING_LEG
    if not (snap.all_same_bar_close and snap.all_closed):
        return FailureCode.TIMESTAMP_MISMATCH

    ts = snap.signal_bar_close_time
    if ts is None:
        return FailureCode.INVALID_OHLC

    # NOTE: the three legs are REQUIRED to share one timestamp; that is the
    # synchronization invariant, not a duplicate. Per-leg duplicate timestamps
    # are detected upstream in the feed (get_synchronized_closed_triangle).
    for bar in (snap.gbpaud_bar, snap.gbpnzd_bar, snap.audnzd_bar):
        if bar is None:
            return FailureCode.MISSING_LEG
        if bar.bar_open_time != ts:
            return FailureCode.TIMESTAMP_MISMATCH
        code = validate_closed_bar(bar)
        if code != FailureCode.OK:
            return code

    # Absolute staleness gate on the closed bar (freshness of the SIGNAL).
    if reference_time is not None and cfg.max_signal_bar_age_s > 0:
        age = (reference_time - snap.gbpaud_bar.bar_close_time).total_seconds()
        if age > cfg.max_signal_bar_age_s:
            return FailureCode.STALE_SIGNAL_BAR
    return FailureCode.OK


def validate_execution_snapshot(snap: TriangleExecutionSnapshot,
                                cfg: TBMarketDataConfig = DEFAULT_MARKET_DATA_CONFIG,
                                reference_time: Optional[datetime] = None,
                                ) -> FailureCode:
    """Fail-closed validation of the execution quote snapshot.

    Gates: bid/ask positivity, ask >= bid, quote age, cross-leg skew,
    clock regression. Returns FailureCode.OK or the first failing code.
    """
    if snap is None:
        return FailureCode.INVALID_QUOTE

    times = []
    for q in (snap.gbpaud_quote, snap.gbpnzd_quote, snap.audnzd_quote):
        if q is None:
            return FailureCode.INVALID_QUOTE
        if not (q.bid > 0 and q.ask > 0):
            return FailureCode.INVALID_QUOTE
        if q.ask < q.bid:
            return FailureCode.INVALID_QUOTE
        if q.tick_time is None:
            return FailureCode.INVALID_QUOTE
        if reference_time is not None and cfg.max_quote_age_ms > 0:
            age_ms = (reference_time - q.tick_time).total_seconds() * 1000.0
            if age_ms > cfg.max_quote_age_ms:
                return FailureCode.STALE_EXECUTION_QUOTES
        times.append(q.tick_time)

    if len(times) == 3:
        skew_ms = (max(times) - min(times)).total_seconds() * 1000.0
        if cfg.max_cross_leg_skew_ms > 0 and skew_ms > cfg.max_cross_leg_skew_ms:
            return FailureCode.CROSS_LEG_SKEW
    return FailureCode.OK


def utcnow() -> datetime:
    """UTC-aware reference clock (transport layer only; session math stays
    on the raw bar hour per canonical fixed-UTC-5 semantics)."""
    return datetime.now(timezone.utc)


def to_utc_aware(dt: datetime) -> datetime:
    """Normalize a naive datetime to UTC-aware (transport only)."""
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
