"""
Volatility Compression Breakout Strategy for Nautilus Trader
"""
from decimal import Decimal
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class VolatilityCompressionConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId = None
    bar_type: str = None
    bb_period: int = 20
    bb_std: float = 2.0
    squeeze_threshold: float = 0.8
    trade_size: Decimal = Decimal("100000")


class VolatilityCompressionStrategy(Strategy):
    def __init__(self, config: VolatilityCompressionConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.bb_period = config.bb_period
        self.bb_std = config.bb_std
        self.trade_size = config.trade_size
        
        self.prices = []
        self.position_open = False
        self.squeeze_active = False
        
    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.log.info(f"Volatility Compression started - BB({self.bb_period},{self.bb_std})")
        
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        if len(self.prices) < self.bb_period:
            return
            
        bb_width = self._calculate_bb_width()
        avg_width = self._calculate_avg_bb_width()
        
        # Check for squeeze
        if bb_width < avg_width * self.squeeze_threshold:
            self.squeeze_active = True
        elif self.squeeze_active:
            # Squeeze released - enter on breakout
            self._enter_long(bar.close)
            self.squeeze_active = False
    
    def _calculate_bb_width(self):
        prices = self.prices[-self.bb_period:]
        sma = sum(prices) / len(prices)
        std = (sum((p - sma)**2 for p in prices) / len(prices)) ** 0.5
        return (sma + self.bb_std * std) - (sma - self.bb_std * std)
    
    def _calculate_avg_bb_width(self):
        widths = []
        for i in range(self.bb_period, len(self.prices)):
            prices = self.prices[i-self.bb_period:i]
            sma = sum(prices) / len(prices)
            std = (sum((p - sma)**2 for p in prices) / len(prices)) ** 0.5
            widths.append((sma + self.bb_std * std) - (sma - self.bb_std * std))
        return sum(widths) / len(widths) if widths else 1
    
    def _enter_long(self, price):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity(self.trade_size, 0),
        )
        self.submit_order(order)
        self.position_open = True