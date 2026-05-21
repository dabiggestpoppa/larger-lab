"""Close specific DMR positions by ticket"""
import MetaTrader5 as mt5
import json, time

cfg_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
with open(cfg_file) as f:
    cfg = json.load(f)

mt5.initialize()
mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])

tickets = [91311115, 91312396, 91312785]
for ticket in tickets:
    # Get position by ticket
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        print(f"Ticket {ticket}: NOT FOUND (already closed?)")
        continue
    
    p = positions[0]
    print(f"Ticket {ticket}: {p.symbol} {'BUY' if p.type==0 else 'SELL'} @ {p.price_open} vol={p.volume} PnL={p.profit}")
    
    tick = mt5.symbol_info_tick(p.symbol)
    sym = mt5.symbol_info(p.symbol)
    if not tick or not sym:
        print(f"  SKIP — no tick/symbol")
        continue
    
    price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
    otype = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": p.symbol,
        "volume": p.volume,
        "type": otype,
        "price": round(price, sym.digits),
        "deviation": 30,
        "magic": cfg['magic_number'],
        "comment": "DMR_CLOSE_ALL",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
        "position": p.ticket
    }
    res = mt5.order_send(req)
    if res:
        print(f"  Result: retcode={res.retcode} comment={res.comment}")
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  ✅ CLOSED")
        else:
            print(f"  ❌ FAILED")
    else:
        print(f"  ❌ order_send returned None: {mt5.last_error()}")
    time.sleep(1)

acct = mt5.account_info()
print(f"\nBalance: {acct.balance} | Equity: {acct.equity}")
mt5.shutdown()
