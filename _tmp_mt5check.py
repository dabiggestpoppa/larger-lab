import MetaTrader5 as mt5
mt5.initialize()
pos = mt5.positions_get()
print(f'Positions: {len(pos) if pos else 0}')
for p in (pos or []):
    side = "BUY" if p.type == 0 else "SELL"
    print(f'  {p.symbol} {side} vol={p.volume:.2f} entry={p.price_open:.5f} SL={p.sl:.5f} TP={p.tp:.5f} P&L={p.profit:.2f}')
acc = mt5.account_info()
if acc:
    print(f'Eq: {acc.equity:.2f}')
mt5.shutdown()
