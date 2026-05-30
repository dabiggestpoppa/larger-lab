"""Phase 1 smoke test — run from project root: python test_phase1.py"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab")

from quant_lab.sniper.ontology_mapper import OntologyMapper, PropFirmOntology, TrailingType, DDType
from quant_lab.sniper.scraper_engine import PropFirmMatchScraper, PayoutJunctionScraper
from quant_lab.sniper.ff_matrix import FFScalingMatrix, CapitalDeploymentRouter, DeploymentDirective

print("✅ All imports OK")

# Test 1: Ontology mapping from raw PropFirmMatch data
sample_raw = {
    "name": "Topstep",
    "url": "https://www.topstep.com",
    "account_sizes": [50000, 100000, 150000],
    "costs": {"50000": 165, "100000": 275, "150000": 395},
    "promo": {"code": "SUMMER20", "discount_pct": 20, "new_customer_only": True},
    "drawdown": {"max_dd_pct": 3.3, "trailing_type": "intraday"},
    "consistency": {"active": True, "max_day_pct": 50},
    "payout": {"cycle_days": 10, "min_trading_days": 5},
    "scaling": {"enabled": False, "min_profit_pct": 0.05, "delay_days": 30},
    "instruments": ["ES", "NQ", "CL", "GC"],
    "news_restricted": True,
    "ff_status": "ARBITRAGE",
}

ont = OntologyMapper.from_propfirm_match(sample_raw)
print(f"✅ Ontology: {ont.firm_name}, BW=${ont.risk_bandwidth:,.0f}, CoC={ont.cost_of_capital():.4f}, Lethal={ont.is_trailing_lethal}, Runners={ont.allows_runners}")

# Test 2: F&F Matrix
ff = FFScalingMatrix()
result = ff.find_optimal_fragmentation(ont, target_aum=50000, max_identities=10)
if result:
    print(f"✅ F&F: strategy={result.strategy}, size=${result.account_size:,} × {result.quantity}, CoC={result.fleet_coc:.4f}, bypass={result.consistency_bypass}")

# Test 3: Capital Deployment Router
router = CapitalDeploymentRouter()
directives = router.generate_deployment_matrix([ont], target_bandwidth=50000)
for d in directives:
    print(f"✅ Directive: #{directives.index(d)+1} {d.firm_name} | strategy={d.strategy} | PES={d.pes_score:.2f} | {d.account_size:,} × {d.quantity} | CoC={d.coc:.4f}")
    for note in d.notes:
        print(f"   → {note}")

# Test 4: Router to JSON
json_out = router.to_json(directives)
print(f"✅ JSON output: {json_out['directive_count']} directives")

# Test 5: Multiple firms with varying constraints
firms_raw = [
    {
        "name": "FirmA_Trailing",
        "account_sizes": [100000],
        "costs": {"100000": 500},
        "promo": {},
        "drawdown": {"max_dd_pct": 5.0, "trailing_type": "intraday"},
        "consistency": {"active": True, "max_day_pct": 30},
        "payout": {"cycle_days": 14},
        "scaling": {},
        "ff_status": "STANDARD",
    },
    {
        "name": "FirmB_Static",
        "account_sizes": [100000],
        "costs": {"100000": 500},
        "promo": {},
        "drawdown": {"max_dd_pct": 5.0, "trailing_type": "static"},
        "consistency": {"active": False, "max_day_pct": 0},
        "payout": {"cycle_days": 14},
        "scaling": {},
        "ff_status": "STANDARD",
    },
    {
        "name": "FirmC_Promo",
        "account_sizes": [50000],
        "costs": {"50000": 200},
        "promo": {"code": "HALF", "discount_pct": 50, "new_customer_only": True},
        "drawdown": {"max_dd_pct": 5.0, "trailing_type": "static"},
        "consistency": {"active": True, "max_day_pct": 30},
        "payout": {"cycle_days": 7},
        "scaling": {},
        "ff_status": "ARBITRAGE",
    },
]

onts = [OntologyMapper.from_propfirm_match(r) for r in firms_raw]
directives = router.generate_deployment_matrix(onts, target_bandwidth=50000)
print(f"\n✅ Multi-firm test: {len(directives)} directives ranked")
for d in directives:
    print(f"   #{directives.index(d)+1}: {d.firm_name} | PES={d.pes_score:.3f} | {d.strategy} | lethal={bool(d.lethal_constraints)} | bypass={d.consistency_bypass}")

print("\n🎉 ALL PHASE 1 SMOKE TESTS PASSED")
