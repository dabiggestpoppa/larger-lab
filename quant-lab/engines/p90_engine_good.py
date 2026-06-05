"""
CEREBUS FX v4.0 — P90 Kinetic Engine (Model A: All Variants)
=============================================================

Reconstructed from CEREBUS ontology per MAD directive (2026-05-29):
  - Base 80 (Play 1): Initial P90 breach of Asian Band
  - Cascade P90: 2nd/3rd P90 in same direction within 120 min
  - EWS: Opposite P90 at target = exit signal, NOT entry

ONTOLOGY SOURCES:
  - cerebus_p90.md               (P90 kinetic threshold, elastic vs plastic deformation)
  - cerebus_dual_engine.md       (Model A table, engine isolation, target interplay)
  - cerebus_unified_topology.md  (Model A: P90 Kinetic Engine, strategy collapse matrix)
  - cerebus_qa_recap.md          (Target hierarchy, regime-behavior matrix)
  - cerebus_forward.md           (Paradigm shift, single state, computable invariants)
  - manual_ontology.md           (55 Q&As)

AXIOMS ENFORCED:
  1. P90 = Engine A ONLY (Kinetic). Never mix Symmetry Trap SL/TP.
  2. Entry = immediate close of P90 candle (NO pullback wait, NO OCC).
  3. SL = 80% of P90 candle body (NOT Zero-Buffer Extreme).
  4. P90 body >= threshold = plastic deformation = pathway accepted.
  5. P90 body < threshold = elastic deformation = ignore (81.2% reversion).
  6. EWS = exit signal ONLY. Never reversal entry.
  7. 12 PM = full state reset.
  8. Engine isolation: P90 entry + SL NEVER crosses with Symmetry Trap mechanics.

MODEL A VARIANTS (cerebus_unified_topology.md Section II):
  | Manual Name    | True Identity            | Key Parameter Difference                    |
  |----------------|--------------------------|---------------------------------------------|
  | Base 80        | Model A (Initial)        | First P90 breach. SL=80% body. TP=-25/-50% AR. |
  | Cascade P90    | Model A (Subsequent)     | 2nd/3rd P90 same dir within 120min. SL=168% of NEW P90 body. |
  | EWS            | Model A (Exit Signal)    | Opposite P90 at target. Force-close, NOT flip. |
  | 45-Min Add     | Model A (Legacy)         | Time-triggered version of Cascade. Superseded. |

Reference: cerebus_dual_engine.md Section III (Bipolar Motor Model table)
Author: CEREBUS Ontology Reconstruction — MAD Directive 2026-05-29
Mode: Mechanical / Structural / Executable
Trader Language: PURGED
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ─── CONSTANTS ────────────────────────────────────────────────────────────

ASIAN_SESSION_START = time(19, 0)
ASIAN_SESSION_END = time(3, 0)
ACTIVATION_START = time(3, 0)
ACTIVATION_END = time(12, 0)

# P90 minimum body as fraction of AU (cerebus_p90.md: P90 is statistical, not fixed)
# Default calibration — should be overridden per-pair from historical data
DEFAULT_P90_THRESHOLDS = {
    # est_hour: min_body_pips
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9,
    9: 6.2, 10: 6.2,
    11: 999.0,  # outside entry window
}

# Tier configuration (same as Symmetry Trap — shared crankshaft)
DEFAULT_TIER_CONFIG = {
    "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
    "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
    "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
}

# Cascade P90 max time window (cerebus_dual_engine.md: within 120 min)
CASCADE_WINDOW_MINUTES = 120


# ─── ENUMS ────────────────────────────────────────────────────────────────

class P90Variant(Enum):
    """Model A parameter variants (cerebus_unified_topology.md Section II)."""
    INITIAL = "INITIAL"             # Base 80 / Play 1
    CASCADE = "CASCADE"            # 2nd/3rd P90 same direction within 120min
    EWS = "EWS"                     # Early Warning (exit signal only)


class EngineState(Enum):
    SEARCH = "SEARCH"               # Waiting for P90 breach
    IN_TRADE = "IN_TRADE"           # Position active, monitoring TP/SL/EWS


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────

@dataclass
class Bar:
    """M5 candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

    @property
    def body(self) -> float:
        return self.close - self.open

    @property
    def body_abs(self) -> float:
        return abs(self.close - self.open)


@dataclass
class P90Signal:
    """Structured output on P90 engine events."""
    event: str                          # "ENTRY", "TP_HIT", "SL_HIT", "EWS_EXIT", "CASCADE_ADD", "12PM_EXIT"
    variant: P90Variant
    direction: TradeDirection
    entry_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    tp2_price: Optional[float] = None  # TP2 for -50% AR target
    p90_body_pips: float = 0.0
    timestamp: Optional[datetime] = None
    reason: str = ""


# ─── TIER CLASSIFICATION (shared with Symmetry Trap) ──────────────────────

def classify_tier(
    asian_range_pips: float,
    tier_config: Dict = DEFAULT_TIER_CONFIG
) -> Tuple[str, float, float]:
    """
    Classify session volatility into discrete Tier.
    Reference: manual_ontology.md Section 1 Q4, Computable Mechanics Q3
    """
    for tier_name in ("T1", "T2", "T3"):
        if tier_name in tier_config and asian_range_pips <= tier_config[tier_name]["ar_max"]:
            cfg = tier_config[tier_name]
            return tier_name, cfg["au"], cfg["trigger"]
    return "NO_GO", 0.0, 0.0


# ─── P90 THRESHOLD CALIBRATION ───────────────────────────────────────────

def get_p90_threshold(est_hour: int, p90_config: Dict[int, float] = None) -> float:
    """
    Get the minimum P90 body size (in pips) for the current EST hour.

    The P90 is calibrated per-pair, per-session from rolling 3-month lookback.
    Default values are EUR/USD reference (cerebus_p90.md Section V).

    Reference: cerebus_p90.md Section V (Calibration Protocol)
    """
    cfg = p90_config or DEFAULT_P90_THRESHOLDS
    return cfg.get(est_hour, 999.0)  # Outside activation window = no entry


def calibrate_p90(all_m5_bars: List[Bar], est_hours: Tuple = (3,4,5,6,7,8,9,10,11),
                  lookback_months: int = 3) -> Dict[int, float]:
    """
    Calibrate P90 thresholds from historical M5 data.

    Reference: cerebus_p90.md Section V:
      1. Filter to activation window (03:00-12:00 EST)
      2. Calculate 90th percentile of absolute body sizes
      3. Per hour or pooled

    Returns:
        Dict mapping est_hour -> min_body_pips (P90 threshold)
    """
    from statistics import quantiles

    body_by_hour: Dict[int, List[float]] = {h: [] for h in est_hours}

    for bar in all_m5_bars:
        # Extract EST hour from timestamp (assumed UTC, offset -5)
        est_hour = (bar.timestamp.hour - 5) % 24
        if est_hour in body_by_hour:
            body_by_hour[est_hour].append(bar.body_abs)

    result = {}
    for hour in est_hours:
        bodies = body_by_hour[hour]
        if len(bodies) >= 10:
            # 90th percentile
            sorted_bodies = sorted(bodies)
            idx = int(len(sorted_bodies) * 0.9)
            result[hour] = sorted_bodies[min(idx, len(sorted_bodies) - 1)]
        else:
            result[hour] = DEFAULT_P90_THRESHOLDS.get(hour, 4.6)

    return result


# ─── CORE P90 ENGINE ──────────────────────────────────────────────────────

class P90Engine:
    """
    CEREBUS Model A: P90 Kinetic Engine — All Variants

    ENTRY (all variants): Immediate close of P90 candle
      - NO pullback wait (unlike Symmetry Trap)
      - NO OCC confirmation (unlike Symmetry Trap)
      - Entry = close of the P90 candle itself

    INVALIDATION: 80% of P90 candle body from the candle's close
      - S LONG: SL = P90_close - (body * 0.80)
      - S SHORT: SL = P90_close + (body * 0.80)

    VARIANT DETECTION:
      - INITIAL: First P90 of session. TP = -25% AR or -50% AR.
      - CASCADE: Same-direction P90 within 120 min of last exit. SL = 168% of NEW P90 body.
      - EWS: Opposite P90 prints at target. Force-close, NOT reversal.

    Reference: cerebus_dual_engine.md Section I (Great Demarcation)
    """

    def __init__(
        self,
        pip_size: float = 0.0001,
        p90_config: Optional[Dict[int, float]] = None,
        tier_config: Optional[Dict] = None,
        symbol: str = "EURUSD",
        target_mode: str = "both",  # "tp1_only" (-25% AR), "tp2_only" (-50% AR), "both"
        config: Optional[Dict] = None,
    ):
        # Config injection: if full config dict provided, extract parameters from it
        if config is not None:
            self.pip_size = config.get("pip_value", pip_size)
            self.p90_config = p90_config or DEFAULT_P90_THRESHOLDS.copy()
            self.tier_config = config.get("tiers", tier_config or DEFAULT_TIER_CONFIG.copy())
            self.symbol = config.get("name", symbol)
        else:
            self.pip_size = pip_size
            self.p90_config = p90_config or DEFAULT_P90_THRESHOLDS.copy()
            self.tier_config = tier_config or DEFAULT_TIER_CONFIG.copy()
            self.symbol = symbol
        self.target_mode = target_mode
        self.logger = logging.getLogger(f"cerebus.p90.{symbol}")

        # ── SL Min Buffer & Spread Buffer (per Architect Directive 2026-06-02) ──
        # min_sl_buffer: minimum SL distance in pips (asset-specific floor)
        # spread_buffer: spread buffer in price units (added to P90 extreme)
        cfg = config or {}
        self.min_sl_buffer = cfg.get("min_sl_buffer", self._default_min_sl_buffer(symbol))
        self.spread_buffer = cfg.get("spread_buffer", self._default_spread_buffer(symbol))
        self.kill_switch_body_pct = 0.80  # 80% body = intra-candle kill switch

        # ── State Machine ──────────────────────────────────────────────
        self.state = EngineState.SEARCH
        self.active_variant = P90Variant.INITIAL

        # ── Trade State ────────────────────────────────────────────────
        self.direction = TradeDirection.FLAT
        self.entry_price: Optional[float] = None
        self.sl_price: Optional[float] = None
        self.tp1_price: Optional[float] = None   # -25% AR
        self.tp2_price: Optional[float] = None   # -50% AR
        self.p90_body_pips: float = 0.0
        self.p90_body_price: float = 0.0
        # ── 80% Kill Switch levels (P90 signal candle extremes) ──
        self.p90_kill_high: Optional[float] = None  # High of P90 signal candle
        self.p90_kill_low: Optional[float] = None   # Low of P90 signal candle

        # ── Session State ──────────────────────────────────────────────
        self.asian_high: float = 0.0
        self.asian_low: float = 0.0
        self.asian_range_pips: float = 0.0
        self.ar_price: float = 0.0
        self.tier_name: str = "T1"
        self.session_active: bool = False

        # ── Cascade State ──────────────────────────────────────────────
        self.p90_count: int = 0                  # P90s fired this session, same dir
        self.last_p90_exit_time: Optional[datetime] = None

        # ── Timing ─────────────────────────────────────────────────────
        self.last_bar_time: Optional[datetime] = None

        # ── Logging ────────────────────────────────────────────────────
        self.signal_log: List[P90Signal] = []

    # ── Session Initialization ────────────────────────────────────────

    def initialize_session(self, asian_high: float, asian_low: float) -> None:
        """
        Initialize session at 03:00 EST from Asian Range.

        Reference: cerebus_qa_recap.md Q1, cerebus_p90.md Section I
        """
        self.asian_high = asian_high
        self.asian_low = asian_low
        self.ar_price = asian_high - asian_low
        self.asian_range_pips = self.ar_price / self.pip_size

        self.tier_name, au_pips, trigger_pips = classify_tier(
            self.asian_range_pips, self.tier_config
        )
        self.session_active = self.tier_name != "NO_GO"

        # Reset state machine
        self.state = EngineState.SEARCH
        self.active_variant = P90Variant.INITIAL
        self.direction = TradeDirection.FLAT
        self.entry_price = None
        self.sl_price = None
        self.tp1_price = None
        self.tp2_price = None
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0
        self.p90_count = 0
        self.last_p90_exit_time = None

        self.logger.info(
            f"Session initialized: tier={self.tier_name}, "
            f"AR={self.asian_range_pips:.1f}p, "
            f"min_sl={self.min_sl_buffer:.1f}p, spread_buf={self.spread_buffer:.5f}"
        )

    # ── Default SL Buffers by Asset Class ───────────────────────────

    @staticmethod
    def _default_min_sl_buffer(symbol: str) -> float:
        """Minimum SL buffer floor in pips (Architect Directive 2026-06-02)."""
        sym = symbol.upper()
        if any(x in sym for x in ['GBPJPY', 'GBPAUD', 'GBPNZD']):
            return 12.0   # GBP crosses need 12+ pip floor
        if 'JPY' in sym:
            return 6.0    # JPY pairs need 6+ pip floor
        if any(x in sym for x in ['XAU', 'XAG']):
            return 150.0  # Gold/Silver in points
        return 8.0        # Default for majors

    @staticmethod
    def _default_spread_buffer(symbol: str) -> float:
        """Spread buffer in price units (added to P90 extreme for SL placement)."""
        sym = symbol.upper()
        if any(x in sym for x in ['GBPJPY', 'GBPAUD', 'GBPNZD']):
            return 0.0003  # ~3 pips on GBP crosses
        if 'JPY' in sym:
            return 0.00015  # ~1.5 pips on JPY
        if any(x in sym for x in ['XAU', 'XAG']):
            return 0.15
        return 0.00015  # ~1.5 pips default

    # ── P90 Validation ───────────────────────────────────────────────

    def _is_p90(self, bar: Bar, est_hour: int) -> bool:
        """
        Check if M5 candle body >= P90 threshold for current hour.

        Reference: cerebus_p90.md Section II (Elastic vs Plastic Deformation)
          - body >= P90 = plastic deformation = pathway accepted
          - body < P90 = elastic deformation = ignore (81.2% reversion)
        """
        body_pips = bar.body_abs / self.pip_size
        threshold = get_p90_threshold(est_hour, self.p90_config)
        return body_pips >= threshold

    def _is_boundary_breach(self, bar: Bar) -> bool:
        """
        Check if candle breaches Asian Range boundary.

        Reference: cerebus_p90.md Section II (Tier Trigger breach + P90 validation)
        BOTH conditions required: spatial breach AND P90 body.
        """
        breach_up = bar.close > self.asian_high
        breach_down = bar.close < self.asian_low
        return breach_up or breach_down

    def _detect_variant(self, bar: Bar, est_hour: int) -> P90Variant:
        """
        Detect which P90 variant applies.

        Reference: cerebus_unified_topology.md Section II Model A Table,
                   cerebus_dual_engine.md Section III Table

        Logic:
          - CASCADE: Same-dir P90 within 120 min of last exit
          - INITIAL: First P90 of session (default)
        """
        # Cascade: same direction P90 within 120 min of last exit
        if (self.last_p90_exit_time is not None and
                self.p90_count > 0 and
                bar.timestamp - self.last_p90_exit_time <= timedelta(minutes=CASCADE_WINDOW_MINUTES)):
            self.logger.info(
                f"Cascade P90 detected: #{self.p90_count + 1}, "
                f"delta={bar.timestamp - self.last_p90_exit_time}"
            )
            return P90Variant.CASCADE

        # Default: Initial
        return P90Variant.INITIAL

    # ── Trade Parameter Calculation ──────────────────────────────────

    def _calc_trade_params(
        self, bar: Bar, variant: P90Variant, direction: TradeDirection
    ) -> Tuple[float, float, Optional[float], Optional[float]]:
        """
        Calculate entry, SL, TP based on variant.

        Reference: cerebus_dual_engine.md Section II (Target Interplay Hierarchy)

        Returns:
            (entry, sl, tp1, tp2)
        """
        body_price = bar.body_abs  # body size in price units
        self.p90_body_price = body_price
        self.p90_body_pips = body_price / self.pip_size

        entry = bar.close

        if variant == P90Variant.INITIAL:
            # Base 80: SL = 80% of P90 body from close
            # TP1 = -25% AR, TP2 = -50% AR
            sl_offset = body_price * 0.80
            ar_target_1 = self.ar_price * 0.25
            ar_target_2 = self.ar_price * 0.50

            if direction == TradeDirection.LONG:
                sl = entry - sl_offset
                tp1 = entry + ar_target_1
                tp2 = entry + ar_target_2
            else:
                sl = entry + sl_offset
                tp1 = entry - ar_target_1
                tp2 = entry - ar_target_2

        elif variant == P90Variant.CASCADE:
            # Cascade: SL = 168% of NEW P90 body
            # Target = -25% AR and -50% AR (same as initial)
            sl_offset = body_price * 1.68
            ar_target_1 = self.ar_price * 0.25
            ar_target_2 = self.ar_price * 0.50

            if direction == TradeDirection.LONG:
                sl = entry - sl_offset
                tp1 = entry + ar_target_1
                tp2 = entry + ar_target_2
            else:
                sl = entry + sl_offset
                tp1 = entry - ar_target_1
                tp2 = entry - ar_target_2

        else:
            # Fallback = Initial params
            sl_offset = body_price * 0.80
            if direction == TradeDirection.LONG:
                sl = entry - sl_offset
                tp1 = entry + self.ar_price * 0.25
                tp2 = entry + self.ar_price * 0.50
            else:
                sl = entry + sl_offset
                tp1 = entry - self.ar_price * 0.25
                tp2 = entry - self.ar_price * 0.50

        # ── STRUCTURAL SL FIX: Enforce P90 Extreme + Min Buffer Floor ──
        # The 80%/168% body SL is the THEORETICAL invalidation point.
        # In live execution, the SL must be at the P90 signal candle extreme
        # plus a spread buffer, with a per-asset minimum floor.
        # Reference: Architect Directive 2026-06-02 (P90 SL fix)
        raw_sl = sl
        if direction == TradeDirection.LONG:
            # SL = Low of P90 candle minus spread buffer
            extreme_sl = bar.low - self.spread_buffer
            # Use max of body-based and extreme-based (more conservative)
            sl = min(sl, extreme_sl)  # lower SL = more conservative for LONG
            if sl > entry - (self.min_sl_buffer * self.pip_size):
                sl = entry - (self.min_sl_buffer * self.pip_size)
        else:
            # SL = High of P90 candle plus spread buffer
            extreme_sl = bar.high + self.spread_buffer
            # Use min of body-based and extreme-based (more conservative)
            sl = max(sl, extreme_sl)  # higher SL = more conservative for SHORT
            if sl < entry + (self.min_sl_buffer * self.pip_size):
                sl = entry + (self.min_sl_buffer * self.pip_size)

        return entry, sl, tp1, tp2

    # ── Main Processing Loop ─────────────────────────────────────────

    def process_bar(self, bar: Bar) -> Optional[P90Signal]:
        """
        Process each M5 bar through P90 engine.

        Reference: cerebus_p90.md Section VI (4-State Machine with P90 integration),
                   cerebus_dual_engine.md Section III (Decision Gate)

        Returns:
            P90Signal on events (ENTRY, TP_HIT, SL_HIT, EWS_EXIT, 12PM_EXIT)
        """
        if not self.session_active:
            return None

        # Extract EST hour
        est_hour = (bar.timestamp.hour - 5) % 24
        self.last_bar_time = bar.timestamp

        # ── EWS Detection (can fire in SEARCH or IN_TRADE) ───────────
        # Opposite P90 at target = exit signal, NOT reversal entry
        # Reference: cerebus_p90.md Section III.3 (EWS P90)
        if self.state == EngineState.IN_TRADE and self._is_p90(bar, est_hour):
            bar_dir = TradeDirection.LONG if bar.body > 0 else TradeDirection.SHORT
            if bar_dir != self.direction and self._is_boundary_breach(bar):
                # Opposite direction P90 = EWS exit
                # Save state before _reset_state() zeros everything
                _entry = self.entry_price
                _sl = self.sl_price
                _tp1 = self.tp1_price
                _var = self.active_variant
                _dir = self.direction
                self._reset_state()
                sig = P90Signal(
                    event="EWS_EXIT",
                    variant=P90Variant.EWS,
                    direction=_dir,
                    entry_price=_entry,
                    sl_price=_sl,
                    tp_price=_tp1,
                    p90_body_pips=self.p90_body_pips,
                    timestamp=bar.timestamp,
                    reason="EWS: Opposite P90 at target — force close, NOT reversal"
                )
                self.signal_log.append(sig)
                self.logger.info(f"EWS EXIT: opposite P90 detected, closing position")
                return sig

        # ── STATE: SEARCH ──────────────────────────────────────────────
        if self.state == EngineState.SEARCH:
            # Check if P90 breach
            if self._is_p90(bar, est_hour) and self._is_boundary_breach(bar):
                direction = TradeDirection.LONG if bar.body > 0 else TradeDirection.SHORT

                # Detect variant
                variant = self._detect_variant(bar, est_hour)

                # Calculate trade params
                entry, sl, tp1, tp2 = self._calc_trade_params(bar, variant, direction)

                # Set state
                self.state = EngineState.IN_TRADE
                self.direction = direction
                self.active_variant = variant
                self.entry_price = entry
                self.sl_price = sl
                self.tp1_price = tp1
                self.tp2_price = tp2
                self.p90_count += 1
                # ── 80% Kill Switch: save P90 signal candle extremes ──
                # Kill switch triggers if next M5 close inside 80% of P90 body
                self.p90_kill_high = bar.high
                self.p90_kill_low = bar.low
                self.p90_kill_entry = entry
                self.p90_kill_body = bar.body_abs

                dir_str = "LONG" if direction == TradeDirection.LONG else "SHORT"
                tp1_str = f"{tp1:.5f}" if tp1 is not None else "N/A"
                tp2_str = f"{tp2:.5f}" if tp2 is not None else "N/A"
                self.logger.info(
                    f"ENTRY [{variant.value}]: {dir_str} @ {entry:.5f}, "
                    f"SL={sl:.5f}, TP1={tp1_str}, TP2={tp2_str}"
                )

                sig = P90Signal(
                    event="ENTRY",
                    variant=variant,
                    direction=direction,
                    entry_price=entry,
                    sl_price=sl,
                    tp_price=tp1,
                    tp2_price=tp2,
                    p90_body_pips=self.p90_body_pips,
                    timestamp=bar.timestamp,
                    reason=f"P90 {variant.value}: body >= threshold, "
                           f"boundary breach, entry on close"
                )
                self.signal_log.append(sig)
                return sig

        # ── STATE: IN_TRADE ────────────────────────────────────────────
        elif self.state == EngineState.IN_TRADE:
            # ── 80% Kill Switch (intra-candle invalidation) ──
            # If the very next M5 candle closes inside 80% of the P90 body,
            # the momentum has failed. Kill immediately.
            if self.p90_kill_body > 0:
                kill_80_pct = self.p90_kill_body * self.kill_switch_body_pct
                if self.direction == TradeDirection.LONG:
                    kill_level = self.p90_kill_entry - kill_80_pct
                    if bar.close <= kill_level:
                        _entry = self.entry_price; _sl = self.sl_price
                        _tp1 = self.tp1_price; _tp2 = self.tp2_price
                        _var = self.active_variant; _dir = self.direction
                        self._reset_state()
                        sig = P90Signal(
                            event="KILL_SWITCH",
                            variant=_var,
                            direction=_dir,
                            entry_price=_entry,
                            sl_price=_sl,
                            tp_price=_tp1,
                            p90_body_pips=self.p90_body_pips,
                            timestamp=bar.timestamp,
                            reason="80% Kill Switch: close inside P90 body"
                        )
                        self.signal_log.append(sig)
                        self.logger.info("KILL SWITCH (80%%): close=%.5f <= kill_level=%.5f", bar.close, kill_level)
                        return sig
                else:  # SHORT
                    kill_level = self.p90_kill_entry + kill_80_pct
                    if bar.close >= kill_level:
                        _entry = self.entry_price; _sl = self.sl_price
                        _tp1 = self.tp1_price; _tp2 = self.tp2_price
                        _var = self.active_variant; _dir = self.direction
                        self._reset_state()
                        sig = P90Signal(
                            event="KILL_SWITCH",
                            variant=_var,
                            direction=_dir,
                            entry_price=_entry,
                            sl_price=_sl,
                            tp_price=_tp1,
                            p90_body_pips=self.p90_body_pips,
                            timestamp=bar.timestamp,
                            reason="80% Kill Switch: close inside P90 body"
                        )
                        self.signal_log.append(sig)
                        self.logger.info("KILL SWITCH (80%%): close=%.5f >= kill_level=%.5f", bar.close, kill_level)
                        return sig

            if self.direction == TradeDirection.LONG:
                # TP2 check first (it's further out)
                if self.tp2_price and bar.high >= self.tp2_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP2 (-50% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP2 HIT (-50% AR): exit={}".format(self.tp2_price if self.tp2_price is not None else "N/A"))
                    return sig

                # TP1 check
                if self.tp1_price and bar.high >= self.tp1_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        tp2_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP1 (-25% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP1 HIT (-25% AR): exit={}".format(self.tp1_price if self.tp1_price is not None else "N/A"))
                    return sig

                # SL check (CLOSE ONLY)
                if bar.close <= self.sl_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_state()
                    sig = P90Signal(
                        event="SL_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="SL hit (80% P90 body, close-only)"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("SL HIT: exit={}".format(_sl if _sl is not None else "N/A"))
                    return sig

            else:  # SHORT
                # TP2 check
                if self.tp2_price and bar.low <= self.tp2_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP2 (-50% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP2 HIT (-50% AR): exit={}".format(self.tp2_price if self.tp2_price is not None else "N/A"))
                    return sig

                # TP1 check
                if self.tp1_price and bar.low <= self.tp1_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_state()
                    sig = P90Signal(
                        event="TP_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        tp2_price=_tp2,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="TP1 (-25% AR) hit"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("TP1 HIT (-25% AR): exit={}".format(self.tp1_price if self.tp1_price is not None else "N/A"))
                    return sig

                # SL check (CLOSE ONLY)
                if bar.close >= self.sl_price:
                    _entry = self.entry_price; _sl = self.sl_price
                    _tp1 = self.tp1_price; _tp2 = self.tp2_price
                    _var = self.active_variant; _dir = self.direction
                    self._reset_state()
                    sig = P90Signal(
                        event="SL_HIT",
                        variant=_var,
                        direction=_dir,
                        entry_price=_entry,
                        sl_price=_sl,
                        tp_price=_tp1,
                        p90_body_pips=self.p90_body_pips,
                        timestamp=bar.timestamp,
                        reason="SL hit (80% P90 body, close-only)"
                    )
                    self.signal_log.append(sig)
                    self.logger.info("SL HIT: exit={}".format(_sl if _sl is not None else "N/A"))
                    return sig

        return None

    # ── State Reset ────────────────────────────────────────────────────

    def _reset_state(self) -> None:
        """Reset to SEARCH, record cascade timing."""
        self.last_p90_exit_time = self.last_bar_time
        self.state = EngineState.SEARCH
        self.direction = TradeDirection.FLAT
        self.entry_price = None
        self.sl_price = None
        self.tp1_price = None
        self.tp2_price = None
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0
        self.p90_kill_high = None
        self.p90_kill_low = None
        self.p90_kill_entry = None
        self.p90_kill_body = 0.0

    def hard_exit(self) -> None:
        """12:00 PM EST forced termination."""
        self.session_active = False
        self.state = EngineState.SEARCH
        self.logger.info("Hard exit: 12 PM EST — session terminated")

    def get_status(self) -> Dict:
        """Return current engine state for monitoring."""
        return {
            "state": self.state.value,
            "variant": self.active_variant.value,
            "direction": self.direction.name,
            "tier": self.tier_name,
            "asian_range_pips": round(self.asian_range_pips, 1),
            "p90_count": self.p90_count,
            "active_trade": self.state == EngineState.IN_TRADE,
            "entry": self.entry_price,
            "sl": self.sl_price,
            "tp1": self.tp1_price,
            "tp2": self.tp2_price,
        }
