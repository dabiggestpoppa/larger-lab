"""Final check: Compare multi-asset results with per-asset MC data."""
import json
from pathlib import Path
from collections import Counter

# 1. Multi-asset results
multi = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json'))
print("=== MULTI-ASSET ST RESULTS (5/31) ===")
eurusd_multi = [r for r in multi['results'] if r['asset_key'] == 'EURUSD'][0]
usdchf_multi = [r for r in multi['results'] if r['asset_key'] == 'USDCHF'][0]
print(f"EURUSD: {eurusd_multi['total_trades']} tr, {eurusd_multi['win_rate']:.1f}% WR")
print(f"USDCHF: {usdchf_multi['total_trades']} tr, {usdchf_multi['win_rate']:.1f}% WR")

# 2. Per-asset MC results (current)
print("\n=== PER-ASSET MC RESULTS (current) ===")
for sym in ['EURUSD', 'USDCHF']:
    p = Path(f'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\reports\\per-asset\\{sym}_mc_results.json')
    if not p.exists():
        print(f"{sym}: FILE NOT FOUND")
        continue
    d = json.load(open(p))
    bt = d.get('backtest', {})
    mc = d.get('monte_carlo', {})
    pnls = d.get('per_trade_pnl', [])
    print(f"{sym}: {bt.get('trades','?')} tr, {bt.get('win_rate','?'):.1f}% WR (from backtest)")
    
    # Recompute WR from per_trade_pnl
    if pnls:
        wins = sum(1 for p in pnls if p > 0)
        losses = sum(1 for p in pnls if p <= 0)
        wr = wins / len(pnls) * 100 if pnls else 0
        print(f"  per_trade_pnl: {len(pnls)} trades, {wins}W/{losses}L = {wr:.1f}% WR")
        
        # Exit type breakdown
        # We don't have exit types in MC data, but we can check PnL distribution
        small_wins = sum(1 for p in pnls if 0 < p < 5)
        med_wins = sum(1 for p in pnls if 5 <= p < 15)
        big_wins = sum(1 for p in pnls if p >= 15)
        small_loss = sum(1 for p in pnls if -5 < p <= 0)
        med_loss = sum(1 for p in pnls if -15 < p <= -5)
        big_loss = sum(1 for p in pnls if p <= -15)
        print(f"  PnL dist: small_wins={small_wins}, med_wins={med_wins}, big_wins={big_wins}")
        print(f"            small_loss={small_loss}, med_loss={med_loss}, big_loss={big_loss}")
        print(f"  PnL range: {min(pnls):.1f} to {max(pnls):.1f}")
        print(f"  Avg PnL: {sum(pnls)/len(pnls):.2f}")

# 3. Check if EURUSD/USDCHF per-asset MC has different format
print("\n=== FILE FORMAT CHECK ===")
for sym in ['EURUSD', 'USDCHF', 'GBPJPY', 'NZDUSD']:
    p = Path(f'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\reports\\per-asset\\{sym}_mc_results.json')
    if not p.exists():
        continue
    d = json.load(open(p))
    has_pnl = 'per_trade_pnl' in d
    has_mc = 'monte_carlo' in d
    has_bt = 'backtest' in d
    print(f"{sym}: keys={list(d.keys())[:5]}... has_pnl={has_pnl}, has_mc={has_mc}, has_bt={has_bt}")

# 4. Check the multi-asset MC results (if they exist)
multi_mc = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\multi_asset\multi_asset_mc_results.json')
if multi_mc.exists():
    print("\n=== MULTI-ASSET MC RESULTS ===")
    d = json.load(open(multi_mc))
    print(f"Keys: {list(d.keys())[:10]}")
    if 'per_trade_pnl' in d:
        pnls = d['per_trade_pnl']
        wins = sum(1 for p in pnls if p > 0)
        print(f"per_trade_pnl: {len(pnls)} trades, {wins}W/{len(pnls)-wins}L = {wins/len(pnls)*100:.1f}% WR")
else:
    print("\nNo multi_asset_mc_results.json found")
