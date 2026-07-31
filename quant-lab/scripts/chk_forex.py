import pickle, os
REPORTS_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

with open(os.path.join(REPORTS_DIR, '_matrix_data.pkl'), 'rb') as f:
    pkl = pickle.load(f)

# Check a few forex pairs that showed negative
for sym in ['EURUSD', 'GBPUSD', 'EURJPY', 'GBPAUD']:
    if sym in pkl:
        print(f'\n{sym}:')
        for mode, e in pkl[sym].items():
            if isinstance(e, dict) and 'net_usd' in e:
                print(f'  {mode}: net_usd={e["net_usd"]:.2f} cost_pct={e.get("cost_pct",0):.1f}% gross={e.get("gross_usd",0):.2f} sprd={e.get("sprd_usd",0):.2f} comm={e.get("comm_usd",0):.2f}')

# The issue: forex pkl was computed with OLD pip values
# EURUSD pip should be $0.10, let's check what was used
print('\n--- EURUSD FLOOR raw ---')
e = pkl['EURUSD']['FLOOR']
print(f'  trigger={e.get("trigger")} trades={e.get("trades")} pnl_pips={e.get("pnl")} gross_usd={e.get("gross_usd")} cost_pct={e.get("cost_pct")}')
print(f'  If pnl={e.get("pnl")} pips and gross_usd={e.get("gross_usd")}, then implied pip value = {e.get("gross_usd",0)/e.get("pnl",1):.4f}')
