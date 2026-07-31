"""
CEREBUS FX v4.0 — P90 CASCADE-ONLY Live Executor
===============================================
MT5 live executor for P90 CASCADE variant only.
INITIAL and EWS variants are filtered out — only CASCADE entries execute.

CASCADE: 2nd/3rd P90 same direction within 120 min of last exit.
SL = 168% of NEW P90 body (not 80%).

Engine Persistence: Engine stays alive across scans within a day to track
p90_count and last_p90_exit_time for CASCADE detection.

Symbol: USDCHF.PRO (separate from Symmetry Trap on EURUSD.PRO)
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, time as dtime
from typing import Dict, Optional

sys.stdout.reconfigure(encoding="utf-8")

import MetaTrader5 as mt5

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.p90_engine import (
    P90Engine,
    P90Variant,
    TradeDirection,
    Bar,
    DEFAULT_P90_THRESHOLDS,
    DEFAULT_TIER_CONFIG,
)

SYMBOL = "USDCHF.PRO"

PARAMS = {
    "LotSize": 0.01,
    "MaxAR": 45.0,
    "MinAR": 3.0,
    "ESTOffset": -5,
    "EntryWindowStart": 2,
    "EntryWindowEnd": 11,
    "HardExitHour": 17,
    "MaxDailyTrades": 1,
    "MagicNumber": 20260532,
    "PipSize": 0.0001,
    "PipDivisor": 10000,
    "Symbol": SYMBOL,
    "SpreadPips": 0.0,
    "Digits": 5,
    "Point": 0.00001,
}

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_logs")

# ─── Persistent Engine State ──────────────────────────────────────────────
# Engine stays alive across scans so CASCADE detection works (needs p90_count & last_exit)

_current_engine = None
_current_engine_date = None


def get_p90_engine(today_est, asian_high, asian_low):
    """Get or create persistent P90 engine for today. Resets at new EST day."""
    global _current_engine, _current_engine_date

    if _current_engine_date != today_est:
        # New day — create fresh engine
        _current_engine = None
        _current_engine_date = today_est

    if _current_engine is None:
        _current_engine = P90Engine(
            pip_size=PARAMS["PipSize"],
            p90_config=DEFAULT_P90_THRESHOLDS,
            tier_config=DEFAULT_TIER_CONFIG,
            symbol=PARAMS["Symbol"],
        )
        _current_engine.initialize_session(asian_high, asian_low)
        if not _current_engine.session_active:
            log(f"Session inactive: tier={_current_engine.tier_name}")
            _current_engine = None
            return None
        log(f"New engine initialized: AR={_current_engine.asian_range_pips:.1f}p tier={_current_engine.tier_name}")

    return _current_engine


def reset_engine():
    """Reset engine (manual or on day change)."""
    global _current_engine, _current_engine_date
    _current_engine = None
    _current_engine_date = None


def pips_to_price(pips):
    return pips / 10000.0

def price_to_pips(price):
    return price * 10000.0

def get_est_hour(dt):
    return (dt.hour + PARAMS["ESTOffset"]) % 24

def get_est_hour_now():
    return (datetime.utcnow().hour + PARAMS["ESTOffset"]) % 24

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "p90_cascade_executor.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_trade(signal_type, details):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "p90_cascade_signals.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "type": signal_type, **details}) + "\n")

def get_symbol_info():
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        log(f"ERROR: Cannot get info for {SYMBOL}")
        return None
    PARAMS["SpreadPips"] = info.spread * info.point * 10000
    PARAMS["Point"] = info.point
    PARAMS["Digits"] = info.digits
    return info

def fetch_recent_bars(count=500):
    bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, count)
    if bars is None or len(bars) == 0:
        return None
    return bars

def check_existing_position():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        for pos in positions:
            if pos.magic == PARAMS["MagicNumber"]:
                return pos
    return None

def check_pending_orders():
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders:
        return sum(1 for o in orders if o.magic == PARAMS["MagicNumber"])
    return 0

def place_order(is_short, sl_price, tp_price, entry_price):
    try:
        info = get_symbol_info()
        if not info:
            return None
        tick = mt5.symbol_info_tick(SYMBOL)
        if not tick:
            log("ERROR: No tick data")
            return None

        digits = PARAMS["Digits"]
        sl_r = round(sl_price, digits)
        tp_r = round(tp_price, digits)
        entry_r = round(entry_price, digits)

        if is_short:
            if tp_r >= entry_r or sl_r <= entry_r:
                log(f"INVALID TP/SL: SHORT TP={tp_r} entry={entry_r} SL={sl_r}")
                return "INVALID_TP_SL"
            otype = mt5.ORDER_TYPE_SELL_LIMIT if entry_price > tick.bid else mt5.ORDER_TYPE_SELL
            oprice = entry_r if entry_price > tick.bid else tick.bid
            act = mt5.TRADE_ACTION_PENDING if entry_price > tick.bid else mt5.TRADE_ACTION_DEAL
        else:
            if sl_r >= entry_r or tp_r <= entry_r:
                log(f"INVALID TP/SL: LONG SL={sl_r} entry={entry_r} TP={tp_r}")
                return "INVALID_TP_SL"
            otype = mt5.ORDER_TYPE_BUY_LIMIT if entry_price < tick.ask else mt5.ORDER_TYPE_BUY
            oprice = entry_r if entry_price < tick.ask else tick.ask
            act = mt5.TRADE_ACTION_PENDING if entry_price < tick.ask else mt5.TRADE_ACTION_DEAL

        oprice = round(oprice, digits)
        label = "LIMIT" if act == mt5.TRADE_ACTION_PENDING else "MARKET"
        dir_str = "SHORT" if is_short else "LONG"
        log(f"ORDER: {label} CASCADE {dir_str} @ {oprice:.5f} SL={sl_r:.5f} TP={tp_r:.5f}")

        # ── Try filling modes in order: IOC → RETURN → FOK ────────────
        filling_modes = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN, mt5.ORDER_FILLING_FOK]
        result = None
        for fill_mode in filling_modes:
            req = {
                "action": act, "symbol": SYMBOL, "volume": PARAMS["LotSize"],
                "type": otype, "price": oprice, "sl": sl_r, "tp": tp_r,
                "magic": PARAMS["MagicNumber"], "comment": f"P90_CASCADE_{dir_str}",
                "type_filling": fill_mode,
            }
            if act == mt5.TRADE_ACTION_DEAL:
                req["deviation"] = 10

            result = mt5.order_send(req)
            if result is None:
                log(f"ERROR: order_send returned None (filling={fill_mode})")
                continue
            if result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                log(f"ORDER PLACED: CASCADE {dir_str} @ {oprice:.5f} ticket={result.order} (filling={fill_mode})")
                return result
            log(f"ORDER FAILED: retcode={result.retcode} comment={result.comment} (filling={fill_mode})")
            # If it's a filling mode error, try next; otherwise stop
            if result.retcode == mt5.TRADE_RETCODE_INVALID_FILL:
                continue
            break

        log(f"ORDER FAILED: all filling modes exhausted for {dir_str} @ {oprice:.5f}")
        return None
    except Exception as e:
        log(f"place_order ERROR: {traceback.format_exc()}")
        return None

def close_position(pos, reason="MANUAL"):
    global _current_engine
    is_short = pos.type == mt5.POSITION_TYPE_SELL
    order_type = mt5.ORDER_TYPE_BUY if is_short else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(SYMBOL)
    price = tick.ask if is_short else tick.bid
    digits = PARAMS["Digits"]
    # ── Try filling modes: IOC → RETURN → FOK ──────────────────────────
    filling_modes = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN, mt5.ORDER_FILLING_FOK]
    result = None
    for fill_mode in filling_modes:
        request = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": pos.volume,
            "type": order_type, "price": round(price, digits), "position": pos.ticket,
            "deviation": 10, "magic": PARAMS["MagicNumber"],
            "comment": f"P90_CASCADE_{reason}", "type_filling": fill_mode,
        }
        result = mt5.order_send(request)
        if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            break
        log(f"CLOSE FAILED (filling={fill_mode}): {result.retcode if result else 'None'}")
        if result and result.retcode != mt5.TRADE_RETCODE_INVALID_FILL:
            break
    if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
        pnl_pips = round(price_to_pips((pos.price_open - price) if is_short else (price - pos.price_open)) - PARAMS["SpreadPips"], 1)
        log(f"CLOSED: {reason} PnL={pnl_pips:+.1f}p ticket={pos.ticket}")
        log_trade("CLOSED", {"reason": reason, "pnl_pips": pnl_pips, "ticket": pos.ticket})
        # Reset engine after trade close so next is INITIAL (which we skip) → actually keep alive
        # Trade closed means we should keep engine — next CASCADE can fire if within 120min
        return True
    log(f"CLOSE FAILED: {result.retcode if result else 'None'}")
    return False


def scan_for_cascade_signal(bars):
    """Scan for P90 CASCADE signals only. Returns signal dict or None."""
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS["ESTOffset"])).date()
    today_est_date = today_est

    # Build day's bars
    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar["time"])
        est_dt = dt + timedelta(hours=PARAMS["ESTOffset"])
        if est_dt.date() == today_est_date:
            today_bars.append({
                "time": bar["time"], "dt": dt, "est_h": get_est_hour(dt),
                "open": bar["open"], "high": bar["high"], "low": bar["low"], "close": bar["close"],
            })

    if len(today_bars) < 5:
        return None

    # Asian Range
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
                ar_pips = price_to_pips(asian_high - asian_low)
                if ar_pips < PARAMS["MinAR"] or ar_pips > PARAMS["MaxAR"]:
                    log(f"SKIP DAY: AR={ar_pips:.1f}p out of bounds")
                    return None
            break

    if asian_high <= 0 or asian_low >= 99999:
        return None

    # Get or create persistent engine
    engine = get_p90_engine(today_est_date, asian_high, asian_low)
    if engine is None:
        return None

    # Feed only NEW bars through engine
    trading_bars = [b for b in today_bars if PARAMS["EntryWindowStart"] <= b["est_h"] < 12]
    latest_signal = None
    for b in trading_bars:
        if engine.last_bar_time and b["dt"] <= engine.last_bar_time:
            continue  # Skip already-processed bars
        bar = Bar(timestamp=b["dt"], open=b["open"], high=b["high"], low=b["low"], close=b["close"])
        signal = engine.process_bar(bar)
        if signal and signal.event == "ENTRY":
            if signal.variant != P90Variant.CASCADE:
                log(f"SKIP: {signal.variant.value} variant — CASCADE only. Will keep scanning.")
                # Don't break — keep feeding bars. CASCADE may come later
                continue
            latest_signal = signal
            log(f"CASCADE FOUND: entry={signal.entry_price:.5f} SL={signal.sl_price:.5f} body={signal.p90_body_pips:.1f}p")
            break
        elif signal and signal.event in ("EWS_EXIT",):
            # EWS exit — keep scanning
            continue
        elif signal and signal.event in ("TP_HIT", "SL_HIT"):
            # Trade resolved — keep scanning for next P90
            continue

    if latest_signal is None:
        return None

    direction = "LONG" if latest_signal.direction == TradeDirection.LONG else "SHORT"
    log(f"P90 CASCADE SIGNAL: {direction} entry={latest_signal.entry_price:.5f} SL={latest_signal.sl_price:.5f} TP={latest_signal.tp_price:.5f}")

    return {
        "direction": direction, "variant": latest_signal.variant.value,
        "entry_price": latest_signal.entry_price, "sl": latest_signal.sl_price,
        "tp": latest_signal.tp_price, "tp2": latest_signal.tp2_price,
        "ar_pips": round(engine.asian_range_pips, 1), "tier": engine.tier_name,
        "p90_body_pips": round(latest_signal.p90_body_pips, 1),
        "p90_dir": "BULL" if latest_signal.direction == TradeDirection.LONG else "BEAR",
    }


def run_once():
    if not mt5.symbol_info(SYMBOL):
        log("ERROR: MT5 not connected")
        return {"action": "error", "msg": "MT5 not connected"}

    get_symbol_info()

    # Check existing position
    pos = check_existing_position()
    if pos:
        est_hour = get_est_hour_now()
        if est_hour >= PARAMS["HardExitHour"]:
            close_position(pos, "HARD_EXIT")
            return {"action": "hard_exit"}
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            pnl_pips = round(price_to_pips((pos.price_open - tick.bid) if pos.type == mt5.POSITION_TYPE_SELL else (tick.ask - pos.price_open)) - PARAMS["SpreadPips"], 1)
            dir_str = "SHORT" if pos.type == mt5.POSITION_TYPE_SELL else "LONG"
            log(f"HOLDING: {dir_str} ticket={pos.ticket} PnL={pnl_pips:+.1f}p")
        return {"action": "holding", "ticket": pos.ticket}

    # Only scan during entry window
    est_hour = get_est_hour_now()
    if not (est_hour >= PARAMS["EntryWindowStart"] and est_hour < PARAMS["EntryWindowEnd"]):
        return {"action": "outside_window", "est_hour": est_hour}

    # Don't scan if we already have an open trade (position exists = already handled above)
    # or if outside hours

    bars = fetch_recent_bars(500)
    if bars is None:
        return {"action": "no_data"}

    signal = scan_for_cascade_signal(bars)
    if signal is None:
        return {"action": "no_signal"}

    is_short = signal["direction"] == "SHORT"
    sl, tp, entry = signal["sl"], signal["tp"], signal["entry_price"]
    digits = PARAMS["Digits"]
    entry_r, sl_r, tp_r = round(entry, digits), round(sl, digits), round(tp, digits)

    if is_short:
        if tp_r >= entry_r or sl_r <= entry_r:
            log(f"SKIP: Invalid TP/SL for SHORT tp={tp_r} entry={entry_r} sl={sl_r}")
            return {"action": "invalid_tp_sl"}
    else:
        if sl_r >= entry_r or tp_r <= entry_r:
            log(f"SKIP: Invalid TP/SL for LONG sl={sl_r} entry={entry_r} tp={tp_r}")
            return {"action": "invalid_tp_sl"}

    result = place_order(is_short, sl, tp, entry)
    if result and result != "INVALID_TP_SL":
        log_trade("SIGNAL_EXECUTED", signal)
        return {"action": "order_placed", "signal": signal}
    return {"action": "order_failed"}


def run_loop(interval_seconds=30):
    global _current_engine_date

    log("=" * 60)
    log("P90 CASCADE-ONLY LIVE EXECUTOR — CEREBUS FX v4.0")
    log(f"Symbol: {SYMBOL} | Lots: {PARAMS['LotSize']} | Magic: {PARAMS['MagicNumber']}")
    log(f"Entry window: {PARAMS['EntryWindowStart']}AM-{PARAMS['EntryWindowEnd']}AM EST | Hard exit: {PARAMS['HardExitHour']}PM")
    log("P90 CASCADE ONLY — INITIAL variant skipped | Engine persistent across scans")
    log("=" * 60)

    # ─── MT5 Self-Healing Init ───────────────────────────────────────────
    mt5_ok = mt5.initialize()
    if not mt5_ok:
        log("MT5 init failed — will retry in loop (self-heal)")

    acct = mt5.account_info() if mt5_ok else None
    if acct:
        log(f"Account: {acct.login} | Balance: ${acct.balance:.2f} | Server: {acct.server}")

    if mt5_ok:
        info = get_symbol_info()
        if info:
            log(f"Spread: {PARAMS['SpreadPips']:.1f} pips")

    log(f"Scanning every {interval_seconds}s | Max {PARAMS['MaxDailyTrades']} trade(s)/day")
    log("=" * 60)

    try:
        cycle = 0
        daily_trade_count = 0
        last_trade_date = None
        last_mt5_check = time.time()
        log("LOOP STARTED")

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

            current_est_date = (datetime.utcnow() + timedelta(hours=PARAMS["ESTOffset"])).date()
            if current_est_date != last_trade_date:
                reset_engine()
                daily_trade_count = 0
                last_trade_date = current_est_date
                log(f"NEW DAY: {current_est_date} | Engine reset | Daily counter reset")

            if daily_trade_count >= PARAMS["MaxDailyTrades"]:
                time.sleep(interval_seconds)
                continue

            log(f"Cycle {cycle} start (EST hour: {get_est_hour_now()})")
            try:
                result = run_once()
                log(f"Cycle {cycle} result: {result['action']}")
                if result["action"] == "order_placed":
                    daily_trade_count += 1
            except Exception as e:
                log(f"CYCLE ERROR: {traceback.format_exc()}")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        log("STOPPED by user")
    except Exception as e:
        log(f"LOOP ERROR: {type(e).__name__}: {e}")
    finally:
        mt5.shutdown()
        log("MT5 disconnected")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="P90 CASCADE-ONLY Live Executor — CEREBUS FX v4.0")
    parser.add_argument("--once", action="store_true", help="Run single scan")
    parser.add_argument("--loop", action="store_true", help="Run continuous loop")
    parser.add_argument("--interval", type=int, default=30, help="Scan interval (seconds)")
    parser.add_argument("--symbol", type=str, default=None, help="Override symbol")
    args = parser.parse_args()

    if args.symbol:
        PARAMS["Symbol"] = args.symbol
        SYMBOL = args.symbol

    if args.loop:
        run_loop(args.interval)
    else:
        if not mt5.initialize():
            print("FATAL: Cannot initialize MT5")
            sys.exit(1)
        try:
            result = run_once()
            print(f"Result: {result}")
        finally:
            mt5.shutdown()
