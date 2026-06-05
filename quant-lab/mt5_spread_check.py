try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        symbols = ['EURUSD.PRO', 'GBPUSD.PRO', 'USDJPY.PRO', 'USDCHF.PRO', 'AUDUSD.PRO', 'NZDUSD.PRO', 'EURGBP.PRO', 'EURJPY.PRO', 'GBPJPY.PRO', 'CHFJPY.PRO']
        for sym in symbols:
            info = mt5.symbol_info(sym)
            if info:
                print('%s: spread=%d points digits=%d point=%f' % (sym, info.spread, info.digits, info.point))
        mt5.shutdown()
    else:
        print('MT5 init failed')
except Exception as e:
    print('Error: %s' % e)
