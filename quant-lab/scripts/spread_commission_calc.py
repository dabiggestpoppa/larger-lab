"""
Spread + Commission Calculator
===============================
Simple math. No overthinking.
"""

import json
import os

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
STEP1_FILE = os.path.join(REPORTS_DIR, "step1_eurusd_baseline.json")

# Current spreads from MT5 (pips)
SPREADS_PIPS = {
    "EURUSD": 0.20,
    "USDJPY": 0.20,
    "CHFJPY": 1.40,
    "NZDUSD": 0.20,
    "AUDUSD": 0.30,
    "USDCHF": 0.70,
    "GBPJPY": 1.00,
}

# Pip value per 0.01 lot in USD (approximate)
# Majors (EUR/USD, GBP/USD, etc): 1 pip = $0.10 per 0.01 lot
# JPY pairs: 1 pip = $0.07 per 0.01 lot (10 JPY per pip, ~$0.067)
PIP_VALUE_USD = {
    "EURUSD": 0.10,
    "USDJPY": 0.07,
    "CHFJPY": 0.07,
    "NZDUSD": 0.10,
    "AUDUSD": 0.10,
    "USDCHF": 0.10,
    "GBPJPY": 0.07,
}

# Sweep backtest trade counts (floor operating point)
SWEEP_DATA = {
    "EURUSD": {"trades": 5593, "wr": 82.9},
    "USDJPY": {"trades": 6220, "wr": 82.2},
    "CHFJPY": {"trades": 9582, "wr": 82.6},
    "NZDUSD": {"trades": 4548, "wr": 82.1},
    "AUDUSD": {"trades": 4530, "wr": 82.9},
    "USDCHF": {"trades": 4944, "wr": 81.5},
    "GBPJPY": {"trades": 4883, "wr": 81.8},
}

COMMISSION_PER_TRADE = 0.07  # $0.07 round-turn


if __name__ == "__main__":
    print("=" * 65)
    print("SPREAD + COMMISSION COST ESTIMATE")
    print("=" * 65)

    # ── EURUSD Detailed ──
    with open(STEP1_FILE) as f:
        baseline = json.load(f)

    total_trades = baseline.get("total_trades", 0)
    wr = baseline.get("win_rate", 0)
    gross_pnl = baseline.get("total_pnl_pips", 0)
    avg_win = baseline.get("avg_win", 0)
    avg_loss = baseline.get("avg_loss", 0)

    print(f"\n[EURUSD BASELINE]")
    print(f"  Trades: {total_trades} | WR: {round(wr,1)}%")
    print(f"  Avg Win: {avg_win}p | Avg Loss: {avg_loss}p")
    print(f"  Gross PnL: {gross_pnl:+.1f} pips")

    spread = SPREADS_PIPS["EURUSD"]
    spread_cost_pips = total_trades * spread
    spread_cost_usd = spread_cost_pips * PIP_VALUE_USD["EURUSD"]

    comm_total = total_trades * COMMISSION_PER_TRADE
    comm_pips = comm_total / PIP_VALUE_USD["EURUSD"]

    net_pnl = gross_pnl - spread_cost_pips - comm_pips

    print(f"\n  Spread: {spread}p x {total_trades} = {spread_cost_pips:.1f}p (${spread_cost_usd:.2f})")
    print(f"  Comm:   ${COMMISSION_PER_TRADE}/tr x {total_trades} = ${comm_total:.2f} ({comm_pips:.1f}p)")
    print(f"  Net PnL: {gross_pnl:+.1f} - {spread_cost_pips:.1f} - {comm_pips:.1f} = {net_pnl:+.1f} pips")
    print(f"  Cost as % of gross: {round((spread_cost_pips + comm_pips) / gross_pnl * 100, 1)}%")

    # ── Per-Pair Summary ──
    print(f"\n{'=' * 65}")
    print(f"[PER-PAIR COST ESTIMATES]")
    print("=" * 65)
    print(f"{'Pair':<10} {'Trades':>7} {'WR':>5} {'Sprd':>5} {'Sprd$':>7} {'Comm$':>7} {'Total$':>8}")
    print("-" * 65)

    grand_trades = 0
    grand_sprd_usd = 0
    grand_comm_usd = 0

    for pair in SPREADS_PIPS:
        spread_p = SPREADS_PIPS[pair]
        pip_val = PIP_VALUE_USD[pair]
        data = SWEEP_DATA.get(pair, {"trades": 0, "wr": 0})
        trades = data["trades"]
        wr_val = data["wr"]

        sprd_usd = trades * spread_p * pip_val
        comm_usd = trades * COMMISSION_PER_TRADE
        total_usd = sprd_usd + comm_usd

        grand_trades += trades
        grand_sprd_usd += sprd_usd
        grand_comm_usd += comm_usd

        print(f"{pair:<10} {trades:>7,} {wr_val:>4.1f}% {spread_p:>4.1f}p ${sprd_usd:>6.2f} ${comm_usd:>6.2f} ${total_usd:>7.2f}")

    grand_total = grand_sprd_usd + grand_comm_usd
    print("-" * 65)
    print(f"{'TOTAL':<10} {grand_trades:>7,} {'':>5} {'':>5} ${grand_sprd_usd:>6.2f} ${grand_comm_usd:>6.2f} ${grand_total:>7.2f}")

    print(f"\n  Spread cost:  ${grand_sprd_usd:.2f}")
    print(f"  Commission:   ${grand_comm_usd:.2f}")
    print(f"  Total cost:   ${grand_total:.2f}")
    print(f"  Per trade avg: ${grand_total/grand_trades:.2f}" if grand_trades > 0 else "")
    print("=" * 65)
