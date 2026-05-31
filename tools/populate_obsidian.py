#!/usr/bin/env python3
import sys, re
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(r'C:\Users\wifik\Desktop\projects\larger-lab')
VAULT = Path(r'C:\Users\wifik\Downloads\o2c')

def sanitize(title):
    safe = re.sub(r'[^\w\s\-]', '', title)
    return re.sub(r'\s+', '_', safe.strip())[:100]

def make_note(title, content_dict, category, tags=None):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f"# {title}", "",
             f"> Category: {category} | Created: {ts}", ""]
    if tags:
        lines += ["Tags: " + " ".join(f"#{t}" for t in tags), ""]
    for key in ("cause", "fix", "result"):
        if content_dict.get(key):
            lines += [f"## {key.upper()}", "", str(content_dict[key]), ""]
    if content_dict.get("extra"):
        lines += ["## DETAILS", "", str(content_dict["extra"]), ""]
    return "\n".join(lines)

def write_note(category, title, content, tags=None, subcategory=None):
    if subcategory:
        dir_path = VAULT / category / subcategory
    else:
        dir_path = VAULT / category
    dir_path.mkdir(parents=True, exist_ok=True)
    filename = sanitize(title) + ".md"
    filepath = dir_path / filename
    body = make_note(title, content, category, tags)
    filepath.write_text(body, encoding='utf-8')
    return str(filepath.relative_to(VAULT))

print(f"Writing to Obsidian vault: {VAULT}")
count = 0

# 1. QUANTLAB BIBLE
bible_src = WORKSPACE / 'quant-lab' / 'QUANTLAB_BIBLE.md'
if bible_src.exists():
    vault_bible = VAULT / 'QUANTLAB_BIBLE.md'
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    header = f"> AUTO-GENERATED from quant-lab/QUANTLAB_BIBLE.md | {ts}\n\n"
    vault_bible.write_text(header + bible_src.read_text(encoding='utf-8'), encoding='utf-8')
    count += 1
    print("  OK: QUANTLAB_BIBLE.md")

# 2. ONTOLOGY CORE
write_note('ontology', 'ONTOLOGY_CORE_Summary',
    {'cause': 'Core ontology summary for quick reference',
     'result': '**6 Axioms:**\n1. ONE system: Constraint Resolution\n2. TWO engines: Kinetic (P90) + Structural (Atomic)\n3. ZERO other strategies\n4. Overlap = Causal Confirmation\n5. Divergence = Geometry Classification\n6. Manual setups are configurations, NOT ontological categories\n\n**AU Math:**\n- AU = 50% of K-Means centroid\n- Tier boundaries = midpoints between centroids\n\n**Time Windows:**\n- Asian: 19:00-03:00 EST\n- Activation: 03:00-12:00 EST\n- Hard Cutoff: 12:00 PM',
     'extra': 'Full ontology: quant-lab/CEREBUS_ONTOLOGY.md'},
    tags=['ontology', 'reference', 'quick-ref'], subcategory='cerebus')
count += 1
print("  OK: ontology/cerebus/ONTOLOGY_CORE_Summary.md")

# 3. ACTIVE STRATEGIES
write_note('doctrine', 'Active_Strategies_Performance',
    {'cause': 'Universal backtest results across 19 assets (2022-01-03 to 2026-05-29)',
     'result': '**Symmetry Trap (Engine B):** 82-97% WR across all 19 assets\nTop: ETHUSD 96.9% | HK50 94.0% | NZDUSD 93.3%\nMulti-asset: 12,488 pooled trades, 81.2% WR, PF 26.58\n\n**P90 Kinetic (Engine A):** CASCADE 85.4% WR, full stack 78.7% WR\n\n**Dual-Engine Convergence:** 94-95% WR when both align',
     'extra': 'Flags: XAGUSD config broken, BTC concentration 55% of pool PnL'},
    tags=['strategy', 'backtest', 'results'])
count += 1
print("  OK: doctrine/Active_Strategies_Performance.md")

# 4. DEPLOYMENT STATUS
write_note('execution', 'Live_Deployment_Status',
    {'cause': 'Live executors running on Ox Securities',
     'result': '| Executor | Symbol | Strategy | Magic | Lots |\n|----------|--------|----------|-------|------|\n| ST | EURUSD.PRO | Symmetry Trap | 20260531 | 0.03 |\n| P90 | USDCHF.PRO | P90 CASCADE | 20260532 | 0.01 |\n\nAccount: 650898 LIVE',
     'extra': 'DO NOT TOUCH quant-lab/mt5/ without MAD approval'},
    tags=['deployment', 'live', 'mt5'])
count += 1
print("  OK: execution/Live_Deployment_Status.md")

# 5. PHASE STATUS
write_note('architecture', 'Backtest_Phase_Status',
    {'cause': 'Tracking completed backtest phases',
     'result': '| Phase | Description | Status |\n|-------|-------------|--------|\n| 1 | 19 individual reports + MC | DONE |\n| 2 | 4 group reports | DONE |\n| 3 | Multi-asset combined | DONE |\n| 4 | Master INDEX | DONE |\n| 5 | Top 5 + Major 6 re-runs | DONE |\n| 6 | P90 multi-asset | NEXT |\n| 7 | Dual-engine convergence | QUEUED |\n| 8 | Nautilus cross-validation | QUEUED |',
     'extra': 'All reports: quant-lab/reports/'},
    tags=['phases', 'status'])
count += 1
print("  OK: architecture/Backtest_Phase_Status.md")

# 6. FAILURE INDEX
write_note('failures', 'Failure_Index_OC2',
    {'cause': 'Track structural friction',
     'result': '**Orchestration:** Auto-work bug (fixed), OWL not delegating (fixed)\n\n**Strategy:** MT5 tester 0 trades, Pine Script fill mismatch, XAGUSD config broken\n\n**Known Issues:** BTC 55% concentration, crypto correlation 58.5%'},
    tags=['failures', 'bugs'])
count += 1
print("  OK: failures/Failure_Index_OC2.md")

# 7. TEAM ROSTER
write_note('architecture', 'Team_Phase01_Status',
    {'cause': 'Phase 00 complete, Phase 01 in progress',
     'result': 'Phase 00: 119 tests (DONE)\nPhase 01: 106 passing (84 P00 + 22 P01), target 150+\n\nCore modules (Error Intel, Pattern Crystallizer, Memory Distiller, Context Injector) all built by CC2.\nRemaining: Vault API expansion (CC1), frontend views (PM2), integration tests (CC1).'},
    tags=['team', 'phase-01'])
count += 1
print("  OK: architecture/Team_Phase01_Status.md")

print(f"\nDONE: {count} notes written to {VAULT}")
