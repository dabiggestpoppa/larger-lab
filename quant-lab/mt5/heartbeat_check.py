import MetaTrader5 as mt5
import sys
from datetime import datetime, timedelta

if not mt5.initialize():
    print('MT5 FAIL')
    sys.exit()

EST = -5

acct = mt5.account_info()
print('Login: {} | Balance: ${:.2f} | Equity: ${:.2f}'.format(acct.login, acct.balance, acct.equity))
print('AutoTrading: {} | Leverage: 1:{}'.format(acct.trade_allowed, acct.leverage))
print()

# Positions
pos = mt5.positions_get()
if pos:
    print('--- OPEN POSITIONS ---')
    for p in pos:
        dir_type = 'BUY' if p.type == 0 else 'SELL'
        print('  [{}] {} vol={} entry={:.5f} SL={:.5f} TP={:.5f} PnL={:+.2f} magic={}'.format(
            dir_type, p.symbol, p.volume, p.price_open, p.sl, p.tp, p.profit, p.magic))
else:
    print('No open positions')

# Pending orders
pend = mt5.orders_get()
if pend:
    print('--- PENDING ORDERS ---')
    for o in pend:
        if o.type == 2:
            dir_type = 'BUY_LIMIT'
        elif o.type == 3:
            dir_type = 'SELL_LIMIT'
        else:
            dir_type = 'TYPE_{}'.format(o.type)
        placed = datetime.fromtimestamp(o.time_setup)
        print('  [{}] {} price={:.5f} vol={} magic={} placed={}'.format(
            dir_type, o.symbol, o.price_current, o.volume_initial, o.magic, placed.strftime('%H:%M')))
else:
    print('No pending orders')

# Deals today
today = datetime.now().replace(hour=0, minute=0, second=0)
deals = mt5.history_deals_get(today, datetime.now())
if deals:
    print('--- TODAYS DEALS ({}) ---'.format(len(deals)))
    for d in deals[-10:]:
        dir_type = 'BUY' if d.type == 0 else 'SELL'
        print('  [{}] {} price={:.5f} vol={} comm={:+.2f}'.format(
            dir_type, d.symbol, d.price, d.volume, d.commission))
else:
    print('No deals today')

# Executor PIDs
print()
print('--- EXECUTOR PROCESSES ---')
import subprocess
result = subprocess.run(['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize'], capture_output=True, text=True)
print(result.stdout if result.stdout else 'None running')

mt5.shutdown()
