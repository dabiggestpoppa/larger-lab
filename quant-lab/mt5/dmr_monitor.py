"""
DMR Live Monitor — Dual Executor Status Dashboard
Shows: open positions, pending orders, today's PnL, executor health
Run: python dmr_monitor.py
"""
import MetaTrader5 as mt5
from datetime import datetime

SYMBOLS = {
    'EURUSD.PRO': {'magic': 20260528, 'label': 'EUR/USD'},
    'USDCHF.PRO': {'magic': 20260529, 'label': 'USD/CHF'},
}

def main():
    if not mt5.initialize():
        print('ERROR: MT5 not connected')
        return

    acct = mt5.account_info()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print('=' * 60)
    print('DMR LIVE MONITOR — Dual Executor Dashboard')
    print('Time:', now)
    print('Account:', acct.login, '| Balance: $' + str(round(acct.balance, 2)))
    print('Equity: $' + str(round(acct.equity, 2)))
    print('AutoTrading:', 'ON' if acct.trade_allowed else 'OFF')
    print('=' * 60)

    total_pnl = 0.0
    total_trades_today = 0

    for sym, cfg in SYMBOLS.items():
        print()
        print('---', cfg['label'], '(' + sym + ') ---')

        # Open positions
        positions = mt5.positions_get(symbol=sym)
        our_pos = None
        if positions:
            for pos in positions:
                if pos.magic == cfg['magic']:
                    our_pos = pos
                    break

        if our_pos:
            pnl = our_pos.profit
            total_pnl += pnl
            direction = 'SHORT' if our_pos.type == 1 else 'LONG'
            entry_price = our_pos.price_open
            sl = our_pos.sl
            tp = our_pos.tp
            print('  POSITION:', direction, str(our_pos.volume) + ' lots')
            print('  Entry:', round(entry_price, 5), '| SL:', round(sl, 5), '| TP:', round(tp, 5))
            print('  PnL: $' + str(round(pnl, 2)))
        else:
            print('  No open position')

        # Pending orders
        orders = mt5.orders_get(symbol=sym)
        our_pending = []
        if orders:
            for o in orders:
                if o.magic == cfg['magic']:
                    our_pending.append(o)

        if our_pending:
            for o in our_pending:
                otype = 'SELL_LIMIT' if o.type == 3 else 'BUY_LIMIT' if o.type == 2 else str(o.type)
                print('  PENDING:', otype, '@', round(o.price_open, 5),
                      '| SL:', round(o.sl, 5), '| TP:', round(o.tp, 5))
        else:
            print('  No pending orders')

        # Today's trade history
        from datetime import timedelta
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        history = mt5.history_deals_get(today_start, datetime.now())
        today_deals = []
        if history:
            for d in history:
                if d.magic == cfg['magic'] and d.entry == 1:  # closing deals
                    today_deals.append(d)
                    total_pnl += d.profit

        if today_deals:
            print('  Closed today:', len(today_deals), 'trades')
            for d in today_deals:
                total_trades_today += 1
                print('    ' + d.type_str + ' PnL: $' + str(round(d.profit + d.swap + d.commission, 2)))
        else:
            print('  No closed trades today')

    print()
    print('=' * 60)
    print('TOTAL PnL (open): $' + str(round(total_pnl, 2)))
    print('Total closed trades today:', total_trades_today)
    print('=' * 60)

    # Executor process check
    print()
    print('--- Executor Process Status ---')
    try:
        import subprocess
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-CimInstance Win32_Process -Filter "Name=\'python.exe\'" | Where-Object { $_.CommandLine -like "*dmr_executor*" } | Select-Object ProcessId, @{N=\'Script\';E={if($_.CommandLine -like "*usdchf*"){"} else {"EUR"}}} | Format-List'],
            capture_output=True, text=True, timeout=5
        )
        if 'ProcessId' in result.stdout:
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    print('  ' + line)
        else:
            print('  WARNING: No executor processes found!')
    except Exception as e:
        print('  Process check failed:', str(e))

    mt5.shutdown()

if __name__ == '__main__':
    main()
