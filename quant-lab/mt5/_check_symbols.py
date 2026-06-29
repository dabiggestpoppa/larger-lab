import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

names = ['EURUSD.PRO','GBPUSD.PRO','USDJPY.PRO','GBPJPY.PRO','CHFJPY.PRO']
for n in names:
    info = mt5.symbol_info(n)
    tick = mt5.symbol_info_tick(n)
    if info:
        bid = tick.bid if tick else "N/A"
        print(f"{n}: visible={info.visible}, bid={bid}, digits={info.digits}")
    else:
        print(f"{n}: NOT FOUND")

mt5.shutdown()
