# Blind Chain Debug

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""
Blind Chain Diagnostic — find what's actually happening
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

AU1 = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}
TIERS = {'T1': {'ar_max': 20, 'trigger': 12}, 'T2': {'ar_max': 30, 'trigger': 15}, 'T3': {'ar_max': 45, 'trigger': 19}}

def classify_tier(ar_pips):
    if ar_pips < 20: return 'T1'
    if ar_pips < 30: return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'

df = load_data()
no_anchor = 0; no_impulse = 0; no_goldilocks = 0; no_cascade = 0; entered = 0

debug_days = []
for dk in sorted(df['est_date'].unique())[:30]:  # First 30 days only for debug
    db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
    ar = compute_asian_range(df, dk)
    if ar is None: continue
    tier = classify_tier(ar['ar_pips'])
    if tier == 'NO_GO' or ar['ar_pips'] < 3: continue
    params = TIERS[tier]
    ah = ar['ah']; al = ar['al']

    window = db[(db['est_hour']>=2)&(db['est_hour']<12)].reset_index(drop=True)
    if len(window) < 10: continue

    # Anchor P90
    anchor = None
    for i in range(len(window)):
        row = window.iloc[i]
        eh = row['est_hour']
        if eh < 2 or eh >= 11: continue
        body = abs(row['close']-row['open'])*10000
        thresh = AU1.get(int(eh), 4.6)
        if body >= thresh and (row['close'] > ah or row['close'] < al):
            anchor = {'idx':i,'row':row,'dir':1 if row['close']>row['open'] else -1}
            break
    if anchor is None: no_anchor += 1; continue

    # Impulse extension
    ad = anchor['dir']; ac = anchor['row']['close']
    imp_ext = ac; imp_idx = anchor['idx']
    for i in range(anchor['idx']+1, len(window)):
        row = window.iloc[i]
        if ad==1 and row['high']>imp_ext: imp_ext=row['high']; imp_idx=i
        elif ad==-1 and row['low']<imp_ext: imp_ext=row['low']; imp_idx=i

    imp_dist = abs(imp_ext-ac)*10000
    if imp_dist < params['trigger']: no_impulse += 1; continue

    # Goldilocks zone
    if ad==1:
        gh = imp_ext - imp_dist*0.32/10000; gl = imp_ext - imp_dist*0.50/10000
    else:
        gl = imp_ext + imp_dist*0.32/10000; gh = imp_ext + imp_dist*0.50/10000

    has_gold = False; gold_idx = None
    for i in range(imp_idx+1, len(window)):
        row = window.iloc[i]
        if gl <= row['close'] <= gh:
            has_gold = True; gold_idx = i; break
        if gl <= row['high'] and row['low'] <= gh:
            has_gold = True; gold_idx = i; break

    if not has_gold: no_goldilocks += 1; continue

    # Micro-P90 in direction from Goldilocks
    has_cascade = False
    for i in range(max(imp_idx+1, gold_idx), len(window)):
        row = window.iloc[i]
        if row['est_hour']>=11: break
        body = abs(row['close']-row['open'])*10000
        is_bull = row['close']>row['open']
        if body>=4.5 and ((ad==1 and is_bull) or (ad==-1 and not is_bull)):
            has_cascade = True; break

    if has_cascade:
        entered += 1
        dir_str = "LONG" if ad==1 else "SHORT"
        debug_days.append(f"  {dk} {dir_str} {tier} AR={ar['ar_pips']:.1f}p impulse={imp_dist:.1f}p gold@{gold_idx}")
    else:
        no_cascade += 1

print(f"=== 30-day diagnostic ===")
print(f"No anchor P90:     {no_anchor}")
print(f"Anchor but small impulse (< trigger): {no_impulse}")
print(f"No Goldilocks revisit: {no_goldilocks}")
print(f"Goldilocks but no micro-P90: {no_cascade}")
print(f"ENTERED cascade: {entered}")

if debug_days:
    print(f"\nTrades that entered:")
    for d in debug_days:
        print(d)

# Also: what was Goldilocks width?
print(f"\n=== Goldilocks zone analysis (first 10 entering days) ===")
count = 0
for dk in sorted(df['est_date'].unique()):
    if count >= 5: break
    db = df[df['est_date']==dk].sort_values('timestamp').reset_index(drop=True)
    ar = compute_asian_range(df, dk)
    if ar is None: continue
    tier = classify_tier(ar['ar_pips'])
    if tier == 'NO_GO': continue
    params = TIERS[tier]
    ah=ar['ah']; al=ar['al']
    window = db[(db['est_hour']>=2)&(db['est_hour']<12)].reset_index(drop=True)
    if len(window)<10: continue

    anchor = None
    for i in range(len(window)):
        row = window.iloc[i]
        eh=row['est_hour']
        if eh<2 or eh>=11: continue
        body=abs(row['close']-row['open'])*10000
        if body>=AU1.get(int(eh),4.6) and (row['close']>ah or row['close']<al):
            anchor={'idx':i,'row':row,'dir':1 if row['close']>row['open'] else -1}; break
    if not anchor: continue
    ad=anchor['dir']; ac=anchor['row']['close']
    imp_ext=ac
    for i in range(anchor['idx']+1,len(window)):
        row=window.iloc[i]
        if ad==1 and row['high']>imp_ext: imp_ext=row['high']
        elif ad==-1 and row['low']<imp_ext: imp_ext=row['low']
    imp_dist=abs(imp_ext-ac)*10000
    if imp_dist < params['trigger']: continue

    if ad==1:
        gh=imp_ext-imp_dist*0.32/10000; gl=imp_ext-imp_dist*0.50/10000
    else:
        gl=imp_ext+imp_dist*0.32/10000; gh=imp_ext+imp_dist*0.50/10000

    print(f"{dk} AR={ar['ar_pips']:.1f}p impulse={imp_dist:.1f}p "
          f"gold=[{gl:.5f},{gh:.5f}] width={gh-gl:.5f}")
    count += 1

```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Citation Workflow]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
