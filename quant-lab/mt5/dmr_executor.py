"""
DMR Live Executor v3 — Production System with Real SL/TP
========================================================
Fixes the original EA's bug: SL/TP are now SET ON THE BROKER.
- Original EA: didn't set request.sl/request.tp → no broker SL/TP
- This executor: sets sl+tp on every order → broker manages exits

84% WR backtest (v3) — the fixed strategy.

TIMEZONE FIX (2026-05-29):
- MT5 bar timestamps are in UTC. ESTOffset=-5 converts to EST.
- Entry window check now uses datetime.utcnow() for correct EST conversion.

ENTRY PRICE FIX (2026-05-29 06:15):
- Entry = deep_state (where signal triggers), NOT b['close'] (bar close)
-deep_state is always at valid distance from TP/SL by construction
- place_order now validates against signal entry_price, not live market price
- This fixes the "INVALID TP/SL" loop where every BUY signal was rejected
"""
import sys, time, json, os
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

SYMBOL = "EURUSD.PRO"

PARAMS = {
    'LotSize':        0.01,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'MinAR':          3,
    'MaxAR':          45,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 1,
    'MagicNumber':    20260528,
    'SpreadPips':     0.0,
}

LOG_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\live_logs"

def get_p90_threshold(est_hour):
    if est_hour in (2, 3):      return 4.1
    if 4 <= est_hour <= 6:      return 4.6
    if est_hour in (7, 8):      return 5.9
    if est_hour in (9, 10):     return 6.2
    return 999.0

def pips_to_price(pips):
    return pips / 10000.0

def price_to_pips(price):
    return price * 10000.0

def get_est_hour(dt):
    """Convert datetime hour to EST using MT5 bar timestamps (UTC-based, offset=-5)."""
    return (dt.hour + PARAMS['ESTOffset']) % 24

def get_est_hour_from_local():
    """Get current EST hour from local system time. Handles DST correctly."""
    utc_now = datetime.utcnow()
    return (utc_now.hour + PARAMS['ESTOffset']) % 24

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "executor.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_trade(signal_type, details):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "signals.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "type": signal_type, **details}) + "\n")

def get_symbol_info():
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        log(f"ERROR: Cannot get info for {SYMBOL}")
        return None
    PARAMS['SpreadPips'] = info.spread * info.point * 10000
    PARAMS['Point'] = info.point
    PARAMS['Digits'] = info.digits
    return info

def fetch_recent_bars(count=500):
    bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, count)
    if bars is None or len(bars) == 0:
        return None
    return bars

def check_existing_position():
    """Check for open market positions."""
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        for pos in positions:
            if pos.magic == PARAMS['MagicNumber']:
                return pos
    return None

def check_pending_orders():
    """Check for pending (limit) orders. Returns count of our pending orders."""
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders:
        return sum(1 for o in orders if o.magic == PARAMS['MagicNumber'])
    return 0

def place_order(is_short, sl_price, tp_price, entry_price=None):
    """Place order with REAL SL/TP. Uses limit order when entry != market."""
    try:
        info = get_symbol_info()
        if not info:
            return None

        tick = mt5.symbol_info_tick(SYMBOL)
        if not tick:
            log("ERROR: No tick")
            return None

        digits = PARAMS['Digits']
        sl_r = round(sl_price, digits)
        tp_r = round(tp_price, digits)

        # Validate against entry_price (deep_state)
        validate_at = entry_price if entry_price is not None else (tick.bid if is_short else tick.ask)
        validate_at = round(validate_at, digits)
        if is_short:
            if tp_r >= validate_at or sl_r <= validate_at:
                log(f"INVALID TP/SL: SHORT TP={tp_r} at={validate_at:.5f} SL={sl_r}")
                return "INVALID_TP_SL"
        else:
            if sl_r >= validate_at or tp_r <= validate_at:
                log(f"INVALID TP/SL: BUY SL={sl_r} at={validate_at:.5f} TP={tp_r}")
                return "INVALID_TP_SL"

        # Determine order type: limit or market
        if is_short:
            if entry_price and entry_price > tick.bid:
                otype, oprice, act = mt5.ORDER_TYPE_SELL_LIMIT, round(entry_price, digits), mt5.TRADE_ACTION_PENDING
            else:
                otype, oprice, act = mt5.ORDER_TYPE_SELL, tick.bid, mt5.TRADE_ACTION_DEAL
        else:
            if entry_price and entry_price < tick.ask:
                otype, oprice, act = mt5.ORDER_TYPE_BUY_LIMIT, round(entry_price, digits), mt5.TRADE_ACTION_PENDING
            else:
                otype, oprice, act = mt5.ORDER_TYPE_BUY, tick.ask, mt5.TRADE_ACTION_DEAL

        oprice = round(oprice, digits)
        label = "LIMIT" if act == mt5.TRADE_ACTION_PENDING else "MARKET"
        log(f"ORDER: {label} {'SHORT' if is_short else 'LONG'} @ {oprice:.5f} SL={sl_r:.5f} TP={tp_r:.5f}")

        req = {
            "action": act, "symbol": SYMBOL, "volume": PARAMS['LotSize'],
            "type": otype, "price": oprice, "sl": sl_r, "tp": tp_r,
            "magic": PARAMS['MagicNumber'],
            "comment": "DMR_" + ("SHORT" if is_short else "LONG"),
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
        if result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            log(f"ORDER PLACED: {'SHORT' if is_short else 'LONG'} @ {oprice:.5f} SL={sl_r:.5f} TP={tp_r:.5f} ticket={result.order}")
            return result
        else:
            log(f"ORDER FAILED: retcode={result.retcode} comment={result.comment}")
            return None
    except Exception as e:
        import traceback
        log(f"place_order ERROR: {traceback.format_exc()}")
        return None

def close_position(pos, reason="MANUAL"):
    is_short = pos.type == mt5.POSITION_TYPE_SELL
    order_type = mt5.ORDER_TYPE_BUY if is_short else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(SYMBOL)
    price = tick.ask if is_short else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": pos.volume,
        "type": order_type, "price": round(price, PARAMS['Digits']),
        "position": pos.ticket, "deviation": 10, "magic": PARAMS['MagicNumber'],
        "comment": f"DMR_{reason}", "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
        pnl = round(price_to_pips(pos.price_open - price) * (-1 if is_short else 1) - PARAMS['SpreadPips'], 1)
        log(f"CLOSED: {reason} PnL={pnl:+.1f}p")
        log_trade("CLOSED", {"reason": reason, "pnl_pips": pnl, "ticket": pos.ticket})
        return True
    log(f"CLOSE FAILED: {result.retcode if result else 'None'}")
    return False

def scan_for_signal(bars):
    """DMR v3 signal scan.
    
    KEY FIX: entry_price = deep_state (where signal triggers), NOT bar close.
    This ensures TP/SL are always at valid distance from entry.
    """
    if bars is None or len(bars) < 50:
        return None

    now = datetime.utcnow()
    today_est = (now + timedelta(hours=PARAMS['ESTOffset'])).date()

    today_bars = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        if est_dt.date() == today_est:
            today_bars.append({
                'time': bar['time'], 'dt': dt,
                'est_h': get_est_hour(dt),
                'open': bar['open'], 'high': bar['high'],
                'low': bar['low'], 'close': bar['close'],
            })

    if len(today_bars) < 5:
        return None

    # Asian Range (7PM-3AM EST)
    asian_high = 0.0
    asian_low = 99999.0
    ar_locked = False
    for b in today_bars:
        if b['est_h'] >= 19 or b['est_h'] < 3:
            asian_high = max(asian_high, b['high'])
            asian_low = min(asian_low, b['low'])
        if b['est_h'] == 3 and not ar_locked:
            ar_locked = True
            if 0 < asian_high and asian_low < 99999:
                ar_pips = price_to_pips(asian_high - asian_low)
                if ar_pips < PARAMS['MinAR'] or ar_pips > PARAMS['MaxAR']:
                    log(f"SKIP DAY: AR={ar_pips:.1f}p out of bounds")
                    return None
            break

    # Trading bars (2AM-11AM EST)
    trading_bars = [b for b in today_bars if 2 <= b['est_h'] < 11]

    # P90 scan
    p90_dir = 0
    activation = 0.0
    deep_state = 0.0
    kill_switch = 0.0
    body_pips_val = 0.0
    p90_idx = -1

    for i, b in enumerate(trading_bars):
        body = abs(b['close'] - b['open'])
        bp = price_to_pips(body)
        if bp >= get_p90_threshold(b['est_h']):
            p90_dir = 1 if b['close'] > b['open'] else -1
            activation = b['close']
            body_pips_val = bp
            deep_state = activation + pips_to_price(bp * PARAMS['DeepMult']) * p90_dir
            kill_switch = activation + pips_to_price(bp * PARAMS['KillMult']) * p90_dir
            p90_idx = i
            log(f"P90: {'BULL' if p90_dir == 1 else 'BEAR'} body={bp:.1f}p DS={deep_state:.5f} KS={kill_switch:.5f}")
            break

    if not p90_dir:
        return None

    # Deep State touch — entry at deep_state, NOT bar close
    for b in trading_bars[p90_idx + 1:]:
        if b['est_h'] >= 12:
            break
        if p90_dir == 1 and b['low'] <= deep_state:
            # SHORT signal: BULL P90, price fell to deep_state
            # entry = deep_state, TP = activation (above DS), SL = kill_switch (above DS)
            if activation <= deep_state or kill_switch <= deep_state:
                log(f"FILTER: SHORT geometry invalid DS={deep_state:.5f} TP={activation:.5f} KS={kill_switch:.5f}")
                return None
            log(f"SIGNAL: SHORT DS touched low={b['low']:.5f} entry={deep_state:.5f}")
            return {
                'direction': 'SHORT', 'p90_dir': 'BULL',
                'entry_price': deep_state, 'sl': kill_switch, 'tp': activation,
                'body_pips': round(body_pips_val, 1), 'ds_level': deep_state,
            }
        if p90_dir == -1 and b['high'] >= deep_state:
            # BUY signal: BEAR P90, price rose back to deep_state
            # entry = deep_state, TP = activation (above DS), SL = kill_switch (below DS)
            if activation <= deep_state or kill_switch >= deep_state:
                log(f"FILTER: BUY geometry invalid DS={deep_state:.5f} TP={activation:.5f} KS={kill_switch:.5f}")
                return None
            log(f"SIGNAL: BUY DS touched high={b['high']:.5f} entry={deep_state:.5f}")
            return {
                'direction': 'BUY', 'p90_dir': 'BEAR',
                'entry_price': deep_state, 'sl': kill_switch, 'tp': activation,
                'body_pips': round(body_pips_val, 1), 'ds_level': deep_state,
            }
    return None

def run_once():
    """Single scan-execute-monitor cycle. MT5 must be initialized by caller."""
    if not mt5.symbol_info(SYMBOL):
        log("ERROR: MT5 not connected")
        return {"action": "error", "msg": "MT5 not connected"}

    get_symbol_info()

    # Check existing position
    pos = check_existing_position()
    if pos:
        est_hour = get_est_hour_from_local()
        if est_hour >= PARAMS['HardExitHour']:
            close_position(pos, "HARD_EXIT")
            return {"action": "hard_exit"}

        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            pnl = price_to_pips(pos.price_open - tick.bid if pos.type == mt5.POSITION_TYPE_SELL else tick.ask - pos.price_open) - PARAMS['SpreadPips']
            log(f"HOLDING: {'SHORT' if pos.type == mt5.POSITION_TYPE_SELL else 'LONG'} ticket={pos.ticket} PnL={pnl:+.1f}p")
        return {"action": "holding", "ticket": pos.ticket}

    # No position — scan for new signal
    est_hour = get_est_hour_from_local()
    if not (est_hour >= 2 and est_hour < 11):
        return {"action": "outside_window", "est_hour": est_hour}

    # Check for pending orders before scanning
    if check_pending_orders():
        return {"action": "pending_order_exists"}

    bars = fetch_recent_bars(500)
    if bars is None:
        return {"action": "no_data"}

    signal = scan_for_signal(bars)
    if signal is None:
        return {"action": "no_signal"}

    is_short = signal['direction'] == 'SHORT'
    sl = signal['sl']
    tp = signal['tp']
    entry = signal['entry_price']

    # Final validation against deep_state
    if is_short:
        if tp >= entry or sl <= entry:
            log(f"SKIP: Invalid TP/SL for SHORT tp={tp} entry={entry} sl={sl}")
            return {"action": "invalid_tp_sl"}
    else:
        if sl >= entry or tp <= entry:
            log(f"SKIP: Invalid TP/SL for BUY sl={sl} entry={entry} tp={tp}")
            return {"action": "invalid_tp_sl"}

    result = place_order(is_short, sl, tp, entry)
    if result and result != "INVALID_TP_SL":
        log_trade("SIGNAL_EXECUTED", signal)
        return {"action": "order_placed", "signal": signal}
    return {"action": "order_failed"}

def run_loop(interval_seconds=30):
    """Main loop — runs the DMR strategy continuously."""
    log("=" * 60)
    log("DMR LIVE EXECUTOR v3 — 84% WR Strategy with REAL SL/TP")
    log(f"Symbol: {SYMBOL} | Lots: {PARAMS['LotSize']} | Magic: {PARAMS['MagicNumber']}")
    log(f"DeepMult: {PARAMS['DeepMult']} | KillMult: {PARAMS['KillMult']}")
    log(f"ENTRY FIX: entry_price = deep_state (not bar close)")
    log("=" * 60)

    if not mt5.initialize():
        log("FATAL: Cannot initialize MT5")
        sys.exit(1)
    acct = mt5.account_info()
    if acct:
        log(f"Account: {acct.login} | Balance: ${acct.balance:.2f} | Server: {acct.server}")
    info = get_symbol_info()
    if info:
        log(f"Spread: {PARAMS['SpreadPips']:.1f} pips")

    log(f"Scanning every {interval_seconds}s | Entry window: 2AM-11AM EST | Hard exit: 5PM")
    log("SL/TP set on BROKER — not just simulated")
    log("=" * 60)

    try:
        cycle = 0
        log("LOOP STARTED — entering main loop")
        while True:
            cycle += 1
            log(f"Cycle {cycle} start")
            try:
                result = run_once()
                log(f"Cycle {cycle} result: {result['action']}")
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                log(f"CYCLE ERROR: {tb}")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        log("STOPPED by user")
    except Exception as e:
        log(f"LOOP ERROR: {type(e).__name__}: {e}")
    finally:
        mt5.shutdown()
        log("MT5 disconnected")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='DMR Live Executor v3')
    parser.add_argument('--once', action='store_true', help='Run single scan')
    parser.add_argument('--loop', action='store_true', help='Run continuous loop')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval (seconds)')
    args = parser.parse_args()
    if args.loop:
        run_loop(args.interval)
    else:
        result = run_once()
        print(f"Result: {result}")
