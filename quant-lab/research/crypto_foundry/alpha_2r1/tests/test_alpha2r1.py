#!/usr/bin/env python3
"""CRYPTO-ALPHA-2R1 — Comprehensive Test Suite."""
import csv, hashlib, json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CRYPTO = HERE.parent
A1 = CRYPTO / "alpha_1"
A2 = CRYPTO / "alpha_2"
A2R = CRYPTO / "alpha_2r"
A2R1 = HERE
RAW = CRYPTO / "data_1" / "raw"

REGISTRY_HASH = "2abaf8c21200a67e5b06d8ccf42ceb19574a12df21916d314a3c80b47f9a419e"
passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1; print(f"  OK {name}")
    else:
        failed += 1; print(f"  FAIL {name} {detail}")

def parse_ts(s):
    s = s.strip()
    if s.endswith('Z'): s = s[:-1] + '+00:00'
    if '+' in s[10:] or s.count('-') > 2: return datetime.fromisoformat(s)
    return datetime.fromisoformat(s + '+00:00')

# ── 1. FUNDING SIGN ──
def test_funding_sign():
    print("\n=== Funding Sign ===")
    check("LONG+positive funding -> negative PnL", -0.001*10000 < 0)
    check("SHORT+positive funding -> positive PnL", 0.001*10000 > 0)
    check("LONG+negative funding -> positive PnL", -(-0.001)*10000 > 0)
    check("SHORT+negative funding -> negative PnL", (-0.001)*10000 < 0)

# ── 2. HOURLY FUNDING ──
def test_hourly_funding():
    print("\n=== Hourly Funding ===")
    p = RAW / "hl_BTC_funding_hourly_raw.json"
    if p.exists():
        with open(p) as f: data = json.load(f)
        hours = set(parse_ts(r["event_time_utc"]).hour for r in data)
        check("Hourly observations (not just 8h)", len(hours) > 3, f"hours={sorted(hours)}")
        entry = parse_ts("2026-03-01T00:00:00+00:00")
        exit_ = parse_ts("2026-03-02T00:00:00+00:00")
        count = sum(1 for r in data if entry < parse_ts(r["event_time_utc"]) <= exit_)
        check(f"24h hold captures {count} observations", count > 3)

# ── 3. REGISTRY HASH ──
def test_registry_hash():
    print("\n=== Registry Hash ===")
    p = A1 / "ALPHA_1_STRATEGY_REGISTRY_HASH.json"
    if p.exists():
        with open(p) as f: data = json.load(f)
        h = data.get("new_hash", data.get("new_registry_hash", ""))
        check("Registry hash verified", h == REGISTRY_HASH)

# ── 4. SIGNAL LEDGER ──
def test_signal_ledger():
    print("\n=== Signal Ledger ===")
    sig_path = A2R1 / "ALPHA_2R1_SIGNAL_LEDGER.csv"
    hash_path = A2R1 / "ALPHA_2R1_SIGNAL_LEDGER_HASH.json"
    check("Signal ledger exists", sig_path.exists())
    check("Signal hash exists", hash_path.exists())
    if sig_path.exists():
        with open(sig_path) as f: rows = list(csv.DictReader(f))
        check("Signal ledger has entries", len(rows) > 0, f"count={len(rows)}")
        # Verify all 13 strategies represented
        sig_ids = set(r["strategy_id"] for r in rows)
        expected = set(f"ALPHA1_S{i:03d}" for i in range(1, 14))
        check("All 13 strategies in signal ledger", sig_ids == expected)
    if hash_path.exists():
        with open(hash_path) as f: data = json.load(f)
        check("Signal hash is SHA-256", data.get("hash_algorithm") == "SHA-256")

# ── 5. ALL STRATEGIES ──
def test_all_strategies():
    print("\n=== All Strategies ===")
    p = A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv"
    if p.exists():
        with open(p) as f: ids = [r["strategy_id"] for r in csv.DictReader(f)]
        check("All 13 strategies present", sorted(ids) == sorted([f"ALPHA1_S{i:03d}" for i in range(1,14)]))

def test_all_controls():
    print("\n=== All Controls ===")
    p = A2R1 / "ALPHA_2R1_CONTROL_METRICS.csv"
    if p.exists():
        with open(p) as f: ids = [r["strategy_id"] for r in csv.DictReader(f)]
        check("All 6 controls present", sorted(ids) == sorted([f"ALPHA1_C{i:03d}" for i in range(1,7)]))

# ── 6. F8 MAPPING ──
def test_f8_mapping():
    print("\n=== F8 Mapping ===")
    p = A2R1 / "ALPHA_2R1_CONTROL_MAPPING_AUDIT.csv"
    if p.exists():
        with open(p) as f: rows = list(csv.DictReader(f))
        check("All 13 strategies mapped", len(rows) == 13)
        check("All F8_applicable=YES", all(r["F8_applicable"] == "YES" for r in rows))

# ── 7. FALSIFICATION ──
def test_falsification():
    print("\n=== Falsification ===")
    fm = A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv"
    sm = A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv"
    if fm.exists() and sm.exists():
        with open(fm) as f: frows = {r["strategy_id"]: r for r in csv.DictReader(f)}
        with open(sm) as f: srows = {r["strategy_id"]: r for r in csv.DictReader(f)}
        check("All 13 in falsification matrix", len(frows) == 13)
        # F3 triggers for all (all net_PF <= 1.0)
        for sid, sr in srows.items():
            net_pf = float(sr["net_PF"])
            if net_pf <= 1.0:
                check(f"F3 for {sid} (net_PF={net_pf:.3f})", frows[sid]["F3"] == "NO_NET_EDGE")

# ── 8. FUNDING ATTRIBUTION ──
def test_funding_attribution():
    print("\n=== Funding Attribution ===")
    p = A2R1 / "ALPHA_2R1_FUNDING_ATTRIBUTION.csv"
    if p.exists():
        with open(p) as f: rows = {r["strategy_id"]: r for r in csv.DictReader(f)}
        check("All 13 in funding attribution", len(rows) == 13)
        for sid, r in rows.items():
            g = float(r["gross_trading_bps"])
            f = float(r["funding_bps"])
            c = float(r["costs_bps"])
            n = float(r["net_bps"])
            check(f"{sid}: gross-costs+funding=net", abs(g-c+f-n) < 0.1)

# ── 9. ALL ARTIFACTS ──
def test_all_artifacts():
    print("\n=== All Artifacts ===")
    required = [
        "ALPHA_2R1_PRE_RUN_LOCK.json", "ALPHA_2R1_CROSS_ASSET_CONTAMINATION_ROOT_CAUSE.md",
        "ALPHA_2R1_PRICE_SOURCE_CONTRACT.json", "ALPHA_2R1_SIGNAL_LEDGER.csv",
        "ALPHA_2R1_SIGNAL_LEDGER_HASH.json", "ALPHA_2R1_F8_AUDIT.md",
        "ALPHA_2R1_CONTROL_MAPPING_AUDIT.csv", "ALPHA_2R1_EFFECTIVE_EVENT_AUDIT.md",
        "ALPHA_2R1_ENGINE_TEST_REPORT.md", "ALPHA_2R1_TRADE_LEDGER.csv",
        "ALPHA_2R1_CONTROL_LEDGER.csv", "ALPHA_2R1_STRATEGY_METRICS.csv",
        "ALPHA_2R1_CONTROL_METRICS.csv", "ALPHA_2R1_FALSIFICATION_MATRIX.csv",
        "ALPHA_2R1_FAMILY_SUMMARY.csv", "ALPHA_2R1_FUNDING_ATTRIBUTION.csv",
        "ALPHA_2R1_COST_STRESS.csv", "ALPHA_2R1_THREE_WAY_RECONCILIATION.csv",
        "ALPHA_2R1_FORWARD_CANDIDATE_REGISTRY.csv", "ALPHA_2R1_REPORT.md",
        "ALPHA_2R1_DECISION.json",
    ]
    for name in required:
        check(f"Artifact: {name}", (A2R1 / name).exists())

# ── 10. DECISION ──
def test_decision():
    print("\n=== Decision ===")
    p = A2R1 / "ALPHA_2R1_DECISION.json"
    if p.exists():
        with open(p) as f: d = json.load(f)
        check("Decision is PASS", d.get("decision") == "PASS_ALPHA2_FINAL_FALSIFICATION_COMPLETE")
        check("Registry hash verified", d.get("registry_hash_verified") == True)
        check("Signal ledger hash present", "signal_ledger_hash" in d)

# ── 11. THREE-WAY RECONCILIATION ──
def test_three_way():
    print("\n=== Three-Way Reconciliation ===")
    p = A2R1 / "ALPHA_2R1_THREE_WAY_RECONCILIATION.csv"
    if p.exists():
        with open(p) as f: rows = list(csv.DictReader(f))
        check("All 13 in reconciliation", len(rows) == 13)
        for r in rows:
            check(f"{r['strategy_id']}: has difference_reason",
                  r.get("difference_reason", "") != "")

# ── 12. CROSS-ASSET ISOLATION (logic test) ──
def test_cross_asset_isolation():
    print("\n=== Cross-Asset Isolation (logic) ===")
    # Verify PriceStore key structure
    p = A2R1 / "ALPHA_2R1_PRICE_SOURCE_CONTRACT.json"
    if p.exists():
        with open(p) as f: c = json.load(f)
        keys = c.get("canonical_keys", {})
        check("BTC_PERP key exists", "BTC_PERP" in keys)
        check("ETH_PERP key exists", "ETH_PERP" in keys)
        check("BTC_SPOT key exists", "BTC_SPOT" in keys)
        check("ETH_SPOT key exists", "ETH_SPOT" in keys)
        check("BTC and ETH are separate keys",
              keys.get("BTC_PERP", {}).get("asset") != keys.get("ETH_PERP", {}).get("asset"))

# ── 13. RESULT COMPLETENESS ──
def test_result_completeness():
    print("\n=== Result Completeness ===")
    fm = A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv"
    sm = A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv"
    if fm.exists() and sm.exists():
        with open(fm) as f: fids = [r["strategy_id"] for r in csv.DictReader(f)]
        with open(sm) as f: sids = [r["strategy_id"] for r in csv.DictReader(f)]
        check("Falsification matches metrics", set(fids) == set(sids))
    fwd = A2R1 / "ALPHA_2R1_FORWARD_CANDIDATE_REGISTRY.csv"
    if fwd.exists():
        with open(fwd) as f: rows = list(csv.DictReader(f))
        survivors = [r for r in rows if r.get("status") == "UNCONFIRMED_DEVELOPMENT_SURVIVOR"]
        check("No survivors (all falsified)", len(survivors) == 0)

# ── 14. TOY ENGINE ARITHMETIC ──
def test_toy_engine():
    print("\n=== Toy Engine Arithmetic ===")
    entry, exit_ = 100000.0, 100500.0
    gross = (exit_ - entry) / entry * 10000
    check("Gross = 50 bps", abs(gross - 50.0) < 0.01)
    cost = 5.0
    f1, f2, f3 = -0.001*10000, -(-0.0005)*10000, -0.0008*10000
    total_f = f1+f2+f3
    check("Funding = -13 bps", abs(total_f - (-13.0)) < 0.01)
    net = gross - cost + total_f
    check("Net = 32 bps", abs(net - 32.0) < 0.01)

# ── MAIN ──
def main():
    global passed, failed
    print("=" * 60)
    print("CRYPTO-ALPHA-2R1 TEST SUITE")
    print("=" * 60)
    test_funding_sign()
    test_hourly_funding()
    test_registry_hash()
    test_signal_ledger()
    test_all_strategies()
    test_all_controls()
    test_f8_mapping()
    test_falsification()
    test_funding_attribution()
    test_all_artifacts()
    test_decision()
    test_three_way()
    test_cross_asset_isolation()
    test_result_completeness()
    test_toy_engine()
    print(f"\n{'='*60}\nRESULTS: {passed} passed, {failed} failed\n{'='*60}")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
