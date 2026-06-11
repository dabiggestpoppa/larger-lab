from symmetry_trap_backtest_24h import SymmetryTrapBacktest, load_m5_csv

bars, sym = load_m5_csv('../data/EURUSD_M5.csv', 0.0001)
bt = SymmetryTrapBacktest(pip_size=0.0001, symbol='EURUSD')
result = bt.run(bars)

hour_data = {}
for t in result.trades:
    h = t.est_hour
    if h not in hour_data:
        hour_data[h] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
    hour_data[h]['trades'] += 1
    if t.pnl_pips > 0:
        hour_data[h]['wins'] += 1
    hour_data[h]['pnl'] += t.pnl_pips

print('24H ST - Hourly breakdown:')
print('Hour  | Trades |   WR   |   PnL')
print('-' * 40)
for h in sorted(hour_data.keys()):
    d = hour_data[h]
    wr = d['wins'] / d['trades'] * 100 if d['trades'] > 0 else 0
    print('{:02d}:00 | {:>6d} | {:>5.1f}% | {:>+8.1f}p'.format(h, d['trades'], wr, d['pnl']))

# Session breakdowns
asian = list(range(19, 24)) + list(range(0, 3))
london = list(range(3, 12))
ny = list(range(12, 19))

print()
for name, hours in [('Asian (19:00-03:00 EST)', asian), ('London (03:00-12:00 EST)', london), ('NY (12:00-19:00 EST)', ny)]:
    t = sum(hour_data.get(h, {}).get('trades', 0) for h in hours)
    w = sum(hour_data.get(h, {}).get('wins', 0) for h in hours)
    p = sum(hour_data.get(h, {}).get('pnl', 0.0) for h in hours)
    wr = w / t * 100 if t > 0 else 0
    print('{}: {} tr, {:.1f}% WR, {:+.1f}p'.format(name, t, wr, p))

print()
print('Total: {} trades, {:.1f}% WR, {:+.1f}p, PF {:.2f}'.format(
    result.total_trades, result.win_rate, result.total_pnl_pips, result.profit_factor))
