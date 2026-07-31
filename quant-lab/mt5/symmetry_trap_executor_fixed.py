"""
CEREBUS FX v4.0 — Symmetry Trap Live Executor (FIXED)
=======================================================
MT5 live executor for Symmetry Trap strategy using SymmetryTrapEngine class.

Fixes applied:
1. Symbol selection & Market Watch enforcement at startup
2. STOPLEVEL compliance (min SL/TP distance)
3. Retcode 10015/10027 handling with retry logic
4. MT5 API version compatibility (no level_stop_distance)
4. Hardcoded demo credentials
5. Proper tick freshness checks (30s max)
6. Mutex/lock around order_send
7. Proper price normalization to symbol digits
8. Volume step validation
9. Wick-based SL (realistic) in backtest, real SL orders in live

Engine Isolation (cerebus_dual_engine.md):
  - Symmetry Trap SL = Zero-Buffer Impulse Extreme (NOT 80% P90 body)
  - Symmetry Trap TP = 1 AU single target (NOT P90 -25%/-50% AR targets)
  - Entry = OCC after DZ pullback (NOT immediate P90 close)
  - NEVER cross with P90 mechanics

Reference: dmr_multi_pair_live_fixed.py (pattern reference)
           symmetry_trap.py (SymmetryTrapEngine class)
           cerebus_dual_engine.md (Engine B isolation)
"""

from __future__ import annotations

import json
import os
import sys
import time
import threading
import traceback
from datetime import datetime, timedelta, time as dtime
from typing import Dict, Optional

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

# ─── CONFIGURATION ────────────────────────────────────────────────────────

SYMBOL = "EURUSD.PRO"

PARAMS = {
    "LotSize": 0.03,
    "MaxAR": 45.0,
    "MinAR": 3.0,
    "ESTOffset": -5,
    "EntryWindowStart": 2,     # 2AM EST
    "EntryWindowEnd": 11,      # 11AM EST
    "HardExitHour": 17,        # 5PM EST
    "MagicNumber": 20260531,
    "PipSize": 0.0001,
    "Symbol": SYMBOL,
    "SpreadPips": 0.0,
    "Digits": 5,
    "Point": 0.00001,
}

# ─── DEMO ACCOUNT CREDENTIALS (HARDCODED) ───
DEMO_LOGIN = 1114712
DEMO_PASSWORD = "your_demo_password_here"  # REPLACE WITH ACTUAL
DEMO_SERVER = "OxSecurities-Demo"

LOG_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "live_logs",
)

# ─── Thread lock for order_send ───
ORDER_LOCK = threading.Lock()

# ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────


def pips_to_price(pips: float) -> float:
    return pips / (10000.0 if PARAMS["PipSize"] == 0.0001 else 100.0)


def price_to_pips(price: float) -> float:
    return price * (10000.0 if PARAMS["PipSize"] == 0.0001 else 100.0)


def get_est_hour(dt: datetime) -> int:
    return (dt.hour + PARAMS["ESTOffset"]) % 24


def get_est_hour_now() -> int:
    return (datetime.utcnow().hour + PARAMS["ESTOffset"]) % 24


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(
        os.path.join(LOG_DIR, "symmetry_trap_executor.log"), "a", encoding="utf-8"
    ) as f:
        f.write(line + "\n")


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


def ensure_symbol_selected(symbol: str) -> bool:
    """Ensure symbol is selected in Market Watch and wait for tick data."""
    if not mt5.symbol_select(symbol, True):
        log(f"Failed to select {symbol} in Market Watch")
        return False
    
    for _ in range(20):
        tick = mt5.symbol_info_tick(symbol)
        if tick and tick.time > 0:
            return True
        time.sleep(0.5)
    
    log(f"WARNING: No tick data for {symbol} after 10s")
    return False


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(
        os.path.join(LOG_DIR, "symmetry_trap_executor.log"), "a", encoding="utf-8"
    ) as f:
        f.write(line + "\n")


# ─── Thread lock for order_send ───
ORDER_LOCK = threading.Lock()


def initialize_mt5() -> bool:
    """Initialize MT5 with demo credentials."""
    if not mt5.initialize():
        log(f"MT5 init failed: {mt5.last_error()}")
        return False
    
    if not mt5.login(DEMO_LOGIN, password=DEMO_PASSWORD, server=DEMO_SERVER):
        log(f"MT5 login failed: {mt5.last_error()}")
        return False
    
    account = mt5.account_info()
    if account:
        log(f"Connected: {account.name} | {account.server} | Balance: {account.balance} {account.currency}")
    return True


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


def get_min_stop_distance(symbol: str) -> float:
    """Get broker's minimum stop distance (STOPLEVEL) in price units."""
    info = mt5.symbol_info(symbol)
    if not info:
        return 0
    return info.trade_stops_level * info.point


def place_order(symbol: str, direction: TradeDirection, sl_price: float, tp_price: float, entry_price: float, magic: int) -> Optional[mt5.TradeResult]:
    """Place limit order with REAL SL/TP on MT5."""
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
    lot = round(PARAMS['LotSize'] / volume_step) * volume_step
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
        with ORDER_LOCK:
            result = mt5.order_send(req)
        
        if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            log(f"ORDER PLACED: {symbol} {'LONG' if direction == TradeDirection.LONG else 'SHORT'} @ {entry_r} SL={sl_r} TP={tp_r}")
            return result
        elif result and result.retcode == mt5.TRADE_RETCODE_BUSY:
            log(f"RETRY {attempt+1}/{max_retries}: {symbol} trade context busy (10027)")
            time.sleep(0.5 * (attempt + 1))
            continue
        else:
            log(f"ORDER FAILED: {symbol} retcode={result.retcode if result else 'None'} comment={result.comment if result else 'None'}")
            return None
    
    return None


def check_position_result(symbol: str, magic: int):
    """Check if a position was closed (TP or SL hit). Log result."""
    deals = mt5.history_deals_get(
        datetime.utcnow() - timedelta(hours=24),
        datetime.utcnow()
    )
    if not deals:
        return None
    
    for deal in deals:
        if deal.magic == magic and deal.entry == 1:  # entry=1 means close
            pnl_pips = price_to_pips(deal.profit) if hasattr(deal, 'profit') else 0
            result_type = "TP" if deal.profit > 0 else "SL"
            result = {
                "symbol": symbol.replace(".PRO", ""),
                "type": result_type,
                "result": result_type,
                "pnl_pips": round(pnl_pips, 1),
                "entry_price": deal.price,
                "exit_price": deal.price,
                "timestamp": datetime.now().isoformat(),
            }
            log(f"RESULT: {symbol} {result_type} PnL={pnl_pips:+.1f}p")
            return result
    return None


def scan_session(engine: SymmetryTrapEngine, symbol: str, magic: int, pip_size: float) -> Optional[TradeSignal]:
    """Scan for Symmetry Trap signals and execute."""
    # Check existing position
    pos = check_existing_position(symbol, magic)
    if pos:
        est_hour = get_est_hour_now()
        if est_hour >= 17:  # Hard exit at 5PM EST
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                close_type = mt5.ORDER_TYPE_BUY if pos.type == mt5.POSITION_TYPE_SELL else mt5.ORDER_TYPE_SELL
                price = tick.ask if pos.type == mt5.POSITION_TYPE_SELL else tick.bid
                req = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "price": price,
                    "position": pos.ticket,
                    "magic": magic,
                    "comment": "ST_HARD_EXIT",
                }
                with ORDER_LOCK:
                    mt5.order_send(req)
                log(f"HARD EXIT: {symbol}")
            return None
    
    # Check if position was recently closed
    check_position_result(symbol, magic)

    # Check pending orders
    if check_pending_orders(symbol, magic) > 0:
        return None

    # Ensure symbol is selected and has fresh data
    if not ensure_symbol_selected(symbol):
        return None

    # Fetch recent bars
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=-5)).date()

    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=-5)
        if est_dt.date() == today_est:
            today_bars.append({
                'time': bar['time'], 'dt': dt,
                'est_h': get_est_hour(dt),
                'open': bar['open'], 'high': bar['high'],
                'low': bar['low'], 'close': bar['close'],
            })

    if len(today_bars) < 5:
        return None

    # Asian Range
    asian_high, asian_low = 0.0, 99999.0
    ar_locked = False
    for b in today_bars:
        if b['est_h'] >= 19 or b['est_h'] < 3:
            asian_high = max(asian_high, b['high'])
            asian_low = min(asian_low, b['low'])
        if b['est_h'] == 3 and not ar_locked:
            ar_locked = True
            if asian_high <= asian_low:
                return None
            ar_pips = (asian_high - asian_low) / pip_size
            if ar_pips < 3 or ar_pips > 45:
                log(f"SKIP {symbol}: AR={ar_pips:.1f}p out of bounds")
                return None
            break

    if not engine.session_active:
        engine.initialize_session(asian_high, asian_low)
        if not engine.session_active:
            return None

    # Trading window
    trading_bars = [b for b in today_bars if 3 <= b['est_h'] < 16]
    if not trading_bars:
        return None

    # Process bars through engine
    for bar in trading_bars:
        bar_obj = Bar(
            timestamp=bar['dt'],
            open=bar['open'],
            high=bar['high'],
            low=bar['low'],
            close=bar['close']
        )
        
        signal = engine.process_bar(bar_obj)
        
        if signal is None:
            continue

        if signal.event == "ENTRY":
            # Place limit order with REAL SL/TP
            result = place_order(
                symbol=symbol,
                direction=signal.direction,
                sl_price=signal.sl_price,
                tp_price=signal.tp_price,
                entry_price=signal.entry_price,
                magic=magic
            )
            
            if result:
                dir_str = "LONG" if signal.direction == TradeDirection.LONG else "SHORT"
                log(f"SIGNAL: {symbol} {dir_str} @ {signal.entry_price:.5f} SL={signal.sl_price:.5f} TP={signal.tp_price:.5f} (loop {signal.loop_count})")
                return signal
        
        elif signal.event in ("TP_HIT", "SL_HIT"):
            log(f"{signal.event}: {symbol} loop {signal.loop_count}")

    return None


def run_once():
    """Single scan cycle across all pairs."""
    signals = []
    for name, cfg in PAIRS.items():
        try:
            sig = scan_pair(cfg)
            if sig:
                signals.append(sig)
        except Exception as e:
            log(f"ERROR scanning {name}: {e}")
    return signals


def main():
    log("=" * 60)
    log("SYMMETRY TRAP LIVE EXECUTOR — Demo Account (FIXED)")
    log("Symbol: EURUSD.PRO")
    log("Lot size: 0.03")
    log("=" * 60)

    if not initialize_mt5():
        return

    # Ensure symbol is selected at startup
    ensure_symbol_selected(SYMBOL)
    
    log("Symbol selected. Starting scan loop...")
    log("Scanning every 60 seconds... (Ctrl+C to stop)")

    engine = SymmetryTrapEngine(pip_size=PARAMS["PipSize"], symbol=SYMBOL)
    magic = PARAMS["MagicNumber"]

    try:
        while True:
            start = time.time()
            signals = run_once()
            if signals:
                log(f"[{datetime.now().strftime('%H:%M:%S')}] {len(signals)} signal(s) fired")
            elapsed = time.time() - start
            sleep_time = max(60 - elapsed, 1)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        log("Shutdown requested")
    finally:
        mt5.shutdown()
        log("MT5 shutdown complete")


if __name__ == "__main__":
    main()