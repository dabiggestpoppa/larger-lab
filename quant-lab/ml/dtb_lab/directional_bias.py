"""
3-Lens Ternary Directional Bias Engine
=======================================
Implements the full directional bias system from the CEREBUS FX v4 Manual.

3 Lenses:
  Lens A (Structural): First M5 close outside Asian Band → direction
  Lens B (Kinetic): First P90 (body >= 4.6p) between 2-6 AM → momentum
  Lens C (Volume): 9 AM Regime Ratio (3AM-9AM range / Asian Range) → conviction

Ternary Logic Matrix:
  STATE 1 (9/9 LOCK):     A == B AND C == CONFIRMED → Full size, deep targets
  STATE 2 (CONFLICT):     A != B → Fakeout/Chop → STAND DOWN
  STATE 3 (EXHAUSTION):   A == B BUT C == FAILED → Scalp -25%, exit
  STATE 4 (COILED):       A == NONE AND B == NONE BUT C == CONFIRMED → 2H Hold

Usage:
    from dtb_lab.directional_bias import DirectionalBias
    bias = DirectionalBias()
    result = bias.evaluate(m5_bars, symbol="EURUSD")
    # result.state, result.direction, result.confidence, result.action
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum


class BiasDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class BiasState(Enum):
    LOCK = "9/9_LOCK"           # A == B AND C == CONFIRMED
    CONFLICT = "KINETIC_CONFLICT"  # A != B
    EXHAUSTION = "EXHAUSTION"   # A == B BUT C == FAILED
    COILED = "COILED_SPRING"    # A == NONE, B == NONE, C == CONFIRMED
    NO_SIGNAL = "NO_SIGNAL"     # No bias yet


class RegimeState(Enum):
    CONFIRMED = "CONFIRMED"     # Ratio >= 1.5x
    CAUTION = "CAUTION"         # Ratio 1.45x - 1.49x
    FAILED = "FAILED"           # Ratio < 1.45x


@dataclass
class BiasResult:
    """Result of the 3-Lens Ternary Bias evaluation."""
    state: BiasState
    direction: BiasDirection
    confidence: float            # 0-1 confidence score
    action: str                  # Human-readable action
    lens_a: BiasDirection        # Structural break direction
    lens_a_time: Optional[str]   # Time of first M5 close outside band
    lens_b: BiasDirection        # P90 momentum direction
    lens_b_time: Optional[str]   # Time of first P90
    lens_c: RegimeState          # 9AM regime state
    regime_ratio: float          # 9AM range / Asian Range
    asian_range_pips: float      # Asian Range size
    details: str                 # Full explanation


class DirectionalBias:
    """
    3-Lens Ternary Directional Bias Engine.

    Lens A: First M5 close outside Asian Band (7PM-3AM EST)
    Lens B: First P90 candle (body >= 4.6p) between 2-6 AM EST
    Lens C: 9 AM Regime Ratio = Daily Range (3AM-9AM) / Asian Range
    """

    # P90 body threshold in pips
    P90_BODY_THRESHOLD = 4.6

    # Regime ratio thresholds
    CONFIRMED_THRESHOLD = 1.50
    CAUTION_THRESHOLD = 1.45

    def evaluate(
        self,
        bars: pd.DataFrame,
        symbol: str = "EURUSD",
    ) -> BiasResult:
        """
        Evaluate the 3-Lens Ternary Bias on M5 data.

        Args:
            bars: M5 OHLCV DataFrame with DatetimeIndex (UTC)
            symbol: Trading symbol

        Returns:
            BiasResult with state, direction, confidence, and action
        """
        if len(bars) < 20:
            return self._no_signal_result()

        bars = bars.copy()
        bars["est_hour"] = (bars.index.hour - 5) % 24
        bars["est_minute"] = bars.index.minute

        # ── Compute Asian Range ──
        asian_mask = (bars["est_hour"] >= 19) | (bars["est_hour"] < 3)
        asian_bars = bars[asian_mask]

        if len(asian_bars) < 2:
            return self._no_signal_result()

        ah = asian_bars["high"].max()
        al = asian_bars["low"].min()
        asian_range = ah - al
        asian_range_pips = asian_range * 10000

        if asian_range_pips < 1:
            return self._no_signal_result()

        # ── Lens A: First M5 close outside Asian Band (after 3AM = 8UTC) ──
        lens_a, lens_a_time = self._evaluate_lens_a(bars, ah, al)

        # ── Lens B: First P90 (body >= 4.6p) between 2-6 AM EST (7-11 UTC) ──
        lens_b, lens_b_time = self._evaluate_lens_b(bars)

        # ── Lens C: 9 AM Regime Ratio ──
        lens_c, regime_ratio = self._evaluate_lens_c(bars, asian_range)

        # ── Ternary Logic Matrix ──
        state, direction, confidence, action, details = self._ternary_matrix(
            lens_a, lens_b, lens_c, regime_ratio
        )

        return BiasResult(
            state=state,
            direction=direction,
            confidence=confidence,
            action=action,
            lens_a=lens_a,
            lens_a_time=lens_a_time,
            lens_b=lens_b,
            lens_b_time=lens_b_time,
            lens_c=lens_c,
            regime_ratio=round(regime_ratio, 3),
            asian_range_pips=round(asian_range_pips, 2),
            details=details,
        )

    def _evaluate_lens_a(
        self, bars: pd.DataFrame, ah: float, al: float
    ) -> Tuple[BiasDirection, Optional[str]]:
        """
        Lens A: First M5 close outside Asian Band after 3AM EST (8 UTC).
        Returns (direction, time_string).
        """
        # Filter bars after 3AM EST (8:00 UTC)
        post_3am = bars[bars.index.hour >= 8]

        for idx, bar in post_3am.iterrows():
            close = bar["close"]
            if close > ah:
                return BiasDirection.LONG, idx.strftime("%H:%M")
            elif close < al:
                return BiasDirection.SHORT, idx.strftime("%H:%M")

        return BiasDirection.NONE, None

    def _evaluate_lens_b(
        self, bars: pd.DataFrame
    ) -> Tuple[BiasDirection, Optional[str]]:
        """
        Lens B: First P90 candle (body >= 4.6 pips) between 2-6 AM EST (7-11 UTC).
        Returns (direction, time_string).
        """
        # Filter bars between 2AM-6AM EST (7:00-11:00 UTC)
        p9o_window = bars[(bars.index.hour >= 7) & (bars.index.hour < 11)]

        for idx, bar in p9o_window.iterrows():
            body = abs(bar["close"] - bar["open"])
            body_pips = body * 10000

            if body_pips >= self.P90_BODY_THRESHOLD:
                if bar["close"] > bar["open"]:
                    return BiasDirection.LONG, idx.strftime("%H:%M")
                else:
                    return BiasDirection.SHORT, idx.strftime("%H:%M")

        return BiasDirection.NONE, None

    def _evaluate_lens_c(
        self, bars: pd.DataFrame, asian_range: float
    ) -> Tuple[RegimeState, float]:
        """
        Lens C: 9 AM Regime Ratio = Daily Range (3AM-9AM) / Asian Range.
        Returns (regime_state, ratio).
        """
        # Daily range from 3AM (8UTC) to 9AM (14UTC)
        daily_window = bars[(bars.index.hour >= 8) & (bars.index.hour < 14)]

        if len(daily_window) < 2:
            return RegimeState.FAILED, 0.0

        daily_range = daily_window["high"].max() - daily_window["low"].min()

        if asian_range <= 0:
            return RegimeState.FAILED, 0.0

        ratio = daily_range / asian_range

        if ratio >= self.CONFIRMED_THRESHOLD:
            return RegimeState.CONFIRMED, ratio
        elif ratio >= self.CAUTION_THRESHOLD:
            return RegimeState.CAUTION, ratio
        else:
            return RegimeState.FAILED, ratio

    def _ternary_matrix(
        self,
        lens_a: BiasDirection,
        lens_b: BiasDirection,
        lens_c: RegimeState,
        regime_ratio: float,
    ) -> Tuple[BiasState, BiasDirection, float, str, str]:
        """
        The Ternary Logic Matrix — combines all 3 lenses into a verdict.
        """

        # ── STATE 1: THE 9/9 LOCK ──
        if (lens_a != BiasDirection.NONE
                and lens_b != BiasDirection.NONE
                and lens_a == lens_b
                and lens_c == RegimeState.CONFIRMED):
            return (
                BiasState.LOCK,
                lens_a,
                0.97,
                f"MAXIMUM CONVICTION (97%): {lens_a.value} bias locked. "
                f"Regime CONFIRMED ({regime_ratio:.2f}x). "
                f"Full size, hold to deep DTB target (-50%/-100% AR).",
                f"Lens A ({lens_a.value}) == Lens B ({lens_b.value}) AND "
                f"Lens C (CONFIRMED, {regime_ratio:.2f}x)"
            )

        # ── STATE 2: KINETIC CONFLICT ──
        if (lens_a != BiasDirection.NONE
                and lens_b != BiasDirection.NONE
                and lens_a != lens_b):
            return (
                BiasState.CONFLICT,
                BiasDirection.NONE,
                0.0,
                f"FAKEOUT EXPOSED: Lens A={lens_a.value}, Lens B={lens_b.value}. "
                f"Structural and kinetic conflict. STAND DOWN.",
                f"Lens A ({lens_a.value}) != Lens B ({lens_b.value}) → "
                f"Chop/fakeout detected"
            )

        # ── STATE 3: EXHAUSTION ──
        if (lens_a != BiasDirection.NONE
                and lens_a == lens_b
                and lens_c == RegimeState.FAILED):
            return (
                BiasState.EXHAUSTION,
                lens_a,
                0.3,
                f"EXHAUSTION BREAKOUT: {lens_a.value} bias but Regime FAILED "
                f"({regime_ratio:.2f}x). Scalp -25% target, exit immediately.",
                f"Lens A ({lens_a.value}) == Lens B ({lens_b.value}) BUT "
                f"Lens C (FAILED, {regime_ratio:.2f}x)"
            )

        # ── STATE 4: COILED SPRING ──
        if (lens_a == BiasDirection.NONE
                and lens_b == BiasDirection.NONE
                and lens_c == RegimeState.CONFIRMED):
            return (
                BiasState.COILED,
                BiasDirection.NONE,
                0.5,
                f"COILED SPRING: No structural break yet, but Regime CONFIRMED "
                f"({regime_ratio:.2f}x). Switch to Setup 5 (2-Hour Hold).",
                f"A=NONE, B=NONE, C=CONFIRMED ({regime_ratio:.2f}x)"
            )

        # ── NO SIGNAL ──
        return (
            BiasState.NO_SIGNAL,
            BiasDirection.NONE,
            0.0,
            "NO SIGNAL: Insufficient data for bias determination.",
            f"A={lens_a.value}, B={lens_b.value}, C={lens_c.value}"
        )

    def _no_signal_result(self) -> BiasResult:
        return BiasResult(
            state=BiasState.NO_SIGNAL,
            direction=BiasDirection.NONE,
            confidence=0.0,
            action="NO SIGNAL: Insufficient data",
            lens_a=BiasDirection.NONE,
            lens_a_time=None,
            lens_b=BiasDirection.NONE,
            lens_b_time=None,
            lens_c=RegimeState.FAILED,
            regime_ratio=0.0,
            asian_range_pips=0.0,
            details="Not enough bars or no Asian Range detected",
        )


def backtest_directional_bias(
    bars: pd.DataFrame,
    symbol: str = "EURUSD",
) -> pd.DataFrame:
    """
    Backtest the 3-Lens Ternary Bias on historical M5 data.

    For each trading day, evaluates the bias and compares against
    actual daily outcome (did price move in the predicted direction?).

    Returns DataFrame with daily bias results and accuracy metrics.
    """
    bias = DirectionalBias()
    bars = bars.copy()
    bars["est_hour"] = (bars.index.hour - 5) % 24
    bars["trade_date"] = bars.index.date

    results = []
    for date, day_bars in bars.groupby("trade_date"):
        if len(day_bars) < 50:  # Need at least a few hours of data
            continue

        # Evaluate bias at end of day (using all bars up to 12PM)
        day_bars_up_to_noon = day_bars[day_bars.index.hour < 17]
        if len(day_bars_up_to_noon) < 20:
            continue

        result = bias.evaluate(day_bars_up_to_noon, symbol)

        # Actual outcome: did price move in the predicted direction?
        if len(day_bars) > 0:
            day_open = day_bars.iloc[0]["open"]
            day_close = day_bars.iloc[-1]["close"]
            day_high = day_bars["high"].max()
            day_low = day_bars["low"].min()

            actual_direction = (
                BiasDirection.LONG if day_close > day_open
                else BiasDirection.SHORT
            )

            # Did the bias direction match the actual daily direction?
            direction_correct = (
                result.direction == actual_direction
                if result.direction != BiasDirection.NONE
                else None
            )

            # Did the day hit the -25% target in the bias direction?
            asian_range = result.asian_range_pips
            if asian_range > 0 and result.direction == BiasDirection.LONG:
                target_25 = day_open + 0.25 * asian_range / 10000
                target_hit = day_high >= target_25
            elif asian_range > 0 and result.direction == BiasDirection.SHORT:
                target_25 = day_open - 0.25 * asian_range / 10000
                target_hit = day_low <= target_25
            else:
                target_hit = None

            results.append({
                "date": str(date),
                "state": result.state.value,
                "direction": result.direction.value,
                "confidence": result.confidence,
                "regime_ratio": result.regime_ratio,
                "asian_range_pips": result.asian_range_pips,
                "actual_direction": actual_direction.value,
                "direction_correct": direction_correct,
                "target_25_hit": target_hit,
                "lens_a": result.lens_a.value,
                "lens_b": result.lens_b.value,
                "lens_c": result.lens_c.value,
            })

    return pd.DataFrame(results)


def generate_accuracy_report(results: pd.DataFrame) -> str:
    """Generate a human-readable accuracy report from backtest results."""
    if len(results) == 0:
        return "No results to report."

    lines = []
    lines.append("=" * 60)
    lines.append("3-LENS TERNARY DIRECTIONAL BIAS — ACCURACY REPORT")
    lines.append("=" * 60)
    lines.append(f"\nTotal trading days: {len(results)}")

    # Overall accuracy (days with a signal)
    signaled = results[results["direction"] != "NONE"]
    if len(signaled) > 0:
        correct = signaled[signaled["direction_correct"] == True]
        accuracy = len(correct) / len(signaled) * 100
        lines.append(f"Days with signal: {len(signaled)}")
        lines.append(f"Direction accuracy: {accuracy:.1f}%")

    # By state
    lines.append("\n── BY STATE ──")
    for state in results["state"].unique():
        state_data = results[results["state"] == state]
        state_signaled = state_data[state_data["direction"] != "NONE"]
        if len(state_signaled) > 0:
            state_correct = state_signaled[state_signaled["direction_correct"] == True]
            state_acc = len(state_correct) / len(state_signaled) * 100
            lines.append(
                f"  {state}: {len(state_data)} days, "
                f"{len(state_signaled)} signaled, "
                f"accuracy={state_acc:.1f}%"
            )
        else:
            lines.append(f"  {state}: {len(state_data)} days, no signals")

    # Target hit rate
    target_data = results[results["target_25_hit"].notna()]
    if len(target_data) > 0:
        hits = target_data[target_data["target_25_hit"] == True]
        hit_rate = len(hits) / len(target_data) * 100
        lines.append(f"\nTarget -25% hit rate: {hit_rate:.1f}% ({len(hits)}/{len(target_data)})")

    # By regime
    lines.append("\n── BY REGIME ──")
    for regime in results["lens_c"].unique():
        regime_data = results[results["lens_c"] == regime]
        regime_signaled = regime_data[regime_data["direction"] != "NONE"]
        if len(regime_signaled) > 0:
            regime_correct = regime_signaled[regime_signaled["direction_correct"] == True]
            regime_acc = len(regime_correct) / len(regime_signaled) * 100
            lines.append(
                f"  {regime}: {len(regime_data)} days, "
                f"accuracy={regime_acc:.1f}%"
            )

    # Lens A vs B conflict analysis
    conflict_days = results[
        (results["lens_a"] != "NONE")
        & (results["lens_b"] != "NONE")
        & (results["lens_a"] != results["lens_b"])
    ]
    if len(conflict_days) > 0:
        conflict_correct = conflict_days[conflict_days["direction_correct"] == True]
        conflict_acc = len(conflict_correct) / len(conflict_days) * 100
        lines.append(
            f"\nA vs B CONFLICT days: {len(conflict_days)}, "
            f"accuracy={conflict_acc:.1f}% (should be < 50%)"
        )

    # Aligned days (A == B)
    aligned_days = results[
        (results["lens_a"] != "NONE")
        & (results["lens_a"] == results["lens_b"])
    ]
    if len(aligned_days) > 0:
        aligned_correct = aligned_days[aligned_days["direction_correct"] == True]
        aligned_acc = len(aligned_correct) / len(aligned_days) * 100
        lines.append(
            f"A == B ALIGNED days: {len(aligned_days)}, "
            f"accuracy={aligned_acc:.1f}% (should be > 80%)"
        )

    lines.append(f"\n{'='*60}")
    return "\n".join(lines)
