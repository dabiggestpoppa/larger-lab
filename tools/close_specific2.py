import MetaTrader5 as mt5
import json, time

cfg_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
with open(cfg_file) as f:
    cfg = json.load(f)

mt5.initialize()
mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])

tickets = [91311115, 91312396, 91312785]
for ticket in tickets:
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        print(f"Ticket {ticket}: NOT FOUND (already closed?)")
        continue
    
    p = positions[0]
    print(f"Ticket {ticket}: {p.symbol} {'BUY' if p.type==0 else 'SELL'} @ {p.price_open} vol={p.volume} PnL={p.profit}")
    
    tick = mt5.symbol_info_tick(p.symbol)
    sym = mt5.symbol_info(p.symbol)
    if not tick or not sym:
        print(f"  SKIP - no tick/symbol")
        continue
    
    price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
    otype = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    
    # Try IOC first, then FOK
    for fill_mode in [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK]:
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
            "type_filling": fill_mode,
            "position": p.ticket
        }
        res = mt5.order_send(req)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  CLOSED (fill_mode={fill_mode})")
            break
        else:
            rc = res.retcode if res else 'None'
            cm = res.comment if res else str(mt5.last_error())
            print(f"  fill_mode={fill_mode} failed: {rc} - {cm}")
        time.sleep(0.5)
    
    time.sleep(1)

acct = mt5.account_info()
print(f"\nBalance: {acct.balance} | Equity: {acct.equity}")

# Check remaining positions
remaining = mt5.positions_get()
if remaining:
    for p in remaining:
        if p.magic == cfg['magic_number']:
            print(f"  STILL OPEN: {p.symbol} ticket={p.ticket} PnL={p.profit}")
else:
    print("No DMR positions remaining")

mt5.shutdown()
print("Done.")
