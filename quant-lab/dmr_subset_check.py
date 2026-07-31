"""Extract 2-year subset stats from standalone backtest trades"""
import csv

trades = []
with open(r"quant-lab\engines\reports\dmr_standalone_trades.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        trades.append(row)

# 2024-2025 subset
sub = [t for t in trades if t["date"][:4] in ("2024", "2025")]
all_pnls = [float(t["pnl_pips"]) for t in trades]
sub_pnls = [float(t["pnl_pips"]) for t in sub]

def stats(pnls, label):
    if not pnls:
        print(f"{label}: No trades")
        return
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = len(pnls)
    wr = len(wins)/total*100
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 0.001
    pf = gp/gl
    print(f"{label}:")
    print(f"  Trades: {total} | W: {len(wins)} L: {len(losses)} | WR: {wr:.1f}%")
    print(f"  PnL: {sum(pnls):+.1f}p | PF: {pf:.2f}")
    print(f"  Avg Win: {sum(wins)/len(wins) if wins else 0:.1f}p | Avg Loss: {sum(losses)/len(losses) if losses else 0:.1f}p")

stats(all_pnls, "DMR 4Y (2023-2026)")
stats(sub_pnls, "DMR 2Y (2024-2025)")
