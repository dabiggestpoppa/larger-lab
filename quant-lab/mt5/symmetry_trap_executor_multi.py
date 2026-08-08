"""
CEREBUS FX v4.0 — Symmetry Trap Live Multi-Asset Executor
===========================================================
THIN ORCHESTRATION LAYER ONLY.

Architecture:
  - Data Feed: engines/mt5_data_feed.py (MT5 → Bar objects)
  - Strategy: engines/symmetry_trap_live.py (wraps backtest engine logic)
  - Execution: mt5/execution_layer.py (pure MT5 order management)
  - This file: Orchestration only - NO strategy logic

Engine Isolation (cerebus_dual_engine.md):
  - Symmetry Trap SL = Zero-Buffer Impulse Extreme (NOT 80% P90 body)
  - Symmetry Trap TP = 1 AU single target (NOT P90 -25%/-50% AR targets)
  - Entry = OCC after DZ pullback (NOT immediate P90 close)
  - NEVER cross with P90 mechanics
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding="utf-8")

import MetaTrader5 as mt5

# ─── Engine Imports ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.symmetry_trap_live import SymmetryTrapLiveEngine, run_live_scan
from mt5.execution_layer import MT5ExecutionLayer, create_execution_layer
from symmetry_trap import TradeDirection

# ─── CONFIGURATION ────────────────────────────────────────────────────────
# List of symbols to trade (can be overridden by command line)
DEFAULT_SYMBOLS = ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "CHFJPY", "GBPJPY", "GBPAUD", "GBPNZD", "GBPCHF", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD", "USDCAD", "AUDJPY", "AUDNZD", "AUDCHF", "AUDCAD", "NZDJPY", "NZDCHF", "NZDCAD", "CADJPY", "CADCHF", "GBPCAD", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "US500", "DE30", "FR40", "HK50"]

# 8 assets for live trading
SYMBOLS_TO_TRADE = ["ETHUSD", "HK50", "NZDUSD.PRO", "BTCUSD", "US500", "EURUSD.PRO", "USDCHF.PRO", "AUDUSD.PRO"]

# Global parameters (symbol-independent)
GLOBAL_PARAMS = {
    "LotSize": 0.03,
    "MagicNumber": 20260531,
    "ESTOffset": -5,
    "EntryWindowStart": 2,     # 2AM EST
    "EntryWindowEnd": 11,      # 11AM EST
    "HardExitHour": 17,        # 5PM EST
}

LOG_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "live_logs_multi",
)

# ─── LOGGING ──────────────────────────────────────────────────────────────

def log(msg: str):
    """Log with timestamp from latest bar (matches backtest engine time source)."""
    # Use MT5 time from latest bar - same as backtest engine
    from engines.mt5_data_feed import get_latest_bar_timestamp
    ts = None
    for symbol in SYMBOLS_TO_TRADE:
        bar_ts = get_latest_bar_timestamp(symbol)
        if bar_ts:
            ts = bar_ts
            break
    
    if ts is None:
        ts = datetime.utcnow()
    
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts_str}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(
        os.path.join(LOG_DIR, "symmetry_trap_executor_multi.log"), "a", encoding="utf-8"
    ) as f:
        f.write(line + "\n")

# ─── MAIN EXECUTION LOOP ────────────────────────────────────────────────

def run_loop(interval_seconds: int = 30):
    """
    Main loop — runs the Symmetry Trap strategy continuously for multiple symbols.
    Uses the new architecture: Data Feed → Live Engine → Execution Layer
    """
    log("=" * 60)
    log("SYMMETRY TRAP LIVE MULTI-ASSET EXECUTOR — CEREBUS FX v4.0")
    log(f"Symbols: {', '.join(SYMBOLS_TO_TRADE)}")
    log(f"Lot size: {GLOBAL_PARAMS['LotSize']} | Magic: {GLOBAL_PARAMS['MagicNumber']}")
    log(
        f"Entry window: {GLOBAL_PARAMS['EntryWindowStart']}AM-{GLOBAL_PARAMS['EntryWindowEnd']}AM EST | "
        f"Hard exit: {GLOBAL_PARAMS['HardExitHour']}PM"
    )
    log(
        "SL = Zero-Buffer Impulse Extreme | TP = 1 AU | Entry on OCC"
    )
    log("Engine B ONLY — never cross with P90 mechanics")
    log("Architecture: MT5 Data Feed → Live Engine (backtest logic) → Execution Layer")
    log("=" * 60)

    # ─── MT5 Self-Healing Init ───────────────────────────────────────────
    mt5_ok = mt5.initialize()
    if not mt5_ok:
        log("MT5 init failed — will retry in loop (self-heal)")

    acct = mt5.account_info() if mt5_ok else None
    if acct:
        log(
            f"Account: {acct.login} | "
            f"Balance: ${acct.balance:.2f} | "
            f"Server: {acct.server}"
        )

    # Create execution layer
    execution = create_execution_layer(
        magic_number=GLOBAL_PARAMS["MagicNumber"],
        lot_size=GLOBAL_PARAMS["LotSize"]
    )

    log(
        f"Scanning every {interval_seconds}s | loops managed by engine (max 5/session)"
    )
    log("=" * 60)

    try:
        cycle = 0
        last_mt5_check = time.time()
        log("LOOP STARTED — entering main loop")

        while True:
            cycle += 1

            # ── MT5 Health Check (every 120s) ───────────────────────────────
            if time.time() - last_mt5_check > 120:
                try:
                    ai = mt5.account_info()
                    if ai is None:
                        log("⚠ MT5 connection lost — reconnecting...")
                        mt5.shutdown()
                        time.sleep(2)
                        if mt5.initialize():
                            log("✅ MT5 reconnected")
                        else:
                            log("❌ MT5 reconnect failed — will retry next cycle")
                    last_mt5_check = time.time()
                except Exception as recon_err:
                    log(f"MT5 health check error: {recon_err} — will retry")
                    last_mt5_check = time.time()

            # 5PM EST hard exit check (global) - use bar timestamp for time
            from engines.mt5_data_feed import get_current_est_hour
            current_est_hour = get_current_est_hour(GLOBAL_PARAMS["ESTOffset"])
            if current_est_hour >= GLOBAL_PARAMS["HardExitHour"]:
                log(f"Hard exit: {current_est_hour}:00 EST >= {GLOBAL_PARAMS['HardExitHour']}PM — closing all positions")
                closed = execution.hard_exit_all(SYMBOLS_TO_TRADE)
                log(f"Hard exit complete: closed {closed} positions")
                break

            log(f"Cycle {cycle} start")
            cycle_results = []
            
            # Run live scan for all symbols (uses backtest engine logic)
            scan_results = run_live_scan(SYMBOLS_TO_TRADE, est_offset=GLOBAL_PARAMS["ESTOffset"])
            
            for result in scan_results:
                if not isinstance(result, dict):
                    continue
                    
                symbol = result.get("symbol")
                action = result.get("action")
                
                if not symbol:
                    continue
                
                cycle_results.append(result)
                log(f"Cycle {cycle} result for {symbol}: {action}")
                
                # Handle signals that require execution
                if action == "signal" and "direction" in result:
                    # New entry signal
                    direction_str = result["direction"]
                    direction = TradeDirection.LONG if direction_str == "LONG" else TradeDirection.SHORT
                    
                    # Check if we already have a position or pending order
                    pos = execution.check_existing_position(symbol)
                    pending = execution.check_pending_orders(symbol)
                    
                    if pos:
                        log(f"SKIP {symbol}: Position already exists (ticket={pos.ticket})")
                        continue
                    if pending > 0:
                        log(f"SKIP {symbol}: Pending order exists")
                        continue
                    
                    # Place the order
                    exec_result = execution.place_limit_order(
                        symbol=symbol,
                        direction=direction,
                        entry_price=result["entry_price"],
                        sl_price=result["sl"],
                        tp_price=result["tp"],
                    )
                    
                    if exec_result:
                        log(f"ORDER PLACED: {symbol} {direction_str} @ {result['entry_price']:.5f}")
                    else:
                        log(f"ORDER FAILED: {symbol} {direction_str}")
                
                elif action == "hard_exit":
                    # Hard exit for this symbol
                    pos = execution.check_existing_position(symbol)
                    if pos:
                        execution.close_position(pos, "HARD_EXIT")
                
                elif action == "holding":
                    # Position management - check for touch/wick exit
                    pos = execution.check_existing_position(symbol)
                    if pos:
                        exit_trigger = execution.check_touch_exit(pos, symbol)
                        if exit_trigger:
                            log(f"WICK/TOUCH EXIT: {symbol} trigger={exit_trigger}")
                            execution.close_position(pos, reason=f"TOUCH_{exit_trigger}")
                        else:
                            # Log holding PnL
                            pnl_pips = execution.get_position_pnl_pips(pos, symbol)
                            dir_str = "SHORT" if pos.type == mt5.POSITION_TYPE_SELL else "LONG"
                            log(f"HOLDING: {symbol} {dir_str} ticket={pos.ticket} PnL={pnl_pips:+.1f}p")

            # Log summary of cycle
            actions = [r.get('action', 'unknown') for r in cycle_results if isinstance(r, dict)]
            if actions:
                log(f"Cycle {cycle} summary: {actions}")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        log("STOPPED by user")
    except Exception as e:
        log(f"LOOP ERROR: {type(e).__name__}: {e}")
        log(traceback.format_exc())
    finally:
        mt5.shutdown()
        log("MT5 disconnected")


# ─── CLI ENTRY POINT ────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Symmetry Trap Live Multi-Asset Executor — CEREBUS FX v4.0"
    )
    parser.add_argument("--once", action="store_true", help="Run single scan for all symbols")
    parser.add_argument("--loop", action="store_true", help="Run continuous loop")
    parser.add_argument(
        "--interval", type=int, default=30, help="Scan interval (seconds)"
    )
    parser.add_argument(
        "--symbols", type=str, default=None, help="Comma-separated list of symbols to trade (overrides default)"
    )
    args = parser.parse_args()

    if args.symbols:
        SYMBOLS_TO_TRADE = [s.strip().upper() for s in args.symbols.split(",")]

    if args.loop:
        run_loop(args.interval)
    else:
        if not mt5.initialize():
            print("FATAL: Cannot initialize MT5")
            sys.exit(1)
        try:
            # Run once for each symbol and collect results
            results = run_live_scan(SYMBOLS_TO_TRADE, est_offset=GLOBAL_PARAMS["ESTOffset"])
            for result in results:
                print(f"Result: {result}")
            print(f"Total results: {len(results)}")
        finally:
            mt5.shutdown()