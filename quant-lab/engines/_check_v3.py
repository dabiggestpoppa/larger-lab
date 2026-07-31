import json
from pathlib import Path

reports_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
targets = ['EURGBP','EURCHF','EURCAD','EURNZD','EURAUD','EURJPY','EURUSD']

# Check v3 campaign
fpath = reports_dir / "full_backtest_campaign_v3.json"
if fpath.exists():
    with open(fpath) as f:
        data = json.load(f)
    print("=== Campaign v3 ===")
    print(f"Keys: {list(data.keys())[:10]}")
    if 'results' in data:
        for r in data['results']:
            if r.get('asset_key', r.get('symbol','')) in targets:
                ak = r.get('asset_key', r.get('symbol',''))
                tr = r.get('total_trades', 0)
                days = r.get('data_days', 0)
                tpd = tr/days if days > 0 else 0
                wr = r.get('win_rate', 0)
                pf = r.get('profit_factor', 0)
                print(f"  {ak:10s} | {tr:5d} tr | {days:5d} d | {tpd:.2f} t/d | WR={wr:.1f}% | PF={pf:.2f}")
    elif isinstance(data, list):
        for r in data[:5]:
            print(f"  Keys: {list(r.keys())[:10]}")
    else:
        print(f"  Type: {type(data)}")
        if isinstance(data, dict):
            for k in list(data.keys())[:5]:
                v = data[k]
                if isinstance(v, dict):
                    print(f"  {k}: trades={v.get('total_trades','?')} wr={v.get('win_rate','?')} pf={v.get('profit_factor','?')}")
else:
    print("No v3 file")

# Also check fx_calibration_summary
fpath2 = reports_dir / "fx_calibration_summary.json"
if fpath2.exists():
    with open(fpath2) as f:
        data2 = json.load(f)
    print("\n=== FX Calibration Summary ===")
    print(f"Keys: {list(data2.keys())[:10]}")
    if 'results' in data2:
        for r in data2['results']:
            ak = r.get('asset_key', r.get('symbol',''))
            if ak in targets:
                tr = r.get('total_trades', 0)
                days = r.get('data_days', 0)
                tpd = tr/days if days > 0 else 0
                wr = r.get('win_rate', 0)
                pf = r.get('profit_factor', 0)
                print(f"  {ak:10s} | {tr:5d} tr | {days:5d} d | {tpd:.2f} t/d | WR={wr:.1f}% | PF={pf:.2f}")
