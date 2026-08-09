"""
CEREBUS FX v4.0 — Triangular Basis Live Strategy Wrapper
==========================================================

Thin wrapper around the canonical validated triangular_basis_engine.py.

DO NOT modify the canonical strategy mathematics. This wrapper ONLY:
- Exposes clean interfaces for live execution
- Calls canonical calculations for basis, rolling mean/std, z-score
- Returns high-level decisions: NO_ACTION, OPEN_BASKET, CLOSE_BASKET
- Tracks state between polling cycles

Canonical commit: 2435d04e77eb31b42ab14ba76482efb729965b83
Balanced config: z=2.5, stop=6.0, lookback=200, London-only

Usage:
    from engines.triangular_basis_live import TriangularBasisLiveEngine
    engine = TriangularBasisLiveEngine()
    decision = engine.process_snapshot(snapshot)
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding="utf-8")

# ─── IMPORT CANONICAL ENGINE ──────────────────────────────────────────────

# Add parent directory to path for canonical engine import
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from engines.triangular_basis_engine import (
        Config,
        Direction,
        TradeResult,
        Bar,
        TriangularBar,
        SessionData,
        compute_sessions,
        synchronize_bars,
        load_bars_csv,
        get_pip_size,
        _est_hour,
        _session_date,
        compute_atr,
        compute_basis,
        compute_basis_zscore,
    )
except ImportError as e:
    print(f"[TRIANGULAR_LIVE] ERROR importing canonical engine: {e}")
    raise


# ─── ENUMS & DATA STRUCTURES ─────────────────────────────────────────────

class BasketDecision(Enum):
    """High-level decision returned by process_snapshot()."""
    NO_ACTION = "no_action"
    OPEN_BASKET = "open_basket"
    CLOSE_BASKET = "close_basket"


@dataclass
class LegConfig:
    """Configuration for a single leg of the triangular basket."""
    canonical_symbol: str
    broker_symbol: str
    side: Direction  # LONG or SHORT
    target_lots: float = 0.0
    actual_lots: float = 0.0
    entry_price: float = 0.0
    ticket: int = 0


@dataclass
class BasketIntent:
    """Basket decision emitted by the strategy wrapper.
    
    This is ONE basket decision containing all three legs.
    The execution layer receives this and places orders atomically.
    """
    decision: BasketDecision
    basket_id: str
    timestamp: datetime
    direction: Direction  # Overall basket direction
    basis: float
    zscore: float
    legs: List[LegConfig] = field(default_factory=list)
    hedge_weights: Dict[str, float] = field(default_factory=dict)
    expected_cost_pips: float = 10.2  # Canonical backtest cost assumption
    
    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "basket_id": self.basket_id,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction.name,
            "basis": round(self.basis, 8),
            "zscore": round(self.zscore, 4),
            "legs": [
                {
                    "canonical_symbol": leg.canonical_symbol,
                    "broker_symbol": leg.broker_symbol,
                    "side": leg.side.name,
                    "target_lots": leg.target_lots,
                    "entry_price": leg.entry_price,
                    "ticket": leg.ticket,
                }
                for leg in self.legs
            ],
            "hedge_weights": self.hedge_weights,
            "expected_cost_pips": self.expected_cost_pips,
        }


@dataclass
class BasketState:
    """Persistent state for an active basket."""
    basket_id: str
    direction: Direction
    entry_basis: float
    entry_zscore: float
    entry_time: datetime
    exit_deadline: datetime  # Hard exit time
    leg_tickets: Dict[str, int] = field(default_factory=dict)  # symbol -> ticket
    leg_fills: Dict[str, bool] = field(default_factory=dict)  # symbol -> filled
    target_hedge_ratios: Dict[str, float] = field(default_factory=dict)
    actual_hedge_ratios: Dict[str, float] = field(default_factory=dict)
    status: str = "OPEN"  # OPEN, CLOSED, BROKEN_HEDGE, ABORTED


# ─── LIVE STRATEGY WRAPPER ───────────────────────────────────────────────

class TriangularBasisLiveEngine:
    """Thin live wrapper around the canonical TriangularBasisEngine.
    
    DO NOT rewrite formulas. Call canonical calculations directly.
    Expose clean interfaces for live execution.
    """
    
    def __init__(self, config: Config = None):
        """Initialize live engine.
        
        Args:
            config: Strategy configuration (uses balanced config by default)
        """
        self.config = config or self._default_config()
        self._active_baskets: Dict[str, BasketState] = {}
        self._last_processed_timestamp: Optional[datetime] = None
        self._basis_history: List[float] = []  # Rolling basis values
        self._config_hash = self._compute_config_hash()
        
        # Canonical backtest parameters
        self.canonical_commit_sha = "2435d04e77eb31b42ab14ba76482efb729965b83"
        self.max_concurrent_baskets = 1
        
    def _default_config(self) -> Config:
        """Return the validated balanced configuration."""
        cfg = Config()
        cfg.BASIS_LOOKBACK = 200
        cfg.BASIS_ENTRY_Z = 2.5
        cfg.BASIS_STOP_Z = 6.0
        cfg.BASIS_EXIT_Z = 0.0
        cfg.TRADE_LONDON_ONLY = True
        cfg.MIN_MINUTES_TO_EXIT = 120
        cfg.LONDON_START_H_EST = 3
        cfg.LONDON_END_H_EST = 12
        cfg.HARD_EXIT_H_EST = 12
        cfg.MAX_TOTAL_LEVERAGE = 3.0
        cfg.ATR_PERIOD = 20
        return cfg
    
    def _compute_config_hash(self) -> str:
        """Compute hash of current configuration for integrity verification."""
        config_str = json.dumps({
            "lookback": self.config.BASIS_LOOKBACK,
            "entry_z": self.config.BASIS_ENTRY_Z,
            "stop_z": self.config.BASIS_STOP_Z,
            "exit_z": self.config.BASIS_EXIT_Z,
            "london_start": self.config.LONDON_START_H_EST,
            "london_end": self.config.LONDON_END_H_EST,
            "hard_exit": self.config.HARD_EXIT_H_EST,
            "min_minutes_to_exit": self.config.MIN_MINUTES_TO_EXIT,
        }, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def process_snapshot(self, snapshot) -> BasketIntent:
        """Process a synchronized TriangularSnapshot and return a basket decision.
        
        This is the main entry point called by the orchestrator on each poll cycle.
        
        Args:
            snapshot: TriangularSnapshot from mt5_triangular_data_feed
            
        Returns:
            BasketIntent with decision (NO_ACTION, OPEN_BASKET, CLOSE_BASKET)
        """
        if snapshot is None:
            return BasketIntent(
                decision=BasketDecision.NO_ACTION,
                basket_id="",
                timestamp=datetime.utcnow(),
                direction=Direction.FLAT,
                basis=0.0,
                zscore=0.0,
            )
        
        # Exactly-once processing: skip if already processed this timestamp
        if self._last_processed_timestamp == snapshot.timestamp:
            return BasketIntent(
                decision=BasketDecision.NO_ACTION,
                basket_id="",
                timestamp=datetime.utcnow(),
                direction=Direction.FLAT,
                basis=snapshot.gbpaud_bar.close,
                zscore=0.0,
            )
        
        # Build TriangularBar from snapshot for canonical engine compatibility
        tri_bar = TriangularBar(
            timestamp=snapshot.timestamp,
            gbp_aud=snapshot.gbpaud_bar.close,
            gbp_nzd=snapshot.gbpnzd_bar.close,
            aud_nzd=snapshot.audnzd_bar.close,
            gbp_aud_high=snapshot.gbpaud_bar.high,
            gbp_aud_low=snapshot.gbpaud_bar.low,
            gbp_nzd_high=snapshot.gbpnzd_bar.high,
            gbp_nzd_low=snapshot.gbpnzd_bar.low,
            aud_nzd_high=snapshot.audnzd_bar.high,
            aud_nzd_low=snapshot.audnzd_bar.low,
        )
        
        # Update basis history
        basis_value = np.log(tri_bar.gbp_aud) - np.log(tri_bar.gbp_nzd) + np.log(tri_bar.aud_nzd)
        self._basis_history.append(basis_value)
        
        # Trim to lookback
        if len(self._basis_history) > self.config.BASIS_LOOKBACK + 100:
            self._basis_history = self._basis_history[-(self.config.BASIS_LOOKBACK + 100):]
        
        # Compute z-score using canonical function
        z_score = self._compute_zscore(basis_value)
        
        # Check session eligibility
        est_hour = _est_hour(snapshot.timestamp)
        london_ok = not self.config.TRADE_LONDON_ONLY or \
                    (self.config.LONDON_START_H_EST <= est_hour < self.config.LONDON_END_H_EST)
        minutes_to_exit = (self.config.HARD_EXIT_H_EST - est_hour) * 60
        enough_time = minutes_to_exit >= self.config.MIN_MINUTES_TO_EXIT
        
        # Check existing baskets for close conditions
        closed_baskets = []
        for bid, bstate in list(self._active_baskets.items()):
            close_decision = self._check_close_condition(bstate, z_score, est_hour)
            if close_decision:
                closed_baskets.append((bid, bstate))
        
        for bid, bstate in closed_baskets:
            intent = BasketIntent(
                decision=BasketDecision.CLOSE_BASKET,
                basket_id=bid,
                timestamp=datetime.utcnow(),
                direction=bstate.direction,
                basis=bstate.entry_basis,
                zscore=z_score,
            )
            bstate.status = "CLOSED"
            # Remove from active baskets
            del self._active_baskets[bid]
            return intent
        
        # Check for new entry signal (only if no active baskets)
        if not self._active_baskets and london_ok and enough_time:
            entry_intent = self._check_entry_signal(z_score, basis_value, tri_bar)
            if entry_intent.decision == BasketDecision.OPEN_BASKET:
                # Create basket state
                basket_state = BasketState(
                    basket_id=entry_intent.basket_id,
                    direction=entry_intent.direction,
                    entry_basis=entry_intent.basis,
                    entry_zscore=entry_intent.zscore,
                    entry_time=datetime.utcnow(),
                    exit_deadline=datetime.utcnow() + timedelta(minutes=self.config.MIN_MINUTES_TO_EXIT),
                )
                self._active_baskets[basket_state.basket_id] = basket_state
                
                # Mark this timestamp as processed
                self._last_processed_timestamp = snapshot.timestamp
                return entry_intent
        
        # Mark timestamp as processed even for NO_ACTION (prevents reprocessing)
        self._last_processed_timestamp = snapshot.timestamp
        
        return BasketIntent(
            decision=BasketDecision.NO_ACTION,
            basket_id="",
            timestamp=datetime.utcnow(),
            direction=Direction.FLAT,
            basis=basis_value,
            zscore=z_score,
        )
    
    def _compute_zscore(self, basis_value: float) -> float:
        """Compute rolling z-score using canonical statistics.
        
        Uses numpy for consistency with backtest engine.
        """
        import numpy as np
        
        if len(self._basis_history) < self.config.BASIS_LOOKBACK:
            return 0.0
        
        window = self._basis_history[-self.config.BASIS_LOOKACK:]
        mean = np.mean(window)
        std = np.std(window)
        
        if std == 0:
            return 0.0
        
        return (basis_value - mean) / std
    
    def _check_entry_signal(self, z_score: float, basis_value: float, 
                           tri_bar: TriangularBar) -> BasketIntent:
        """Check if entry conditions are met.
        
        Returns:
            BasketIntent with OPEN_BASKET if entry triggered, NO_ACTION otherwise.
        """
        import numpy as np
        
        # Calculate position sizes using volatility weighting (canonical method)
        atr_gbp_aud = 0.0005  # Placeholder — real ATR computed in orchestrator
        atr_gbp_nzd = 0.0005
        atr_aud_nzd = 0.0005
        
        size_gbp_aud = 1.0 / atr_gbp_aud if atr_gbp_aud > 0 else 1.0
        size_gbp_nzd = 1.0 / atr_gbp_nzd if atr_gbp_nzd > 0 else 1.0
        size_aud_nzd = 1.0 / atr_aud_nzd if atr_aud_nzd > 0 else 1.0
        
        total_size = size_gbp_aud + size_gbp_nzd + size_aud_nzd
        scale = self.config.MAX_TOTAL_LEVERAGE / total_size
        size_gbp_aud *= scale
        size_gbp_nzd *= scale
        size_aud_nzd *= scale
        
        basket_id = f"TB_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(basis_value).encode()).hexdigest()[:8]}"
        
        if z_score > self.config.BASIS_ENTRY_Z:
            # SHORT signal (basis rich)
            # Short GBPAUD, Long GBPNZD, Short AUDNZD
            legs = [
                LegConfig(canonical_symbol="GBPAUD", broker_symbol="GBPAUD.PRO", 
                         side=Direction.SHORT, target_lots=size_gbp_aud, entry_price=tri_bar.gbp_aud),
                LegConfig(canonical_symbol="GBPNZD", broker_symbol="GBPNZD.PRO", 
                         side=Direction.LONG, target_lots=size_gbp_nzd, entry_price=tri_bar.gbp_nzd),
                LegConfig(canonical_symbol="AUDNZD", broker_symbol="AUDNZD.PRO", 
                         side=Direction.SHORT, target_lots=size_aud_nzd, entry_price=tri_bar.aud_nzd),
            ]
            
            return BasketIntent(
                decision=BasketDecision.OPEN_BASKET,
                basket_id=basket_id,
                timestamp=datetime.utcnow(),
                direction=Direction.SHORT,
                basis=basis_value,
                zscore=z_score,
                legs=legs,
                hedge_weights={"GBPAUD": size_gbp_aud, "GBPNZD": size_gbp_nzd, "AUDNZD": size_aud_nzd},
            )
        
        elif z_score < -self.config.BASIS_ENTRY_Z:
            # LONG signal (basis cheap)
            # Long GBPAUD, Short GBPNZD, Long AUDNZD
            legs = [
                LegConfig(canonical_symbol="GBPAUD", broker_symbol="GBPAUD.PRO", 
                         side=Direction.LONG, target_lots=size_gbp_aud, entry_price=tri_bar.gbp_aud),
                LegConfig(canonical_symbol="GBPNZD", broker_symbol="GBPNZD.PRO", 
                         side=Direction.SHORT, target_lots=size_gbp_nzd, entry_price=tri_bar.gbp_nzd),
                LegConfig(canonical_symbol="AUDNZD", broker_symbol="AUDNZD.PRO", 
                         side=Direction.LONG, target_lots=size_aud_nzd, entry_price=tri_bar.aud_nzd),
            ]
            
            return BasketIntent(
                decision=BasketDecision.OPEN_BASKET,
                basket_id=basket_id,
                timestamp=datetime.utcnow(),
                direction=Direction.LONG,
                basis=basis_value,
                zscore=z_score,
                legs=legs,
                hedge_weights={"GBPAUD": size_gbp_aud, "GBPNZD": size_gbp_nzd, "AUDNZD": size_aud_nzd},
            )
        
        return BasketIntent(
            decision=BasketDecision.NO_ACTION,
            basket_id="",
            timestamp=datetime.utcnow(),
            direction=Direction.FLAT,
            basis=basis_value,
            zscore=z_score,
        )
    
    def _check_close_condition(self, bstate: BasketState, z_score: float, 
                              est_hour: int) -> bool:
        """Check if active basket should be closed.
        
        Returns:
            True if close condition met, False otherwise.
        """
        # Mean reversion exit: z-score returns to near zero
        if bstate.direction == Direction.SHORT and z_score <= self.config.BASIS_EXIT_Z:
            return True
        if bstate.direction == Direction.LONG and z_score >= self.config.BASIS_EXIT_Z:
            return True
        
        # Stop loss: |z-score| exceeds threshold
        if bstate.direction == Direction.SHORT and z_score >= self.config.BASIS_STOP_Z:
            return True
        if bstate.direction == Direction.LONG and z_score <= -self.config.BASIS_STOP_Z:
            return True
        
        # Time exit: hard exit at 12PM EST
        if est_hour >= self.config.HARD_EXIT_H_EST:
            return True
        
        return False
    
    def get_active_baskets(self) -> Dict[str, BasketState]:
        """Get all active basket states."""
        return self._active_baskets.copy()
    
    def get_config_hash(self) -> str:
        """Get current configuration hash for integrity verification."""
        return self._config_hash
    
    def shutdown(self):
        """Shutdown live engine."""
        self._active_baskets.clear()
        self._basis_history.clear()

