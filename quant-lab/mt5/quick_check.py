import MetaTrader5 as mt5
if not mt5.initialize():
    print('MT5 init failed')
    exit()
acct = mt5.account_info()
print('Login:', acct.login)
print('Balance: $' + str(round(acct.balance, 2)))
print('Server:', acct.server)
print('AutoTrading:', acct.trade_allowed)
for sym in ['EURUSD.PRO', 'USDCHF.PRO']:
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)
    if info and tick:
        spread = round((tick.ask - tick.bid) / info.point, 1)
        print(sym + ': bid=' + str(round(tick.bid, 5)) + ' ask=' + str(round(tick.ask, 5)) + ' spread=' + str(spread) + ' pts')
mt5.shutdown()
