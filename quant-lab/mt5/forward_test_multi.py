"""
CEREBUS FX v4.0 — Symmetry Trap Forward Test Multi-Asset
=========================================================
Simple forward test to verify live behavior matches backtest expectations.
Runs for a specified duration and logs signals.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

sys.stdout.reconfigure(encoding="utf-8")

import MetaTrader5 as mt5

# ─── Engine Import ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.symmetry_trap import (
    SymmetryTrapEngine,
    TradeSignal,
    TradeDirection,
    Bar,
    EngineState,
    DEFAULT_TIER_CONFIG,
)
from configs.asset_configs import ASSET_CONFIGS

# ─── CONFIGURATION ────────────────────────────────────────────────────────
# Test the 8 assets mentioned
SYMBOLS_TO_TEST = ["ETHUSD", "HK50", "NZDUSD", "BTCUSD", "US500", "EURUSD", "USDCHF", "AUDUSD"]

TEST_DURATION_MINUTES = 30  # Run test for 30 minutes
LOG_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "forward_test_logs",
)

# ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────

def get_symbol_config(symbol: str) -> Dict:
    """Get configuration for a symbol from ASSET_CONFIGS."""
    config = ASSET_CONFIGS.get(symbol)
    if not config:
        raise ValueError(f"No configuration found for symbol {symbol}")
    return config

def get_params_for_symbol(symbol: str) -> Dict:
    """Build PARAMS dictionary for a given symbol."""
    config = get_symbol_config(symbol)
    params = {
        "LotSize": 0.03,
        "MagicNumber": 20260531,
        "Symbol": symbol,
        "PipSize": config["pip_value"],
        "SpreadPips": 0.0,
        "Point": 0.0,
        "Digits": 0,
        "MaxAR": config["tiers"]["T3"]["ar_max"],
        "MinAR": 3.0,
        "ESTOffset": -5,
        "EntryWindowStart": 2,
        "EntryWindowEnd": 11,
        "HardExitHour": 17,
    }
    return params

def update_symbol_params(symbol: str, params: Dict) -> Dict:
    """Update params with MT5 symbol info."""
    info = mt5.symbol_info(symbol)
    if info:
        params["SpreadPips"] = info.spread * info.point * 10000
        params["Point"] = info.point
        params["Digits"] = info.digits
    return params

def normalize_price(symbol: str, price: float) -> float:
    """Normalize price to symbol's digits."""
    info = mt5.symbol_info(symbol)
    if not info:
        return price
    return round(price, info.digits)

def log_test(msg: str):
    """Log to both console and test log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(
        os.path.join(LOG_DIR, "forward_test.log"), "a", encoding="utf-8"
    ) as f:
        f.write(line + "\n")

def fetch_recent_bars(symbol: str, count: int = 500):
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if bars is None or len(bars) == 0:
        return None
    return bars

def scan_for_symmetry_trap_signal(symbol: str, params: Dict) -> Optional[Dict]:
    """
    Scan M5 bars for Symmetry Trap signals using SymmetryTrapEngine for a given symbol.
    Returns signal dict or None.
    """
    # Build engine for this symbol
    engine = SymmetryTrapEngine(
        pip_size=params["PipSize"],
        tier_config=DEFAULT_TIER_CONFIG,
        symbol=symbol,
    )
    
    # Build today's bars in EST
    now = datetime.utcnow()
    today_est = (now + timedelta(hours=params["ESTOffset"])).date()

    bars = fetch_recent_bars(symbol, 500)
    if bars is None:
        return None

    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar["time"])
        est_dt = dt + timedelta(hours=params["ESTOffset"])
        if est_dt.date() == today_est:
            today_bars.append({
                "time": bar["time"],
                "dt": dt,
                "est_h": (dt.hour + params["ESTOffset"]) % 24,
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
            })

    if len(today_bars) < 5:
        return None

    # Asian Range (7PM-3AM EST)
    asian_high = 0.0
    asian_low = 99999.0
    ar_locked = False
    for b in today_bars:
        if b["est_h"] >= 19 or b["est_h"] < 3:
            asian_high = max(asian_high, b["high"])
            asian_low = min(asian_low, b["low"])
        if b["est_h"] == 3 and not ar_locked:
            ar_locked = True
            if 0 < asian_high and asian_low < 99999:
                ar_pips = ((asian_high - asian_low) / params["PipSize"])
                if ar_pips < params["MinAR"] or ar_pips > params["MaxAR"]:
                    log_test(f"SKIP DAY {symbol}: AR={ar_pips:.1f}p out of bounds")
                    return None
            break

    if asian_high <= 0 or asian_low >= 99999:
        return None

    # Trading window: 2AM-11AM EST
    trading_bars = [b for b in today_bars if 2 <= b["est_h"] < 11]

    if not trading_bars:
        return None

    # Feed all trading bars through engine
    for b in trading_bars:
        bar = Bar(
            timestamp=b["dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        signal = engine.process_bar(bar)

        if signal and signal.event == "ENTRY":
            direction = (
                "LONG"
                if signal.direction == TradeDirection.LONG
                else "SHORT"
            )

            log_test(
                f"SYMMETRY TRAP SIGNAL: {symbol} {direction} "
                f"entry={signal.entry_price:.5f} "
                f"SL={signal.sl_price:.5f} (Zero-Buffer) "
                f"TP={signal.tp_price:.5f} (1 AU = {signal.au_used:.1f}p) "
                f"tier={engine.tier_name}"
            )

            return {
                "symbol": symbol,
                "direction": direction,
                "entry_price": signal.entry_price,
                "sl": signal.sl_price,
                "tp": signal.tp_price,
                "ar_pips": round(engine.asian_range_pips, 1),
                "tier": engine.tier_name,
                "au_pips": signal.au_used,
                "impulse_size_pips": round(
                    engine.impulse_size_pips, 1
                ),
                "timestamp": datetime.now().isoformat()
            }

        elif signal and signal.event == "KILL_SWITCH":
            log_test(f"Kill switch activated — no trade today for {symbol}")
            return None
        elif signal and signal.event in ("TP_HIT", "SL_HIT"):
            # Trade resolved intraday — no new entry
            log_test(f"{signal.event}: {symbol} loop {signal.loop_count}")
            return None

    return None

# ─── MAIN FORWARD TEST ────────────────────────────────────────────────────

def run_forward_test():
    """
    Run forward test for specified duration.
    """
    log_test("=" * 60)
    log_test("SYMMETRY TRAP FORWARD TEST — MULTI-ASSET")
    log_test(f"Symbols: {', '.join(SYMBOLS_TO_TEST)}")
    log_test(f"Duration: {TEST_DURATION_MINUTES} minutes")
    log_test("=" * 60)

    # ─── MT5 Init ───────────────────────────────────────────────
    if not mt5.initialize():
        log_test("FATAL: Cannot initialize MT5")
        return

    acct = mt5.account_info()
    if acct:
        log_test(
            f"Account: {acct.login} | "
            f"Balance: ${acct.balance:.2f} | "
            f"Server: {acct.server}"
        )

    # Update params for each symbol with MT5 info
    symbol_params = {}
    for symbol in SYMBOLS_TO_TEST:
        try:
            params = get_params_for_symbol(symbol)
            params = update_symbol_params(symbol, params)
            symbol_params[symbol] = params
            log_test(f"Initialized {symbol}: PipSize={params['PipSize']}, Digits={params['Digits']}")
        except Exception as e:
            log_test(f"ERROR initializing {symbol}: {e}")

    log_test("=" * 60)
    log_test("Starting forward test...")
    log_test("=" * 60)

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=TEST_DURATION_MINUTES)
    signal_count = 0
    check_count = 0

    try:
        while datetime.now() < end_time:
            check_count += 1
            log_test(f"--- Check {check_count} at {datetime.now().strftime('%H:%M:%S')} ---")
            
            for symbol in SYMBOLS_TO_TEST:
                if symbol not in symbol_params:
                    continue
                    
                try:
                    params = symbol_params[symbol]
                    signal = scan_for_symmetry_trap_signal(symbol, params)
                    if signal:
                        signal_count += 1
                        log_test(f"SIGNAL #{signal_count}: {signal}")
                    else:
                        log_test(f"No signal for {symbol}")
                except Exception as e:
                    log_test(f"ERROR scanning {symbol}: {e}")

            # Sleep for 30 seconds between checks
            time.sleep(30)

    except KeyboardInterrupt:
        log_test("TEST STOPPED by user")
    except Exception as e:
        log_test(f"TEST ERROR: {type(e).__name__}: {e}")
    finally:
        mt5.shutdown()
        log_test("MT5 disconnected")

    # Final summary
    elapsed = datetime.now() - start_time
    log_test("=" * 60)
    log_test("FORWARD TEST COMPLETE")
    log_test(f"Duration: {elapsed}")
    log_test(f"Total checks: {check_count}")
    log_test(f"Total signals: {signal_count}")
    log_test("=" * 60)


if __name__ == "__main__":
    run_forward_test()