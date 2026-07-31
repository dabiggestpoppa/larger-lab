import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

with open(os.path.join(reports, 'trigger_sweep_max_accuracy.json')) as f:
    data = json.load(f)

target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

print("Low-Cost Hex FLOOR configs:")
print("=" * 80)

for pair in target_pairs:
    val = data.get(pair, [])
    if not val:
        continue
    # Get entry with max trades (FLOOR)
    best = max(val, key=lambda x: x.get('trades', 0) if isinstance(x, dict) else 0)
    if isinstance(best, dict):
        trigger = best.get('t1_trigger', 0)
        trades = best.get('trades', 0)
        wr = best.get('wr', 0)
        pf = best.get('pf', 0)
        avg_w = best.get('avg_w', 0)
        avg_l = abs(best.get('avg_l', 0))
        pnl = best.get('pnl', 0)
        tr_per_day = best.get('tr_per_day', 0)
        max_dd = best.get('max_dd', 0)
        
        is_jpy = 'JPY' in pair
        pip_val = 0.01 if is_jpy else 0.0001
        
        # avg_w is in price units, convert to pips
        au_pips = avg_w / pip_val if pip_val > 0 else avg_w
        sl_pips = avg_l / pip_val if pip_val > 0 else avg_l
        
        # For tier config, use AU values at 3 levels
        au1 = round(au_pips * 0.7, 0)  # Conservative
        au2 = round(au_pips, 0)         # Standard  
        au3 = round(au_pips * 1.3, 0)   # Aggressive
        
        print(f'{pair}:')
        print(f'  trigger={trigger}, au_tiers=[{au1}/{au2}/{au3}], sl~{sl_pips:.1f}p')
        print(f'  trades={trades}, wr={wr:.1f}%, pf={pf:.1f}, tr/day={tr_per_day:.3f}')
        print(f'  pnl={pnl:.0f} pips, max_dd={max_dd:.0f} pips')
        print()
