#!/usr/bin/env python3
"""Quick test to verify MT5 order placement works."""
import MetaTrader5 as mt5
import time

LOGIN = 650898
PASSWORD = "Teflondon1718!"
SERVER = "OxSecurities-Live"
SYMBOL = "EURUSD.PRO"

print("=" * 50)
print("MT5 Order Placement Test")
print("=" * 50)

if not mt5.initialize():
    print(f"Init failed: {mt5.last_error()}")
    exit(1)
print("MT5 initialized OK")

auth = mt5.login(login=LOGIN, password=PASSWORD, server=SERVER)
if not auth:
    print(f"Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)
print(f"Logged in: {LOGIN} / {SERVER}")

acct = mt5.account_info()
if acct:
    print(f"Balance: {acct.balance} | Equity: {acct.equity} | Trade allowed: {acct.trade_allowed}")

term = mt5.terminal_info()
if term:
    print(f"Terminal trade_allowed: {term.trade_allowed}")

sym = mt5.symbol_info(SYMBOL)
if not sym:
    print(f"Symbol {SYMBOL} not found!")
    mt5.shutdown()
    exit(1)

print(f"\n{SYMBOL}: Visible={sym.visible} Digits={sym.digits} Point={sym.point}")
print(f"  Volume min={sym.volume_min} step={sym.volume_step}")

if not sym.visible:
    mt5.symbol_select(SYMBOL, True)
    time.sleep(2)
    sym = mt5.symbol_info(SYMBOL)
    print(f"  After select: Visible={sym.visible}")

tick = mt5.symbol_info_tick(SYMBOL)
if not tick:
    print("No tick!")
    mt5.shutdown()
    exit(1)
print(f"Tick: Bid={tick.bid} Ask={tick.ask}")

positions = mt5.positions_get(symbol=SYMBOL)
print(f"Existing positions: {len(positions) if positions else 0}")

# Place test BUY 0.01
print(f"\n--- TEST: BUY 0.01 {SYMBOL} ---")
price = tick.ask
sl = round(price - 0.0050, sym.digits)
tp = round(price + 0.0050, sym.digits)

req = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": SYMBOL,
    "volume": 0.01,
    "type": mt5.ORDER_TYPE_BUY,
    "price": round(price, sym.digits),
    "sl": sl, "tp": tp,
    "deviation": 20, "magic": 99999999,
    "comment": "DMR_TEST",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

res = mt5.order_send(req)
if res is None:
    print(f"FAILED: None response, error: {mt5.last_error()}")
elif res.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"SUCCESS! Ticket={res.order} Price={res.price}")
    time.sleep(2)
    # Close it
    pos_list = mt5.positions_get(ticket=res.order)
    if pos_list:
        p = pos_list[0]
        bid = mt5.symbol_info_tick(SYMBOL).bid
        close_req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": SYMBOL, "volume": 0.01,
            "type": mt5.ORDER_TYPE_SELL,
            "price": round(bid, sym.digits),
            "deviation": 20, "magic": 99999999,
            "comment": "DMR_TEST_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            "position": res.order
        }
        cr = mt5.order_send(close_req)
        if cr and cr.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Closed OK. Open PnL was: {p.profit}")
        else:
            print(f"Close failed: {cr.retcode if cr else mt5.last_error()}")
else:
    names = {10004:"Requote",10005:"Rejected",10010:"Invalid",10014:"BadVol",10015:"BadPrice",10016:"BadStops",10017:"Disabled",10018:"Closed",10019:"NoFunds",10026:"AutoDisabled"}
    n = names.get(res.retcode, f"Code {res.retcode}")
    print(f"FAILED: {n} — {res.comment}")

mt5.shutdown()
print("\nDone.")
