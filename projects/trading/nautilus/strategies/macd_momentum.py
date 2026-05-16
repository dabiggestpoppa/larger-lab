"""
MACD Momentum Strategy for Nautilus Trader
"""
from decimal import Decimal
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class MACDMomentumConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId = None
    bar_type: str = None
    fast: int = 12
    slow: int = 26
    signal: int = 9
    slope_lookback: int = 3
    trade_size: Decimal = Decimal("100000")


class MACDMomentumStrategy(Strategy):
    def __init__(self, config: MACDMomentumConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.fast = config.fast
        self.slow = config.slow
        self.signal = config.signal
        self.trade_size = config.trade_size
        
        self.prices = []
        self.macd_hist = []
        self.position_open = False
        
    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.log.info(f"MACD Momentum started - ({self.fast},{self.slow},{self.signal})")
        
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        if len(self.prices) < self.slow + self.signal:
            return
            
        macd, signal_line, hist = self._calculate_macd()
        self.macd_hist.append(hist)
        
        if len(self.macd_hist) >= self.slope_lookback + 1:
            slope = self._calculate_slope()
            
            if not self.position_open and slope > 0 and hist > 0:
                self._enter_long(bar.close)
            elif self.position_open and slope < 0:
                self._close_position()
    
    def _calculate_macd(self):
        fast_ema = self._ema(self.prices, self.fast)
        slow_ema = self._ema(self.prices, self.slow)
        macd = fast_ema - slow_ema
        signal = self._ema([macd], self.signal)
        return macd, signal, macd - signal
    
    def _ema(self, data, period):
        if len(data) < period:
            return 0
        multiplier = 2 / (period + 1)
        ema = data[0]
        for price in data[1:]:
            ema = price * multiplier + ema * (1 - multiplier)
        return ema
    
    def _calculate_slope(self):
        return self.macd_hist[-1] - self.macd_hist[-self.slope_lookback]
    
    def _enter_long(self, price):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity(self.trade_size, 0),
        )
        self.submit_order(order)
        self.position_open = True
        
    def _close_position(self):
        self.position_open = False