import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\portfolio_risk_simulations.json') as f:
    data = json.load(f)

ff = data.get('fixed_fractional', {})
for strat, pairs in ff.items():
    print(f"\n=== {strat} ===")
    for pair, risks in pairs.items():
        for risk, v in risks.items():
            print(f"  {pair} @ {risk}: PnL=${v['total_pnl']:,.0f} DD={v['max_drawdown_pct']:.2%} PF={v['profit_factor']:.1f} avg_lots={v['avg_lots']:.1f}")
