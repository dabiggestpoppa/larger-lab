"""Update remaining forex + crypto firms with true costs"""
import sys, json; sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from quant_lab.sniper.database import init_database, get_connection, upsert_firm

REMAINING_TRUE_COSTS = {
    # FOREX — from earlier challenge page scrape
    "Blueberry Funded": {
        5: {"act": 10, "fee": 24, "total": 34},
        10: {"act": 10, "fee": 45, "total": 55},
        25: {"act": 10, "fee": 90, "total": 100},
        50: {"act": 10, "fee": 165, "total": 175},
        100: {"act": 10, "fee": 330, "total": 340},
    },
    "E8 Markets": {
        5: {"act": 0, "fee": 25, "total": 25},
        10: {"act": 0, "fee": 50, "total": 50},
        25: {"act": 0, "fee": 90, "total": 90},
        50: {"act": 0, "fee": 150, "total": 150},
        100: {"act": 0, "fee": 260, "total": 260},
    },
    "For Traders": {
        50: {"act": 0, "fee": 150, "total": 150},
        100: {"act": 0, "fee": 275, "total": 275},
    },
    "Blue Guardian": {
        50: {"act": 0, "fee": 175, "total": 175},
        100: {"act": 0, "fee": 300, "total": 300},
    },
    "BrightFunded": {
        25: {"act": 0, "fee": 100, "total": 100},
        50: {"act": 0, "fee": 175, "total": 175},
        100: {"act": 0, "fee": 300, "total": 300},
    },
    "FundingPips": {
        25: {"act": 0, "fee": 149, "total": 149},
        50: {"act": 0, "fee": 249, "total": 249},
        100: {"act": 0, "fee": 399, "total": 399},
    },
    "The5ers": {
        40: {"act": 0, "fee": 275, "total": 275},
        80: {"act": 0, "fee": 475, "total": 475},
    },
    "Goat Funded Trader": {
        50: {"act": 0, "fee": 150, "total": 150},
        100: {"act": 0, "fee": 250, "total": 250},
    },
    "Maven": {
        50: {"act": 0, "fee": 150, "total": 150},
        100: {"act": 0, "fee": 275, "total": 275},
    },
    "Trade The Pool": {
        50: {"act": 0, "fee": 200, "total": 200},
        100: {"act": 0, "fee": 350, "total": 350},
    },
    "Alpha Capital": {
        50: {"act": 0, "fee": 200, "total": 200},
        100: {"act": 0, "fee": 350, "total": 350},
    },
    # CRYPTO
    "Crypto Fund Trader": {
        2: {"act": 0, "fee": 125, "total": 125},  # 2.5K instant
        5: {"act": 0, "fee": 58, "total": 58},
        10: {"act": 0, "fee": 110, "total": 110},
        25: {"act": 0, "fee": 240, "total": 240},
        50: {"act": 0, "fee": 389, "total": 389},
        100: {"act": 0, "fee": 660, "total": 660},
        200: {"act": 0, "fee": 1250, "total": 1250},
    },
}

init_database()
conn = get_connection()
updated = 0

for firm_name, sizes in REMAINING_TRUE_COSTS.items():
    row = conn.execute("SELECT firm_id FROM prop_firms WHERE name = ?", (firm_name,)).fetchone()
    if not row:
        print(f"  SKIP: {firm_name} not in DB")
        continue

    firm_id = row["firm_id"]
    true_cost = {}
    act_fees = {}
    bill_types = {}

    for size_k, data in sizes.items():
        sk = str(int(size_k))
        true_cost[sk] = data["total"]
        act_fees[sk] = data["act"]
        bill_types[sk] = "one-time"

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
print(f"\nTotal updated: {updated}")
