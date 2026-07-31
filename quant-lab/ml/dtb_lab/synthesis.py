"""
Directional Bias Synthesis — Final Combined System
===================================================
Combines the best findings from all attempts into one clean system.

Architecture:
  Layer 1: 3-Lens Ternary (base direction + conflict filter)
  Layer 2: Pathway Tagger (GEAR_SHIFT / DELAYED / STALL / FADE detection)
  Layer 3: Temporal Squeeze (pace tracking for forced compression)

Output: Direction + Confidence + Actionable trade call
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

import sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from dtb_lab.directional_bias import DirectionalBias, BiasDirection, BiasState


class TradeAction(Enum):
    FULL_SIZE = "FULL_SIZE"
    SCALP = "SCALP"
    STAND_DOWN = "STAND_DOWN"
    COILED_WAIT = "COILED_WAIT"


@dataclass
class SynthesisResult:
    """Final trade call from the synthesis system."""
    direction: BiasDirection
    confidence: float            # 0-1
    action: TradeAction
    pathway: str                 # GEAR_SHIFT, DELAYED, BASELINE, STALL, FADE, NONE
    regime: str                  # CONFIRMED, CAUTION, FAILED
    asian_range_pips: float
    regime_ratio: float
    details: str


class DirectionalSynthesis:
    """
    Final combined directional bias system.

    Combines:
    - 3-Lens Ternary (base direction + conflict filter)
    - Pathway tagging (GEAR_SHIFT detection for high-confidence trades)
    - Temporal squeeze (pace tracking for forced compression)
    """

    def __init__(self):
        self.bias = DirectionalBias()

    def evaluate(self, bars: pd.DataFrame, symbol: str = "EURUSD") -> SynthesisResult:
        """
        Full synthesis evaluation.

        1. Run 3-Lens Ternary for base direction
        2. Detect pathway (GEAR_SHIFT, DELAYED, STALL, etc.)
        3. Apply pathway-specific confidence adjustment
        4. Output final trade call
        """
        if len(bars) < 20:
            return self._no_signal()

        bars = bars.copy()
        bars["est_hour"] = (bars.index.hour - 5) % 24

        # ── Layer 1: 3-Lens Ternary ──
        bias_result = self.bias.evaluate(bars, symbol)

        if bias_result.direction == BiasDirection.NONE:
            return SynthesisResult(
                direction=BiasDirection.NONE,
                confidence=0.0,
                action=TradeAction.STAND_DOWN,
                pathway="NONE",
                regime=bias_result.lens_c.value,
                asian_range_pips=bias_result.asian_range_pips,
                regime_ratio=bias_result.regime_ratio,
                details="No bias signal — lenses didn't fire",
            )

        # ── Layer 2: Pathway Detection ──
        pathway = self._detect_pathway(bars, bias_result)

        # ── Layer 3: Temporal Squeeze ──
        squeeze = self._detect_squeeze(bars, bias_result)

        # ── Combine into final verdict ──
        direction = bias_result.direction
        regime = bias_result.lens_c.value
        ar = bias_result.asian_range_pips
        rr = bias_result.regime_ratio

        # Base confidence from 3-Lens
        base_conf = bias_result.confidence

        # Pathway adjustment
        if pathway == "GEAR_SHIFT":
            # GEAR_SHIFT days have 84-86% accuracy — boost confidence
            confidence = min(0.90, base_conf * 1.2)
            action = TradeAction.FULL_SIZE
            detail = f"GEAR_SHIFT detected. High-confidence {direction.value} trade."

        elif pathway == "DELAYED_RESOLVER":
            # Delayed but still valid — standard size
            confidence = 0.70
            action = TradeAction.FULL_SIZE
            detail = f"DELAYED_RESOLVER. {direction.value} bias confirmed late."

        elif pathway == "MIDPOINT_STALL":
            # Stall at -25% — scalp only
            confidence = 0.40
            action = TradeAction.SCALP
            detail = f"MIDPOINT_STALL. Scalp -25% target, exit quickly."

        elif pathway == "POST_12PM_FADE":
            # Fade after target — scalp only
            confidence = 0.35
            action = TradeAction.SCALP
            detail = f"POST_12PM_FADE. Target hit but fading. Scalp only."

        elif pathway == "BASELINE":
            # Normal day — use base confidence
            if regime == "CONFIRMED":
                confidence = 0.70
                action = TradeAction.FULL_SIZE
                detail = f"BASELINE + CONFIRMED. Standard {direction.value} trade."
            else:
                confidence = 0.50
                action = TradeAction.SCALP
                detail = f"BASELINE + {regime}. Reduced size."

        else:
            confidence = base_conf
            action = TradeAction.FULL_SIZE
            detail = f"Default: {direction.value} bias, confidence={confidence:.0%}"

        # Squeeze override
        if squeeze and action == TradeAction.FULL_SIZE:
            detail += " [SQUEEZE: Compressed delivery expected]"

        return SynthesisResult(
            direction=direction,
            confidence=round(confidence, 2),
            action=action,
            pathway=pathway,
            regime=regime,
            asian_range_pips=ar,
            regime_ratio=rr,
            details=detail,
        )

    def _detect_pathway(
        self, bars: pd.DataFrame, bias_result
    ) -> str:
        """
        Detect which structural pathway the day is taking.
        Uses price action up to 12PM.
        """
        bars_12pm = bars[bars.index.hour < 17]
        if len(bars_12pm) < 20:
            return "NONE"

        session_open = bars_12pm.iloc[0]["open"]
        high_12pm = bars_12pm["high"].max()
        low_12pm = bars_12pm["low"].min()
        price_12pm = bars_12pm.iloc[-1]["close"]

        ar = bias_result.asian_range_pips
        if ar < 1:
            return "NONE"

        # MFE in bias direction
        if bias_result.direction == BiasDirection.LONG:
            mfe = (high_12pm - session_open) * 10000
        else:
            mfe = (session_open - low_12pm) * 10000

        # Predicted MFE from tier multiplier
        predicted_mfe = ar * bias_result.regime_ratio * 0.5
        if bias_result.lens_c.value == "CONFIRMED":
            predicted_mfe *= 1.5
        elif bias_result.lens_c.value == "FAILED":
            predicted_mfe *= 0.7

        # Target hit?
        if bias_result.direction == BiasDirection.LONG:
            target_25 = session_open + 0.25 * ar / 10000
            target_hit = high_12pm >= target_25
        else:
            target_25 = session_open - 0.25 * ar / 10000
            target_hit = low_12pm <= target_25

        # ── GEAR_SHIFT: MFE significantly exceeds prediction ──
        if predicted_mfe > 0 and mfe > predicted_mfe * 1.20:
            return "GEAR_SHIFT"

        # ── DELAYED_RESOLVER: Regime failed but target still hit late ──
        if (bias_result.lens_c.value in ["FAILED", "CAUTION"]
                and target_hit):
            # Check if target was hit late (after 11:30)
            late_bars = bars_12pm[bars_12pm.index.hour >= 16]  # 11:00+ EST
            if len(late_bars) > 0:
                if bias_result.direction == BiasDirection.LONG:
                    late_high = late_bars["high"].max()
                    late_hit = late_high >= target_25
                else:
                    late_low = late_bars["low"].min()
                    late_hit = late_low <= target_25
                if late_hit:
                    return "DELAYED_RESOLVER"

        # ── MIDPOINT_STALL: Target hit early but price faded ──
        if target_hit and price_12pm < (session_open + 0.5 * (high_12pm - session_open)):
            return "MIDPOINT_STALL"

        # ── POST_12PM_FADE: Target hit before 12PM but faded after ──
        if target_hit:
            post_12pm = bars[bars.index.hour >= 17]
            if len(post_12pm) > 0:
                post_close = post_12pm.iloc[-1]["close"]
                fade = abs(post_close - price_12pm) * 10000
                if fade > 3:
                    return "POST_12PM_FADE"

        return "BASELINE"

    def _detect_squeeze(
        self, bars: pd.DataFrame, bias_result
    ) -> bool:
        """
        Detect temporal squeeze: market is behind schedule and must compress.
        """
        bars_12pm = bars[bars.index.hour < 17]
        if len(bars_12pm) < 20:
            return False

        session_open = bars_12pm.iloc[0]["open"]
        high_12pm = bars_12pm["high"].max()
        low_12pm = bars_12pm["low"].min()

        # Pace at 9AM (14 UTC)
        bars_9am = bars_12pm[bars_12pm.index.hour < 14]
        if len(bars_9am) < 5:
            return False

        if bias_result.direction == BiasDirection.LONG:
            delivered = (bars_9am["high"].max() - session_open) * 10000
        else:
            delivered = (session_open - bars_9am["low"].min()) * 10000

        # Expected pace by 9AM: ~30% of total expected
        expected_total = bias_result.asian_range_pips * 2.5
        expected_by_9am = expected_total * 0.30

        if expected_by_9am > 0:
            pace = delivered / expected_by_9am
            # Squeeze if behind schedule (< 20% of expected by 9AM)
            return pace < 0.20

        return False

    def _no_signal(self) -> SynthesisResult:
        return SynthesisResult(
            direction=BiasDirection.NONE,
            confidence=0.0,
            action=TradeAction.STAND_DOWN,
            pathway="NONE",
            regime="FAILED",
            asian_range_pips=0.0,
            regime_ratio=0.0,
            details="Insufficient data",
        )


def backtest_synthesis(
    df: pd.DataFrame,
    symbol: str = "EURUSD",
) -> pd.DataFrame:
    """Run synthesis backtest on M5 data."""
    synth = DirectionalSynthesis()
    df = df.copy()
    df['est_hour'] = (df.index.hour - 5) % 24
    df['trade_date'] = df.index.date

    results = []
    for date, day_bars in df.groupby("trade_date"):
        if len(day_bars) < 50:
            continue

        bars_12pm = day_bars[day_bars.index.hour < 17]
        if len(bars_12pm) < 20:
            continue

        result = synth.evaluate(bars_12pm, symbol)

        # Actual outcome
        session_open = bars_12pm.iloc[0]["open"]
        price_12pm = bars_12pm.iloc[-1]["close"]

        dir_correct = (
            (result.direction == BiasDirection.LONG and price_12pm > session_open)
            or (result.direction == BiasDirection.SHORT and price_12pm < session_open)
        ) if result.direction != BiasDirection.NONE else None

        results.append({
            "date": str(date),
            "direction": result.direction.value,
            "confidence": result.confidence,
            "action": result.action.value,
            "pathway": result.pathway,
            "regime": result.regime,
            "asian_range_pips": result.asian_range_pips,
            "regime_ratio": result.regime_ratio,
            "direction_correct": 1 if dir_correct else (0 if dir_correct is not None else None),
            "details": result.details,
        })

    return pd.DataFrame(results)


def report(results: pd.DataFrame, symbol: str):
    """Generate synthesis report."""
    if len(results) == 0:
        print("No results!")
        return

    print("=" * 60)
    print(f"DIRECTIONAL BIAS SYNTHESIS — FINAL REPORT ({symbol})")
    print("=" * 60)
    print(f"\nTotal days: {len(results)}")

    signaled = results[results["direction"] != "NONE"]
    print(f"Days with signal: {len(signaled)}")

    if len(signaled) > 0:
        correct = signaled[signaled["direction_correct"] == 1]
        acc = len(correct) / len(signaled) * 100
        print(f"Overall direction accuracy: {acc:.1f}%")

    # By action
    print(f"\n── BY ACTION ──")
    for action in signaled["action"].unique():
        ad = signaled[signaled["action"] == action]
        if len(ad) > 0:
            ac = ad[ad["direction_correct"] == 1]
            acc = len(ac) / len(ad) * 100
            print(f"  {action:15s}: {len(ad):4d} days, acc={acc:.1f}%")

    # By pathway
    print(f"\n── BY PATHWAY ──")
    for pathway in signaled["pathway"].unique():
        pd = signaled[signaled["pathway"] == pathway]
        if len(pd) > 0:
            pc = pd[pd["direction_correct"] == 1]
            pacc = len(pc) / len(pd) * 100
            print(f"  {pathway:20s}: {len(pd):4d} days, acc={pacc:.1f}%")

    # By confidence bucket
    print(f"\n── BY CONFIDENCE ──")
    for lo, hi, label in [(0.0, 0.4, "LOW"), (0.4, 0.7, "MEDIUM"), (0.7, 1.0, "HIGH")]:
        cd = signaled[(signaled["confidence"] >= lo) & (signaled["confidence"] < hi)]
        if len(cd) > 0:
            cc = cd[cd["direction_correct"] == 1]
            cacc = len(cc) / len(cd) * 100
            print(f"  {label:8s} ({lo:.1f}-{hi:.1f}): {len(cd):4d} days, acc={cacc:.1f}%")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    from pathlib import Path
    RAW_DATA_DIR = Path("../data")

    for sym in ["EURUSD", "USDCHF"]:
        p = RAW_DATA_DIR / f"{sym}_M5.csv"
        if not p.exists():
            print(f"SKIP {sym}: no data")
            continue
        df = pd.read_csv(p)
        df['dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        df = df.dropna(subset=['dt']).set_index('dt').sort_index()

        results = backtest_synthesis(df, sym)
        if len(results) > 0:
            report(results, sym)
            results.to_csv(f"dtb_lab/synthesis_{sym}.csv", index=False)
