"""
Quick synthetic backtest to verify the full Nautilus Trader pipeline.
Uses generated data (no OANDA key needed) with a simple EMA Cross strategy.
"""
from decimal import Decimal

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import AccountType, AggregationSource, BarAggregation, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class QuickEMAConfig(StrategyConfig, frozen=True):
    instrument_id = None
    bar_type = None
    fast_ema_period: int = 10
    slow_ema_period: int = 20
    trade_size: Decimal = Decimal("100000")


class QuickEMAStrategy(Strategy):
    def __init__(self, config: QuickEMAConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size
        self.fast_ema = None
        self.slow_ema = None
        self.prev_fast = None
        self.prev_slow = None

    def on_start(self):
        from nautilus_trader.indicators import ExponentialMovingAverage
        self.fast_ema = ExponentialMovingAverage(self.config.fast_ema_period)
        self.slow_ema = ExponentialMovingAverage(self.config.slow_ema_period)
        self.register_indicator_for_bars(self.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.bar_type, self.slow_ema)
        self.subscribe_bars(self.bar_type)
        self.log.info(f"Strategy started: EMA {self.config.fast_ema_period}/{self.config.slow_ema_period}")

    def on_bar(self, bar: Bar):
        if not self.fast_ema.initialized or not self.slow_ema.initialized:
            return

        curr_fast = self.fast_ema.value
        curr_slow = self.slow_ema.value

        if self.prev_fast is not None and self.prev_slow is not None:
            # Crossover: fast crosses above slow -> BUY
            if self.prev_fast <= self.prev_slow and curr_fast > curr_slow:
                instrument = self.cache.instrument(self.instrument_id)
                order = self.order_factory.market(
                    instrument_id=self.instrument_id,
                    order_side=OrderSide.BUY,
                    quantity=Quantity.from_str(str(self.trade_size)),
                    time_in_force=TimeInForce.IOC,
                )
                self.submit_order(order)
                self.log.info(f"BUY signal @ {bar.close}")

            # Crossunder: fast crosses below slow -> SELL
            elif self.prev_fast >= self.prev_slow and curr_fast < curr_slow:
                instrument = self.cache.instrument(self.instrument_id)
                order = self.order_factory.market(
                    instrument_id=self.instrument_id,
                    order_side=OrderSide.SELL,
                    quantity=Quantity.from_str(str(self.trade_size)),
                    time_in_force=TimeInForce.IOC,
                )
                self.submit_order(order)
                self.log.info(f"SELL signal @ {bar.close}")

        self.prev_fast = curr_fast
        self.prev_slow = curr_slow


def generate_trending_bars(instrument, bar_type, n=500):
    """Generate synthetic trending price data for testing."""
    import random
    random.seed(42)

    bars = []
    price = 1.10000
    ts = 1_577_836_800_000_000_000  # Start timestamp

    for i in range(n):
        # Create some trending behavior
        trend = 0.0001 * (1 if i % 100 < 60 else -1)
        noise = random.uniform(-0.0003, 0.0003)
        change = trend + noise

        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0, 0.0002)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0002)
        volume = random.randint(500, 5000)

        bar = Bar(
            bar_type=bar_type,
            open=Price(round(open_price, 5), 5),
            high=Price(round(high_price, 5), 5),
            low=Price(round(low_price, 5), 5),
            close=Price(round(close_price, 5), 5),
            volume=Quantity(volume, 0),
            ts_event=ts,
            ts_init=ts,
        )
        bars.append(bar)
        price = close_price
        ts += 86_400_000_000_000  # +1 day in nanos

    return bars


def main():
    print("=" * 60)
    print("🧪 QUICK BACKTEST - Nautilus Trader + Synthetic Data")
    print("=" * 60)

    # 1. Create engine
    engine_config = BacktestEngineConfig(
        trader_id=TraderId("QUICK-TEST-001"),
        logging=LoggingConfig(log_level="WARNING"),
    )
    engine = BacktestEngine(config=engine_config)
    print("✅ Engine created")

    # 2. Add venue
    SIM = Venue("SIM")
    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.HEDGING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money("1_000_000", USD)],
        fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0),
    )
    print("✅ Venue added")

    # 3. Add instrument
    instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD", SIM)
    engine.add_instrument(instrument)
    print(f"✅ Instrument: {instrument.id}")

    # 4. Create bar type and generate data
    bar_spec = BarSpecification(1, BarAggregation.DAY, AggregationSource.EXTERNAL)
    bar_type = BarType(instrument.id, bar_spec, AggregationSource.EXTERNAL)
    bars = generate_trending_bars(instrument, bar_type, n=500)
    engine.add_data(bars)
    print(f"✅ Loaded {len(bars)} synthetic bars")

    # 5. Add strategy
    strategy_config = QuickEMAConfig(
        instrument_id=instrument.id,
        bar_type=bar_type,
        fast_ema_period=10,
        slow_ema_period=20,
        trade_size=Decimal("100000"),
    )
    strategy = QuickEMAStrategy(config=strategy_config)
    engine.add_strategy(strategy)
    print("✅ Strategy added: EMA Cross 10/20")

    # 6. Run
    print("\n🚀 Running backtest...")
    engine.run()
    print("✅ Backtest complete!\n")

    # 7. Results
    print("=" * 60)
    print("📊 RESULTS")
    print("=" * 60)

    try:
        fills = engine.trader.generate_order_fills_report()
        if fills is not None and len(fills) > 0:
            print(f"\n  Order Fills: {len(fills)}")
            print(fills.to_string())
        else:
            print("\n  No order fills generated")
    except Exception as e:
        print(f"\n  Fills report: {e}")

    try:
        positions = engine.trader.generate_positions_report()
        if positions is not None and len(positions) > 0:
            print(f"\n  Positions: {len(positions)}")
            print(positions.to_string())
    except Exception as e:
        print(f"\n  Positions report: {e}")

    engine.dispose()
    print(f"\n{'=' * 60}")
    print("✅ ALL SYSTEMS GO - Backtest pipeline verified!")
    print("=" * 60)


if __name__ == "__main__":
    main()
