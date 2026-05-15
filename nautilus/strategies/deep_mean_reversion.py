"""
Deep Mean Rebalancing — CEREBUS FX v4.0 (Part 4, Pages 20-29)
=============================================================

Resolution Output Stall Play for Nautilus Trader.

CORE LOGIC (per manual):
  When the resolution output extends aggressively, it often reaches the Stall Zone
  (168%) or Deep State (200%) to harvest available resolution pathways before
  rebalancing.

THE SETUP:
  Trigger: Resolution output touches Stall Zone (168%) or Deep State (200%)
  Condition: Must occur before 12:00 PM EST
  Filter: The -50% Daily Target has NOT yet been hit

EXECUTION OPTIONS:
  Option 1: Binary Options (Time-Based)
    Session (EST) | Dynamic Expiry | Target Win Rate
    2 AM – 6 AM   | 90 Minutes     | ~84%
    6 AM – 9 AM   | 60 Minutes     | ~78%
    9 AM – 12 PM  | 45 Minutes     | ~74%

  Option 2: CFD Limit Order at Deep State (Deep Value)
    LIMIT ORDER at 200% Deep State Level
    Constraint Boundary: 8 pips beyond 200% level (approx. 220% extension)
    Take Profit: TP1 = Return to 0%, TP2 = -50% Daily Range
    R:R Potential: 1:5 to 1:7

Author: Quant Lab — based on CEREBUS FX v4.0 manual
"""
from decimal import Decimal
from datetime import datetime, timezone

from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class DeepMeanReversionConfig(StrategyConfig, frozen=True):
    """Configuration for Deep Mean Reversion strategy."""
    
    instrument_id: InstrumentId = None
    bar_type: str = None
    # Risk management
    initial_capital: Decimal = Decimal("100000")
    risk_per_trade_pct: Decimal = Decimal("0.0025")  # 0.25% per trade
    # Strategy params
    asian_range_pips: Decimal = Decimal("25")
    daily_target_pips: Decimal = Decimal("58")
    # Extension levels (per manual)
    stall_zone_pct: Decimal = Decimal("1.68")  # 168%
    deep_state_pct: Decimal = Decimal("2.0")   # 200%
    kill_switch_pct: Decimal = Decimal("2.2")  # 220%
    # Session timing (UTC)
    entry_end_hour: int = 17  # 12 PM EST


class DeepMeanReversionStrategy(Strategy):
    """
    Deep Mean Rebalancing — CEREBUS FX v4.0 (Part 4)
    
    Resolution Output Stall Play:
    1. Wait for price to reach 168% or 200% extension
    2. Enter limit order at 200% level
    3. Target return to 0% (activation level) and -50% daily range
    """
    
    def __init__(self, config: DeepMeanReversionConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.asian_range = config.asian_range_pips
        self.daily_target = config.daily_target_pips
        
        # State tracking
        self.activation_level = None  # P90 level (0%)
        self.stall_zone_level = None  # 168% extension
        self.deep_state_level = None  # 200% extension
        self.kill_switch_level = None  # 220% extension
        self.position_open = False
        
    def on_start(self):
        """Called when strategy starts."""
        self.subscribe_bars(self.bar_type)
        self.log.info(f"Deep Mean Reversion started - Asian Range: {self.asian_range} pips")
        
    def on_bar(self, bar: Bar):
        """Called on each new bar."""
        current_hour = bar.ts_event // 3600000000000
        
        # Check if we should avoid the play (after 12 PM EST)
        if current_hour >= self.entry_end_hour:
            return
            
        # Check for deep state entry
        if not self.position_open:
            self._check_deep_state_entry(bar)
        else:
            self._manage_position(bar)
            
    def set_activation_level(self, level: Price):
        """Set the activation level (P90 close) for calculations."""
        self.activation_level = level
        # Calculate extension levels
        range_in_price = self.asian_range / 10000  # Convert pips to price
        
        if level:
            self.stall_zone_level = level + (range_in_price * float(self.stall_zone_pct - 1))
            self.deep_state_level = level + (range_in_price * float(self.deep_state_pct - 1))
            self.kill_switch_level = level + (range_in_price * float(self.kill_switch_pct - 1))
            
    def _check_deep_state_entry(self, bar: Bar):
        """Check if price has reached deep state for entry."""
        if self.deep_state_level is None:
            return
            
        # Check if price touched or exceeded deep state level
        if bar.low <= self.deep_state_level <= bar.high:
            self._enter_reversion_trade(bar)
            
    def _enter_reversion_trade(self, bar: Bar):
        """Enter the reversion trade at deep state."""
        # Determine direction (opposite to the move that got us here)
        direction = OrderSide.SELL if bar.close > self.activation_level else OrderSide.BUY
        
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=direction,
            quantity=Quantity("100000", 0),  # Standard lot
            price=Price(str(self.deep_state_level)),
        )
        
        self.submit_order(order)
        self.position_open = True
        self.log.info(f"Deep state entry: {direction} at {self.deep_state_level}")
        
    def _manage_position(self, bar: Bar):
        """Manage open position."""
        # Check TP1 (return to activation level)
        if self.activation_level:
            if (self.p90_direction == OrderSide.BUY and bar.low <= self.activation_level) or \
               (self.p90_direction == OrderSide.SELL and bar.high >= self.activation_level):
                self.close_all()
                self.log.info("TP1 hit: Return to activation level")