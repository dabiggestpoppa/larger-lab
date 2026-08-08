"""
Symmetry Trap Live Engine Wrapper
==================================
Wraps the backtest engine logic for live execution using MT5 data feed.
This is a THIN wrapper - all strategy logic lives in symmetry_trap_backtest.py.
Only the data source changes (MT5 instead of CSV).
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add engines directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5

from symmetry_trap import (
    SymmetryTrapEngine,
    TradeSignal,
    TradeDirection,
    Bar,
    EngineState,
    DEFAULT_TIER_CONFIG,
    TP_MODE,
)
from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    TradeRecord,
    BacktestResult,
    compute_stats,
)
from mt5_data_feed import (
    fetch_m5_bars,
    get_current_est_hour,
    get_symbol_pip_size,
    get_symbol_config,
    build_today_bars,
    calculate_asian_range,
    filter_trading_bars,
)
from trading_costs import apply_costs_to_pnl

logger = logging.getLogger("cerebus.symmetry_trap_live")


class SymmetryTrapLiveEngine:
    """
    Live engine wrapper that uses the exact same logic as SymmetryTrapBacktest
    but fetches data from MT5 instead of CSV files.
    """
    
    def __init__(
        self,
        symbol: str,
        est_offset: int = -5,
        entry_window_start: int = 2,
        entry_window_end: int = 11,
        hard_exit_hour: int = 17,
        lot_size: float = 0.01,
    ):
        self.symbol = symbol
        self.est_offset = est_offset
        self.entry_window_start = entry_window_start
        self.entry_window_end = entry_window_end
        self.hard_exit_hour = hard_exit_hour
        self.lot_size = lot_size
        
        # Get config from ASSET_CONFIGS (single source of truth)
        self.config = get_symbol_config(symbol)
        self.pip_size = self.config["pip_value"]
        
        # Initialize backtest engine with same config
        self.backtest_engine = SymmetryTrapBacktest(
            pip_size=self.pip_size,
            config=self.config,
            est_offset=est_offset,
        )
        
        # Session state
        self.session_initialized = False
        self.asian_high = 0.0
        self.asian_low = 0.0
        self.asian_range_pips = 0.0
        self.today_bars = []
        self.today_est = None
        self.yesterday_est = None
        self.trading_bars = []
        
        logger.info(f"Live engine initialized for {symbol}: pip_size={self.pip_size}")
    
    def refresh_data(self, bar_count: int = 1000) -> bool:
        """
        Fetch latest bars from MT5 and rebuild today's session data.
        Returns True if successful, False otherwise.
        """
        # Fetch bars from MT5
        bars = fetch_m5_bars(self.symbol, bar_count)
        if not bars:
            logger.warning(f"Failed to fetch bars for {self.symbol}")
            return False
        
        # Build today's bars using same logic as backtest
        self.today_bars, self.today_est, self.yesterday_est = build_today_bars(
            bars, self.est_offset
        )
        
        if len(self.today_bars) < 5:
            logger.warning(f"Insufficient bars for {self.symbol}: {len(self.today_bars)}")
            return False
        
        # Calculate Asian Range using same logic as backtest
        self.asian_high, self.asian_low, self.asian_range_pips, ar_locked = calculate_asian_range(
            self.today_bars, self.today_est, self.yesterday_est, self.pip_size
        )
        
        if self.asian_high <= 0 or self.asian_low >= 99999:
            logger.warning(f"No valid Asian Range for {self.symbol}")
            return False
        
        # Filter trading window bars
        self.trading_bars = filter_trading_bars(
            self.today_bars, self.entry_window_start, self.entry_window_end
        )
        
        if not self.trading_bars:
            logger.debug(f"No trading window bars for {self.symbol}")
            return False
        
        # Initialize session in engine (same as backtest)
        self.backtest_engine.engine.initialize_session(self.asian_high, self.asian_low)
        self.session_initialized = self.backtest_engine.engine.session_active
        
        if not self.session_initialized:
            logger.info(f"Session not active for {self.symbol} (AR={self.asian_range_pips:.1f}p)")
            return False
        
        logger.debug(
            f"{self.symbol}: AR={self.asian_range_pips:.1f}p, "
            f"tier={self.backtest_engine.engine.tier_name}, "
            f"trading_bars={len(self.trading_bars)}"
        )
        return True
    
    def scan_for_signal(self) -> Optional[Dict]:
        """
        Scan for Symmetry Trap signal using the exact same logic as backtest.
        Returns signal dict or None.
        """
        if not self.session_initialized:
            return {"action": "session_not_active", "symbol": self.symbol}
        
        # Check hard exit
        current_est_hour = get_current_est_hour(self.est_offset)
        if current_est_hour >= self.hard_exit_hour:
            return {"action": "hard_exit", "symbol": self.symbol}
        
        # Check if we're in trading window
        if not (self.entry_window_start <= current_est_hour < self.entry_window_end):
            return {"action": "outside_window", "symbol": self.symbol, "est_hour": current_est_hour}
        
        # Feed trading bars through engine (same as backtest)
        for b in self.trading_bars:
            bar = Bar(
                timestamp=b["dt"],
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
            )
            signal = self.backtest_engine.engine.process_bar(bar)
            
            if signal and signal.event == "ENTRY":
                direction = "LONG" if signal.direction == TradeDirection.LONG else "SHORT"
                
                logger.info(
                    f"SYMMETRY TRAP SIGNAL: {self.symbol} {direction} "
                    f"entry={signal.entry_price:.5f} "
                    f"SL={signal.sl_price:.5f} (Zero-Buffer) "
                    f"TP={signal.tp_price:.5f} (1 AU = {signal.au_used:.1f}p) "
                    f"tier={self.backtest_engine.engine.tier_name}"
                )
                
                return {
                    "action": "signal",
                    "symbol": self.symbol,
                    "direction": direction,
                    "entry_price": signal.entry_price,
                    "sl": signal.sl_price,
                    "tp": signal.tp_price,
                    "ar_pips": round(self.backtest_engine.engine.asian_range_pips, 1),
                    "tier": self.backtest_engine.engine.tier_name,
                    "au_pips": signal.au_used,
                    "impulse_size_pips": round(self.backtest_engine.engine.impulse_size_pips, 1),
                }
            
            elif signal and signal.event == "KILL_SWITCH":
                logger.info(f"Kill switch activated — no trade today for {self.symbol}")
                return {"action": "kill_switch", "symbol": self.symbol}
            
            elif signal and signal.event in ("TP_HIT", "SL_HIT"):
                logger.info(f"{signal.event}: {self.symbol} loop {signal.loop_count}")
                return {"action": "signal", "symbol": self.symbol, "event": signal.event, "loop_count": signal.loop_count}
        
        return {"action": "no_signal", "symbol": self.symbol}
    
    def calculate_pnl(self, entry_price: float, exit_price: float, direction: str) -> float:
        """
        Calculate net PnL in pips after trading costs.
        Uses the EXACT same function as backtest engine.
        """
        gross_pnl_pips = round(
            (exit_price - entry_price) / self.pip_size
            * (1 if direction == "LONG" else -1), 1
        )
        net_pnl_pips = apply_costs_to_pnl(gross_pnl_pips, self.symbol, direction, self.lot_size)
        return net_pnl_pips


def run_live_scan(symbols: List[str], est_offset: int = -5) -> List[Dict]:
    """
    Run a single scan cycle for all symbols.
    Returns list of signal results.
    """
    results = []
    
    for symbol in symbols:
        try:
            engine = SymmetryTrapLiveEngine(symbol, est_offset=est_offset)
            if engine.refresh_data():
                result = engine.scan_for_signal()
                if result:
                    results.append(result)
            else:
                results.append({"action": "data_refresh_failed", "symbol": symbol})
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            results.append({"action": "error", "symbol": symbol, "error": str(e)})
    
    return results