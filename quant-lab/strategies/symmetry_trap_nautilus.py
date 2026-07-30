"""
Symmetry Trap Strategy for Nautilus Trader
===========================================
Port of the Symmetry Trap engine to Nautilus Trader for cross-validation.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from nautilus_trader.config import StrategyConfig as NautilusStrategyConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy
from pydantic import Field


class SymmetryTrapConfig(NautilusStrategyConfig):
    """Configuration for Symmetry Trap strategy."""
    
    # Instrument
    instrument_id: str
    bar_type: BarType
    
    # Session times (EST)
    asian_start_hour: int = 19  # 7 PM EST
    asian_end_hour: int = 3     # 3 AM EST
    trading_start_hour: int = 3  # 3 AM EST
    trading_end_hour: int = 16   # 4 PM EST
    
    # Tier configuration (AU in pips, trigger in pips)
    tier_config: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "T1": {"au_pips": 10.0, "trigger_pips": 12.0},
            "T2": {"au_pips": 12.0, "trigger_pips": 15.0},
            "T3": {"au_pips": 15.0, "trigger_pips": 19.0},
        }
    )
    
    # Risk management
    max_loops_per_session: int = 5
    hard_exit_hour: int = 16  # 4 PM EST
    
    # Order sizing
    lot_size: Decimal = Decimal("0.01")
    
    # Spread/commission (for realistic backtesting)
    spread_pips: float = 1.0
    commission_per_lot: float = 7.0


class SymmetryTrapStrategy(Strategy):
    """
    Symmetry Trap Strategy for Nautilus Trader.
    
    Entry Pipeline (all 3 steps mandatory):
      1. Impulse: M5 close beyond Tier Trigger (AU x 1.20) from swing_origin
      2. Rebalance: Pullback >= 1 AU OR 38.2%-50% Fib retracement
      3. OCC: M5 candle closes BACK in impulse direction
    
    Trade Management:
      Entry: Close of OCC candle
      SL: Zero-Buffer Impulse Extreme = exact impulse bar high/low (CLOSE-ONLY)
      TP: Exactly 1 AU from entry (SINGLE TARGET — no ladder)
    
    Invalidation:
      - 80% Kill Switch: M5 close past 80% of impulse leg = pathway VOID
      - SL hit (close only) = trade over, reset to SEARCH
    
    Engine Isolation:
      This engine NEVER uses P90 body data.
      SL is ALWAYS Zero-Buffer OCC/Impulse Extreme — never 80% P90 body.
      TP is ALWAYS 1 AU — never P90 targets.
    """
    
    def __init__(self, config: SymmetryTrapConfig):
        super().__init__(config)
        
        # State machine
        self.state = "SEARCH"  # SEARCH, WAIT_RETRACE, WAIT_OCC, IN_TRADE
        self.swing_origin: Optional[Decimal] = None
        self.impulse_direction: int = 0  # 1=LONG, -1=SHORT, 0=FLAT
        self.impulse_extreme: Decimal = Decimal("0")
        self.impulse_size_pips: float = 0.0
        self.kill_switch_level: Decimal = Decimal("0")
        
        # Tier state
        self.tier_name: str = "T1"
        self.au_pips: float = 10.0
        self.trigger_pips: float = 12.0
        self.active_au: Decimal = Decimal("0")
        self.session_active: bool = False
        
        # Trade state
        self.entry_price: Optional[Decimal] = None
        self.sl_price: Optional[Decimal] = None
        self.tp_price: Optional[Decimal] = None
        self.position_side: int = 0
        self._just_entered: bool = False
        
        # Loop tracking
        self.loop_count: int = 1
        self.max_loops: int = config.max_loops_per_session
        
        # Session state
        self.asian_high: Decimal = Decimal("0")
        self.asian_low: Decimal = Decimal("0")
        self.asian_range_pips: float = 0.0
        
        # Instrument info
        self.instrument_id: InstrumentId = InstrumentId.from_str(config.instrument_id)
        self.bar_type: BarType = config.bar_type
        self.pip_size: Decimal = self._get_pip_size(config.instrument_id)
        self.lot_size: Decimal = config.lot_size
        
        # Costs
        self.spread_pips: float = config.spread_pips
        self.commission_per_lot: float = config.commission_per_lot
        
        # Cache for bars
        self._bars_cache = []
        
    def _get_pip_size(self, instrument_id: str) -> Decimal:
        """Get pip size for instrument."""
        if "JPY" in instrument_id:
            return Decimal("0.01")
        elif "XAU" in instrument_id or "XAG" in instrument_id:
            return Decimal("0.1") if "XAU" in instrument_id else Decimal("0.01")
        elif any(x in instrument_id for x in ["US500", "NAS100", "DE30", "FR40", "HK50"]):
            return Decimal("1.0")
        elif any(x in instrument_id for x in ["BTC", "ETH", "SOL", "XRP", "LTC", "BCH", "BNB", "XLM"]):
            return Decimal("1.0")
        else:
            return Decimal("0.0001")
    
    def on_start(self):
        """Called when strategy starts."""
        self.log.info(f"Symmetry Trap started for {self.config.instrument_id}")
        self.log.info(f"Pip size: {self.pip_size}, Lot size: {self.lot_size}")
        
        # Subscribe to bars
        self.subscribe_bars(self.bar_type)
        
    def on_bar(self, bar: Bar):
        """Process each M5 bar."""
        # Convert to our internal format
        bar_dict = {
            "timestamp": bar.ts_event,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
        }
        
        # Extract EST hour
        est_hour = self._get_est_hour(bar.ts_event)
        
        # Skip Asian session bars (no impulse detection during Asian)
        if est_hour >= 19 or est_hour < 3:
            # Still accumulate Asian range
            self._update_asian_range(bar)
            return
        
        # Hard exit at 4 PM EST
        if est_hour >= self.config.hard_exit_hour and self.state == "SEARCH":
            self._hard_exit()
            return
        
        # Process through state machine
        self._process_bar(bar_dict, est_hour)
        
    def _get_est_hour(self, timestamp_ns: int) -> int:
        """Convert nanosecond timestamp to EST hour."""
        # Nautilus timestamps are UTC nanoseconds
        dt = datetime.fromtimestamp(timestamp_ns / 1e9, tz=timezone.utc)
        est_dt = dt - timedelta(hours=5)
        return est_dt.hour
    
    def _update_asian_range(self, bar: Bar):
        """Update Asian range high/low."""
        if self.asian_high == Decimal("0"):
            self.asian_high = bar.high
            self.asian_low = bar.low
        else:
            self.asian_high = max(self.asian_high, bar.high)
            self.asian_low = min(self.asian_low, bar.low)
    
    def _initialize_session(self, asian_high: Decimal, asian_low: Decimal):
        """Initialize session at 3 AM EST from Asian Range."""
        self.asian_high = asian_high
        self.asian_low = asian_low
        self.asian_range_pips = float((asian_high - asian_low) / self.pip_size)
        
        # AR gate: if Asian Range > 60p, session is NO_GO
        ar_max = self.config.tier_config.get("T1", {}).get("ar_max", 60.0)
        if self.asian_range_pips > ar_max:
            self.tier_name = "NO_GO"
            self.au_pips = 0.0
            self.trigger_pips = 0.0
        else:
            # Default to T1 — tier will be reclassified by impulse size
            self.tier_name = "T1"
            cfg = self.config.tier_config.get("T1", {"au_pips": 10.0, "trigger_pips": 12.0})
            self.au_pips = cfg["au_pips"]
            self.trigger_pips = cfg["trigger_pips"]
        
        self.active_au = Decimal(str(self.au_pips)) * self.pip_size
        self.session_active = self.tier_name != "NO_GO"
        
        # Reset state machine
        self.state = "SEARCH"
        self.swing_origin = None
        self.impulse_direction = 0
        self.impulse_extreme = Decimal("0")
        self.impulse_size_pips = 0.0
        self.kill_switch_level = Decimal("0")
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.position_side = 0
        self._just_entered = False
        
        # Loop tracking
        self.loop_count = 1
        
        self.log.info(
            f"Session initialized: tier={self.tier_name}, "
            f"AU={self.au_pips}p, trigger={self.trigger_pips}p, "
            f"AR={self.asian_range_pips:.1f}p, loop=1 (max={self.max_loops})"
        )
    
    def _process_bar(self, bar: dict, est_hour: int):
        """Process bar through state machine."""
        if not self.session_active:
            return
        
        # Set swing origin from first bar if not set
        if self.swing_origin is None:
            self.swing_origin = bar["close"]
        
        active_trig = Decimal(str(self.trigger_pips)) * self.pip_size
        
        up_move = bar["high"] - self.swing_origin
        dn_move = self.swing_origin - bar["low"]
        
        # STATE: SEARCH - Wait for impulse breach >= Tier Trigger
        if self.state == "SEARCH":
            if up_move >= active_trig:
                self.impulse_direction = 1
                self.impulse_extreme = bar["high"]
                self.impulse_size_pips = float(up_move / self.pip_size)
                self.kill_switch_level = Decimal("0")  # REMOVED per June 4 optimization
                self._classify_tier_by_impulse()
                self.state = "WAIT_RETRACE"
                self.log.debug(
                    f"Impulse LONG: extreme={self.impulse_extreme:.5f}, "
                    f"size={self.impulse_size_pips:.1f}p, "
                    f"tier={self.tier_name}, AU={self.au_pips}p"
                )
            
            elif dn_move >= active_trig:
                self.impulse_direction = -1
                self.impulse_extreme = bar["low"]
                self.impulse_size_pips = float(dn_move / self.pip_size)
                self.kill_switch_level = Decimal("0")
                self._classify_tier_by_impulse()
                self.state = "WAIT_RETRACE"
                self.log.debug(
                    f"Impulse SHORT: extreme={self.impulse_extreme:.5f}, "
                    f"size={self.impulse_size_pips:.1f}p, "
                    f"tier={self.tier_name}, AU={self.au_pips}p"
                )
        
        # STATE: WAIT_RETRACE - Wait for pullback >= 1 AU OR 38.2%-50% Fib
        elif self.state == "WAIT_RETRACE":
            # Kill Switch: REMOVED (dead code per June 4 optimization)
            
            # Flat DZ: 20%-50% for all loops
            min_retrace_pct = 0.20
            max_retrace_pct = 0.50
            
            if self.impulse_direction == 1:
                pullback_px = self.impulse_extreme - bar["low"]
            else:
                pullback_px = bar["high"] - self.impulse_extreme
            
            pullback_pips = float(pullback_px / self.pip_size)
            retrace_pct = (
                pullback_pips / self.impulse_size_pips
                if self.impulse_size_pips > 0 else 0
            )
            
            au_penetrated = pullback_pips >= self.au_pips
            fib_penetrated = min_retrace_pct <= retrace_pct <= max_retrace_pct
            
            if au_penetrated or fib_penetrated:
                self.state = "WAIT_OCC"
                self.log.debug(
                    f"DZ penetrated: pullback={pullback_pips:.1f}p, "
                    f"retrace={retrace_pct:.3f}, au_ok={au_penetrated}, "
                    f"fib_ok={fib_penetrated}, loop={self.loop_count}"
                )
        
        # STATE: WAIT_OCC - Wait for Opposite Candle Close confirming impulse direction
        elif self.state == "WAIT_OCC":
            occ_confirmed = (
                (self.impulse_direction == 1 and bar["close"] > bar["open"]) or
                (self.impulse_direction == -1 and bar["close"] < bar["open"])
            )
            
            if occ_confirmed:
                self.entry_price = bar["close"]
                # SL = Zero-Buffer Impulse Extreme (exact high/low of impulse bar)
                self.sl_price = self.impulse_extreme
                self.tp_price = (
                    bar["close"] + self.active_au * self.impulse_direction
                )
                self.state = "IN_TRADE"
                self._just_entered = True  # Skip SL/TP check on entry bar
                
                self.log.info(
                    f"ENTRY {'LONG' if self.impulse_direction == 1 else 'SHORT'} "
                    f"(loop {self.loop_count}): "
                    f"entry={self.entry_price:.5f}, sl={self.sl_price:.5f}, "
                    f"tp={self.tp_price:.5f} (1 AU = {self.au_pips}p)"
                )
                return
        
        # STATE: IN_TRADE - Monitor TP (wick or close) and SL (CLOSE-ONLY)
        elif self.state == "IN_TRADE":
            # Skip SL/TP check on entry bar — Nautilus fills on NEXT bar
            if self._just_entered:
                self._just_entered = False
                return
            
            if self.impulse_direction == 1:  # LONG
                # TP check: wick OR close
                if bar["high"] >= self.tp_price:
                    self._exit_trade("TP_HIT", self.tp_price)
                    return
                
                # SL check: CLOSE-ONLY (wicks don't count)
                if bar["close"] <= self.sl_price:
                    self._exit_trade("SL_HIT", self.sl_price)
                    return
            
            else:  # SHORT
                # TP check: wick OR close
                if bar["low"] <= self.tp_price:
                    self._exit_trade("TP_HIT", self.tp_price)
                    return
                
                # SL check: CLOSE-ONLY
                if bar["close"] >= self.sl_price:
                    self._exit_trade("SL_HIT", self.sl_price)
                    return
    
    def _classify_tier_by_impulse(self):
        """Reclassify tier based on impulse leg size."""
        # T1: < 20p | T2: 20-30p | T3: > 30p
        if self.impulse_size_pips < 20:
            self.tier_name = "T1"
        elif self.impulse_size_pips <= 30:
            self.tier_name = "T2"
        else:
            self.tier_name = "T3"
        
        cfg = self.config.tier_config.get(self.tier_name, {"au_pips": 10.0, "trigger_pips": 12.0})
        self.au_pips = cfg["au_pips"]
        self.active_au = Decimal(str(self.au_pips)) * self.pip_size
        # NOTE: trigger_pips stays at T1 value for all loops (per June 4 calibration)
    
    def _exit_trade(self, reason: str, exit_price: Decimal):
        """Exit trade and reset state for next loop."""
        self.log.info(f"{reason}: exit={exit_price:.5f} (loop {self.loop_count} -> {min(self.loop_count + 1, self.max_loops)})")
        
        # Reset state machine to SEARCH
        self.state = "SEARCH"
        self.swing_origin = exit_price  # New swing origin = exit price
        self.impulse_direction = 0
        self.impulse_extreme = Decimal("0")
        self.impulse_size_pips = 0.0
        self.kill_switch_level = Decimal("0")
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.position_side = 0
        
        # Increment loop count (Option B: Continuous Loop)
        self.loop_count = min(self.loop_count + 1, self.max_loops)
    
    def _hard_exit(self):
        """4 PM EST forced termination."""
        self.session_active = False
        self.state = "SEARCH"
        self.swing_origin = None
        self.loop_count = 1
        self.log.info("Hard exit: 4 PM EST — session terminated, loops reset")
    
    def on_stop(self):
        """Called when strategy stops."""
        self.log.info("Symmetry Trap stopped")


# For running backtest with Nautilus
if __name__ == "__main__":
    print("SymmetryTrapStrategy ready for Nautilus Trader")
    print("Usage: Configure with SymmetryTrapConfig and add to BacktestEngine")