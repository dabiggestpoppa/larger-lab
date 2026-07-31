"""
CEREBUS Trade Orchestrator
===========================
Sits on top of ST/P90 engines. Uses ML predictions to manage trades.
Does NOT replace ST/P90 — it maximizes the existing high-probability setups.

The engines call entries (80%+ WR). The orchestrator decides:
1. Position sizing — boost vs reduce
2. Risk management — hedge, move SL, close early
3. Setup selection — which setups to take vs skip
4. Timing — when to add, hold, exit

Signal Flow:
  ST/P90 Engine → Entry Signal (80%+ WR)
       ↓
  ML Orchestrator → Size/Risk/Timing Decision
       ↓
  Trade Management → SL moves, hedges, exits
"""

from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# STATE DEFINITIONS (from Holy Grail ontology)
# ═══════════════════════════════════════════════════════════════════════════

class TradeState(Enum):
    NO_POSITION = "NO_POSITION"
    T1_ACTIVE = "T1_ACTIVE"
    T2_ACTIVE = "T2_ACTIVE"
    T3_ACTIVE = "T3_ACTIVE"
    TARGET_25_HIT = "TARGET_25_HIT"
    TARGET_50_HIT = "TARGET_50_HIT"
    TARGET_100_HIT = "TARGET_100_HIT"
    STALL_ZONE = "STALL_ZONE"
    DEEP_STATE = "DEEP_STATE"
    REKEY_SEQUENCE = "REKEY_SEQUENCE"
    REKEY_CONSOLID = "REKEY_CONSOLID"
    REKEY_EXTENSION = "REKEY_EXTENSION"
    FAILURE = "FAILURE"
    HARD_EXIT = "HARD_EXIT"
    REGIME_FLIP = "REGIME_FLIP"


class RegimeState(Enum):
    CONFIRMED = "CONFIRMED"
    CAUTION = "CAUTION"
    FAILED = "FAILED"
    NO_GO = "NO_GO"


# ═══════════════════════════════════════════════════════════════════════════
# HOLY GRAIL TRANSITION PROBABILITIES (from extracted data)
# ═══════════════════════════════════════════════════════════════════════════

# These are the known probabilities from the Holy Grail sweeps.
# The ML model will learn to refine these from actual price data.

TRANSITION_PROBS = {
    # From AR_SET
    ("AR_SET", "P90_FIRED"): 0.95,       # 95% of sessions get a P90

    # From P90_FIRED (by tier)
    ("P90_FIRED", "T1_ACTIVE"): 0.40,    # ~40% are T1 (<20p AR)
    ("P90_FIRED", "T2_ACTIVE"): 0.35,    # ~35% are T2 (20-30p AR)
    ("P90_FIRED", "T3_ACTIVE"): 0.25,    # ~25% are T3 (30-45p AR)

    # From T1_ACTIVE
    ("T1_ACTIVE", "TARGET_25"): 0.982,   # -25% hit rate (T1, from Holy Grail)
    ("T1_ACTIVE", "FAILURE"): 0.018,     # 1.8% failure rate

    # From T2_ACTIVE
    ("T2_ACTIVE", "TARGET_25"): 0.964,   # -25% hit rate (T2)
    ("T2_ACTIVE", "FAILURE"): 0.036,

    # From T3_ACTIVE
    ("T3_ACTIVE", "TARGET_25"): 0.922,   # -25% hit rate (T3)
    ("T3_ACTIVE", "FAILURE"): 0.078,

    # From TARGET_25
    ("TARGET_25", "TARGET_50"): 0.964,   # -50% hit rate after -25%
    ("TARGET_25", "STALL_ZONE"): 0.342,  # 34.2% reach stall zone
    ("TARGET_25", "REVERSAL"): 0.042,    # 4.2% full reversal after -25%

    # From TARGET_50
    ("TARGET_50", "TARGET_100"): 0.922,  # -100% hit rate after -50%
    ("TARGET_50", "REVERSAL"): 0.028,    # 2.8% reversal after -50%

    # From TARGET_100
    ("TARGET_100", "REKEY"): 0.715,      # 132% violation rate
    ("TARGET_100", "TARGET_168"): 0.872, # -168% hit rate

    # From REKEY
    ("REKEY", "REKEY_CONSOLID"): 0.850,  # 85% consolidation (12-24h)
    ("REKEY", "REKEY_EXTENSION"): 0.780, # -50% extension target

    # From FAILURE
    ("FAILURE", "SOFT"): 0.642,           # Type 1: Soft failure (midpoint only)
    ("FAILURE", "INTERNAL_RESET"): 0.249, # Type 2: Same-side recycle
    ("FAILURE", "REGIME_FLIP"): 0.109,    # Type 3: Opposite-side confirmed

    # Second acceptance (after failure)
    ("FAILURE", "2ND_ACCEPTANCE"): 0.505, # 50.5% get valid 2nd break
}

# Session performance (from Holy Grail)
SESSION_PROBS = {
    "2-4AM": {"expansion_wr": 0.942, "stall_rate": 0.311},
    "4-7AM": {"expansion_wr": 0.886, "stall_rate": 0.354},
    "7-11AM": {"expansion_wr": 0.824, "stall_rate": 0.382},
}

# Day-of-week execution rules (from Holy Grail)
DAY_RULES = {
    "Monday": {"first_break_real": 0.60, "second_break_real": 0.40, "rule": "Reduce size"},
    "Tuesday": {"first_break_real": 0.80, "second_break_real": 0.20, "rule": "Play first violation"},
    "Wednesday": {"first_break_real": 0.75, "second_break_real": 0.25, "rule": "Play first violation"},
    "Thursday": {"first_break_real": 0.55, "second_break_real": 0.45, "rule": "Wait for second"},
    "Friday": {"first_break_real": 0.70, "second_break_real": 0.30, "rule": "Mixed"},
}

# Seasonal adjustments (from Holy Grail)
SEASONAL_ADJUSTMENTS = {
    "Q1": {"failure_rate": 0.138, "risk": "HIGH", "size_multiplier": 0.75},
    "Q2": {"failure_rate": 0.052, "risk": "LOW", "size_multiplier": 1.0},
    "Q3": {"failure_rate": 0.051, "risk": "LOW", "size_multiplier": 1.0},
    "Q4": {"failure_rate": 0.138, "risk": "HIGH", "size_multiplier": 0.75},
}

# Target trimming matrix (from Holy Grail, by tier)
TARGET_TRIMMING = {
    "T1": {"TP1_-25%": 0.20, "TP2_-50%": 0.50, "TP3_Daily_-50%": 0.25, "Runner": 0.05},
    "T2": {"TP1_-25%": 0.20, "TP2_-50%": 0.50, "TP3_Daily_-50%": 0.30, "Runner": 0.0},
    "T3": {"TP1_-25%": 0.30, "TP2_-50%": 0.70, "TP3+": 0.0, "Runner": 0.0},
}


# ═══════════════════════════════════════════════════════════════════════════
# TRADE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class TradeSetup:
    """Current trade setup being evaluated."""
    symbol: str
    tier: int  # 1, 2, 3
    ar_pips: float
    regime: RegimeState
    session: str  # "2-4AM", "4-7AM", "7-11AM"
    day_of_week: str
    quarter: str
    ilm_alignment: str  # "FULL", "PARTIAL", "NONE"
    is_wednesday_pm: bool
    consecutive_losses: int
    spread_vs_avg: float
    # Directional Bias fields (from 3-Lens Ternary + Pathway)
    bias_state: Optional[str] = None       # "9/9_LOCK", "KINETIC_CONFLICT", "EXHAUSTION", "COILED_SPRING"
    bias_direction: Optional[str] = None  # "LONG", "SHORT", "NONE"
    bias_confidence: Optional[float] = None  # 0-1
    # DTB Magnitude fields (from DTB v4 cascade)
    dtb_predicted_pips: Optional[float] = None  # Predicted remaining pips
    dtb_checkpoint: Optional[str] = None  # "T0", "T1", "T2"


@dataclass
class TradeDecision:
    """Orchestrator's decision for a trade."""
    action: str  # "ENTER", "SKIP", "REDUCE", "HEDGE", "EXIT"
    size_multiplier: float  # 0.0 to 1.0
    reason: str
    targets: Dict[str, float] = field(default_factory=dict)
    sl_buffer_pips: float = 0.0
    hedge_ratio: float = 0.0
    time_stop_bars: int = 0


class TradeOrchestrator:
    """
    Manages trades using Holy Grail probabilities + ML predictions.
    Does NOT replace ST/P90 engines — maximizes existing setups.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.transition_probs = TRANSITION_PROBS
        self.session_probs = SESSION_PROBS
        self.day_rules = DAY_RULES
        self.seasonal = SEASONAL_ADJUSTMENTS
        self.target_trimming = TARGET_TRIMMING

    def evaluate_entry(self, setup: TradeSetup) -> TradeDecision:
        """
        Decide whether to enter a trade and at what size.
        Uses Holy Grail probabilities as priors, refined by current conditions.
        """
        reasons = []
        size_mult = 1.0

        # ── Directional Bias filter (3-Lens Ternary + Pathway) ──
        # This is the "Vector" — does the market want to move in this direction?
        if hasattr(setup, 'bias_state') and setup.bias_state is not None:
            bias_state = setup.bias_state
            if bias_state == "KINETIC_CONFLICT":
                return TradeDecision("SKIP", 0.0,
                    "BIAS CONFLICT: Structural and kinetic lenses disagree — fakeout risk")
            elif bias_state == "EXHAUSTION":
                size_mult *= 0.3
                reasons.append("BIAS EXHAUSTION: Direction valid but regime failed — scalp only")
            elif bias_state == "9/9_LOCK":
                reasons.append("BIAS LOCK: 3 lenses aligned, high conviction")
            elif bias_state == "COILED_SPRING":
                size_mult *= 0.5
                reasons.append("COILED: No breakout yet but regime confirmed — reduced size")

        # ── Regime check ──
        if setup.regime == RegimeState.FAILED:
            return TradeDecision("SKIP", 0.0, "Regime FAILED — no trade")
        elif setup.regime == RegimeState.CAUTION:
            size_mult *= 0.5
            reasons.append("Regime CAUTION: half size")
        elif setup.regime == RegimeState.CONFIRMED:
            reasons.append("Regime CONFIRMED: full size")

        # ── ILM alignment ──
        if setup.ilm_alignment == "FULL":
            size_mult *= 1.0
            reasons.append("Full ILM alignment")
        elif setup.ilm_alignment == "PARTIAL":
            size_mult *= 0.7
            reasons.append("Partial ILM alignment: reduce 30%")
        else:
            size_mult *= 0.3
            reasons.append("No ILM alignment: micro size only")

        # ── Day-of-week adjustment ──
        day_rule = self.day_rules.get(setup.day_of_week, {})
        if setup.day_of_week in ["Tuesday", "Wednesday"]:
            reasons.append(f"{setup.day_of_week}: Play first violation")
        elif setup.day_of_week == "Thursday":
            size_mult *= 0.7
            reasons.append("Thursday: Wait for second violation, reduce size")
        elif setup.day_of_week == "Monday":
            size_mult *= 0.8
            reasons.append("Monday: Reduce size, indecisive")

        # ── Seasonal adjustment ──
        seasonal = self.seasonal.get(setup.quarter, {})
        if seasonal.get("risk") == "HIGH":
            size_mult *= seasonal.get("size_multiplier", 0.75)
            reasons.append(f"{setup.quarter} HIGH RISK: reduce to {seasonal.get('size_multiplier', 0.75)}x")

        # ── Wednesday PM bifurcation ──
        if setup.is_wednesday_pm:
            size_mult *= 0.7
            reasons.append("Wednesday PM: Reduce 30% (bifurcation risk)")

        # ── Consecutive losses ──
        if setup.consecutive_losses >= 3:
            size_mult *= 0.5
            reasons.append(f"{setup.consecutive_losses} consecutive losses: half size")
        elif setup.consecutive_losses >= 5:
            return TradeDecision("SKIP", 0.0, "5+ consecutive losses: stand down")

        # ── Spread check ──
        if setup.spread_vs_avg > 2.0:
            size_mult *= 0.5
            reasons.append(f"Spread {setup.spread_vs_avg:.1f}x above avg: reduce size")

        # ── DTB Magnitude: Use predicted remaining pips to set targets ──
        dtb_target_pips = None
        if hasattr(setup, 'dtb_predicted_pips') and setup.dtb_predicted_pips is not None:
            dtb_target_pips = setup.dtb_predicted_pips
            reasons.append(f"DTB: {dtb_target_pips:.1f}p predicted remaining")

        # ── Tier-based target trimming ──
        tier_key = f"T{setup.tier}"
        trimming = self.target_trimming.get(tier_key, {})

        # Build targets — use DTB prediction if available
        targets = {}
        if setup.tier == 1:
            targets = {
                "TP1_-25%": 0.20,
                "TP2_-50%": 0.50,
                "TP3_Daily_-50%": 0.25,
                "Runner": 0.05,
            }
        elif setup.tier == 2:
            targets = {
                "TP1_-25%": 0.20,
                "TP2_-50%": 0.50,
                "TP3_Daily_-50%": 0.30,
                "Runner": 0.0,
            }
        elif setup.tier == 3:
            targets = {
                "TP1_-25%": 0.30,
                "TP2_-50%": 0.70,
                "TP3+": 0.0,
                "Runner": 0.0,
            }

        # If DTB predicted pips available, set dynamic TP
        if dtb_target_pips is not None and dtb_target_pips > 0:
            targets["DTB_Target"] = dtb_target_pips
            # Adjust runner based on DTB confidence
            if dtb_target_pips > 50:
                targets["Runner"] = 0.10  # High confidence — hold more
            else:
                targets["Runner"] = 0.02  # Low confidence — trim more

        # ── Final decision ──
        if size_mult < 0.1:
            return TradeDecision("SKIP", 0.0, " | ".join(reasons))

        action = "ENTER" if size_mult >= 0.5 else "REDUCE"

        return TradeDecision(
            action=action,
            size_multiplier=min(size_mult, 1.0),
            reason=" | ".join(reasons),
            targets=targets,
            sl_buffer_pips=setup.ar_pips * 0.8,
            time_stop_bars=288,
        )

    def evaluate_during_trade(
        self,
        setup: TradeSetup,
        current_state: TradeState,
        bars_in_trade: int,
        targets_hit: List[str],
        current_pnl_pips: float,
    ) -> TradeDecision:
        """
        Manage an active trade. Called every bar.
        Decides: hold, trim, hedge, or exit.
        """
        reasons = []

        # ── Target hit management ──
        if "TARGET_25" in targets_hit and "TARGET_50" not in targets_hit:
            # -25% hit, holding for -50%
            if current_pnl_pips > 0:
                reasons.append("-25% hit: Move SL to breakeven")
            # Check stall zone proximity
            if current_state == TradeState.STALL_ZONE:
                return TradeDecision(
                    "HEDGE", 0.5,
                    "Stall zone reached: Hedge with DMR at 38.2% Fib",
                    hedge_ratio=0.5,
                )

        if "TARGET_50" in targets_hit and "TARGET_100" not in targets_hit:
            # -50% hit, holding for -100%
            if current_pnl_pips > 0:
                reasons.append("-50% hit: Trail SL to -25% level")

        # ── 132% violation check ──
        if current_state == TradeState.REKEY_SEQUENCE:
            return TradeDecision(
                "EXIT", 0.0,
                "132% violation: Exit original, begin rekey sequence",
            )

        # ── Failure detection ──
        if current_state == TradeState.FAILURE:
            # Check for second acceptance
            if bars_in_trade < 48:  # Within first 4 hours
                return TradeDecision(
                    "HOLD", 0.5,
                    "Failure detected: Hold for second acceptance (50.5% chance)",
                )
            else:
                return TradeDecision(
                    "EXIT", 0.0,
                    "Failure + no second acceptance: Exit",
                )

        # ── Time stop ──
        if bars_in_trade >= 288:  # 24 hours
            return TradeDecision("EXIT", 0.0, "Time stop: 24 hours elapsed")

        # ── Hard exit approaching ──
        if bars_in_trade >= 240:  # 20 hours (4 hours before hard exit)
            reasons.append("Approaching 12PM hard exit: Tighten SL")
            return TradeDecision("HOLD", 0.3, " | ".join(reasons))

        # ── Regime deterioration ──
        if setup.regime == RegimeState.FAILED:
            return TradeDecision("EXIT", 0.0, "Regime deteriorated to FAILED")

        return TradeDecision("HOLD", 1.0, " | ".join(reasons) if reasons else "Hold position")

    def get_weekly_forecast(self, setup: TradeSetup) -> Dict[str, float]:
        """
        Generate a full weekly probability forecast for a setup.
        Returns probability of each target being hit by day.
        """
        base_25 = 0.982 if setup.tier == 1 else (0.964 if setup.tier == 2 else 0.922)
        base_50 = 0.964
        base_100 = 0.922
        base_168 = 0.872
        rekey = 0.715

        # Adjust for day of week
        day_adj = {
            "Monday": 0.95, "Tuesday": 1.0, "Wednesday": 0.98,
            "Thursday": 0.90, "Friday": 0.85
        }.get(setup.day_of_week, 1.0)

        # Adjust for season
        seasonal_adj = {
            "Q1": 0.92, "Q2": 1.0, "Q3": 1.0, "Q4": 0.92
        }.get(setup.quarter, 1.0)

        # Adjust for regime
        regime_adj = {
            RegimeState.CONFIRMED: 1.0,
            RegimeState.CAUTION: 0.85,
            RegimeState.FAILED: 0.5,
        }.get(setup.regime, 0.5)

        adj = day_adj * seasonal_adj * regime_adj

        return {
            "P(-25% by Tue)": round(base_25 * adj, 3),
            "P(-50% by Wed)": round(base_50 * adj, 3),
            "P(-100% by Thu)": round(base_100 * adj, 3),
            "P(-168% by Fri)": round(base_168 * adj, 3),
            "P(132% violation)": round(rekey * adj, 3),
            "P(failure)": round((1 - base_25) * adj, 3),
            "expected_trading_days": round(5 * adj, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    orch = TradeOrchestrator()

    # Example: EURUSD T1 setup on Tuesday Q2
    setup = TradeSetup(
        symbol="EURUSD",
        tier=1,
        ar_pips=12.5,
        regime=RegimeState.CONFIRMED,
        session="2-4AM",
        day_of_week="Tuesday",
        quarter="Q2",
        ilm_alignment="FULL",
        is_wednesday_pm=False,
        consecutive_losses=0,
        spread_vs_avg=1.0,
    )

    # Entry decision
    decision = orch.evaluate_entry(setup)
    print(f"Entry Decision: {decision.action}")
    print(f"Size Multiplier: {decision.size_multiplier:.1f}")
    print(f"Reason: {decision.reason}")
    print(f"Targets: {decision.targets}")

    # Weekly forecast
    forecast = orch.get_weekly_forecast(setup)
    print(f"\nWeekly Forecast:")
    for k, v in forecast.items():
        print(f"  {k}: {v}")

    # DTB Cascade Prediction
    try:
        from dtb_lab.dtb_predictor import DTBPredictor
        predictor = DTBPredictor()
        cascade = predictor.predict_cascade(
            _build_m5_from_setup(setup), setup.symbol
        )
        if cascade.best_prediction:
            pred = cascade.best_prediction
            print(f"\nDTB Cascade Prediction ({pred.checkpoint}):")
            print(f"  Remaining Distribution: {pred.remaining_pips:.1f} pips")
            print(f"  Confidence: {pred.confidence:.0%}")
            print(f"  Regime: {pred.regime}")
            print(f"  Tier: {pred.tier}")
            print(f"  Omega_L: {pred.omega_l:.3f}")
            print(f"  Loops: {pred.l_actual}/{pred.l_theoretical:.1f}")
            if cascade.variance_compression:
                print(f"  Variance Compression: {cascade.variance_compression:.1%}")
    except Exception as e:
        print(f"\nDTB Predictor not available: {e}")


def _build_m5_from_setup(setup: TradeSetup) -> pd.DataFrame:
    """
    Build a minimal M5 DataFrame from TradeSetup for DTB prediction.
    In production, this would use real-time market data.
    For now, returns empty DataFrame (DTB needs real bars).
    """
    return pd.DataFrame()
