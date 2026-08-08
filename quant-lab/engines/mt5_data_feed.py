"""
MT5 Data Feed Module
====================
Provides MT5 bar fetching and time utilities compatible with the backtest engine.
This is the ONLY place where MT5-specific data fetching logic lives.
All strategy logic remains in symmetry_trap_backtest.py and symmetry_trap.py.
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional

# Add engines directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5

from symmetry_trap import Bar
from configs.asset_configs import ASSET_CONFIGS

logger = logging.getLogger("cerebus.mt5_data_feed")


def fetch_m5_bars(symbol: str, count: int = 1000) -> Optional[List[Bar]]:
    """
    Fetch M5 bars from MT5 and convert to Bar objects compatible with backtest engine.
    
    Args:
        symbol: MT5 symbol (e.g., "EURUSD.PRO", "BTCUSD")
        count: Number of bars to fetch
        
    Returns:
        List of Bar objects sorted by timestamp, or None on failure
    """
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if rates is None or len(rates) == 0:
        logger.warning(f"No bars returned for {symbol}")
        return None
    
    bars = []
    for rate in rates:
        dt = datetime.fromtimestamp(rate["time"])
        bars.append(Bar(
            timestamp=dt,
            open=rate["open"],
            high=rate["high"],
            low=rate["low"],
            close=rate["close"],
        ))
    
    bars.sort(key=lambda b: b.timestamp)
    logger.debug(f"Fetched {len(bars)} bars for {symbol}")
    return bars


def get_latest_bar_timestamp(symbol: str) -> Optional[datetime]:
    """
    Get the timestamp of the most recent M5 bar for a symbol.
    Used for time synchronization - matches backtest engine behavior of using bar timestamps.
    
    Args:
        symbol: MT5 symbol
        
    Returns:
        datetime of latest bar, or None on failure
    """
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1)
    if rates is None or len(rates) == 0:
        return None
    return datetime.fromtimestamp(rates[-1]["time"])


def get_current_est_hour(est_offset: int = -5) -> int:
    """
    Get current EST hour using the latest bar timestamp from any traded symbol.
    This matches the backtest engine's approach of using bar timestamps exclusively.
    
    Args:
        est_offset: EST offset from UTC (default -5)
        
    Returns:
        Current EST hour (0-23)
    """
    # Try to get time from any available symbol
    symbols_to_try = [
        "EURUSD.PRO", "GBPUSD.PRO", "USDCHF.PRO", "USDJPY.PRO",
        "AUDUSD.PRO", "NZDUSD.PRO", "BTCUSD", "ETHUSD", "US500"
    ]
    
    for symbol in symbols_to_try:
        ts = get_latest_bar_timestamp(symbol)
        if ts:
            return (ts.hour + est_offset) % 24
    
    # Fallback to system time if MT5 unavailable
    logger.warning("MT5 time unavailable, falling back to system time")
    from datetime import datetime
    return (datetime.utcnow().hour + est_offset) % 24


def get_symbol_pip_size(symbol: str) -> float:
    """
    Get pip size for a symbol from ASSET_CONFIGS.
    Single source of truth for pip size - used by both backtest and live.
    
    Args:
        symbol: MT5 symbol (e.g., "EURUSD.PRO", "BTCUSD")
        
    Returns:
        Pip size as float
    """
    base_symbol = symbol.replace(".PRO", "")
    config = ASSET_CONFIGS.get(base_symbol)
    if config:
        return config["pip_value"]
    
    # Fallback defaults
    if "JPY" in base_symbol:
        return 0.01
    elif base_symbol in ("XAUUSD", "XAGUSD"):
        return 0.1 if base_symbol == "XAUUSD" else 0.01
    elif base_symbol in ("US500", "DE30", "FR40", "HK50"):
        return 1.0
    elif base_symbol in ("BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"):
        return 1.0
    return 0.0001


def get_symbol_config(symbol: str) -> dict:
    """
    Get full asset config for a symbol from ASSET_CONFIGS.
    Single source of truth for all asset configuration.
    
    Args:
        symbol: MT5 symbol (e.g., "EURUSD.PRO", "BTCUSD")
        
    Returns:
        Config dictionary
    """
    base_symbol = symbol.replace(".PRO", "")
    config = ASSET_CONFIGS.get(base_symbol)
    if not config:
        raise ValueError(f"No configuration found for symbol {symbol} (base: {base_symbol})")
    return config


def build_today_bars(bars: List[Bar], est_offset: int = -5) -> tuple:
    """
    Build today's bars in EST from raw MT5 bars.
    Replicates the backtest engine's day grouping logic exactly.
    
    Args:
        bars: List of Bar objects from MT5
        est_offset: EST offset from UTC
        
    Returns:
        Tuple of (today_bars, today_est_date, yesterday_est_date)
        where today_bars is list of dicts with bar data + est_h
    """
    if not bars:
        return [], None, None
    
    # Use latest bar to determine "today" in EST
    latest_bar = bars[-1]
    mt5_time = latest_bar.timestamp
    today_est = (mt5_time + timedelta(hours=est_offset)).date()
    yesterday_est = today_est - timedelta(days=1)
    
    today_bars = []
    for bar in bars:
        est_dt = bar.timestamp + timedelta(hours=est_offset)
        # Include bars from today AND yesterday (Asian session spans 19:00-03:00 EST across two days)
        if est_dt.date() == today_est or est_dt.date() == yesterday_est:
            today_bars.append({
                "time": int(bar.timestamp.timestamp()),
                "dt": bar.timestamp,
                "est_h": (bar.timestamp.hour + est_offset) % 24,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
            })
    
    return today_bars, today_est, yesterday_est


def calculate_asian_range(today_bars: List[dict], today_est, yesterday_est, pip_size: float) -> tuple:
    """
    Calculate Asian Range (19:00-03:00 EST) from today's bars.
    Replicates the backtest engine's _find_asian_range logic exactly.
    
    Args:
        today_bars: List of bar dicts from build_today_bars
        today_est: Today's EST date
        yesterday_est: Yesterday's EST date
        pip_size: Pip size for this symbol
        
    Returns:
        Tuple of (asian_high, asian_low, asian_range_pips, ar_locked)
    """
    asian_high = 0.0
    asian_low = 99999.0
    ar_locked = False
    asian_bars_count = 0
    asian_hours = set()
    
    for b in today_bars:
        est_dt = b["dt"] + timedelta(hours=-5)  # EST offset is -5
        # Asian session: 19:00-23:59 (yesterday EST) and 00:00-03:00 (today EST)
        if (b["est_h"] >= 19 and est_dt.date() == yesterday_est) or (b["est_h"] < 3 and est_dt.date() == today_est):
            asian_high = max(asian_high, b["high"])
            asian_low = min(asian_low, b["low"])
            asian_bars_count += 1
            asian_hours.add(b["est_h"])
        if b["est_h"] == 3 and est_dt.date() == today_est and not ar_locked:
            ar_locked = True
            break
    
    if asian_high <= 0 or asian_low >= 99999:
        return 0.0, 99999.0, 0.0, False
    
    asian_range_pips = (asian_high - asian_low) / pip_size
    return asian_high, asian_low, asian_range_pips, ar_locked


def filter_trading_bars(today_bars: List[dict], entry_window_start: int = 2, entry_window_end: int = 11) -> List[dict]:
    """
    Filter bars to trading window (default 2AM-11AM EST).
    Replicates backtest engine's trading window filtering.
    
    Args:
        today_bars: List of bar dicts from build_today_bars
        entry_window_start: Start hour (inclusive)
        entry_window_end: End hour (exclusive)
        
    Returns:
        Filtered list of trading bars
    """
    return [b for b in today_bars if entry_window_start <= b["est_h"] < entry_window_end]