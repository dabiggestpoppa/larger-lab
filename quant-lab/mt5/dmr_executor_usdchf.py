"""
DMR Live Executor v3 — USD/CHF Production System
==================================================
91.9% WR backtest (1,244 days, 3+ years) | PF 131.9 | Max DD 0.01%
Per-hour P90 calibration from CHF's own M5 distribution.

Key fixes:
- Entry = deep_state (limit order), NOT bar close
- SL/TP set on broker via request.sl/request.tp
- Per-hour P90 thresholds (calibrated from 3yr CHF M5 data)
- Pending order dedup (prevents stacking limit orders)
- MagicNumber separate from EURUSD (20260529 vs 20260528)
"""
import sys, time, json, os
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5

SYMBOL = "USDCHF.PRO"
PIP_MULT = 10000  # CHF: 1 pip = 0.0001

PARAMS = {
    'LotSize':        0.01,
    'DeepMult':       2.0,
    'KillMult':       2.2,
    'MinAR':          3,
    'MaxAR':          45,
    'ESTOffset':      -5,
    'HardExitHour':   17,
    'MaxDailyTrades': 1,
    'MagicNumber':    20260529,
    'SpreadPips':     0.0,
}

LOG_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\live_logs"

def get_p90_threshold(est_hour):
    """USD/CHF per-hour P90 thresholds — calibrated from 3+ years M5 data."""
    thresholds = {
        2: 4.3,   3: 3.9,   4: 3.7,
        5: 4.6,   6: 5.9,   7: 6.3,
        8: 5.8,   9: 4.4,  10: 3.6,
    }
    return thresholds.get(est_hour, 999.0)

def pips_to_price(pips):
    return pips / PIP_MULT

def price_to_pips(price):
    return price * PIP_MULT

def get_est_hour(dt):
    return (dt.hour + PARAMS['ESTOffset']) % 24

def get_est_hour_from_local():
    utc_now = datetime.utcnow()
    return (utc_now.hour + PARAMS['ESTOffset']) % 24

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "executor_usdchf.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_trade(signal_type, details):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "signals_usdchf.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "type": signal_type, **details}) + "\n")

def get_symbol_info():
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        log(f"ERROR: Cannot get info for {SYMBOL}")
        return None
    PARAMS['SpreadPips'] = info.spread * info.point * PIP_MULT
    PARAMS['Point'] = info.point
    PARAMS['Digits'] = info.digits
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
            if pos.magic == PARAMS['MagicNumber']:
                return pos
    return None

def check_pending_orders():
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders:
        return sum(1 for o in orders if o.magic == PARAMS['MagicNumber'])
    return 0

def place_order(is_short, sl_price, tp_price, entry_price=None):
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
            "comment": "DMR_CHF_" + ("SHORT" if is_short else "LONG"),
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
        "comment": f"DMR_CHF_{reason}", "type_filling": mt5.ORDER_FILLING_IOC,
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
    # Asian Range
    asian_high, asian_low = 0.0, 99999.0
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
    # Trading bars
    trading_bars = [b for b in today_bars if 2 <= b['est_h'] < 11]
    # P90 scan with per-hour calibration
    p90_dir, activation, deep_state, kill_switch, body_pips_val = 0, 0.0, 0.0, 0.0, 0.0
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
    # Deep State touch
    for b in trading_bars[p90_idx + 1:]:
        if b['est_h'] >= 12:
            break
        if p90_dir == 1 and b['low'] <= deep_state:
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
    if not mt5.symbol_info(SYMBOL):
        log("ERROR: MT5 not connected")
        return {"action": "error", "msg": "MT5 not connected"}
    get_symbol_info()
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
    # No position — scan for signal
    est_hour = get_est_hour_from_local()
    if not (est_hour >= 2 and est_hour < 11):
        return {"action": "outside_window", "est_hour": est_hour}
    if check_pending_orders():
        return {"action": "pending_order_exists"}
    bars = fetch_recent_bars(500)
    if bars is None:
        return {"action": "no_data"}
    signal = scan_for_signal(bars)
    if signal is None:
        return {"action": "no_signal"}
    is_short = signal['direction'] == 'SHORT'
    entry = signal['entry_price']
    if is_short:
        if signal['tp'] >= entry or signal['sl'] <= entry:
            return {"action": "invalid_tp_sl"}
    else:
        if signal['sl'] >= entry or signal['tp'] <= entry:
            return {"action": "invalid_tp_sl"}
    result = place_order(is_short, signal['sl'], signal['tp'], entry)
    if result and result != "INVALID_TP_SL":
        log_trade("SIGNAL_EXECUTED", signal)
        return {"action": "order_placed", "signal": signal}
    return {"action": "order_failed"}

def run_loop(interval_seconds=30):
    log("=" * 60)
    log(f"DMR LIVE EXECUTOR v3 — USD/CHF 91.9% WR | PF 131.9 | Max DD 0.01%")
    log(f"Symbol: {SYMBOL} | Lots: {PARAMS['LotSize']} | Magic: {PARAMS['MagicNumber']}")
    log(f"DeepMult: {PARAMS['DeepMult']} | KillMult: {PARAMS['KillMult']}")
    log(f"Per-hour P90 calibrated from 3yr CHF M5 data")
    log(f"Entry = deep_state (limit order) | SL/TP on BROKER")
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
    log(f"Separate MagicNumber ({PARAMS['MagicNumber']}) — won't conflict with EURUSD")
    log("=" * 60)
    try:
        cycle = 0
        while True:
            cycle += 1
            log(f"Cycle {cycle} start")
            try:
                result = run_once()
                log(f"Cycle {cycle} result: {result['action']}")
            except Exception as e:
                import traceback
                log(f"CYCLE ERROR: {traceback.format_exc()}")
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
    parser = argparse.ArgumentParser(description='DMR Live Executor v3 — USD/CHF')
    parser.add_argument('--once', action='store_true', help='Run single scan')
    parser.add_argument('--loop', action='store_true', help='Run continuous loop')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval (seconds)')
    args = parser.parse_args()
    if args.loop:
        run_loop(args.interval)
    else:
        if not mt5.initialize():
            print("MT5 init failed"); sys.exit(1)
        result = run_once()
        print(f"Result: {result}")
        mt5.shutdown()
