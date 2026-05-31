"""
Update database with true costs from challenge page scraping.
Run once after scraping all firm challenge pages.
"""
import sys, json
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

from quant_lab.sniper.database import init_database, get_connection, list_firms, upsert_firm

# True cost data structure: {firm_name: {size_k: {activation, fee, billing, total, type}}}
TRUE_COSTS = {
    # FUTURES — verified from /challenge pages
    "Apex Trader Funding": {
        25: {"act": 69, "fee": 19.90, "billing": "one-time", "total": 88.90, "type": "1-Step Intraday"},
        50: {"act": 79, "fee": 24.90, "billing": "one-time", "total": 103.90, "type": "1-Step Intraday"},
        100: {"act": 99, "fee": 39.90, "billing": "one-time", "total": 138.90, "type": "1-Step Intraday"},
        150: {"act": 129, "fee": 59.90, "billing": "one-time", "total": 188.90, "type": "1-Step Intraday"},
    },
    "My Funded Futures": {
        25: {"act": 0, "fee": 57.00, "billing": "monthly", "total": 57.00, "type": "1-Step"},
        50: {"act": 0, "fee": 91.80, "billing": "monthly", "total": 91.80, "type": "1-Step"},
        100: {"act": 0, "fee": 172.00, "billing": "monthly", "total": 172.00, "type": "1-Step"},
        150: {"act": 0, "fee": 238.50, "billing": "monthly", "total": 238.50, "type": "1-Step"},
    },
    "Topstep": {
        50: {"act": 0, "fee": 95, "billing": "monthly", "total": 95, "type": "Classic"},
        100: {"act": 0, "fee": 149, "billing": "monthly", "total": 149, "type": "Classic"},
        150: {"act": 0, "fee": 229, "billing": "monthly", "total": 229, "type": "Classic"},
    },
    "Lucid Trading": {
        25: {"act": 0, "fee": 50.00, "billing": "one-time", "total": 50.00, "type": "1-Step"},
        50: {"act": 0, "fee": 70.00, "billing": "one-time", "total": 70.00, "type": "1-Step"},
        100: {"act": 0, "fee": 112.50, "billing": "one-time", "total": 112.50, "type": "1-Step"},
        150: {"act": 0, "fee": 185.00, "billing": "one-time", "total": 185.00, "type": "1-Step"},
    },
    "Tradeify": {
        25: {"act": 0, "fee": 65.40, "billing": "one-time", "total": 65.40, "type": "1-Step"},
        50: {"act": 0, "fee": 87.00, "billing": "one-time", "total": 87.00, "type": "1-Step"},
        100: {"act": 0, "fee": 159.00, "billing": "one-time", "total": 159.00, "type": "1-Step"},
        150: {"act": 0, "fee": 221.40, "billing": "one-time", "total": 221.40, "type": "1-Step"},
    },
    "E8 Futures": {
        25: {"act": 0, "fee": 88, "billing": "monthly", "total": 88, "type": "Standard"},
        50: {"act": 0, "fee": 120, "billing": "monthly", "total": 120, "type": "Standard"},
        100: {"act": 0, "fee": 208, "billing": "monthly", "total": 208, "type": "Standard"},
        150: {"act": 0, "fee": 312, "billing": "monthly", "total": 312, "type": "Standard"},
    },
    "FundedNext Futures": {
        25: {"act": 0, "fee": 55, "billing": "one-time", "total": 55, "type": "Standard"},
        50: {"act": 0, "fee": 85, "billing": "one-time", "total": 85, "type": "Standard"},
        100: {"act": 0, "fee": 150, "billing": "one-time", "total": 150, "type": "Standard"},
    },
    "Goat Funded Futures": {
        50: {"act": 0, "fee": 130, "billing": "one-time", "total": 130, "type": "Standard"},
        100: {"act": 0, "fee": 200, "billing": "one-time", "total": 200, "type": "Standard"},
    },
    "Traders Launch": {
        50: {"act": 0, "fee": 140, "billing": "one-time", "total": 140, "type": "Standard"},
        100: {"act": 0, "fee": 210, "billing": "one-time", "total": 210, "type": "Standard"},
    },
    "Take Profit Trader": {
        50: {"act": 0, "fee": 125, "billing": "one-time", "total": 125, "type": "Standard"},
        100: {"act": 0, "fee": 185, "billing": "one-time", "total": 185, "type": "Standard"},
        150: {"act": 0, "fee": 250, "billing": "one-time", "total": 250, "type": "Standard"},
    },
    "TradeDay": {
        50: {"act": 0, "fee": 115, "billing": "one-time", "total": 115, "type": "Standard"},
        100: {"act": 0, "fee": 165, "billing": "one-time", "total": 165, "type": "Standard"},
        150: {"act": 0, "fee": 225, "billing": "one-time", "total": 225, "type": "Standard"},
    },
    "FuturesElite": {
        50: {"act": 0, "fee": 125, "billing": "one-time", "total": 125, "type": "Standard"},
        100: {"act": 0, "fee": 195, "billing": "one-time", "total": 195, "type": "Standard"},
    },
    "Alpha Futures": {
        50: {"act": 0, "fee": 120, "billing": "one-time", "total": 120, "type": "Standard"},
        100: {"act": 0, "fee": 190, "billing": "one-time", "total": 190, "type": "Standard"},
    },
    "Top One Futures": {
        50: {"act": 0, "fee": 115, "billing": "one-time", "total": 115, "type": "Standard"},
        100: {"act": 0, "fee": 175, "billing": "one-time", "total": 175, "type": "Standard"},
    },
    "Funded Futures Family": {
        50: {"act": 0, "fee": 140, "billing": "one-time", "total": 140, "type": "Standard"},
        100: {"act": 0, "fee": 210, "billing": "one-time", "total": 210, "type": "Standard"},
    },
    # FOREX/CFD
    "Blueberry Funded": {
        50: {"act": 10, "fee": 165, "billing": "one-time", "total": 175, "type": "Evaluation"},
        100: {"act": 10, "fee": 330, "billing": "one-time", "total": 340, "type": "Evaluation"},
    },
    "E8 Markets": {
        50: {"act": 0, "fee": 150, "billing": "one-time", "total": 150, "type": "Standard"},
        100: {"act": 0, "fee": 260, "billing": "one-time", "total": 260, "type": "Standard"},
    },
}


def update_true_costs():
    """Update database firms with true cost data."""
    init_database()
    conn = get_connection()

    updated = 0
    skipped = 0

    for firm_name, sizes in TRUE_COSTS.items():
        # Find firm in DB
        row = conn.execute("SELECT firm_id FROM prop_firms WHERE name = ?", (firm_name,)).fetchone()
        if not row:
            print(f"  SKIP: {firm_name} not in DB")
            skipped += 1
            continue

        firm_id = row["firm_id"]

        # Build true_cost_per_size, activation_fees, billing_types
        true_cost = {}
        act_fees = {}
        bill_types = {}

        for size_k, data in sizes.items():
            true_cost[str(size_k)] = data["total"]
            act_fees[str(size_k)] = data["act"]
            bill_types[str(size_k)] = data["billing"]

        conn.execute("""
            UPDATE prop_firms SET
                true_cost_per_size = ?,
                activation_fees = ?,
                billing_types = ?,
                last_updated = datetime('now')
            WHERE firm_id = ?
        """, (json.dumps(true_cost), json.dumps(act_fees), json.dumps(bill_types), firm_id))

        print(f"  UPDATED: {firm_name} — {len(sizes)} sizes")
        updated += 1

    conn.commit()
    conn.close()

    print(f"\nUpdated: {updated} | Skipped: {skipped}")
    return updated


if __name__ == '__main__':
    update_true_costs()
