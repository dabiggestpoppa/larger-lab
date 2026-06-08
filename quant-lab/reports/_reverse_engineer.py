"""
The June 4 cost sweep files show commission_pips for each pair.
From commission_pips and $0.07 commission, derive $/pip at 0.01 lot.

commission_pips = $0.07 / ($/pip_at_0.01lot)
So: $/pip_at_0.01lot = $0.07 / commission_pips
And: $/pip_per_lot = $/pip_at_0.01lot / 0.01 = $/pip_at_0.01lot * 100
"""
import json

files = [
    r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\fx_eur_cost_sweep.json',
    r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\fx_gbp_cost_sweep.json',
    r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\fx_chfjpy_cost_sweep.json',
]

print(f"{'Symbol':<12} {'comm_pips':>10} {'$/pip@0.01':>12} {'$/pip/lot':>12}")
print("-" * 50)

for fpath in files:
    with open(fpath) as f:
        data = json.load(f)
    for sym, modes in data.items():
        for mode_name, vals in modes.items():
            if mode_name == 'costs':
                comm = vals['commission_pips']
                spread = vals['spread_pips']
                pip_size = vals['pip_size']
                if comm > 0:
                    $per_pip_001 = 0.07 / comm
                    $per_pot_lot = $per_pip_001 * 100
                    print(f"{sym:<12} {comm:>10.4f} ${$per_pip_001:>11.4f} ${$per_pot_lot:>11.2f}  (pip_size={pip_size})")
