import json
d = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json'))
print("=== MULTI-ASSET ST RESULTS (5/31) ===")
for r in d['results']:
    lt = r.get('long_trades', '?')
    lw = r.get('long_wr', '?')
    st = r.get('short_trades', '?')
    sw = r.get('short_wr', '?')
    print(f"{r['asset_key']:10s}: total={r['total_trades']:4d} wr={r['win_rate']:5.1f}% | long={lt}/{lw}% | short={st}/{sw}%")

print("\n=== EURUSD PER-ASSET MC (current) ===")
import glob, os
for f in sorted(glob.glob(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset/*_mc_results.json')):
    d2 = json.load(open(f))
    sym = d2.get('asset', os.path.basename(f))
    bt = d2.get('backtest', {})
    print(f"{sym}: trades={bt.get('trades','?')}, wr={bt.get('win_rate','?')}, pnl={bt.get('pnl_p','?')}")
