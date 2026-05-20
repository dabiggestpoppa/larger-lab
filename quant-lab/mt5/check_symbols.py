import MetaTrader5 as mt5
mt5.initialize()
mt5.login(login=1114712, password='Teflondon1718!', server='OxSecurities-Demo')
acct = mt5.account_info()
print('Account:', acct.login, '|', acct.server, '| Balance:', acct.balance)
symbols = mt5.symbols_get()
forex = [s.name for s in symbols if any(x in s.name for x in ['EUR','GBP','USD','JPY','CHF','AUD','NZD','CAD'])]
print('Forex symbols:')
for s in sorted(forex)[:40]:
    info = mt5.symbol_info(s)
    if info:
        print(' ', s, '| visible:', info.visible, '| digits:', info.digits, '| bid:', mt5.symbol_info_tick(s).bid if mt5.symbol_info_tick(s) else 'N/A')
mt5.shutdown()
