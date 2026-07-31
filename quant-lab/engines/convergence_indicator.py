"""
CEREBUS FX v4.0 — Convergence Indicator (Overlay)
=================================================

Standalone overlay that reads P90 Kinetic Engine (Model A) and
Symmetry Trap Structural Engine (Model B) states and emits convergence signals.

CONVERGENCE DEFINITION (CEREBUS Axioms):
  - P90 fires ENTRY signal (INITIAL or CASCADE variant)
  - Symmetry Trap is in active structural state (WAIT_RETRACE, WAIT_OCC, or IN_TRADE)
  - Both engines agree on direction (LONG vs SHORT)

CONVERGENCE STRENGTH:
  - STRONG: CASCADE variant + Symmetry Trap active
  - WEAK:   INITIAL variant + Symmetry Trap active

Engine Isolation:
  This overlay reads engine states — it does NOT modify either engine.
  P90 and Symmetry Trap remain fully independent.

Reference: cerebus_unified_topology.md (Axiom 6: Convergence Criteria)
Author: CEREBUS Ontology Reconstruction — MAD Directive 2026-05-29
Mode: Read-Only Overlay / Statistical Tracker
Trader Language: PURGED
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

# ─── ENGINE IMPORTS (read-only — no modifications) ────────────────────────

from p90_engine import (
    P90Engine,
    P90Signal,
    P90Variant,
    EngineState as P90EngineState,
    TradeDirection,
    Bar,
    DEFAULT_TIER_CONFIG,
)

from symmetry_trap import (
    SymmetryTrapEngine,
    TradeSignal as STTradeSignal,
    EngineState as STEngineState,
    SymmetryTrapEngine as _STE,  # noqa: F401 — verify import
)

# ─── CONSTANTS ────────────────────────────────────────────────────────────

# States considered "active structural" for Symmetry Trap
ST_ACTIVE_STATES = {
    STEngineState.WAIT_RETRACE,
    STEngineState.WAIT_OCC,
    STEngineState.IN_TRADE,
}

ASIAN_SESSION_END = time(3, 0)
ACTIVATION_END = time(12, 0)


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────

@dataclass
class ConvergenceSignal:
    """
    Emitted when P90 entry + Symmetry Trap active state + direction agreement.

    Fields:
        timestamp:       When convergence was detected
        direction:       LONG or SHORT (both engines must agree)
        convergence_strength: STRONG (CASCADE) or WEAK (INITIAL)
        p90_variant:     P90 variant that fired (INITIAL or CASCADE)
        st_tier:         Symmetry Trap tier (T1/T2/T3)
        st_loop:         Symmetry Trap current loop (1-5)
        st_state:        Symmetry Trap state when convergence detected
        p90_sl:          P90 stop-loss level
        p90_tp1:         P90 TP1 level (-25% AR)
        p90_tp2:         P90 TP2 level (-50% AR)
        st_sl:           Symmetry Trap stop-loss level
        st_tp:           Symmetry Trap TP level (1 AU)
        p90_entry:       P90 entry price
        st_entry:        Symmetry Trap entry price (if IN_TRADE) or None
    """
    timestamp: datetime
    direction: TradeDirection
    convergence_strength: str          # "STRONG" or "WEAK"
    p90_variant: P90Variant
    st_tier: str
    st_loop: int
    st_state: str
    p90_sl: Optional[float]
    p90_tp1: Optional[float]
    p90_tp2: Optional[float]
    st_sl: Optional[float]
    st_tp: Optional[float]
    p90_entry: float
    st_entry: Optional[float]


@dataclass
class TradeRecord:
    """Completed trade tracked by the convergence indicator."""
    entry_timestamp: datetime
    exit_timestamp: datetime
    direction: TradeDirection
    entry_price: float
    exit_price: float
    is_convergence: bool
    pnl_pips: float
    hit_tp: bool


# ─── CONVERGENCE INDICATOR ────────────────────────────────────────────────

class ConvergenceIndicator:
    """
    Standalone overlay: reads P90 + Symmetry Trap, emits convergence signals.

    This is a READ-ONLY observer — it never modifies engine behavior.

    Usage:
        indicator = ConvergenceIndicator()
        indicator.initialize_session(asian_high=1.0950, asian_low=1.0930)
        for bar in bars:
            result = indicator.process_bar(bar)
            if result:
                print(f"Convergence: {result}")
        indicator.generate_report()
    """

    def __init__(
        self,
        pip_size: float = 0.0001,
        p90_config: Optional[Dict[int, float]] = None,
        tier_config: Optional[Dict] = None,
        symbol: str = "EURUSD",
    ):
        self.pip_size = pip_size
        self.symbol = symbol
        self.logger = logging.getLogger(f"cerebus.convergence.{symbol}")

        # ── Both engines (fully independent) ──────────────────────────
        self.p90 = P90Engine(
            pip_size=pip_size,
            p90_config=p90_config,
            tier_config=tier_config,
            symbol=symbol,
        )
        self.st = SymmetryTrapEngine(
            pip_size=pip_size,
            tier_config=tier_config,
            symbol=symbol,
        )

        # ── Convergence state ─────────────────────────────────────────
        self.convergence_signals: List[ConvergenceSignal] = []
        self.active_convergence: Optional[ConvergenceSignal] = None

        # ── P90 trade tracking (convergence vs non-convergence) ───────
        self.p90_trades: List[TradeRecord] = []

        # ── Current P90 trade being monitored (for PnL tracking) ──────
        self._current_p90_trade: Optional[Dict] = None       # {entry, sl, direction, is_conv, ts}
        self._pending_convergence: Optional[ConvergenceSignal] = None

        # ── Statistics ────────────────────────────────────────────────
        self.stats = {
            "total_bars_processed": 0,
            "total_p90_entries": 0,
            "total_convergence_signals": 0,
            "strong_convergence": 0,
            "weak_convergence": 0,
            "convergence_trades": 0,
            "convergence_wins": 0,
            "convergence_losses": 0,
            "convergence_pnl_pips": 0.0,
            "non_convergence_trades": 0,
            "non_convergence_wins": 0,
            "non_convergence_losses": 0,
            "non_convergence_pnl_pips": 0.0,
        }

    # ── Session Initialization ──────────────────────────────────────

    def initialize_session(
        self,
        asian_high: float,
        asian_low: float,
    ) -> None:
        """
        Initialize both engines for the session.

        Args:
            asian_high: Asian session high price
            asian_low:  Asian session low price
        """
        self.p90.initialize_session(asian_high, asian_low)
        self.st.initialize_session(asian_high, asian_low)
        # Reset per-session convergence tracking
        self.active_convergence = None
        self._pending_convergence = None
        self._current_p90_trade = None
        self.logger.info(
            f"Convergence session initialized: "
            f"P90 tier={self.p90.tier_name}, ST tier={self.st.tier_name}"
        )

    # ── Main Processing Loop ─────────────────────────────────────────

    def process_bar(self, bar: Bar) -> Optional[ConvergenceSignal]:
        """
        Feed bar to BOTH engines and detect convergence.

        Args:
            bar: M5 OHLC candle

        Returns:
            ConvergenceSignal if convergence detected, None otherwise
        """
        self.stats["total_bars_processed"] += 1

        # ── Feed both engines (order: P90 first, then ST) ────────────
        p90_signal = self.p90.process_bar(bar)
        st_signal = self.st.process_bar(bar)

        # ── Track P90 entry for trade monitoring ─────────────────────
        if p90_signal and p90_signal.event == "ENTRY":
            self.stats["total_p90_entries"] += 1
            self._current_p90_trade = {
                "entry": p90_signal.entry_price,
                "sl": p90_signal.sl_price,
                "tp1": p90_signal.tp_price,
                "tp2": p90_signal.tp2_price,
                "direction": p90_signal.direction,
                "variant": p90_signal.variant,
                "timestamp": p90_signal.timestamp,
                "is_convergence": False,     # updated below if convergence detected
            }

            # ── Check convergence ─────────────────────────────────────
            convergence = self._check_convergence(bar, p90_signal)
            if convergence:
                self._current_p90_trade["is_convergence"] = True
                self._pending_convergence = convergence
                return convergence

        # ── Track P90 exit for PnL ───────────────────────────────────
        if p90_signal and p90_signal.event in ("TP_HIT", "SL_HIT", "EWS_EXIT", "12PM_EXIT"):
            if self._current_p90_trade is not None:
                self._record_p90_trade(p90_signal)
                self._current_p90_trade = None
                self.active_convergence = None
                self._pending_convergence = None

        return None

    # ── Convergence Detection ────────────────────────────────────────

    def _check_convergence(
        self, bar: Bar, p90_signal: P90Signal
    ) -> Optional[ConvergenceSignal]:
        """
        Detect convergence: P90 entry + ST active state + direction agreement.

        Criteria:
          1. P90 just emitted ENTRY signal
          2. Symmetry Trap state ∈ {WAIT_RETRACE, WAIT_OCC, IN_TRADE}
          3. Both engines trade direction matches

        Returns:
            ConvergenceSignal if all criteria met, None otherwise
        """
        st_state = self.st.state

        # Criterion 2: ST must be in active structural state
        if st_state not in ST_ACTIVE_STATES:
            return None

        # Criterion 3: Direction agreement
        st_direction = self.st.impulse_direction
        if st_direction == TradeDirection.FLAT:
            return None
        if st_direction != p90_signal.direction:
            return None

        # ── All criteria met → convergence detected ──────────────────
        # Strength classification
        if p90_signal.variant == P90Variant.CASCADE:
            strength = "STRONG"
            self.stats["strong_convergence"] += 1
        else:
            strength = "WEAK"
            self.stats["weak_convergence"] += 1

        self.stats["total_convergence_signals"] += 1

        signal = ConvergenceSignal(
            timestamp=bar.timestamp,
            direction=p90_signal.direction,
            convergence_strength=strength,
            p90_variant=p90_signal.variant,
            st_tier=self.st.tier_name,
            st_loop=self.st.loop_count,
            st_state=st_state.value,
            p90_sl=p90_signal.sl_price,
            p90_tp1=p90_signal.tp_price,
            p90_tp2=p90_signal.tp2_price,
            st_sl=self.st.sl_price,
            st_tp=self.st.tp_price,
            p90_entry=p90_signal.entry_price,
            st_entry=self.st.entry_price if st_state == STEngineState.IN_TRADE else None,
        )

        self.convergence_signals.append(signal)
        self.active_convergence = signal

        dir_str = "LONG" if p90_signal.direction == TradeDirection.LONG else "SHORT"
        self.logger.info(
            f"CONVERGENCE [{strength}]: {dir_str} @ {bar.close:.5f}, "
            f"P90={p90_signal.variant.value}, "
            f"ST state={st_state.value}, loop={self.st.loop_count}, "
            f"tier={self.st.tier_name}"
        )

        return signal

    # ── Trade Recording & Statistics ─────────────────────────────────

    def _record_p90_trade(self, exit_signal: P90Signal) -> None:
        """
        Record completed P90 trade for convergence vs non-convergence comparison.
        """
        trade = self._current_p90_trade
        if trade is None:
            return

        entry = trade["entry"]
        direction = trade["direction"]
        exit_price = exit_signal.entry_price  # engine stores exit at entry_price

        # Calculate PnL in pips
        if direction == TradeDirection.LONG:
            pnl_pips = (exit_price - entry) / self.pip_size
        else:
            pnl_pips = (entry - exit_price) / self.pip_size

        hit_tp = exit_signal.event == "TP_HIT"
        is_convergence = trade["is_convergence"]

        record = TradeRecord(
            entry_timestamp=trade["timestamp"],
            exit_timestamp=exit_signal.timestamp,
            direction=direction,
            entry_price=entry,
            exit_price=exit_price,
            is_convergence=is_convergence,
            pnl_pips=pnl_pips,
            hit_tp=hit_tp,
        )
        self.p90_trades.append(record)

        # Update statistics
        if is_convergence:
            self.stats["convergence_trades"] += 1
            self.stats["convergence_pnl_pips"] += pnl_pips
            if pnl_pips > 0:
                self.stats["convergence_wins"] += 1
            else:
                self.stats["convergence_losses"] += 1
        else:
            self.stats["non_convergence_trades"] += 1
            self.stats["non_convergence_pnl_pips"] += pnl_pips
            if pnl_pips > 0:
                self.stats["non_convergence_wins"] += 1
            else:
                self.stats["non_convergence_losses"] += 1

    # ── Hard Exit ────────────────────────────────────────────────────

    def hard_exit(self) -> None:
        """Force exit all positions (12:00 PM EST)."""
        self.p90.hard_exit()
        self.st.hard_exit()
        self.logger.info("Convergence indicator: hard exit — 12 PM EST")

    # ── Reporting ─────────────────────────────────────────────────────

    def generate_report(self) -> str:
        """
        Generate full convergence analysis report.

        Returns:
            Formatted report string
        """
        lines: List[str] = []
        sep = "=" * 72
        lines.append(sep)
        lines.append("  CEREBUS CONVERGENCE INDICATOR — ANALYSIS REPORT")
        lines.append(sep)
        lines.append("")

        # ── Summary ───────────────────────────────────────────────────
        s = self.stats
        lines.append("─── OVERVIEW ───────────────────────────────────────────")
        lines.append(f"  Bars processed:              {s['total_bars_processed']}")
        lines.append(f"  Total P90 entries:           {s['total_p90_entries']}")
        lines.append(f"  Convergence signals:         {s['total_convergence_signals']}")
        lines.append(f"    STRONG (CASCADE + ST):     {s['strong_convergence']}")
        lines.append(f"    WEAK (INITIAL + ST):       {s['weak_convergence']}")
        lines.append("")

        # ── Convergence Trade Performance ─────────────────────────────
        lines.append("─── CONVERGENCE TRADE PERFORMANCE ─────────────────────")
        if s["convergence_trades"] > 0:
            conv_wr = (s["convergence_wins"] / s["convergence_trades"]) * 100
            lines.append(f"  Trades:                      {s['convergence_trades']}")
            lines.append(f"  Wins / Losses:               {s['convergence_wins']} / {s['convergence_losses']}")
            lines.append(f"  Win Rate:                    {conv_wr:.1f}%")
            lines.append(f"  Net PnL:                     {s['convergence_pnl_pips']:+.1f} pips")
            avg = s["convergence_pnl_pips"] / s["convergence_trades"]
            lines.append(f"  Avg PnL per trade:           {avg:+.1f} pips")
        else:
            lines.append("  No convergence trades recorded.")
        lines.append("")

        # ── Non-Convergence Trade Performance ─────────────────────────
        lines.append("─── NON-CONVERGENCE TRADE PERFORMANCE ─────────────────")
        if s["non_convergence_trades"] > 0:
            non_conv_wr = (s["non_convergence_wins"] / s["non_convergence_trades"]) * 100
            lines.append(f"  Trades:                      {s['non_convergence_trades']}")
            lines.append(f"  Wins / Losses:               {s['non_convergence_wins']} / {s['non_convergence_losses']}")
            lines.append(f"  Win Rate:                    {non_conv_wr:.1f}%")
            lines.append(f"  Net PnL:                     {s['non_convergence_pnl_pips']:+.1f} pips")
            avg = s["non_convergence_pnl_pips"] / s["non_convergence_trades"]
            lines.append(f"  Avg PnL per trade:           {avg:+.1f} pips")
        else:
            lines.append("  No non-convergence trades recorded.")
        lines.append("")

        # ── Comparison Table ──────────────────────────────────────────
        lines.append("─── CONVERGENCE vs NON-CONVERGENCE COMPARISON ─────────")
        conv_trades = s["convergence_trades"]
        non_conv_trades = s["non_convergence_trades"]
        conv_wr = (s["convergence_wins"] / conv_trades * 100) if conv_trades > 0 else 0.0
        non_conv_wr = (s["non_convergence_wins"] / non_conv_trades * 100) if non_conv_trades > 0 else 0.0
        wr_delta = conv_wr - non_conv_wr
        pnl_delta = s["convergence_pnl_pips"] - s["non_convergence_pnl_pips"]

        header = f"  {'Metric':<30} {'Convergence':>13} {'Non-Convergence':>16} {'Delta':>10}"
        lines.append(header)
        lines.append("  " + "-" * 69)
        lines.append(
            f"  {'Trades':<30} {conv_trades:>13} {non_conv_trades:>16} {conv_trades - non_conv_trades:>+10}"
        )
        lines.append(
            f"  {'Win Rate (%)':<30} {conv_wr:>13.1f} {non_conv_wr:>16.1f} {wr_delta:>+10.1f}"
        )
        lines.append(
            f"  {'Net PnL (pips)':<30} {s['convergence_pnl_pips']:>+13.1f} "
            f"{s['non_convergence_pnl_pips']:>+16.1f} {pnl_delta:>+10.1f}"
        )
        if conv_trades > 0:
            conv_avg = s["convergence_pnl_pips"] / conv_trades
        else:
            conv_avg = 0.0
        if non_conv_trades > 0:
            non_conv_avg = s["non_convergence_pnl_pips"] / non_conv_trades
        else:
            non_conv_avg = 0.0
        lines.append(
            f"  {'Avg PnL per trade (pips)':<30} {conv_avg:>+13.1f} "
            f"{non_conv_avg:>+16.1f} {conv_avg - non_conv_avg:>+10.1f}"
        )
        lines.append("")

        # ── Convergence Signal Log ────────────────────────────────────
        if self.convergence_signals:
            lines.append("─── CONVERGENCE SIGNAL LOG ────────────────────────────")
            for i, sig in enumerate(self.convergence_signals, 1):
                dir_str = "LONG" if sig.direction == TradeDirection.LONG else "SHORT"
                lines.append(
                    f"  [{i:>3}] {sig.timestamp.strftime('%Y-%m-%d %H:%M')}  "
                    f"{dir_str:>5}  {sig.convergence_strength:>6}  "
                    f"P90={sig.p90_variant.value:<8}  "
                    f"ST={sig.st_state:<14}  "
                    f"Loop={sig.st_loop}  Tier={sig.st_tier}"
                )
                lines.append(
                    f"        Entry={sig.p90_entry:.5f}  "
                    f"P90 SL={sig.p90_sl:.5f}  "
                    f"P90 TP1={sig.p90_tp1:.5f}  P90 TP2={sig.p90_tp2:.5f}"
                )
                if sig.st_entry is not None:
                    lines.append(
                        f"        ST Entry={sig.st_entry:.5f}  "
                        f"ST SL={sig.st_sl:.5f}  ST TP={sig.st_tp:.5f}"
                    )
            lines.append("")

        lines.append(sep)
        lines.append("  END OF REPORT")
        lines.append(sep)

        report = "\n".join(lines)
        print(report)
        return report

    # ── Status ───────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Return current indicator + both engine states."""
        return {
            "symbol": self.symbol,
            "total_convergence_signals": self.stats["total_convergence_signals"],
            "active_convergence": self.active_convergence is not None,
            "p90": self.p90.get_status(),
            "symmetry_trap": self.st.get_status(),
            "stats": dict(self.stats),
        }


# ─── STANDALONE BACKTEST ───────────────────────────────────────────────────

def run_convergence_backtest(csv_path: str) -> ConvergenceIndicator:
    """
    Standalone backtest: load CSV, feed through both engines, collect results.

    CSV expected columns: timestamp, open, high, low, close, volume
    Timestamp format: YYYY-MM-DD HH:MM:SS or ISO 8601

    Args:
        csv_path: Path to OHLCV CSV file

    Returns:
        ConvergenceIndicator with full results (call generate_report() on it)
    """
    logger = logging.getLogger("cerebus.convergence.backtest")
    logger.info(f"Loading CSV: {csv_path}")

    # ── Load CSV ──────────────────────────────────────────────────────
    bars: List[Bar] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row["timestamp"].strip()
            # Try multiple timestamp formats
            ts: Optional[datetime] = None
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S%z",
            ):
                try:
                    ts = datetime.strptime(ts_str, fmt)
                    break
                except ValueError:
                    continue
            if ts is None:
                raise ValueError(f"Cannot parse timestamp: {ts_str}")

            bars.append(Bar(
                timestamp=ts,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            ))

    logger.info(f"Loaded {len(bars)} bars")

    if not bars:
        raise ValueError("No bars loaded from CSV")

    # ── Identify sessions (gaps > 4h = new session) ──────────────────
    # Each session = one day of M5 data
    sessions: List[List[Bar]] = []
    current_session: List[Bar] = [bars[0]]

    for i in range(1, len(bars)):
        gap = bars[i].timestamp - bars[i - 1].timestamp
        if gap > timedelta(hours=4):
            sessions.append(current_session)
            current_session = [bars[i]]
        else:
            current_session.append(bars[i])
    sessions.append(current_session)

    logger.info(f"Identified {len(sessions)} sessions")

    # ── Create indicator ──────────────────────────────────────────────
    indicator = ConvergenceIndicator()
    total_conv_before = 0

    # ── Run each session ─────────────────────────────────────────────
    for sess_idx, session_bars in enumerate(sessions):
        if not session_bars:
            continue

        # Determine Asian Range: use bars prior to 03:00 EST in this session
        # For simplicity, use first bar as proxy for Asian range
        # In production, you'd compute actual Asian range from 19:00-03:00
        session_high = max(b.high for b in session_bars)
        session_low = min(b.low for b in session_bars)

        # Use a tighter range: first few bars or full pre-03 range
        # Fallback: use 50% of session range as proxy for Asian range
        full_range = session_high - session_low
        asian_proxy_high = session_low + full_range * 0.6
        asian_proxy_low = session_low + full_range * 0.4

        # Ensure range is at least 5 pips
        min_range = 5 * indicator.pip_size
        if asian_proxy_high - asian_proxy_low < min_range:
            mid = (asian_proxy_high + asian_proxy_low) / 2
            asian_proxy_high = mid + min_range / 2
            asian_proxy_low = mid - min_range / 2

        indicator.initialize_session(asian_proxy_high, asian_proxy_low)

        for bar in session_bars:
            indicator.process_bar(bar)

        conv_this_session = (
            indicator.stats["total_convergence_signals"] - total_conv_before
        )
        total_conv_before = indicator.stats["total_convergence_signals"]
        logger.info(
            f"Session {sess_idx + 1}: {len(session_bars)} bars, "
            f"{conv_this_session} convergence signals"
        )

    # ── Print report ─────────────────────────────────────────────────
    print()
    indicator.generate_report()

    return indicator


# ─── CLI ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python convergence_indicator.py <csv_path>")
        print("  CSV columns: timestamp, open, high, low, close, volume")
        sys.exit(1)

    csv_file = sys.argv[1]
    logging.basicConfig(level=logging.WARNING)
    run_convergence_backtest(csv_file)
