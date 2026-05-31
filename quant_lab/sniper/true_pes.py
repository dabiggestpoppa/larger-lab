"""
True Cost PES Recalculation — 2026-05-30
Uses real pricing from PropFirmMatch /challenges pages (activation + challenge fee)
instead of promo prices from the comparison table.

Key findings:
- Apex $5K at $0.42? → ACTUALLY $69 activation + $X challenge (need $5K plan)
- Apex 50K: $79 activation + $24.90 = $103.90 (not $24.90!)
- Topstep 50K: $149 activation + $49/month (Express) or $95/month (Classic, no activation)
- Lucid 50K: $70 one-time (no activation)
- E8 Futures 50K: $120/month (no activation)
- Blueberry 50K: ~$175 ($10 activation + $165 challenge)
- MAD was right: the "cheap" firms aren't that cheap once you count activation
"""

import sys, json
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

# ── REAL PRICING (from browser scrape of /challenge pages) ───
#.Size → {activation, challenge_fee, billing}
# "monthly" = recurring; "one time" = single payment

REAL_FUTURES = {
    # Scraped from /futures/prop-firms/{slug}/challenges
    "Apex Trader Funding":     {25: dict(act=69, fee=19.90, billing="one-time"), 50: dict(act=79, fee=24.90, billing="one-time"), 100: dict(act=99, fee=39.90, billing="one-time"), 150: dict(act=129, fee=59.90, billing="one-time")},
    "My Funded Futures":       {25: dict(act=0, fee=57.00, billing="monthly"), 50: dict(act=0, fee=91.80, billing="monthly"), 100: dict(act=0, fee=172.00, billing="monthly"), 150: dict(act=0, fee=238.50, billing="monthly")},
    "Topstep":                 {50: dict(act=0, fee=95, billing="monthly"), 100: dict(act=0, fee=149, billing="monthly"), 150: dict(act=0, fee=229, billing="monthly")},
    "Lucid Trading":           {25: dict(act=0, fee=50.00, billing="one-time"), 50: dict(act=0, fee=70.00, billing="one-time"), 100: dict(act=0, fee=112.50, billing="one-time"), 150: dict(act=0, fee=185.00, billing="one-time")},
    "Tradeify":                {25: dict(act=0, fee=65.40, billing="one-time"), 50: dict(act=0, fee=87.00, billing="one-time"), 100: dict(act=0, fee=159.00, billing="one-time"), 150: dict(act=0, fee=221.40, billing="one-time")},
    "E8 Futures":              {25: dict(act=0, fee=88, billing="monthly"), 50: dict(act=0, fee=120, billing="monthly"), 100: dict(act=0, fee=208, billing="monthly"), 150: dict(act=0, fee=312, billing="monthly")},
    "FundedNext Futures":      {25: dict(act=0, fee=55, billing="one-time TBD"), 50: dict(act=0, fee=85, billing="one-time TBD"), 100: dict(act=0, fee=150, billing="one-time TBD")},
    "Goat Funded Futures":      {50: dict(act=0, fee=130, billing="one-time TBD"), 100: dict(act=0, fee=200, billing="one-time TBD")},
    "Traders Launch":          {50: dict(act=0, fee=140, billing="one-time TBD"), 100: dict(act=0, fee=210, billing="one-time TBD")},
    "Take Profit Trader":      {50: dict(act=0, fee=125, billing="one-time TBD"), 100: dict(act=0, fee=185, billing="one-time TBD"), 150: dict(act=0, fee=250, billing="one-time TBD")},
    "TradeDay":                {50: dict(act=0, fee=115, billing="one-time TBD"), 100: dict(act=0, fee=165, billing="one-time TBD"), 150: dict(act=0, fee=225, billing="one-time TBD")},
    "FuturesElite":            {50: dict(act=0, fee=125, billing="one-time TBD"), 100: dict(act=0, fee=195, billing="one-time TBD")},
    "Alpha Futures":           {50: dict(act=0, fee=120, billing="one-time TBD"), 100: dict(act=0, fee=190, billing="one-time TBD")},
    "Top One Futures":         {50: dict(act=0, fee=115, billing="one-time TBD"), 100: dict(act=0, fee=175, billing="one-time TBD")},
    "Funded Futures Family":   {50: dict(act=0, fee=140, billing="one-time TBD"), 100: dict(act=0, fee=210, billing="one-time TBD")},
}

REAL_FOREX = {
    # Scraped from /prop-firms/{slug}/challenges (forex section)
    "Blueberry Funded":  {5: dict(act=10, fee=24, billing="one-time"), 10: dict(act=10, fee=45, billing="one-time"), 25: dict(act=10, fee=90, billing="one-time"), 50: dict(act=10, fee=165, billing="one-time"), 100: dict(act=10, fee=330, billing="one-time"), 200: dict(act=10, fee=660, billing="one-time")},
    "E8 Markets":        {5: dict(act=0, fee=25, billing="one-time"), 10: dict(act=0, fee=50, billing="one-time"), 25: dict(act=0, fee=90, billing="one-time"), 50: dict(act=0, fee=150, billing="one-time"), 100: dict(act=0, fee=260, billing="one-time"), 200: dict(act=0, fee=480, billing="one-time")},
    "For Traders":       {50: dict(act=0, fee=150, billing="one-time TBD"), 100: dict(act=0, fee=275, billing="one-time TBD")},
    "Blue Guardian":     {50: dict(act=0, fee=175, billing="one-time TBD"), 100: dict(act=0, fee=300, billing="one-time TBD")},
    "BrightFunded":      {25: dict(act=0, fee=100, billing="one-time TBD"), 50: dict(act=0, fee=175, billing="one-time TBD"), 100: dict(act=0, fee=300, billing="one-time TBD")},
    "FundingPips":       {25: dict(act=0, fee=149, billing="one-time TBD"), 50: dict(act=0, fee=249, billing="one-time TBD"), 100: dict(act=0, fee=399, billing="one-time TBD")},
    "The5ers":           {40: dict(act=0, fee=275, billing="one-time TBD"), 80: dict(act=0, fee=475, billing="one-time TBD")},
    "Goat Funded Trader":{50: dict(act=0, fee=150, billing="one-time TBD"), 100: dict(act=0, fee=250, billing="one-time TBD")},
    "Maven":             {50: dict(act=0, fee=150, billing="one-time TBD"), 100: dict(act=0, fee=275, billing="one-time TBD")},
    "Trade The Pool":    {50: dict(act=0, fee=200, billing="one-time TBD"), 100: dict(act=0, fee=350, billing="one-time TBD")},
    "Alpha Capital":     {50: dict(act=0, fee=200, billing="one-time TBD"), 100: dict(act=0, fee=350, billing="one-time TBD")},
    "Crypto Fund Trader":{50: dict(act=0, fee=250, billing="one-time TBD"), 100: dict(act=0, fee=400, billing="one-time TBD")},
}


def calc_pes(account_size_dollars: int, total_activation: float, challenge_fee: float,
             billing: str, monthly_edge_return: float = 0.35,
             days_to_payout_cycle: int = 14) -> dict:
    """
    Calculate PES (Propagation Efficiency Score) with TRUE cost.

    Total capital at risk:
    - One-time: activation + challenge_fee (sunk cost, ~3 month lifespan)
    - Monthly: first month = activation + monthly_fee

    Omega (Ω) = account_size / total_cost
    Alpha (α) = expected_return_per_cycle / account_size
    PES = Ω × α (how efficiently capital propagates through the well)

    Higher PES = more leverage per dollar at risk = better.
    PES > 1.0 = profitable propagation
    PES < 1.0 = money sink
    """
    total_first_cost = total_activation + challenge_fee

    if billing == "monthly":
        # Monthly: cost is ongoing. First cycle cost = 1 month + activation
        # Subsequent cycles: just monthly fee
        # Amortize over first payout cycle (14 days ≈ 0.5 month)
        cycle_cost = total_activation + challenge_fee  # first month
        # Monthly cost drag
        monthly_cost = challenge_fee
    else:
        # One-time: activation + challenge fee, lasts ~3 months (90 days)
        cycle_cost = total_first_cost
        monthly_cost = total_first_cost / 3  # amortized

    # Expected return per payout cycle
    # CEREBUS edge: ~85.7% WR, ~3.5% avg daily return on account
    expected_cycle_return = monthly_edge_return * account_size_dollars * (days_to_payout_cycle / 30)

    # Net return after cost
    net_return = expected_cycle_return - cycle_cost

    # Omega: leverage ratio (account size / total cost)
    omega = account_size_dollars / total_first_cost if total_first_cost > 0 else 0

    # PES = velocity = net return / total cost
    pes = net_return / total_first_cost if total_first_cost > 0 else 0

    # Cost efficiency: cost per $1000 of account
    cost_per_1k = (total_first_cost / account_size_dollars) * 1000

    # Crossover: monthly cost = monthly return → go live instead
    monthly_return = monthly_edge_return * account_size_dollars / 30 * 14  # 2-week return
    crossover = monthly_cost / (monthly_edge_return / 30) if monthly_edge_return > 0 else float('inf')

    return {
        "account_size": account_size_dollars,
        "total_first_cost": round(total_first_cost, 2),
        "omega": round(omega, 1),
        "expected_cycle_return": round(expected_cycle_return, 2),
        "net_return": round(net_return, 2),
        "pes": round(pes, 4),
        "cost_per_1k": round(cost_per_1k, 2),
        "monthly_cost": round(monthly_cost, 2),
        "billing": billing,
        "profitable": pes > 0,
    }


def run_full_analysis():
    """Run PES on all firms with real pricing."""
    EDGE_DAILY_RETURN = 0.035  # 3.5% avg daily return (CEREBUS)

    FUTURES_ACCOUNTS = [25, 50, 100]  # K
    FOREX_ACCOUNTS = [50, 100]  # K

    results = []

    print("=" * 100)
    print("TRUE COST PES ANALYSIS — 2026-05-30")
    print(f"Edge: {EDGE_DAILY_RETURN:.1%} daily return | Source: PropFirmMatch /challenges pages")
    print(f"{'='*100}\n")

    print(f"{'#':<4} {'Firm':<30} {'Size':<7} {'Act.':<7} {'Fee':<9} {'Total':<9} {'Ω':<7} {'PES':<8} {'$/1K':<7} {'Billing'}")
    print("-" * 100)

    count = 0
    # Futures
    for firm, sizes in REAL_FUTURES.items():
        for size_k, data in sizes.items():
            if size_k not in FUTURES_ACCOUNTS:
                continue
            r = calc_pes(
                account_size_dollars=size_k * 1000,
                total_activation=data['act'],
                challenge_fee=data['fee'],
                billing=data['billing'],
                monthly_edge_return=EDGE_DAILY_RETURN,
            )
            count += 1
            r['rank'] = count
            r['firm'] = firm
            r['size_k'] = size_k
            r['category'] = 'futures'
            r['act'] = data['act']
            r['fee'] = data['fee']
            results.append(r)
            print(f"{count:<4} {firm:<30} {size_k}K{'':<3} ${data['act']:<6.0f} ${data['fee']:<8.2f} ${r['total_first_cost']:<8.2f} {r['omega']:<7.1f} {r['pes']:<8.4f} ${r['cost_per_1k']:<6.2f} {data['billing']}")

    # Forex
    for firm, sizes in REAL_FOREX.items():
        for size_k, data in sizes.items():
            if size_k not in FOREX_ACCOUNTS:
                continue
            r = calc_pes(
                account_size_dollars=size_k * 1000,
                total_activation=data['act'],
                challenge_fee=data['fee'],
                billing=data['billing'],
                monthly_edge_return=EDGE_DAILY_RETURN,
            )
            count += 1
            r['rank'] = count
            r['firm'] = firm
            r['size_k'] = size_k
            r['category'] = 'forex'
            r['act'] = data['act']
            r['fee'] = data['fee']
            results.append(r)
            print(f"{count:<4} {firm:<30} {size_k}K{'':<3} ${data['act']:<6.0f} ${data['fee']:<8.2f} ${r['total_first_cost']:<8.2f} {r['omega']:<7.1f} {r['pes']:<8.4f} ${r['cost_per_1k']:<6.2f} {data['billing']}")

    # Sort by PES
    results.sort(key=lambda x: x['pes'], reverse=True)

    print(f"\n{'='*100}")
    print(f"RANKED BY PES (highest = best capital efficiency):")
    print(f"{'='*100}\n")
    print(f"{'#':<4} {'Firm':<30} {'Size':<7} {'True Cost':<10} {'Ω':<7} {'PES':<8} {'Cat.':<8} {'Profitable?'}")
    print("-" * 100)

    for i, r in enumerate(results, 1):
        prof = "✅ YES" if r['profitable'] else "❌ NO"
        print(f"{i:<4} {r['firm']:<30} {r['size_k']}K{'':<3} ${r['total_first_cost']:<9.2f} {r['omega']:<7.1f} {r['pes']:<8.4f} {r['category']:<8} {prof}")

    winners = [r for r in results if r['profitable']]
    losers = [r for r in results if not r['profitable']]

    print(f"\n✅ Profitable: {len(winners)} | ❌ Unprofitable: {len(losers)}")

    if winners:
        print(f"\n🏆 TOP 5 EXPLOITS (true cost):")
        for i, r in enumerate(winners[:5], 1):
            print(f"   {i}. {r['firm']} {r['size_k']}K — PES {r['pes']:.4f} | Ω {r['omega']:.1f}x | ${r['total_first_cost']:.0f} total")

    if losers:
        print(f"\n⚠️ UNPROFITABLE (PES < 0) — AVOID:")
        for r in losers:
            print(f"   {r['firm']} {r['size_k']}K — PES {r['pes']:.4f} (${r['total_first_cost']:.0f} cost, ${r['net_return']:.0f} net loss/cycle)")

    return results


if __name__ == '__main__':
    import json as _json
    from pathlib import Path
    from datetime import datetime

    results = run_full_analysis()

    # Save results
    output = {
        "generated": datetime.utcnow().isoformat(),
        "method": "true_cost_pes",
        "source": "propfirmmatch_challenge_pages",
        "results": results,
    }
    out_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\sniper\true_pes_results.json")
    with open(out_path, 'w') as f:
        _json.dump(output, f, indent=2)
    print(f"\nResults saved: {out_path}")
