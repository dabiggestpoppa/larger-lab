"""
RSI Mean Reversion Strategy for Nautilus Trader
"""
from decimal import Decimal
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class RSIMeanReversionConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId = None
    bar_type: str = None
    rsi_period: int = 14
    rsi_low: float = 30.0
    rsi_high: float = 70.0
    atr_period: int = 14
    trade_size: Decimal = Decimal("100000")


class RSIMeanReversionStrategy(Strategy):
    def __init__(self, config: RSIMeanReversionConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.rsi_period = config.rsi_period
        self.rsi_low = config.rsi_low
        self.rsi_high = config.rsi_high
        self.trade_size = config.trade_size
        
        self.prices = []
        self.position_open = False
        
    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.log.info(f"RSI Mean Reversion started - RSI({self.rsi_period})")
        
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        if len(self.prices) < self.rsi_period + 1:
            return
            
        # Calculate RSI
        rsi = self._calculate_rsi()
        
        if not self.position_open and rsi < self.rsi_low:
            self._enter_long(bar.close)
        elif self.position_open and rsi > self.rsi_high:
            self._close_position()
    
    def _calculate_rsi(self):
        prices = self.prices[-self.rsi_period-1:]
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _enter_long(self, price):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity(self.trade_size, 0),
        )
        self.submit_order(order)
        self.position_open = True
        
    def _close_position(self):
        # Close logic would go here
        self.position_open = False