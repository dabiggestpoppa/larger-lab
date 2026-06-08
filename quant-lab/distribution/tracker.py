"""
CEREBUS Distribution Tracker
=============================
Part 5 of the CEREBUS FX v4 Manual — P90P Window Distribution Tracker Enhanced.

Tracks the distribution of P90 signals across time windows to determine:
- Session bias (direction of constraint resolution)
- Regime classification (CONFIRMED/CAUTION/FAILED)
- Target calculation with multi-factor boosts
- Accuracy tracking (predicted vs actual)

Usage:
    tracker = DistributionTracker()
    tracker.update_asian_range(pair, range_pips, date)
    tracker.update_p90_signal(pair, direction, body_pips, timestamp)
    tracker.update_regime(pair, daily_range_3am_9am)
    prediction = tracker.get_prediction(pair)
    tracker.record_actual(pair, actual_high, actual_low)
    accuracy = tracker.get_accuracy_report()

Reference: CEREBUS FX v4 Manual, Part 5 — P90P Window Distribution Tracker Enhanced
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from enum import Enum
import json
import os


class Regime(Enum):
    CONFIRMED = "CONFIRMED"    # Ratio >= 1.50x
    CAUTION = "CAUTION"        # Ratio 1.45-1.49x
    FAILED = "FAILED"          # Ratio < 1.45x


class Tier(Enum):
    T1 = "T1"  # Asian Range < 20 pips (Gold, tight constraint deficit)
    T2 = "T2"  # Asian Range 20-30 pips (Standard)
    T3 = "T3"  # Asian Range 30-45 pips (Caution, wide constraint deficit)


class Direction(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    UNKNOWN = "UNKNOWN"


@dataclass
class P90Signal:
    """A single P90 signal (kinetic breach)."""
    timestamp: datetime
    direction: Direction
    body_pips: float
    is_initial: bool = False
    is_cascade: bool = False
    cascade_timing_minutes: float = 0.0  # Minutes from initial P90


@dataclass
class SessionData:
    """Data for a single trading session (one day, one pair)."""
    pair: str
    session_date: date
    
    # Asian Range (constraint deficit)
    asian_range_pips: float = 0.0
    tier: Tier = Tier.T2
    
    # P90 Signals
    initial_p90: Optional[P90Signal] = None
    cascade_p90s: List[P90Signal] = field(default_factory=list)
    session_bias: Direction = Direction.UNKNOWN
    
    # Regime
    daily_range_3am_9am: float = 0.0
    regime_ratio: float = 0.0
    regime: Regime = Regime.FAILED
    
    # Targets
    base_target: float = 0.0
    adjusted_target: float = 0.0
    final_target: float = 0.0
    precision_zone: float = 0.0
    expected_accuracy: float = 0.0
    
    # Actual results
    actual_high: float = 0.0
    actual_low: float = 0.0
    actual_extension: float = 0.0
    
    # Accuracy
    predicted_target: float = 0.0
    error_pips: float = 0.0
    within_zone: bool = False


# ── MANUAL CONSTANTS ──────────────────────────────────────────

# Tier classification (Asian Range)
TIER_THRESHOLDS = {
    Tier.T1: (0, 20),      # < 20 pips
    Tier.T2: (20, 30),     # 20-30 pips
    Tier.T3: (30, 45),     # 30-45 pips
}

# Tier base multipliers (from manual)
TIER_MULTIPLIERS = {
    Tier.T1: 3.12,
    Tier.T2: 2.68,
    Tier.T3: 2.18,
}

# Regime thresholds
REGIME_THRESHOLDS = {
    Regime.CONFIRMED: 1.50,
    Regime.CAUTION: 1.45,
    Regime.FAILED: 0.0,  # < 1.45
}

# Completion rates by regime
COMPLETION_RATES = {
    Regime.CONFIRMED: 0.902,
    Regime.CAUTION: 0.861,
    Regime.FAILED: 0.738,
}

# Regime boosts
REGIME_BOOSTS = {
    Regime.CONFIRMED: 1.10,
    Regime.CAUTION: 1.05,
    Regime.FAILED: 0.90,
}

# Precision zones by tier and regime
PRECISION_ZONES = {
    (Tier.T1, Regime.CONFIRMED): 2.0,
    (Tier.T1, Regime.CAUTION): 2.5,
    (Tier.T1, Regime.FAILED): 3.5,
    (Tier.T2, Regime.CONFIRMED): 2.5,
    (Tier.T2, Regime.CAUTION): 3.0,
    (Tier.T2, Regime.FAILED): 4.0,
    (Tier.T3, Regime.CONFIRMED): 3.0,
    (Tier.T3, Regime.CAUTION): 3.5,
    (Tier.T3, Regime.FAILED): 4.5,
}

# Expected accuracy by tier and regime
EXPECTED_ACCURACY = {
    (Tier.T1, Regime.CONFIRMED): 0.945,
    (Tier.T1, Regime.CAUTION): 0.920,
    (Tier.T1, Regime.FAILED): 0.870,
    (Tier.T2, Regime.CONFIRMED): 0.935,
    (Tier.T2, Regime.CAUTION): 0.910,
    (Tier.T2, Regime.FAILED): 0.860,
    (Tier.T3, Regime.CONFIRMED): 0.920,
    (Tier.T3, Regime.CAUTION): 0.890,
    (Tier.T3, Regime.FAILED): 0.840,
}

# Cascade timing boosts
CASCADE_TIMING_BOOSTS = {
    "optimal": 0.07,    # 45-60 min from initial
    "good": 0.03,       # 30-90 min
    "late": 0.00,       # 90+ min
}

# P90 confirmation boost
P90_CONFIRMED_BOOST = 0.03


class DistributionTracker:
    """
    P90P Window Distribution Tracker — Enhanced.
    
    Tracks session bias, regime, targets, and accuracy for the CEREBUS trading system.
    """
    
    def __init__(self, data_dir: str = None):
        self.sessions: Dict[str, List[SessionData]] = {}  # pair -> sessions
        self.current_session: Dict[str, SessionData] = {}  # pair -> current session
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "quant-lab", "reports", "distribution"
        )
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_tier(self, asian_range_pips: float) -> Tier:
        """Classify tier based on Asian Range."""
        if asian_range_pips < 20:
            return Tier.T1
        elif asian_range_pips < 30:
            return Tier.T2
        else:
            return Tier.T3
    
    def _get_regime(self, daily_range: float, asian_range: float) -> Regime:
        """Classify regime based on ratio."""
        if asian_range <= 0:
            return Regime.FAILED
        ratio = daily_range / asian_range
        if ratio >= 1.50:
            return Regime.CONFIRMED
        elif ratio >= 1.45:
            return Regime.CAUTION
        else:
            return Regime.FAILED
    
    def _calculate_target(self, session: SessionData) -> Tuple[float, float, float]:
        """
        Calculate the final target using the enhanced formula.
        
        Formula: Final Target = (Current Range ÷ Completion%) × Regime Boost
        
        Returns: (base_target, adjusted_target, final_target)
        """
        tier_mult = TIER_MULTIPLIERS[session.tier]
        
        # Base target = Asian Range × Tier Multiplier
        base_target = session.asian_range_pips * tier_mult
        
        # Adjusted target at 6 AM checkpoint
        # Target = Current Range ÷ 0.65 × 1.05 (if P90 confirmed)
        adjusted_target = base_target  # Will be updated at 6 AM
        
        # Final target with regime boost
        completion = COMPLETION_RATES[session.regime]
        boost = REGIME_BOOSTS[session.regime]
        
        # P90 confirmation boost
        p90_boost = 1.0
        if session.initial_p90:
            p90_boost += P90_CONFIRMED_BOOST
        
        # Cascade timing boost
        cascade_boost = 1.0
        if session.cascade_p90s:
            first_cascade = session.cascade_p90s[0]
            timing = first_cascade.cascade_timing_minutes
            if 45 <= timing <= 60:
                cascade_boost += CASCADE_TIMING_BOOSTS["optimal"]
            elif 30 <= timing <= 90:
                cascade_boost += CASCADE_TIMING_BOOSTS["good"]
        
        final_target = (base_target / completion) * boost * p90_boost * cascade_boost
        
        # Precision zone
        precision = PRECISION_ZONES.get((session.tier, session.regime), 3.0)
        
        # Expected accuracy
        accuracy = EXPECTED_ACCURACY.get((session.tier, session.regime), 0.85)
        
        return base_target, adjusted_target, final_target, precision, accuracy
    
    def start_session(self, pair: str, session_date: date, asian_range_pips: float):
        """Start tracking a new session."""
        tier = self._get_tier(asian_range_pips)
        session = SessionData(
            pair=pair,
            session_date=session_date,
            asian_range_pips=asian_range_pips,
            tier=tier,
        )
        self.current_session[pair] = session
        
        if pair not in self.sessions:
            self.sessions[pair] = []
    
    def record_initial_p90(self, pair: str, direction: Direction, body_pips: float, 
                           timestamp: datetime):
        """Record the initial P90 signal (sets session bias)."""
        session = self.current_session.get(pair)
        if not session:
            return
        
        session.initial_p90 = P90Signal(
            timestamp=timestamp,
            direction=direction,
            body_pips=body_pips,
            is_initial=True,
        )
        session.session_bias = direction
    
    def record_cascade_p90(self, pair: str, direction: Direction, body_pips: float,
                           timestamp: datetime):
        """Record a cascade P90 signal."""
        session = self.current_session.get(pair)
        if not session or not session.initial_p90:
            return
        
        # Only count same-direction cascades
        if direction != session.session_bias:
            return
        
        timing = (timestamp - session.initial_p90.timestamp).total_seconds() / 60.0
        
        signal = P90Signal(
            timestamp=timestamp,
            direction=direction,
            body_pips=body_pips,
            is_cascade=True,
            cascade_timing_minutes=timing,
        )
        session.cascade_p90s.append(signal)
    
    def update_regime(self, pair: str, daily_range_3am_9am: float):
        """Update regime classification (called at 9 AM checkpoint)."""
        session = self.current_session.get(pair)
        if not session:
            return
        
        session.daily_range_3am_9am = daily_range_3am_9am
        session.regime_ratio = daily_range_3am_9am / session.asian_range_pips if session.asian_range_pips > 0 else 0
        session.regime = self._get_regime(daily_range_3am_9am, session.asian_range_pips)
        
        # Calculate targets
        base, adjusted, final, precision, accuracy = self._calculate_target(session)
        session.base_target = base
        session.adjusted_target = adjusted
        session.final_target = final
        session.precision_zone = precision
        session.expected_accuracy = accuracy
        session.predicted_target = final
    
    def record_actual(self, pair: str, actual_high: float, actual_low: float,
                      entry_price: float = 0.0):
        """Record actual session results."""
        session = self.current_session.get(pair)
        if not session:
            return
        
        session.actual_high = actual_high
        session.actual_low = actual_low
        
        if entry_price > 0:
            if session.session_bias == Direction.LONG:
                session.actual_extension = actual_high - entry_price
            else:
                session.actual_extension = entry_price - actual_low
        
        # Calculate accuracy
        if session.predicted_target > 0:
            session.error_pips = abs(session.actual_extension - session.predicted_target)
            session.within_zone = session.error_pips <= session.precision_zone
        
        # Store session
        self.sessions[session.pair].append(session)
    
    def get_prediction(self, pair: str) -> Optional[Dict]:
        """Get the current prediction for a pair."""
        session = self.current_session.get(pair)
        if not session:
            return None
        
        return {
            "pair": pair,
            "date": str(session.session_date),
            "asian_range": session.asian_range_pips,
            "tier": session.tier.value,
            "session_bias": session.session_bias.value,
            "regime": session.regime.value,
            "regime_ratio": round(session.regime_ratio, 2),
            "base_target": round(session.base_target, 1),
            "final_target": round(session.final_target, 1),
            "precision_zone": session.precision_zone,
            "expected_accuracy": session.expected_accuracy,
            "p90_confirmed": session.initial_p90 is not None,
            "cascade_count": len(session.cascade_p90s),
        }
    
    def get_accuracy_report(self, pair: str = None, last_n: int = 20) -> Dict:
        """Get accuracy report for a pair or all pairs."""
        pairs = [pair] if pair else list(self.sessions.keys())
        
        report = {}
        for p in pairs:
            sessions = self.sessions.get(p, [])[-last_n:]
            if not sessions:
                continue
            
            completed = [s for s in sessions if s.actual_extension > 0]
            if not completed:
                continue
            
            within_zone = sum(1 for s in completed if s.within_zone)
            avg_error = sum(s.error_pips for s in completed) / len(completed)
            
            report[p] = {
                "total_sessions": len(completed),
                "within_zone": within_zone,
                "accuracy_rate": round(within_zone / len(completed), 3),
                "avg_error_pips": round(avg_error, 1),
                "expected_accuracy": completed[-1].expected_accuracy if completed else 0,
            }
        
        return report
    
    def save(self, filename: str = "distribution_tracker.json"):
        """Save tracker data to JSON."""
        path = os.path.join(self.data_dir, filename)
        data = {}
        for pair, sessions in self.sessions.items():
            data[pair] = []
            for s in sessions:
                data[pair].append({
                    "date": str(s.session_date),
                    "asian_range": s.asian_range_pips,
                    "tier": s.tier.value,
                    "bias": s.session_bias.value,
                    "regime": s.regime.value,
                    "regime_ratio": round(s.regime_ratio, 2),
                    "base_target": round(s.base_target, 1),
                    "final_target": round(s.final_target, 1),
                    "precision_zone": s.precision_zone,
                    "expected_accuracy": s.expected_accuracy,
                    "actual_extension": round(s.actual_extension, 2),
                    "error_pips": round(s.error_pips, 2),
                    "within_zone": s.within_zone,
                })
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return path
    
    def load(self, filename: str = "distribution_tracker.json"):
        """Load tracker data from JSON."""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        for pair, sessions in data.items():
            self.sessions[pair] = []
            for s in sessions:
                session = SessionData(
                    pair=pair,
                    session_date=date.fromisoformat(s["date"]),
                    asian_range_pips=s["asian_range"],
                    tier=Tier(s["tier"]),
                    session_bias=Direction(s["bias"]),
                    regime=Regime(s["regime"]),
                    regime_ratio=s["regime_ratio"],
                    base_target=s["base_target"],
                    final_target=s["final_target"],
                    precision_zone=s["precision_zone"],
                    expected_accuracy=s["expected_accuracy"],
                    actual_extension=s["actual_extension"],
                    error_pips=s["error_pips"],
                    within_zone=s["within_zone"],
                )
                self.sessions[pair].append(session)


# ── HELPER FUNCTIONS ──────────────────────────────────────────

def get_tier_from_range(asian_range_pips: float) -> str:
    """Get tier classification from Asian Range."""
    if asian_range_pips < 20:
        return "T1"
    elif asian_range_pips < 30:
        return "T2"
    else:
        return "T3"


def get_regime_from_ratio(daily_range: float, asian_range: float) -> str:
    """Get regime classification from ratio."""
    if asian_range <= 0:
        return "FAILED"
    ratio = daily_range / asian_range
    if ratio >= 1.50:
        return "CONFIRMED"
    elif ratio >= 1.45:
        return "CAUTION"
    else:
        return "FAILED"


def calculate_target(asian_range: float, tier: str, regime: str,
                     p90_confirmed: bool = False, cascade_optimal: bool = False) -> Dict:
    """
    Calculate target using the enhanced formula.
    
    Formula: Final Target = (Asian Range × Tier Multiplier ÷ Completion%) × Regime Boost × P90 Boost × Cascade Boost
    """
    tier_mult = TIER_MULTIPLIERS.get(Tier(tier), 2.68)
    completion = COMPLETION_RATES.get(Regime(regime), 0.861)
    boost = REGIME_BOOSTS.get(Regime(regime), 1.0)
    
    base_target = asian_range * tier_mult
    
    p90_boost = 1.03 if p90_confirmed else 1.0
    cascade_boost = 1.07 if cascade_optimal else 1.0
    
    final_target = (base_target / completion) * boost * p90_boost * cascade_boost
    
    tier_enum = Tier(tier)
    regime_enum = Regime(regime)
    precision = PRECISION_ZONES.get((tier_enum, regime_enum), 3.0)
    accuracy = EXPECTED_ACCURACY.get((tier_enum, regime_enum), 0.85)
    
    return {
        "base_target": round(base_target, 1),
        "final_target": round(final_target, 1),
        "precision_zone": precision,
        "expected_accuracy": accuracy,
    }


if __name__ == "__main__":
    # Example usage
    tracker = DistributionTracker()
    
    # Start a session
    tracker.start_session("EURUSD", date(2026, 6, 4), 25.0)
    
    # Record initial P90
    tracker.record_initial_p90(
        "EURUSD", Direction.LONG, 5.2,
        datetime(2026, 6, 4, 2, 30)
    )
    
    # Record cascade P90 (45 min later = optimal)
    tracker.record_cascade_p90(
        "EURUSD", Direction.LONG, 4.8,
        datetime(2026, 6, 4, 3, 15)
    )
    
    # Update regime at 9 AM
    tracker.update_regime("EURUSD", 62.0)
    
    # Get prediction
    pred = tracker.get_prediction("EURUSD")
    print("Prediction:", json.dumps(pred, indent=2))
    
    # Record actual
    tracker.record_actual("EURUSD", 1.0924, 1.0850, 1.0870)
    
    # Get accuracy report
    report = tracker.get_accuracy_report("EURUSD")
    print("Accuracy:", json.dumps(report, indent=2))
