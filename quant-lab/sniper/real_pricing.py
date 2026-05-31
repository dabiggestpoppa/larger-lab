"""
Real Prop Firm Pricing — Compiled from browser scrape 2026-05-30
Source: PropFirmMatch /{firm}/challenge pages (actual pricing tables)
Updated PES calculator using true all-in cost (activation + challenge fee)
"""

import sys, json
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

from pathlib import Path
from datetime import datetime, date
from quant_lab.sniper.database import init_database, list_firms, upsert_firm, insert_pes_snapshot, get_connection
from quant_lab.sniper.pes_calculator import PESCalculator, FirmProfile, EngineEdge

# ── REAL PRICING DATA (from browser scrape) ──────────────────
# Format: {firm_name: {size_k: {activation, promo, original, billing, total}}}
# "total" = activation + promo (true all-in first cost)

REAL_PRICING = {
    # ── FUTURES ──────────────────────────────────────────────
    "Apex Trader Funding": {
        25:  {"activation": 69.00, "promo": 19.90, "original": 199.00, "billing": "one time", "total": 88.90, "type": "1-Step Intraday"},
        50:  {"activation": 79.00, "promo": 24.90, "original": 249.00, "billing": "one time", "total": 103.90, "type": "1-Step Intraday"},
        100: {"activation": 99.00, "promo": 39.90, "original": 399.00, "billing": "one time", "total": 138.90, "type": "1-Step Intraday"},
        150: {"activation": 129.00, "promo": 59.90, "original": 599.00, "billing": "one time", "total": 188.90, "type": "1-Step Intraday"},
    },
    "My Funded Futures": {
        25:  {"activation": 0, "promo": 57.00, "original": 95.00, "billing": "monthly", "total": 57.00, "type": "1-Step monthly"},
        50:  {"activation": 0, "promo": 91.80, "original": 153.00, "billing": "monthly", "total": 91.80, "type": "1-Step monthly"},
        100: {"activation": 0, "promo": 172.00, "original": 344.00, "billing": "monthly", "total": 172.00, "type": "1-Step monthly"},
        150: {"activation": 0, "promo": 238.50, "original": 477.00, "billing": "monthly", "total": 238.50, "type": "1-Step monthly"},
    },
    "Topstep": {
        50:  {"activation": 149, "promo": 49, "original": None, "billing": "monthly", "total": 198, "type": "Express monthly"},
        100: {"activation": 149, "promo": 99, "original": None, "billing": "monthly", "total": 248, "type": "Express monthly"},
        150: {"activation": 149, "promo": 149, "original": None, "billing": "monthly", "total": 298, "type": "Express monthly"},
        # Also has no-activation plans:
        50:  {"activation": 0, "promo": 95, "original": None, "billing": "monthly", "total": 95, "type": "Classic monthly"},
        100: {"activation": 0, "promo": 149, "original": None, "billing": "monthly", "total": 149, "type": "Classic monthly"},
        150: {"activation": 0, "promo": 229, "original": None, "billing": "monthly", "total": 229, "type": "Classic monthly"},
    },
    "Lucid Trading": {
        25:  {"activation": 0, "promo": 50.00, "original": None, "billing": "one time", "total": 50.00, "type": "1-Step"},
        50:  {"activation": 0, "promo": 70.00, "original": None, "billing": "one time", "total": 70.00, "type": "1-Step"},
        100: {"activation": 0, "promo": 112.50, "original": None, "billing": "one time", "total": 112.50, "type": "1-Step"},
        150: {"activation": 0, "promo": 185.00, "original": None, "billing": "one time", "total": 185.00, "type": "1-Step"},
    },
    "Tradeify": {
        25:  {"activation": 0, "promo": 65.40, "original": None, "billing": "one time", "total": 65.40, "type": "1-Step"},
        50:  {"activation": 0, "promo": 87.00, "original": None, "billing": "one time", "total": 87.00, "type": "1-Step"},
        100: {"activation": 0, "promo": 159.00, "original": None, "billing": "one time", "total": 159.00, "type": "1-Step"},
        150: {"activation": 0, "promo": 221.40, "original": None, "billing": "one time", "total": 221.40, "type": "1-Step"},
    },
    "Alpha Futures": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "Top One Futures": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "Funded Futures Family": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "E8 Futures": {
        25:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "FundedNext Futures": {
        25:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "Goat Funded Futures": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "Traders Launch": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "Take Profit Trader": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "TradeDay": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    "FuturesElite": {
        50:  {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
        100: {"activation": None, "promo": None, "original": None, "billing": None, "total": None, "type": "NEEDS_SCRAPE"},
    },
    # ── FOREX/CFD ─────────────────────────────────────────────
    "Blueberry Funded": {
        5:   {"activation": 0, "promo": 29, "original": None, "billing": "one time", "total": 29, "type": "Evaluation"},
        10:  {"activation": 0, "promo": 55, "original": None, "billing": "one time", "total": 55, "type": "Evaluation"},
        25:  {"activation": 0, "promo": 89, "original": None, "billing": "one time", "total": 89, "type": "Evaluation"},
        50:  {"activation": 0, "promo": 149, "original": None, "billing": "one time", "total": 149, "type": "Evaluation"},
        100: {"activation": 0, "promo": 249, "original": None, "billing": "one time", "total": 249, "type": "Evaluation"},
        150: {"activation": 0, "promo": 325, "original": None, "billing": "one time", "total": 325, "type": "Evaluation"},
        200: {"activation": 0, "promo": 399, "original": None, "billing": "one time", "total": 399, "type": "Evaluation"},
    },
    "E8 Markets": {
        5:   {"activation": 0, "promo": 25, "original": None, "billing": "one time", "total": 25, "type": "Standard"},
        10:  {"activation": 0, "promo": 50, "original": None, "billing": "one time", "total": 50, "type": "Standard"},
        25:  {"activation": 0, "promo": 90, "original": None, "billing": "one time", "total": 90, "type": "Standard"},
        50:  {"activation": 0, "promo": 150, "original": None, "billing": "one time", "total": 150, "type": "Standard"},
        100: {"activation": 0, "promo": 260, "original": None, "billing": "one time", "total": 260, "type": "Standard"},
        200: {"activation": 0, "promo": 480, "original": None, "billing": "one time", "total": 480, "type": "Standard"},
    },
}


def get_best_size(firm_name: str, target_size_k: int = 50) -> tuple:
    """Get the best available pricing for a firm near the target size."""
    pricing = REAL_PRICING.get(firm_name)
    if not pricing:
        return None, None, None

    # First try exact match
    if target_size_k in pricing and pricing[target_size_k].get('total') is not None:
        p = pricing[target_size_k]
        return target_size_k, p['total'], p.get('billing', 'unknown')

    # Find nearest available
    available = [(sk, p) for sk, p in pricing.items() if p.get('total') is not None]
    if not available:
        return None, None, None

    nearest = min(available, key=lambda x: abs(x[0] - target_size_k))
    return nearest[0], nearest[1]['total'], nearest[1].get('billing', 'unknown')


def compute_adjusted_pes(firm_name: str, size_k: int, total_cost: float, omega: float,
                         edge_daily_return: float = 0.035, days_per_cycle: int = 21,
                         payout_rate: float = 0.90) -> dict:
    """
    Compute PES using TRUE cost instead of promo table price.
    
    Adjusted PES = (Omega × α × payout_rate × daily_return × days) / total_true_cost
    
    Where:
    - Omega = leverage = account_size / total_cost
    - α = edge quality (1.0 = perfect)
    - total_true_cost = activation + challenge fee
    """
    if total_cost is None or total_cost <= 0:
        return {"pes": 0, "error": "No pricing data"}

    account_size = size_k * 1000
    omega = account_size / total_cost
    expected_return = edge_daily_return * days_per_cycle * account_size * payout_rate
    velocity = expected_return / total_cost

    return {
        "firm": firm_name,
        "size_k": size_k,
        "total_cost": total_cost,
        "omega": round(omega, 2),
        "expected_return_21d": round(expected_return, 2),
        "velocity": round(velocity, 4),
        "pes": round(velocity, 4),
        "cost_per_1k": round(total_cost / size_k, 2),
    }


# ── CEREBUS EDGE (unchanged) ────────────────────────────────
EDGE = EngineEdge(
    win_rate=0.857,
    profit_factor=8.0,
    sharpe=8.5,
    avg_daily_return=0.035,
    max_dd_pct=0.03,
    avg_trades_per_day=2.0,
    payout_rate=0.90,
    days_per_cycle=21,
)


if __name__ == '__main__':
    init_database()

    print("=" * 65)
    print("PES RECALCULATION — TRUE COST (activation + challenge fee)")
    print(f"Edge: WR {EDGE.win_rate:.1%} | PF {EDGE.profit_factor} | Sharpe {EDGE.sharpe}")
    print("=" * 65)

    results = []
    for firm_name, pricing in REAL_PRICING.items():
        for size_k, data in pricing.items():
            total = data.get('total')
            if total is None:
                continue
            r = compute_adjusted_pes(firm_name, size_k, total,
                                     omega=(size_k * 1000) / total,
                                     edge_daily_return=EDGE.avg_daily_return,
                                     days_per_cycle=EDGE.days_per_cycle,
                                     payout_rate=EDGE.payout_rate)
            r['billing'] = data.get('billing', 'unknown')
            r['type'] = data.get('type', 'unknown')
            r['activation'] = data.get('activation', 0)
            results.append(r)

    # Sort by PES descending
    results.sort(key=lambda x: x['pes'], reverse=True)

    print(f"\n{'Rank':<5} {'Firm':<30} {'Size':<8} {'True Cost':<11} {'Ω':<8} {'PES':<8} {'Billing'}")
    print("-" * 90)

    for i, r in enumerate(results, 1):
        print(f"{i:<5} {r['firm']:<30} {r['size_k']}K{'':<4} ${r['total_cost']:<10.2f} {r['omega']:<8.1f} {r['pes']:<8.4f} {r['billing']}")

    print(f"\n{'='*65}")
    print("KEY INSIGHTS:")
    print(f"{'='*65}")

    # Find best by category
    futures = [r for r in results if r['firm'] in [
        "Apex Trader Funding", "My Funded Futures", "Topstep", "Lucid Trading", "Tradeify"
    ]]
    forex = [r for r in results if r['firm'] in [
        "Blueberry Funded", "E8 Markets"
    ]]

    if futures:
        best_futures = max(futures, key=lambda x: x['pes'])
        print(f"\nBEST FUTURES: {best_futures['firm']} {best_futures['size_k']}K — PES {best_futures['pes']:.4f} (${best_futures['total_cost']:.2f} total)")

    if forex:
        best_forex = max(forex, key=lambda x: x['pes'])
        print(f"BEST FOREX/CFD: {best_forex['firm']} {best_forex['size_k']}K — PES {best_forex['pes']:.4f} (${best_forex['total_cost']:.2f} total)")

    # Worst (negative expected value)
    low_pes = [r for r in results if r['pes'] < 1.0]
    if low_pes:
        print(f"\n⚠️ LOW PES (<1.0) — These lose money over time:")
        for r in low_pes:
            print(f"   {r['firm']} {r['size_k']}K — PES {r['pes']:.4f} (${r['total_cost']:.0f} cost)")
