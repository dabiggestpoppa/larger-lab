"""
Asian Session Breakout Strategy for Nautilus Trader
"""
from decimal import Decimal
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class AsianBreakoutConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId = None
    bar_type: str = None
    range_hours: int = 8
    stop_atr_mult: float = 1.5
    take_profit_mult: float = 2.0
    trade_size: Decimal = Decimal("100000")


class AsianBreakoutStrategy(Strategy):
    def __init__(self, config: AsianBreakoutConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.range_hours = config.range_hours
        self.trade_size = config.trade_size
        
        self.asian_high = 0
        self.asian_low = 0
        self.range_set = False
        self.position_open = False
        
    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.log.info(f"Asian Breakout started - Range: {self.range_hours}h")
        
    def on_bar(self, bar: Bar):
        hour = (bar.ts_event // 3600000000000) % 24
        
        # Set Asian range (hours 19-3 UTC)
        if 19 <= hour or hour < 3:
            self.asian_high = max(self.asian_high, bar.high)
            self.asian_low = min(self.asian_low, bar.low) if self.asian_low > 0 else bar.low
            self.range_set = True
        elif self.range_set and not self.position_open:
            # Check breakout
            if bar.close > self.asian_high:
                self._enter_long(bar.close)
            elif bar.close < self.asian_low:
                self._enter_short(bar.close)
    
    def _enter_long(self, price):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity(self.trade_size, 0),
        )
        self.submit_order(order)
        self.position_open = True
        
    def _enter_short(self, price):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=Quantity(self.trade_size, 0),
        )
        self.submit_order(order)
        self.position_open = True