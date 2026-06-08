"""
Look at actual backtest output (JSON) that has both pips and $ figures.
If we can find records with both, we can derive $/pip directly.
"""
import json, os, glob

reports_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Look for any files with per-trade data
for f in sorted(glob.glob(os.path.join(reports_dir, '*.json'))):
    try:
        with open(f) as fh:
            data = json.load(fh)
        # Check structure
        if isinstance(data, dict):
            first_key = list(data.keys())[0] if data else None
            if first_key:
                first_val = data[first_key]
                keys = list(first_val.keys()) if isinstance(first_val, dict) else []
                # Look for files with trade-level data
                if 'trades' in keys or 'pnl' in keys or 'trade' in str(keys).lower():
                    fn = os.path.basename(f)
                    print(f"{fn}: keys={keys[:10]}")
    except:
        pass
