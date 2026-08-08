"""
MT5 Execution Layer
===================
Pure MT5 order and position management.
NO strategy logic - only execution.
Takes signals from live engine and executes them on MT5.
"""

from __future__ import annotations

import logging
import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add engines directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engines"))

import MetaTrader5 as mt5

from symmetry_trap import TradeDirection

logger = logging.getLogger("cerebus.mt5_execution")


class MT5ExecutionLayer:
    """
    Handles all MT5 order placement, position management, and trade closure.
    Pure execution - no strategy logic.
    """
    
    def __init__(self, magic_number: int = 20260531, lot_size: float = 0.03):
        self.magic_number = magic_number
        self.lot_size = lot_size
    
    def get_symbol_info(self, symbol: str) -> Optional[object]:
        """Get MT5 symbol info."""
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.error(f"Cannot get info for {symbol}")
        return info
    
    def normalize_price(self, symbol: str, price: float) -> float:
        """Normalize price to symbol's digits."""
        info = self.get_symbol_info(symbol)
        if not info:
            return price
        return round(price, info.digits)
    
    def get_min_stop_distance(self, symbol: str) -> float:
        """Get broker's minimum stop distance (STOPLEVEL) in price units."""
        info = self.get_symbol_info(symbol)
        if not info:
            return 0
        return info.trade_stops_level * info.point
    
    def check_existing_position(self, symbol: str) -> Optional[object]:
        """Check for existing position with our magic number."""
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            for pos in positions:
                if pos.magic == self.magic_number:
                    return pos
        return None
    
    def check_pending_orders(self, symbol: str) -> int:
        """Check for pending orders with our magic number."""
        orders = mt5.orders_get(symbol=symbol)
        if orders:
            return sum(1 for o in orders if o.magic == self.magic_number)
        return 0
    
    def validate_stop_levels(self, symbol: str, direction: TradeDirection, 
                             entry_price: float, sl_price: float, tp_price: float) -> bool:
        """Validate SL/TP distances meet broker's STOPLEVEL requirements."""
        info = self.get_symbol_info(symbol)
        if not info:
            return False
        
        min_stop_dist = self.get_min_stop_distance(symbol)
        if min_stop_dist <= 0:
            return True
        
        entry_r = self.normalize_price(symbol, entry_price)
        sl_r = self.normalize_price(symbol, sl_price)
        tp_r = self.normalize_price(symbol, tp_price)
        
        if direction == TradeDirection.LONG:
            sl_dist = entry_r - sl_r
            tp_dist = tp_r - entry_r
        else:
            sl_dist = sl_r - entry_r
            tp_dist = entry_r - tp_r
        
        if sl_dist < min_stop_dist:
            logger.warning(f"SKIP {symbol}: SL distance {sl_dist:.5f} < min {min_stop_dist:.5f}")
            return False
        if tp_dist < min_stop_dist:
            logger.warning(f"SKIP {symbol}: TP distance {tp_dist:.5f} < min {min_stop_dist:.5f}")
            return False
        
        return True
    
    def normalize_volume(self, symbol: str, volume: float) -> float:
        """Normalize volume to symbol's volume step."""
        info = self.get_symbol_info(symbol)
        if not info:
            return volume
        
        volume_step = info.volume_step
        vol = round(volume / volume_step) * volume_step
        if vol < info.volume_min:
            vol = info.volume_min
        if vol > info.volume_max:
            vol = info.volume_max
        return vol
    
    def place_limit_order(self, symbol: str, direction: TradeDirection,
                          entry_price: float, sl_price: float, tp_price: float) -> Optional[object]:
        """
        Place a limit order with SL/TP on MT5.
        Returns MT5 TradeResult or None on failure.
        """
        # Validate stop levels
        if not self.validate_stop_levels(symbol, direction, entry_price, sl_price, tp_price):
            return None
        
        info = self.get_symbol_info(symbol)
        if not info:
            return None
        
        entry_r = self.normalize_price(symbol, entry_price)
        sl_r = self.normalize_price(symbol, sl_price)
        tp_r = self.normalize_price(symbol, tp_price)
        volume = self.normalize_volume(symbol, self.lot_size)
        
        if direction == TradeDirection.LONG:
            otype = mt5.ORDER_TYPE_BUY_LIMIT
        else:
            otype = mt5.ORDER_TYPE_SELL_LIMIT
        
        req = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": otype,
            "price": entry_r,
            "sl": sl_r,
            "tp": tp_r,
            "magic": self.magic_number,
            "comment": f"ST_{'LONG' if direction == TradeDirection.LONG else 'SHORT'}",
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        # Retry logic for trade context busy
        max_retries = 3
        for attempt in range(max_retries):
            result = mt5.order_send(req)
            if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                logger.info(
                    f"ORDER PLACED: {symbol} {'LONG' if direction == TradeDirection.LONG else 'SHORT'} "
                    f"@ {entry_r:.5f} SL={sl_r:.5f} TP={tp_r:.5f}"
                )
                return result
            elif result and result.retcode == mt5.TRADE_RETCODE_BUSY:
                logger.warning(f"RETRY {attempt+1}/{max_retries}: {symbol} trade context busy")
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                logger.error(
                    f"ORDER FAILED: {symbol} retcode={result.retcode if result else 'None'} "
                    f"comment={result.comment if result else 'None'}"
                )
                return None
        
        return None
    
    def close_position(self, position, reason: str = "MANUAL") -> bool:
        """
        Close a position.
        Returns True on success, False on failure.
        """
        if position is None:
            return False
        
        symbol = position.symbol
        is_short = position.type == mt5.POSITION_TYPE_SELL
        order_type = mt5.ORDER_TYPE_BUY if is_short else mt5.ORDER_TYPE_SELL
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger.error(f"No tick for {symbol}")
            return False
        
        price = tick.ask if is_short else tick.bid
        digits = self.get_symbol_info(symbol).digits if self.get_symbol_info(symbol) else 0
        
        # Try filling modes: IOC → RETURN → FOK
        filling_modes = [
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_RETURN,
            mt5.ORDER_FILLING_FOK,
        ]
        
        result = None
        for fill_mode in filling_modes:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": order_type,
                "price": round(price, digits),
                "position": position.ticket,
                "magic": position.magic,
                "comment": f"ST_{reason}",
                "type_filling": fill_mode,
            }
            result = mt5.order_send(request)
            if result and result.retcode in (
                mt5.TRADE_RETCODE_DONE,
                mt5.TRADE_RETCODE_PLACED,
            ):
                break
            logger.warning(f"CLOSE FAILED (filling={fill_mode}): {result.retcode if result else 'None'}")
            if result and result.retcode != mt5.TRADE_RETCODE_INVALID_FILL:
                break
        
        if result and result.retcode in (
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_PLACED,
        ):
            # Calculate PnL in pips
            pip_size = 0.01 if "JPY" in symbol or "XAU" in symbol or "XAG" in symbol else 0.0001
            pnl_pips = round(
                (position.price_open - price) / pip_size if is_short
                else (price - position.price_open) / pip_size,
                1,
            )
            logger.info(f"CLOSED: {symbol} {reason} PnL={pnl_pips:+.1f}p")
            return True
        
        logger.error(f"CLOSE FAILED: all filling modes exhausted for ticket={position.ticket}")
        return False
    
    def check_touch_exit(self, position, symbol: str) -> Optional[str]:
        """
        Check if position should be closed due to wick/touch of SL or TP.
        Returns "SL", "TP", or None.
        """
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return None
        
        # Get latest bar for wick check
        bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 2)
        if bars is None or len(bars) < 1:
            return None
        
        latest_bar = bars[-1]
        bar_high = float(latest_bar["high"])
        bar_low = float(latest_bar["low"])
        
        current_price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
        
        sl_price = getattr(position, "sl", None)
        tp_price = getattr(position, "tp", None)
        
        if sl_price is None or tp_price is None:
            return None
        
        direction_str = "LONG" if position.type == mt5.POSITION_TYPE_BUY else "SHORT"
        
        if direction_str == "LONG":
            if (current_price is not None and current_price <= sl_price) or bar_low <= sl_price:
                return "SL"
            if (current_price is not None and current_price >= tp_price) or bar_high >= tp_price:
                return "TP"
        elif direction_str == "SHORT":
            if (current_price is not None and current_price >= sl_price) or bar_high >= sl_price:
                return "SL"
            if (current_price is not None and current_price <= tp_price) or bar_low <= tp_price:
                return "TP"
        
        return None
    
    def get_position_pnl_pips(self, position, symbol: str) -> float:
        """Get current unrealized PnL in pips for a position."""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return 0.0
        
        pip_size = 0.01 if "JPY" in symbol or "XAU" in symbol or "XAG" in symbol else 0.0001
        
        if position.type == mt5.POSITION_TYPE_SELL:
            pnl = (position.price_open - tick.bid) / pip_size
        else:
            pnl = (tick.ask - position.price_open) / pip_size
        
        return round(pnl, 1)
    
    def hard_exit_all(self, symbols: List[str]) -> int:
        """Close all positions for given symbols. Returns count of closed positions."""
        closed = 0
        for symbol in symbols:
            pos = self.check_existing_position(symbol)
            if pos:
                if self.close_position(pos, "HARD_EXIT"):
                    closed += 1
        return closed


def create_execution_layer(magic_number: int = 20260531, lot_size: float = 0.03) -> MT5ExecutionLayer:
    """Factory function to create execution layer."""
    return MT5ExecutionLayer(magic_number=magic_number, lot_size=lot_size)