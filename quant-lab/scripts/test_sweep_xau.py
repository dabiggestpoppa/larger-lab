import sys, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

print('Loading XAU data...')
bars, _ = load_m5_csv(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\XAUUSD_M5.csv', pip_size=0.1)
print(f'Loaded {len(bars)} bars')

base = ASSET_CONFIGS['XAUUSD']

# Test 3 different multipliers
for mult in [0.3, 1.0, 2.0]:
    tiers = {}
    for tn in ['T1','T2','T3']:
        t = base['tiers'][tn]
        tiers[tn] = {'ar_max': round(t['ar_max']*mult,1), 'au': round(t['au']*mult,1), 'trigger': round(t['trigger']*mult,1)}
    
    t0 = time.time()
    bt = SymmetryTrapBacktest(pip_size=base['pip_value'], tier_config=tiers, symbol='XAUUSD', config=None)
    result = bt.run(bars)
    elapsed = time.time() - t0
    
    print(f'mult={mult:.1f} | t1_trigger={tiers["T1"]["trigger"]:.1f} | '
          f'trades={result.total_trades} | WR={result.win_rate:.1f}% | PF={result.profit_factor:.2f} | '
          f'pnl={result.total_pnl_pips:.1f} | maxDD={result.max_drawdown_pips:.1f} | {elapsed:.1f}s')
