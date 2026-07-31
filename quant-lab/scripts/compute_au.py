import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

with open(os.path.join(reports, 'trigger_sweep_max_accuracy.json')) as f:
    data = json.load(f)

target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

# For each pair, get the FLOOR entry (max trades) and compute AU from avg_w
for pair in target_pairs:
    val = data.get(pair, [])
    if not val:
        continue
    best = max(val, key=lambda x: x.get('trades', 0) if isinstance(x, dict) else 0)
    if isinstance(best, dict):
        avg_w = best.get('avg_w', 0)
        avg_l = abs(best.get('avg_l', 0))
        trigger = best.get('t1_trigger', 0)
        pnl = best.get('pnl', 0)
        trades = best.get('trades', 0)
        wr = best.get('wr', 0)
        
        # AU ≈ avg_w for winning trades (TP hit)
        # For JPY pairs, pip_size = 0.01, for others 0.0001
        is_jpy = 'JPY' in pair
        pip = 0.01 if is_jpy else 0.0001
        
        au_pips = avg_w  # avg_w is already in pips based on the sweep
        sl_pips = avg_l  # avg_l is in pips
        
        print(f'{pair}: trigger={trigger}, au~{au_pips:.1f}p, sl~{sl_pips:.1f}p, trades={trades}, wr={wr:.1f}%, pnl={pnl:.0f}')
        print(f'  RR = {au_pips/sl_pips:.2f}' if sl_pips > 0 else '  RR = inf')
