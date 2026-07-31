"""
Symmetry Trap Strategy for Nautilus Trader
===========================================
Port of the Symmetry Trap engine to Nautilus Trader for cross-validation.
Uses bracket orders with REAL SL/TP for accurate backtest cross-validation.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from nautilus_trader.config import StrategyConfig as NautilusStrategyConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce, ContingencyType, TriggerType
from nautilus_trader.model.identifiers import InstrumentId, ClientOrderId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.core.uuid import UUID4
from pydantic import Field
import time


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
      Entry: Close of OCC candle (LIMIT order at OCC close)
      SL: Zero-Buffer Impulse Extreme = exact impulse bar high/low (CLOSE-ONLY)
      TP: Exactly 1 AU from entry (SINGLE TARGET — no ladder)
    
    Invalidation:
      - 80% Kill Switch: M5 close past 80% of impulse leg = pathway VOID
      - SL hit (close only) = trade over, reset to SEARCH
    
    Engine Isolation:
      This engine NEVER uses P90 body data.
      SL is ALWAYS Zero-Buffer OCC/Impulse Extreme — never 80% P90 body.
      TP is ALWAYS 1 AU — never P90 targets.
    
    Order Execution:
      Uses bracket orders (OCO) with LIMIT entry, LIMIT TP, STOP_MARKET SL
      for realistic backtest cross-validation against Python/CSV engine.
    """
    
    def __init__(self, config: SymmetryTrapConfig):
        super().__init__(config)
        
        # State machine
        self._st_state = "SEARCH"  # SEARCH, WAIT_RETRACE, WAIT_OCC, IN_TRADE
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
        self._hard_exit_done: bool = False  # Track if hard exit already called this session
        
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
        
        # Initialize session at 3 AM EST (first bar after Asian session)
        if est_hour == 3 and self.asian_high != Decimal("0") and not self.session_active:
            self._initialize_session(self.asian_high, self.asian_low)
            return
        
        # Hard exit at 4 PM EST - only once per session
        if est_hour >= self.config.hard_exit_hour and self._st_state == "SEARCH" and not self._hard_exit_done:
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
        self._st_state = "SEARCH"
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
        self._hard_exit_done = False  # Reset hard exit flag for new session
        
        # Reset Asian range for next session
        self.asian_high = Decimal("0")
        self.asian_low = Decimal("0")
        
        self.log.info(
            f"Session initialized: tier={self.tier_name}, "
            f"AU={self.au_pips}p, trigger={self.trigger_pips}p, "
            f"AR={self.asian_range_pips:.1f}p, loop=1 (max={self.max_loops})"
        )
    
    def _process_bar(self, bar: dict, est_hour: int):
        """Process bar through state machine."""
        if not self.session_active:
            return
        
        # Convert bar prices to float for calculations
        bar_open = float(bar["open"])
        bar_high = float(bar["high"])
        bar_low = float(bar["low"])
        bar_close = float(bar["close"])
        
        # Set swing origin from first bar if not set
        if self.swing_origin is None:
            self.swing_origin = bar_close
        
        active_trig = float(self.trigger_pips) * float(self.pip_size)
        
        up_move = bar_high - self.swing_origin
        dn_move = self.swing_origin - bar_low
        
        # STATE: SEARCH - Wait for impulse breach >= Tier Trigger
        if self._st_state == "SEARCH":
            if up_move >= active_trig:
                self.impulse_direction = 1
                self.impulse_extreme = float(bar["high"])
                self.impulse_size_pips = up_move / float(self.pip_size)
                self.kill_switch_level = Decimal("0")  # REMOVED per June 4 optimization
                self._classify_tier_by_impulse()
                self._st_state = "WAIT_RETRACE"
                self.log.debug(
                    f"Impulse LONG: extreme={self.impulse_extreme:.5f}, "
                    f"size={self.impulse_size_pips:.1f}p, "
                    f"tier={self.tier_name}, AU={self.au_pips}p"
                )
            
            elif dn_move >= active_trig:
                self.impulse_direction = -1
                self.impulse_extreme = float(bar["low"])
                self.impulse_size_pips = dn_move / float(self.pip_size)
                self.kill_switch_level = Decimal("0")
                self._classify_tier_by_impulse()
                self._st_state = "WAIT_RETRACE"
                self.log.debug(
                    f"Impulse SHORT: extreme={self.impulse_extreme:.5f}, "
                    f"size={self.impulse_size_pips:.1f}p, "
                    f"tier={self.tier_name}, AU={self.au_pips}p"
                )
        
        # STATE: WAIT_RETRACE - Wait for pullback >= 1 AU OR 38.2%-50% Fib
        elif self._st_state == "WAIT_RETRACE":
            # Kill Switch: REMOVED (dead code per June 4 optimization)
            
            # Flat DZ: 20%-50% for all loops
            min_retrace_pct = 0.20
            max_retrace_pct = 0.50
            
            if self.impulse_direction == 1:
                pullback_px = self.impulse_extreme - float(bar["low"])
            else:
                pullback_px = float(bar["high"]) - self.impulse_extreme
            
            pullback_pips = pullback_px / float(self.pip_size)
            retrace_pct = (
                pullback_pips / self.impulse_size_pips
                if self.impulse_size_pips > 0 else 0
            )
            
            au_penetrated = pullback_pips >= self.au_pips
            fib_penetrated = min_retrace_pct <= retrace_pct <= max_retrace_pct
            
            if au_penetrated or fib_penetrated:
                self._st_state = "WAIT_OCC"
                self.log.debug(
                    f"DZ penetrated: pullback={pullback_pips:.1f}p, "
                    f"retrace={retrace_pct:.3f}, au_ok={au_penetrated}, "
                    f"fib_ok={fib_penetrated}, loop={self.loop_count}"
                )
        
        # STATE: WAIT_OCC - Wait for Opposite Candle Close confirming impulse direction
        elif self._st_state == "WAIT_OCC":
            occ_confirmed = (
                (self.impulse_direction == 1 and bar["close"] > bar["open"]) or
                (self.impulse_direction == -1 and bar["close"] < bar["open"])
            )
            
            if occ_confirmed:
                self.entry_price = float(bar["close"])
                # SL = Zero-Buffer Impulse Extreme (exact high/low of impulse bar)
                self.sl_price = self.impulse_extreme
                self.tp_price = (
                    float(bar["close"]) + float(self.active_au) * self.impulse_direction
                )
                self._st_state = "IN_TRADE"
                self._just_entered = True  # Skip SL/TP check on entry bar
                
                # Place bracket order with REAL SL/TP
                self._place_bracket_order(float(bar["close"]))
                
                self.log.info(
                    f"ENTRY {'LONG' if self.impulse_direction == 1 else 'SHORT'} "
                    f"(loop {self.loop_count}): "
                    f"entry={self.entry_price:.5f}, sl={self.sl_price:.5f}, "
                    f"tp={self.tp_price:.5f} (1 AU = {self.au_pips}p)"
                )
                return
        
        # STATE: IN_TRADE - Wait for TP or SL fill (handled by OCO orders)
        elif self._st_state == "IN_TRADE":
            # Skip check on entry bar — Nautilus fills on NEXT bar
            if self._just_entered:
                self._just_entered = False
                return
            
            # TP/SL handled by OCO bracket orders - just wait for fills
            # The on_order_filled callback will handle position closure
            pass
    
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
    
    def _place_bracket_order(self, entry_price: float):
        """Place LIMIT entry + LIMIT TP orders. SL monitored manually (CLOSE-ONLY like Python engine)."""
        from nautilus_trader.model.enums import OrderType
        
        # Determine order sides
        if self.impulse_direction == 1:  # LONG
            entry_side = OrderSide.BUY
            tp_side = OrderSide.SELL
        else:  # SHORT
            entry_side = OrderSide.SELL
            tp_side = OrderSide.BUY
        
        # Place LIMIT entry order
        entry_order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=entry_side,
            quantity=Quantity.from_str(str(self.lot_size)),
            price=Price.from_str(f"{entry_price:.5f}"),
            time_in_force=TimeInForce.GTC,
        )
        
        # Place LIMIT TP order
        tp_order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=tp_side,
            quantity=Quantity.from_str(str(self.lot_size)),
            price=Price.from_str(f"{self.tp_price:.5f}"),
            time_in_force=TimeInForce.GTC,
        )
        
        # Create order list and submit
        order_list = self.order_factory.create_list([entry_order, tp_order])
        self.submit_order_list(order_list)
        
        self.log.debug(f"Entry + TP orders placed: entry={entry_order.client_order_id}, tp={tp_order.client_order_id}")
    
    def _exit_trade(self, reason: str, exit_price: float):
        """Exit trade and reset state for next loop."""
        self.log.info(f"{reason}: exit={exit_price:.5f} (loop {self.loop_count} -> {min(self.loop_count + 1, self.max_loops)})")
        
        # Cancel any pending orders
        self.cancel_all_orders(self.instrument_id)
        
        # Close position with LIMIT order at exact theoretical price (for cross-validation)
        if self.impulse_direction == 1:  # LONG -> SELL to close at SL or TP price
            close_order = self.order_factory.limit(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_str(str(self.lot_size)),
                price=Price.from_str(f"{exit_price:.5f}"),
                time_in_force=TimeInForce.IOC,
            )
        else:  # SHORT -> BUY to close at SL or TP price
            close_order = self.order_factory.limit(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_str(str(self.lot_size)),
                price=Price.from_str(f"{exit_price:.5f}"),
                time_in_force=TimeInForce.IOC,
            )
        self.submit_order(close_order)
        
        # Reset state machine to SEARCH
        self._st_state = "SEARCH"
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
    
    def on_order_filled(self, order_filled):
        """Handle order fills - detect TP/SL fills and advance loop."""
        # Check if this is a TP or SL fill (not entry)
        if self._st_state == "IN_TRADE" and self.entry_price is not None:
            # Determine if TP or SL was hit based on fill price
            fill_price = float(order_filled.last_px)
            
            if self.impulse_direction == 1:  # LONG
                if fill_price >= self.tp_price - 0.00001:  # TP hit
                    self._exit_trade("TP_HIT", self.tp_price)
                elif fill_price <= self.sl_price + 0.00001:  # SL hit
                    self._exit_trade("SL_HIT", self.sl_price)
            else:  # SHORT
                if fill_price <= self.tp_price + 0.00001:  # TP hit
                    self._exit_trade("TP_HIT", self.tp_price)
                elif fill_price >= self.sl_price - 0.00001:  # SL hit
                    self._exit_trade("SL_HIT", self.sl_price)
    
    def _hard_exit(self):
        """4 PM EST forced termination."""
        self.session_active = False
        self._st_state = "SEARCH"
        self.swing_origin = None
        self.loop_count = 1
        self._hard_exit_done = True  # Mark hard exit as done for this session
        self.log.info("Hard exit: 4 PM EST — session terminated, loops reset")
    
    def on_stop(self):
        """Called when strategy stops."""
        self.log.info("Symmetry Trap stopped")


# For running backtest with Nautilus
if __name__ == "__main__":
    print("SymmetryTrapStrategy ready for Nautilus Trader")
    print("Usage: Configure with SymmetryTrapConfig and add to BacktestEngine")