import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\multi_asset_forex_m5.json') as f:
    d = json.load(f)

print("DMR (Deep_Mean_Reversion) Backtest Results:")
print("-" * 70)
dmr = d['Deep_Mean_Reversion']
for sym, data in dmr.items():
    if isinstance(data, dict):
        print(f"  {sym:12} | WR: {data.get('win_rate', 0):5.1f}% | PnL: {data.get('total_pnl_pips', 0):+7.0f}p | Trades: {data.get('total_trades', 0):4} | PF: {data.get('profit_factor', 0):6.1f}")
