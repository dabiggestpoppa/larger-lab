"""Close all DMR positions and pending orders"""
import MetaTrader5 as mt5
import json, time

cfg_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
with open(cfg_file) as f:
    cfg = json.load(f)

mt5.initialize()
mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])

acct = mt5.account_info()
print(f"Balance: {acct.balance} | Equity: {acct.equity}")

# Close all positions
positions = mt5.positions_get()
closed = 0
if positions:
    for p in positions:
        if p.magic == cfg['magic_number']:
            tick = mt5.symbol_info_tick(p.symbol)
            if not tick:
                print(f"  SKIP {p.symbol} ticket {p.ticket} — no tick")
                continue
            sym = mt5.symbol_info(p.symbol)
            price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
            otype = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": otype,
                "price": round(price, sym.digits),
                "deviation": 20,
                "magic": cfg['magic_number'],
                "comment": "DMR_CLOSE_ALL",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
                "position": p.ticket
            }
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"  CLOSED {p.symbol} ticket {p.ticket} PnL:{p.profit}")
                closed += 1
            else:
                print(f"  FAILED {p.symbol} ticket {p.ticket}: {res.retcode if res else 'None'}")
            time.sleep(0.5)

print(f"\nClosed {closed} positions")

# Cancel pending orders
orders = mt5.orders_get()
cancelled = 0
if orders:
    for o in orders:
        if o.magic == cfg['magic_number']:
            req = {"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket, "symbol": o.symbol, "magic": cfg['magic_number']}
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"  CANCELLED order {o.ticket} {o.symbol}")
                cancelled += 1
            time.sleep(0.3)

print(f"Cancelled {cancelled} pending orders")

acct2 = mt5.account_info()
print(f"\nFinal: Balance={acct2.balance} | Equity={acct2.equity}")
mt5.shutdown()
print("Done.")
