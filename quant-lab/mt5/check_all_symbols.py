import MetaTrader5 as mt5
mt5.initialize()
mt5.login(login=1114712, password='Teflondon1718!', server='OxSecurities-Demo')
symbols = mt5.symbols_get()
all_names = sorted([s.name for s in symbols])
print('All symbols:')
for n in all_names:
    print(' ', n)
mt5.shutdown()
