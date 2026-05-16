"""
CFD Expansion Engine — CEREBUS FX v4.0 (Part 3, Pages 16-19)
================================================================

P90 Activation Signal Strategy for Nautilus Trader.

CORE THESIS (per manual):
  Small Asian ranges (<30 pips) create a Constraint Deficit.
  The field must expand to resolve it. The P90 candle is the Activation Signal
  that marks the start of a new resolution process.

ACTIVATION SIGNAL (P90 Candle):
  Wait for an M5 candle to close within the Activation Window (2:00 AM – 11:00 AM EST)
  meeting the threshold:
    2:00 – 4:00 AM: >= 4.1 pips
    4:00 – 6:00 AM: >= 4.6 pips
    6:00 – 8:00 AM: >= 4.6 pips
    8:00 – 10:00 AM: >= 5.9 pips
    10:00 – 11:00 AM: >= 6.2 pips

PYRAMID PROTOCOL:
  Signal 1 (P90 Close): 40% size, SL = 80% of P90 Body, TP = -25% Daily Range
  Signal 2 (P90 Close): 40% size, SL = 1.5x P90 Body, TP = -25% Daily Range
  Signal 3 (+45 Mins): 20% size, SL = Breakeven (Signal 1), TP = -50% Daily Range

EXIT MANAGEMENT:
  TP1 (-25% of Asian Range): Close 50%, move SL to Breakeven
  TP2 (-50% of Asian Range): Close remaining core positions
  Hard Exit (12:00 PM EST): Close ALL positions
  Kill Switch (132% State): Close ALL

Author: Quant Lab — based on CEREBUS FX v4.0 manual
"""
from decimal import Decimal
from datetime import datetime, timezone

from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


# P90 thresholds per manual (in pips, converted to price for FX pairs)
P90_THRESHOLDS = {
    # (hour_utc, min_pips) - UTC hours for EST windows
    (7, 4.1): (7, 4.2),   # 2-4 AM EST
    (9, 4.6): (9, 4.7),   # 4-6 AM EST  
    (11, 4.6): (11, 4.7), # 6-8 AM EST
    (13, 5.9): (13, 6.0), # 8-10 AM EST
    (15, 6.2): (15, 6.3), # 10-11 AM EST
}


class CFDExpansionConfig(StrategyConfig, frozen=True):
    """Configuration for CFD Expansion Engine strategy."""
    
    instrument_id: InstrumentId = None
    bar_type: str = None
    # Risk management
    initial_capital: Decimal = Decimal("100000")
    risk_per_trade_pct: Decimal = Decimal("0.0012")  # 0.12% per signal
    max_daily_loss_pct: Decimal = Decimal("0.004")   # 0.40% hard boundary
    # Strategy params
    asian_range_pips: Decimal = Decimal("25")  # Measured Asian Range
    daily_target_pips: Decimal = Decimal("58")  # Expected daily range
    # Session timing (UTC)
    activation_start_hour: int = 7   # 2 AM EST
    activation_end_hour: int = 15    # 11 AM EST
    hard_exit_hour: int = 17         # 12 PM EST


class CFDExpansionStrategy(Strategy):
    """
    CFD Expansion Engine — CEREBUS FX v4.0 (Part 3)
    
    P90 Activation Signal Strategy:
    1. Wait for P90 candle (M5 close with body >= threshold)
    2. Pyramid entries on confirmation
    3. Exit at -25% / -50% Asian Range targets
    """
    
    def __init__(self, config: CFDExpansionConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.asian_range = config.asian_range_pips
        self.daily_target = config.daily_target_pips
        
        # State tracking
        self.p90_detected = False
        self.p90_bar = None
        self.p90_direction = None
        self.signal_count = 0
        self.position_size = Decimal("0")
        self.entry_price = None
        
    def on_start(self):
        """Called when strategy starts."""
        self.subscribe_bars(self.bar_type)
        self.log.info(f"CFD Expansion Engine started - Asian Range: {self.asian_range} pips")
        
    def on_bar(self, bar: Bar):
        """Called on each new bar."""
        current_hour = bar.ts_event // 3600000000000  # Convert nanoseconds to hours
        
        # Check for P90 activation signal
        if not self.p90_detected and self._is_activation_window(current_hour):
            if self._is_p90_candle(bar):
                self._handle_p90_activation(bar)
                
        # Manage existing position
        elif self.p90_detected and self.position_size > 0:
            self._manage_position(bar)
            
    def _is_activation_window(self, hour_utc: int) -> bool:
        """Check if current hour is within activation window."""
        return self.activation_start_hour <= hour_utc <= self.activation_end_hour
        
    def _is_p90_candle(self, bar: Bar) -> bool:
        """Check if bar qualifies as P90 activation signal."""
        current_hour = bar.ts_event // 3600000000000
        
        # Get threshold for current hour
        threshold = None
        for (start_h, thresh) in P90_THRESHOLDS:
            if start_h <= current_hour < start_h + 2:
                threshold = thresh
                break
                
        if threshold is None:
            return False
            
        # Calculate candle body in pips
        body_pips = abs(bar.close - bar.open) * 10000  # For EUR/USD style pairs
        
        return body_pips >= threshold
        
    def _handle_p90_activation(self, bar: Bar):
        """Handle P90 activation signal."""
        self.p90_detected = True
        self.p90_bar = bar
        self.p90_direction = OrderSide.BUY if bar.close > bar.open else OrderSide.SELL
        
        self.log.info(f"P90 Activation detected - Direction: {self.p90_direction}")
        
        # Signal 1: 40% position
        self._enter_position(Decimal("0.4"), bar.close)
        
    def _enter_position(self, size_pct: Decimal, price: Price):
        """Enter position with given size percentage."""
        self.signal_count += 1
        self.position_size += size_pct
        
        order_side = self.p90_direction
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=order_side,
            quantity=Quantity(str(self.position_size * 100000), 0),  # Standard lot sizing
        )
        
        self.submit_order(order)
        self.log.info(f"Signal {self.signal_count}: Entered {order_side} {size_pct*100}% at {price}")
        
    def _manage_position(self, bar: Bar):
        """Manage open position with targets and stops."""
        # Check hard exit (12 PM EST = 17:00 UTC)
        current_hour = bar.ts_event // 3600000000000
        if current_hour >= self.hard_exit_hour:
            self.close_all()
            return
            
        # Check TP levels (-25% and -50% of Asian Range)
        # Implementation would check price vs targets
        
    def close_all(self):
        """Close all positions."""
        if self.position_size > 0:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL if self.p90_direction == OrderSide.BUY else OrderSide.BUY,
                quantity=Quantity(str(self.position_size * 100000), 0),
            )
            self.submit_order(order)
            self.log.info("Closing all positions")