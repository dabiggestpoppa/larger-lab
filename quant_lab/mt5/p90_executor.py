"""
CEREBUS FX v4.0 — P90 Live Executor
=====================================
MT5 live executor for P90 strategy using P90Engine class.

Follows the DMR executor pattern EXACTLY for:
  - MT5 initialization & connection
  - Order placement with REAL SL/TP (request.sl, request.tp)
  - Limit orders when entry != market (deep_state pattern)
  - Position monitoring & management
  - Logging

Engine Isolation (cerebus_dual_engine.md):
  - P90 SL = 80% body (NOT Zero-Buffer)
  - P90 entry = immediate close of P90 candle (NO OCC, NO pullback wait)
  - NEVER cross with Symmetry Trap mechanics

Reference: dmr_executor.py (pattern reference)
           p90_engine.py (P90Engine class)
           cerebus_p90.md (P90 ontology)
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

# ─── Engine Import ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.p90_engine import (
    P90Engine,
    P90Variant,
    TradeDirection,
    Bar,
    DEFAULT_P90_THRESHOLDS,
    DEFAULT_TIER_CONFIG,
)

# ─── CONFIGURATION ────────────────────────────────────────────────────────

SYMBOL = "EURUSD.PRO"

PARAMS = {
    "LotSize": 0.01,
    "MaxAR": 45.0,
    "MinAR": 3.0,
    "ESTOffset": -5,
    "EntryWindowStart": 2,     # 2AM EST
    "EntryWindowEnd": 11,      # 11AM EST (scan until 11)
    "HardExitHour": 17,        # 5PM EST full termination
    "MaxDailyTrades": 1,
    "MagicNumber": 20260530,
    "PipSize": 0.0001,
    "Symbol": SYMBOL,
    "SpreadPips": 0.0,
    "Digits": 5,
    "Point": 0.00001,
}

LOG_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "live_logs",
)

# ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────


def pips_to_price(pips: float) -> float:
    return pips / (10000.0 if PARAMS["PipSize"] == 0.0001 else 100.0)


def price_to_pips(price: float) -> float:
    return price * (10000.0 if PARAMS["PipSize"] == 0.0001 else 100.0)


def get_est_hour(dt: datetime) -> int:
    """Convert datetime to EST hour."""
    return (dt.hour + PARAMS["ESTOffset"]) % 24


def get_est_hour_now() -> int:
    """Get current EST hour from UTC."""
    return (datetime.utcnow().hour + PARAMS["ESTOffset"]) % 24


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "p90_executor.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_trade(signal_type: str, details: dict):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "p90_signals.jsonl"), "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {"ts": datetime.now().isoformat(), "type": signal_type, **details}
            )
            + "\n"
        )


# ─── MT5 HELPERS ───────────────────────────────────────────────────────────


def get_symbol_info() -> Optional[object]:
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        log(f"ERROR: Cannot get info for {SYMBOL}")
        return None
    PARAMS["SpreadPips"] = info.spread * info.point * 10000
    PARAMS["Point"] = info.point
    PARAMS["Digits"] = info.digits
    return info


def fetch_recent_bars(count: int = 500):
    bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, count)
    if bars is None or len(bars) == 0:
        return None
    return bars


def check_existing_position():
    """Check for open market positions with our magic number."""
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        for pos in positions:
            if pos.magic == PARAMS["MagicNumber"]:
                return pos
    return None


def check_pending_orders():
    """Check for pending (limit) orders. Returns count of our pending orders."""
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders:
        return sum(1 for o in orders if o.magic == PARAMS["MagicNumber"])
    return 0


# ─── ORDER PLACEMENT ───────────────────────────────────────────────────────


def place_order(
    is_short: bool,
    sl_price: float,
    tp_price: float,
    entry_price: float,
) -> Optional[object]:
    """
    Place order with REAL SL/TP on broker.
    Uses limit order when entry != market price.

    P90 Entry: immediate P90 candle close (may be远离 current market).
    Limit orders used when entry price is not at market.

    Reference: dmr_executor.py place_order()
    """
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

        # Validate TP/SL against entry_price (engine deep state / P90 close)
        entry_r = round(entry_price, digits)
        if is_short:
            if tp_r >= entry_r or sl_r <= entry_r:
                log(f"INVALID TP/SL: SHORT TP={tp_r} entry={entry_r} SL={sl_r}")
                return "INVALID_TP_SL"
        else:
            if sl_r >= entry_r or tp_r <= entry_r:
                log(f"INVALID TP/SL: LONG SL={sl_r} entry={entry_r} TP={tp_r}")
                return "INVALID_TP_SL"

        # Determine order type: limit vs market
        if is_short:
            if entry_price and entry_price > tick.bid:
                # Entry above market → SELL LIMIT
                otype = mt5.ORDER_TYPE_SELL_LIMIT
                oprice = round(entry_price, digits)
                act = mt5.TRADE_ACTION_PENDING
            else:
                # Entry at or below market → market SELL
                otype = mt5.ORDER_TYPE_SELL
                oprice = tick.bid
                act = mt5.TRADE_ACTION_DEAL
        else:
            if entry_price and entry_price < tick.ask:
                # Entry below market → BUY LIMIT
                otype = mt5.ORDER_TYPE_BUY_LIMIT
                oprice = round(entry_price, digits)
                act = mt5.TRADE_ACTION_PENDING
            else:
                # Entry at or above market → market BUY
                otype = mt5.ORDER_TYPE_BUY
                oprice = tick.ask
                act = mt5.TRADE_ACTION_DEAL

        oprice = round(oprice, digits)
        label = "LIMIT" if act == mt5.TRADE_ACTION_PENDING else "MARKET"
        direction_str = "SHORT" if is_short else "LONG"
        log(
            f"ORDER: {label} {direction_str} @ {oprice:.5f} "
            f"SL={sl_r:.5f} TP={tp_r:.5f}"
        )

        req = {
            "action": act,
            "symbol": SYMBOL,
            "volume": PARAMS["LotSize"],
            "type": otype,
            "price": oprice,
            "sl": sl_r,
            "tp": tp_r,
            "magic": PARAMS["MagicNumber"],
            "comment": f"P90_{direction_str}",
        }

        if act == mt5.TRADE_ACTION_PENDING:
            req["type_filling"] = mt5.ORDER_FILLING_RETURN
        else:
            req["deviation"] = 10
            req["type_filling"] = mt5.ORDER_FILLING_IOC

        result = mt5.order_send(req)
        if result is None:
            log("ERROR: order_send returned None")
            return None

        if result.retcode in (
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_PLACED,
        ):
            log(
                f"ORDER PLACED: {direction_str} @ {oprice:.5f} "
                f"SL={sl_r:.5f} TP={tp_r:.5f} ticket={result.order}"
            )
            return result
        else:
            log(
                f"ORDER FAILED: retcode={result.retcode} "
                f"comment={result.comment}"
            )
            return None

    except Exception as e:
        log(f"place_order ERROR: {traceback.format_exc()}")
        return None


def close_position(pos, reason: str = "MANUAL"):
    is_short = pos.type == mt5.POSITION_TYPE_SELL
    order_type = mt5.ORDER_TYPE_BUY if is_short else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(SYMBOL)
    price = tick.ask if is_short else tick.bid
    digits = PARAMS["Digits"]

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": pos.volume,
        "type": order_type,
        "price": round(price, digits),
        "position": pos.ticket,
        "deviation": 10,
        "magic": PARAMS["MagicNumber"],
        "comment": f"P90_{reason}",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result and result.retcode in (
        mt5.TRADE_RETCODE_DONE,
        mt5.TRADE_RETCODE_PLACED,
    ):
        pnl_pips = round(
            price_to_pips(
                (pos.price_open - price)
                if is_short
                else (price - pos.price_open)
            )
            - PARAMS["SpreadPips"],
            1,
        )
        log(f"CLOSED: {reason} PnL={pnl_pips:+.1f}p")
        log_trade("CLOSED", {"reason": reason, "pnl_pips": pnl_pips, "ticket": pos.ticket})
        return True

    log(f"CLOSE FAILED: {result.retcode if result else 'None'}")
    return False


# ─── P90 SIGNAL SCANNING ──────────────────────────────────────────────────


def scan_for_p90_signal(bars) -> Optional[Dict]:
    """
    Scan M5 bars for P90 signals using P90Engine.

    Returns signal dict or None.
    Signal dict keys:
        direction, variant, entry_price, sl, tp, tp2,
        ar_pips, tier, p90_body_pips, p90_dir

    Reference: dmr_executor.py scan_for_signal() pattern
               p90_engine.py P90Engine class
    """
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()

    # Group bars by EST date
    today_est = (now + timedelta(hours=PARAMS["ESTOffset"])).date()

    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar["time"])
        est_dt = dt + timedelta(hours=PARAMS["ESTOffset"])
        if est_dt.date() == today_est:
            est_hour = get_est_hour(dt)
            today_bars.append(
                {
                    "time": bar["time"],
                    "dt": dt,
                    "est_h": est_hour,
                    "open": bar["open"],
                    "high": bar["high"],
                    "low": bar["low"],
                    "close": bar["close"],
                }
            )

    if len(today_bars) < 5:
        return None

    # Asian Range (7PM-3AM EST): compute from day's bars
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

    # Entry window: 2AM-11AM EST trading bars
    trading_bars = [b for b in today_bars if PARAMS["EntryWindowStart"] <= b["est_h"] < 12]

    if not trading_bars:
        return None

    # Build P90Engine
    engine = P90Engine(
        pip_size=PARAMS["PipSize"],
        p90_config=DEFAULT_P90_THRESHOLDS,
        tier_config=DEFAULT_TIER_CONFIG,
        symbol=PARAMS["Symbol"],
    )

    engine.initialize_session(asian_high, asian_low)

    if not engine.session_active:
        log(f"Session inactive: tier={engine.tier_name}")
        return None

    # Feed trading bars through engine
    latest_signal = None
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
            latest_signal = signal
            break
        elif signal and signal.event in ("TP_HIT", "SL_HIT", "EWS_EXIT"):
            # Exit or resolution before entry → no signal today
            break

    if latest_signal is None:
        return None

    # Build signal dict
    direction = (
        "LONG"
        if latest_signal.direction == TradeDirection.LONG
        else "SHORT"
    )

    log(
        f"P90 SIGNAL: {direction} [{latest_signal.variant.value}] "
        f"entry={latest_signal.entry_price:.5f} "
        f"SL={latest_signal.sl_price:.5f} "
        f"TP={latest_signal.tp_price:.5f} "
        f"TP2={latest_signal.tp2_price:.5f if latest_signal.tp2_price else 'N/A'}"
    )

    return {
        "direction": direction,
        "variant": latest_signal.variant.value,
        "entry_price": latest_signal.entry_price,
        "sl": latest_signal.sl_price,
        "tp": latest_signal.tp_price,
        "tp2": latest_signal.tp2_price,
        "ar_pips": round(engine.asian_range_pips, 1),
        "tier": engine.tier_name,
        "p90_body_pips": round(latest_signal.p90_body_pips, 1),
        "p90_dir": "BULL" if latest_signal.direction == TradeDirection.LONG else "BEAR",
    }


# ─── MAIN EXECUTION CYCLE ──────────────────────────────────────────────────


def run_once():
    """
    Single scan-execute-monitor cycle.
    MT5 must be initialized by caller.
    """
    if not mt5.symbol_info(SYMBOL):
        log("ERROR: MT5 not connected")
        return {"action": "error", "msg": "MT5 not connected"}

    get_symbol_info()

    # Check existing position
    pos = check_existing_position()
    if pos:
        est_hour = get_est_hour_now()

        # Hard exit at 5PM
        if est_hour >= PARAMS["HardExitHour"]:
            close_position(pos, "HARD_EXIT")
            return {"action": "hard_exit"}

        # Monitor PnL
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            pnl_pips = round(
                price_to_pips(
                    (pos.price_open - tick.bid)
                    if pos.type == mt5.POSITION_TYPE_SELL
                    else (tick.ask - pos.price_open)
                )
                - PARAMS["SpreadPips"],
                1,
            )
            dir_str = "SHORT" if pos.type == mt5.POSITION_TYPE_SELL else "LONG"
            log(
                f"HOLDING: {dir_str} ticket={pos.ticket} "
                f"PnL={pnl_pips:+.1f}p"
            )
        return {"action": "holding", "ticket": pos.ticket}

    # No position — scan for new signal
    est_hour = get_est_hour_now()
    if not (est_hour >= PARAMS["EntryWindowStart"] and est_hour < PARAMS["EntryWindowEnd"]):
        return {"action": "outside_window", "est_hour": est_hour}

    # Check pending orders
    if check_pending_orders():
        return {"action": "pending_order_exists"}

    bars = fetch_recent_bars(500)
    if bars is None:
        return {"action": "no_data"}

    signal = scan_for_p90_signal(bars)
    if signal is None:
        return {"action": "no_signal"}

    is_short = signal["direction"] == "SHORT"
    sl = signal["sl"]
    tp = signal["tp"]
    entry = signal["entry_price"]

    # Final validation
    digits = PARAMS["Digits"]
    entry_r = round(entry, digits)
    sl_r = round(sl, digits)
    tp_r = round(tp, digits)

    if is_short:
        if tp_r >= entry_r or sl_r <= entry_r:
            log(
                f"SKIP: Invalid TP/SL for SHORT "
                f"tp={tp_r} entry={entry_r} sl={sl_r}"
            )
            return {"action": "invalid_tp_sl"}
    else:
        if sl_r >= entry_r or tp_r <= entry_r:
            log(
                f"SKIP: Invalid TP/SL for LONG "
                f"sl={sl_r} entry={entry_r} tp={tp_r}"
            )
            return {"action": "invalid_tp_sl"}

    result = place_order(is_short, sl, tp, entry)
    if result and result != "INVALID_TP_SL":
        log_trade("SIGNAL_EXECUTED", signal)
        return {"action": "order_placed", "signal": signal}

    return {"action": "order_failed"}


# ─── MAIN LOOP ────────────────────────────────────────────────────────────


def run_loop(interval_seconds: int = 30):
    """
    Main loop — runs the P90 strategy continuously.

    Reference: dmr_executor.py run_loop()
    """
    log("=" * 60)
    log("P90 LIVE EXECUTOR — CEREBUS FX v4.0")
    log(
        f"Symbol: {SYMBOL} | Lots: {PARAMS['LotSize']} | "
        f"Magic: {PARAMS['MagicNumber']}"
    )
    log(
        f"Entry window: {PARAMS['EntryWindowStart']}AM-{PARAMS['EntryWindowEnd']}AM EST | "
        f"Hard exit: {PARAMS['HardExitHour']}PM"
    )
    log("P90 SL = 80% body | Entry on P90 close | NO OCC wait")
    log("Engine A ONLY — never cross with Symmetry Trap mechanics")
    log("=" * 60)

    if not mt5.initialize():
        log("FATAL: Cannot initialize MT5")
        sys.exit(1)

    acct = mt5.account_info()
    if acct:
        log(
            f"Account: {acct.login} | "
            f"Balance: ${acct.balance:.2f} | "
            f"Server: {acct.server}"
        )

    info = get_symbol_info()
    if info:
        log(f"Spread: {PARAMS['SpreadPips']:.1f} pips")

    log(
        f"Scanning every {interval_seconds}s | "
        f"Max {PARAMS['MaxDailyTrades']} trade(s)/day"
    )
    log("=" * 60)

    try:
        cycle = 0
        daily_trade_count = 0
        last_trade_date = None
        log("LOOP STARTED — entering main loop")

        while True:
            cycle += 1

            # Reset daily counter on new EST day
            current_est_date = (
                datetime.utcnow() + timedelta(hours=PARAMS["ESTOffset"])
            ).date()
            if current_est_date != last_trade_date:
                daily_trade_count = 0
                last_trade_date = current_est_date

            # Check max daily trades
            if daily_trade_count >= PARAMS["MaxDailyTrades"]:
                time.sleep(interval_seconds)
                continue

            log(f"Cycle {cycle} start")
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


# ─── CLI ENTRY POINT ──────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="P90 Live Executor — CEREBUS FX v4.0")
    parser.add_argument("--once", action="store_true", help="Run single scan")
    parser.add_argument("--loop", action="store_true", help="Run continuous loop")
    parser.add_argument(
        "--interval", type=int, default=30, help="Scan interval (seconds)"
    )
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
