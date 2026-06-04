import json
from pathlib import Path
from datetime import datetime

reports_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
targets = ['EURGBP','EURCHF','EURCAD','EURNZD','EURAUD','EURJPY']

# Find all NAUTILUS_SYMMETRY_TRAP files for these pairs
for asset in targets:
    pattern = f"NAUTILUS_SYMMETRY_TRAP_{asset}*.json"
    files = sorted(reports_dir.glob(pattern))
    if files:
        # Get the latest
        latest = files[-1]
        with open(latest) as f:
            d = json.load(f)
        tr = d.get('total_trades', d.get('trades', '?'))
        wr = d.get('win_rate', d.get('wr', '?'))
        pf = d.get('profit_factor', d.get('pf', '?'))
        days = d.get('data_days', d.get('n_days', '?'))
        tpd = tr/days if isinstance(tr, int) and isinstance(days, int) else '?'
        print(f"{asset:10s} | {str(latest.name):50s} | tr={tr} | days={days} | tpd={tpd} | WR={wr}% | PF={pf}")
    else:
        print(f"{asset:10s} | NO FILES")
