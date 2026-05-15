"""
EMA Cross strategy for Nautilus Trader.
Mirrors the Pine Script EMA crossover logic for cross-validation.

Pine Script equivalent:
    //@version=6
    strategy("EMA Cross", overlay=true)
    fast = ta.ema(close, 10)
    slow = ta.ema(close, 20)
    if ta.crossover(fast, slow)
        strategy.entry("Long", strategy.long)
    if ta.crossunder(fast, slow)
        strategy.close("Long")
"""
from decimal import Decimal

from nautilus_trader.core.message import Event
from nautilus_trader.indicator import MovingAverage
from nautilus_trader.indicator.ma import ExponentialMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.trading.strategy import StrategyConfig


class EMACrossConfig(StrategyConfig, frozen=True):
    """Configuration for EMA Cross strategy."""
    instrument_id: InstrumentId = None
    bar_type: str = None
    fast_ema_period: int = 10
    slow_ema_period: int = 20
    trade_size: Decimal = Decimal("100000")
    close_positions_on_stop: bool = True


class EMACrossStrategy(Strategy):
    """
    EMA Crossover strategy matching Pine Script logic.

    Entry: Fast EMA crosses above Slow EMA → BUY
    Exit: Fast EMA crosses below Slow EMA → CLOSE

    This mirrors the Pine Script:
        if ta.crossover(fast, slow) → strategy.entry("Long", strategy.long)
        if ta.crossunder(fast, slow) → strategy.close("Long")
    """

    def __init__(self, config: EMACrossConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size
        self.close_positions_on_stop = config.close_positions_on_stop

        # Indicators
        self.fast_ema = ExponentialMovingAverage(config.fast_ema_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_ema_period)

        # State
        self.previous_fast = None
        self.previous_slow = None
        self.position_open = False

    def on_start(self):
        """Called when strategy starts."""
        self.register_indicator_for_bars(self.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.bar_type, self.slow_ema)
        self.subscribe_bars(self.bar_type)
        self.log.info(
            f"EMA Cross started: fast={self.fast_ema.period}, slow={self.slow_ema.period}"
        )

    def on_bar(self, bar: Bar):
        """Called on each new bar."""
        # Wait for both indicators to be initialized
        if not self.fast_ema.initialized or not self.slow_ema.initialized:
            return

        current_fast = self.fast_ema.value
        current_slow = self.slow_ema.value

        if self.previous_fast is not None and self.previous_slow is not None:
            # Crossover: fast crosses above slow → BUY
            if self.previous_fast <= self.previous_slow and current_fast > current_slow:
                self._enter_long()

            # Crossunder: fast crosses below slow → CLOSE
            elif self.previous_fast >= self.previous_slow and current_fast < current_slow:
                self._close_position()

        self.previous_fast = current_fast
        self.previous_slow = current_slow

    def _enter_long(self):
        """Enter a long position."""
        if self.position_open:
            return

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str(str(self.trade_size)),
            time_in_force=TimeInForce.IOC,
        )
        self.submit_order(order)
        self.position_open = True
        self.log.info(f"📈 EMA Crossover → BUY at {self.fast_ema.value:.5f}")

    def _close_position(self):
        """Close existing position."""
        if not self.position_open:
            return

        position = self.cache.position(self.instrument_id)
        if position is not None and position.quantity > 0:
            close_order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=position.quantity,
                time_in_force=TimeInForce.IOC,
            )
            self.submit_order(close_order)
            self.position_open = False
            self.log.info(f"📉 EMA Crossunder → CLOSE at {self.fast_ema.value:.5f}")

    def on_stop(self):
        """Called when strategy stops."""
        if self.close_positions_on_stop:
            self._close_position()
        self.log.info("EMA Cross strategy stopped")

    def on_event(self, event: Event):
        """Handle events."""
        if isinstance(event, OrderFilled):
            self.log.info(f"Order filled: {event}")
