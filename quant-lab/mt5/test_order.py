import MetaTrader5 as mt5
import sys
sys.stdout.reconfigure(encoding='utf-8')

if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

acct = mt5.account_info()
print(f"Account: {acct.login} | Balance: ${acct.balance:.2f}")
print(f"Trade allowed: {acct.trade_allowed} | Expert: {acct.trade_expert}")

tick = mt5.symbol_info_tick("EURUSD.PRO")
if tick:
    print(f"Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f}")

info = mt5.symbol_info("EURUSD.PRO")
digits = info.digits

# Test BUY_LIMIT order
entry_price = 1.16272
sl_price = 1.16263
tp_price = 1.16364

# Check if AutoTrading is enabled by trying to place a limit order
request = {
    "action":       mt5.TRADE_ACTION_PENDING,
    "symbol":       "EURUSD.PRO",
    "volume":       0.01,
    "type":         mt5.ORDER_TYPE_BUY_LIMIT,
    "price":        round(entry_price, digits),
    "sl":           round(sl_price, digits),
    "tp":           round(tp_price, digits),
    "magic":        20260528,
    "comment":      "DMR_TEST",
    "type_filling": mt5.ORDER_FILLING_RETURN,
}

print(f"\nSending BUY_LIMIT @ {entry_price:.5f} SL={sl_price:.5f} TP={tp_price:.5f}")
result = mt5.order_send(request)

if result is None:
    print("order_send returned None")
else:
    print(f"retcode={result.retcode} | comment={result.comment}")
    if result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
        print(f"ORDER PLACED ticket={result.order}")
        # Cancel it immediately (test only)
        cancel_req = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": result.order,
        }
        cancel_result = mt5.order_send(cancel_req)
        print(f"Cancel: retcode={cancel_result.retcode if cancel_result else 'None'}")
    elif result.retcode == 10027:
        print("AutoTrading DISABLED")
    else:
        print(f"Failed: {result.comment}")

mt5.shutdown()
print("Done")
