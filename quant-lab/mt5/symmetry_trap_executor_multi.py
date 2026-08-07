"""
CEREBUS FX v4.0 — Symmetry Trap Live Multi-Asset Executor
===========================================================
MT5 live executor for Symmetry Trap strategy across multiple assets.
Follows the DMR executor pattern for each asset.

Engine Isolation (cerebus_dual_engine.md):
  - Symmetry Trap SL = Zero-Buffer Impulse Extreme (NOT 80% P90 body)
  - Symmetry Trap TP = 1 AU single target (NOT P90 -25%/-50% AR targets)
  - Entry = OCC after DZ pullback (NOT immediate P90 close)
  - NEVER cross with P90 mechanics
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, time as dtime
from typing import Dict, List, Optional

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
# List of symbols to trade (can be overridden by command line)
DEFAULT_SYMBOLS = ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "CHFJPY", "GBPJPY", "GBPAUD", "GBPNZD", "GBPCHF", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD", "USDCAD", "AUDJPY", "AUDNZD", "AUDCHF", "AUDCAD", "NZDJPY", "NZDCHF", "NZDCAD", "CADJPY", "CADCHF", "GBPCAD", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "US500", "DE30", "FR40", "HK50"]

# We'll focus on the 8 assets mentioned, but can trade all if needed.
# For now, let's use the 8 assets: ETHUSD, HK50, NZDUSD, BTCUSD, US500, EURUSD, USDCHF, AUDUSD
# Note: HK50 had zero trades in backtest, but we include it anyway.
SYMBOLS_TO_TRADE = ["ETHUSD", "HK50", "NZDUSD", "BTCUSD", "US500", "EURUSD", "USDCHF", "AUDUSD"]

# Global parameters that are symbol-independent
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
    params = GLOBAL_PARAMS.copy()
    params.update({
        "Symbol": symbol,
        "PipSize": config["pip_value"],
        "SpreadPips": 0.0,  # Will be updated from MT5
        "Point": 0.0,       # Will be updated from MT5
        "Digits": 0,        # Will be updated from MT5
        "MaxAR": config["tiers"]["T3"]["ar_max"],  # Use T3 ar_max as max AR (conservative)
        "MinAR": 3.0,
        "ESTOffset": -5,
        "EntryWindowStart": 2,     # 2AM EST
        "EntryWindowEnd": 11,      # 11AM EST
        "HardExitHour": 17,        # 5PM EST
    })
    return params

def pips_to_price(pips: float, pip_size: float) -> float:
    return pips / (10000.0 if pip_size == 0.0001 else 100.0)

def price_to_pips(price: float, pip_size: float) -> float:
    return price * (10000.0 if pip_size == 0.0001 else 100.0)

def get_est_hour(dt: datetime, est_offset: int) -> int:
    return (dt.hour + est_offset) % 24

def get_est_hour_now(est_offset: int) -> int:
    return (datetime.utcnow().hour + est_offset) % 24

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(
        os.path.join(LOG_DIR, "symmetry_trap_executor_multi.log"), "a", encoding="utf-8"
    ) as f:
        f.write(line + "\n")

# ─── MT5 HELPERS (PER SYMBOL) ────────────────────────────────────────────

def get_symbol_info(symbol: str) -> Optional[object]:
    info = mt5.symbol_info(symbol)
    if info is None:
        log(f"ERROR: Cannot get info for {symbol}")
        return None
    return info

def update_symbol_params(symbol: str, params: Dict):
    """Update params with MT5 symbol info."""
    info = get_symbol_info(symbol)
    if info:
        params["SpreadPips"] = info.spread * info.point * 10000
        params["Point"] = info.point
        params["Digits"] = info.digits
    return params

def fetch_recent_bars(symbol: str, count: int = 500):
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if bars is None or len(bars) == 0:
        return None
    return bars

def check_existing_position(symbol: str, magic: int):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for pos in positions:
            if pos.magic == magic:
                return pos
    return None

def check_pending_orders(symbol: str, magic: int) -> int:
    orders = mt5.orders_get(symbol=symbol)
    if orders:
        return sum(1 for o in orders if o.magic == magic)
    return 0

def normalize_price(symbol: str, price: float) -> float:
    """Normalize price to symbol's digits."""
    info = mt5.symbol_info(symbol)
    if not info:
        return price
    return round(price, info.digits)

def get_min_stop_distance(symbol: str) -> float:
    """Get broker's minimum stop distance (STOPLEVEL) in price units."""
    info = mt5.symbol_info(symbol)
    if not info:
        return 0
    return info.trade_stops_level * info.point

def place_order(symbol: str, direction: TradeDirection, sl_price: float, tp_price: float, entry_price: float, magic: int, lot_size: float) -> Optional[mt5.TradeResult]:
    """Place limit order with REAL SL/TP on MT5 for a given symbol."""
    info = mt5.symbol_info(symbol)
    if not info:
        log(f"ERROR: Cannot get info for {symbol}")
        return None
    
    digits = info.digits
    sl_r = normalize_price(symbol, sl_price)
    tp_r = normalize_price(symbol, tp_price)
    entry_r = normalize_price(symbol, entry_price)

    # Validate STOPLEVEL compliance
    min_stop_dist = get_min_stop_distance(symbol)
    if min_stop_dist > 0:
        if direction == TradeDirection.LONG:
            sl_dist = entry_r - sl_r
            tp_dist = tp_r - entry_r
        else:
            sl_dist = sl_r - entry_r
            tp_dist = entry_r - tp_r
        
        if sl_dist < min_stop_dist:
            log(f"SKIP {symbol}: SL distance {sl_dist:.5f} < min {min_stop_dist:.5f}")
            return None
        if tp_dist < min_stop_dist:
            log(f"SKIP {symbol}: TP distance {tp_dist:.5f} < min {min_stop_dist:.5f}")
            return None

    # Validate volume step
    volume_step = info.volume_step
    lot = round(lot_size / volume_step) * volume_step
    if lot < info.volume_min:
        lot = info.volume_min
    if lot > info.volume_max:
        lot = info.volume_max

    if direction == TradeDirection.LONG:
        otype = mt5.ORDER_TYPE_BUY_LIMIT
        oprice = entry_r
    else:
        otype = mt5.ORDER_TYPE_SELL_LIMIT
        oprice = entry_r

    req = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": otype,
        "price": oprice,
        "sl": sl_r,
        "tp": tp_r,
        "magic": magic,
        "comment": f"ST_{'LONG' if direction == TradeDirection.LONG else 'SHORT'}",
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    # Thread-safe order send with retry
    max_retries = 3
    for attempt in range(max_retries):
        result = mt5.order_send(req)
        if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            log(f"ORDER PLACED: {symbol} {'LONG' if direction == TradeDirection.LONG else 'SHORT'} @ {entry_r:.5f} SL={sl_r:.5f} TP={tp_r:.5f}")
            return result
        elif result and result.retcode == mt5.TRADE_RETCODE_BUSY:
            log(f"RETRY {attempt+1}/{max_retries}: {symbol} trade context busy (10027)")
            time.sleep(0.5 * (attempt + 1))
            continue
        else:
            log(f"ORDER FAILED: {symbol} retcode={result.retcode if result else 'None'} comment={result.comment if result else 'None'}")
            return None
    
    return None

def close_position(pos, reason: str = "MANUAL"):
    """Close a position."""
    if pos is None:
        return False
    symbol = pos.symbol
    is_short = pos.type == mt5.POSITION_TYPE_SELL
    order_type = mt5.ORDER_TYPE_BUY if is_short else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        log(f"ERROR: No tick for {symbol}")
        return False
    price = tick.ask if is_short else tick.bid
    digits = mt5.symbol_info(symbol).digits if mt5.symbol_info(symbol) else 0

    # Try filling modes: IOC → RETURN → FOK
    filling_modes = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN, mt5.ORDER_FILLING_FOK]
    result = None
    for fill_mode in filling_modes:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "price": round(price, digits),
            "position": pos.ticket,
            "magic": pos.magic,
            "comment": f"ST_{reason}",
            "type_filling": fill_mode,
        }
        result = mt5.order_send(request)
        if result and result.retcode in (
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_PLACED,
        ):
            break
        log(f"CLOSE FAILED (filling={fill_mode}): {result.retcode if result else 'None'}")
        if result and result.retcode != mt5.TRADE_RETCODE_INVALID_FILL:
            break

    if result and result.retcode in (
        mt5.TRADE_RETCODE_DONE,
        mt5.TRADE_RETCODE_PLACED,
    ):
        # Calculate PnL in pips
        pip_size = 0.01 if "JPY" in symbol or "XAU" in symbol or "XAG" in symbol else 0.0001
        pnl_pips = round(
            price_to_pips(
                (pos.price_open - price)
                if is_short
                else (price - pos.price_open)
            ) / pip_size,
            1,
        )
        log(f"CLOSED: {symbol} {reason} PnL={pnl_pips:+.1f}p")
        return True

    log(f"CLOSE FAILED: all filling modes exhausted for ticket={pos.ticket}")
    return False

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
    
    # Check existing position
    pos = check_existing_position(symbol, params["MagicNumber"])
    if pos:
        est_hour = get_est_hour_now(params["ESTOffset"])
        if est_hour >= params["HardExitHour"]:
            close_position(pos, "HARD_EXIT")
            return {"action": "hard_exit", "symbol": symbol}
        
        # Check for touch/wick exit
        tick = mt5.symbol_info_tick(symbol)
        bars = fetch_recent_bars(symbol, 2)
        if bars is None or len(bars) < 1:
            return {"action": "holding", "symbol": symbol, "ticket": pos.ticket}
        
        latest_bar = bars[-1]
        current_price = None
        if tick:
            current_price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
        
        # Check touch/wick exit
        sl_price = getattr(pos, "sl", None)
        tp_price = getattr(pos, "tp", None)
        if sl_price is not None and tp_price is not None:
            direction_str = "LONG" if pos.type == mt5.POSITION_TYPE_BUY else "SHORT"
            bar_high = float(latest_bar["high"])
            bar_low = float(latest_bar["low"])
            
            exit_trigger = None
            if direction_str == "LONG":
                if (current_price is not None and current_price <= sl_price) or bar_low <= sl_price:
                    exit_trigger = "SL"
                if (current_price is not None and current_price >= tp_price) or bar_high >= tp_price:
                    exit_trigger = "TP"
            elif direction_str == "SHORT":
                if (current_price is not None and current_price >= sl_price) or bar_high >= sl_price:
                    exit_trigger = "SL"
                if (current_price is not None and current_price <= tp_price) or bar_low <= tp_price:
                    exit_trigger = "TP"
            
            if exit_trigger:
                log(
                    f"WICK/TOUCH EXIT: {symbol} {direction_str} ticket={pos.ticket} trigger={exit_trigger} "
                    f"bar_high={bar_high:.5f} bar_low={bar_low:.5f} "
                    f"sl={sl_price:.5f} tp={tp_price:.5f}"
                )
                if close_position(pos, reason=f"TOUCH_{exit_trigger}"):
                    return {"action": "position_closed", "symbol": symbol, "ticket": pos.ticket}
                else:
                    return {"action": "close_failed", "symbol": symbol, "ticket": pos.ticket}
        
        # If no exit, return holding
        if tick:
            pnl_pips = round(
                price_to_pips(
                    (pos.price_open - tick.bid)
                    if pos.type == mt5.POSITION_TYPE_SELL
                    else (tick.ask - pos.price_open)
                )
                / params["PipSize"],
                1,
            )
            dir_str = (
                "SHORT" if pos.type == mt5.POSITION_TYPE_SELL else "LONG"
            )
            log(
                f"HOLDING: {symbol} {dir_str} ticket={pos.ticket} "
                f"PnL={pnl_pips:+.1f}p"
            )
        return {"action": "holding", "symbol": symbol, "ticket": pos.ticket}

    # No position — scan for new signal
    est_hour = get_est_hour_now(params["ESTOffset"])
    if not (
        est_hour >= params["EntryWindowStart"]
        and est_hour < params["EntryWindowEnd"]
    ):
        return {"action": "outside_window", "symbol": symbol, "est_hour": est_hour}

    if check_pending_orders(symbol, params["MagicNumber"]):
        return {"action": "pending_order_exists", "symbol": symbol}

    bars = fetch_recent_bars(symbol, 500)
    if bars is None:
        return {"action": "no_data", "symbol": symbol}

    # Build today's bars in EST
    now = datetime.utcnow()
    today_est = (now + timedelta(hours=params["ESTOffset"])).date()

    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar["time"])
        est_dt = dt + timedelta(hours=params["ESTOffset"])
        if est_dt.date() == today_est:
            today_bars.append({
                "time": bar["time"],
                "dt": dt,
                "est_h": get_est_hour(dt, params["ESTOffset"]),
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
            })

    if len(today_bars) < 5:
        return {"action": "insufficient_data", "symbol": symbol}

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
                ar_pips = price_to_pips(asian_high - asian_low, params["PipSize"])
                if ar_pips < params["MinAR"] or ar_pips > params["MaxAR"]:
                    log(f"SKIP DAY {symbol}: AR={ar_pips:.1f}p out of bounds")
                    return {"action": "ar_out_of_bounds", "symbol": symbol}
            break

    if asian_high <= 0 or asian_low >= 99999:
        return {"action": "no_asian_range", "symbol": symbol}

    # Trading window: 2AM-11AM EST (we already checked est_hour is in [2,11) above, but we need to filter bars)
    trading_bars = [b for b in today_bars if params["EntryWindowStart"] <= b["est_h"] < 11]

    if not trading_bars:
        return {"action": "no_trading_bars", "symbol": symbol}

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

            log(
                f"SYMMETRY TRAP SIGNAL: {symbol} {direction} "
                f"entry={signal.entry_price:.5f} "
                f"SL={signal.sl_price:.5f} (Zero-Buffer) "
                f"TP={signal.tp_price:.5f} (1 AU = {signal.au_used:.1f}p) "
                f"tier={engine.tier_name}"
            )

            return {
                "action": "signal",
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
            }

        elif signal and signal.event == "KILL_SWITCH":
            log(f"Kill switch activated — no trade today for {symbol}")
            return {"action": "kill_switch", "symbol": symbol}
        elif signal and signal.event in ("TP_HIT", "SL_HIT"):
            # Trade resolved intraday — no new entry
            log(f"{signal.event}: {symbol} loop {signal.loop_count}")
            return {"action": "signal", "symbol": symbol, "event": signal.event, "loop_count": signal.loop_count}

    return {"action": "no_signal", "symbol": symbol}

# ─── MAIN EXECUTION LOOP ────────────────────────────────────────────────

def run_loop(interval_seconds: int = 30):
    """
    Main loop — runs the Symmetry Trap strategy continuously for multiple symbols.
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

    if mt5_ok:
        # Update params for each symbol with MT5 info (spread, point, digits)
        # We'll do this per symbol in the loop
        pass

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
                        log("��⚠ MT5 connection lost — reconnecting...")
                        mt5.shutdown()
                        time.sleep(2)
                        if mt5.initialize():
                            log("��✅ MT5 reconnected")
                        else:
                            log("��❌ MT5 reconnect failed — will retry next cycle")
                    last_mt5_check = time.time()
                except Exception as recon_err:
                    log(f"MT5 health check error: {recon_err} — will retry")
                    last_mt5_check = time.time()

            # 5PM EST hard exit check (global)
            current_est_hour = get_est_hour_now(-5)  # ESTOffset is -5
            if current_est_hour >= GLOBAL_PARAMS["HardExitHour"]:
                log(f"Hard exit: {current_est_hour}:00 EST >= {GLOBAL_PARAMS['HardExitHour']}PM — closing all positions")
                # Close all positions for our symbols
                for symbol in SYMBOLS_TO_TRADE:
                    pos = check_existing_position(symbol, GLOBAL_PARAMS["MagicNumber"])
                    if pos:
                        close_position(pos, "HARD_EXIT")
                break

            log(f"Cycle {cycle} start")
            cycle_results = []
            for symbol in SYMBOLS_TO_TRADE:
                try:
                    # Get params for this symbol (with MT5 updated spread, point, digits)
                    params = get_params_for_symbol(symbol)
                    params = update_symbol_params(symbol, params)
                    
                    result = scan_for_symmetry_trap_signal(symbol, params)
                    if result:
                        cycle_results.append(result)
                        log(f"Cycle {cycle} result for {symbol}: {result.get('action', 'unknown')}")
                    else:
                        log(f"Cycle {cycle} result for {symbol}: None")
                except Exception as e:
                    log(f"CYCLE ERROR for {symbol}: {traceback.format_exc()}")

            # Log summary of cycle
            actions = [r.get('action', 'unknown') for r in cycle_results if isinstance(r, dict)]
            if actions:
                log(f"Cycle {cycle} summary: {actions}")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        log("STOPPED by user")
    except Exception as e:
        log(f"LOOP ERROR: {type(e).__name__}: {e}")
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
            results = []
            for symbol in SYMBOLS_TO_TRADE:
                params = get_params_for_symbol(symbol)
                params = update_symbol_params(symbol, params)
                result = scan_for_symmetry_trap_signal(symbol, params)
                if result:
                    results.append(result)
                    print(f"Result for {symbol}: {result}")
                else:
                    print(f"Result for {symbol}: None")
            print(f"Total results: {len(results)}")
        finally:
            mt5.shutdown()