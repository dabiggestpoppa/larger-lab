import json
from pathlib import Path

reports_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
targets = ['EURGBP','EURCHF','EURCAD','EURNZD','EURAUD','EURJPY']

for asset in targets:
    fpath = reports_dir / f"{asset}_atomic_structure.json"
    if fpath.exists():
        with open(fpath) as f:
            data = json.load(f)
        # Try to extract key metrics
        trades = data.get('total_trades', data.get('trades', '?'))
        wr = data.get('win_rate', data.get('wr', '?'))
        pf = data.get('profit_factor', data.get('pf', '?'))
        days = data.get('data_days', '?')
        tpd = data.get('trades_per_day', round(trades/days, 2) if isinstance(trades, int) and isinstance(days, int) else '?')
        print(f"{asset:10s} | trades={trades} | days={days} | tr/day={tpd} | WR={wr}% | PF={pf}")
    else:
        print(f"{asset:10s} | NO FILE")
