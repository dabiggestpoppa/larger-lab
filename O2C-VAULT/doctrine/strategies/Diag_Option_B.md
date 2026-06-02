# Diag Option B

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
from shared import load_data, compute_asian_range
from symmetry_trap_option_b import run_symmetry_trap_option_b

df = load_data()
dates = sorted(df['est_date'].unique())

loop_data = {i: {'wins': [], 'losses': []} for i in range(1, 9)}

for dk in dates:
    db = df[df['est_date']==dk].sort_values('timestamp').reset_index(drop=True)
    ar = compute_asian_range(db, dk)
    if ar is None or ar.get('tier') == 'NO_GO': continue
    ar['date_key'] = dk
    trades = run_symmetry_trap_option_b(db, ar)
    for t in trades:
        loop = t['loop']
        sl_dist = abs(t['entry'] - t['sl']) / 0.0001
        tp_dist = abs(t['tp'] - t['entry']) / 0.0001
        rr_theoretical = tp_dist / sl_dist if sl_dist > 0 else 0
        rec = {
            'sl_dist': round(sl_dist, 1),
            'tp_dist': round(tp_dist, 1),
            'rr_theoretical': round(rr_theoretical, 2),
            'pnl': t['pnl_pips'],
            'exit_type': t['type']
        }
        if t['pnl_pips'] > 0:
            loop_data[loop]['wins'].append(rec)
        else:
            loop_data[loop]['losses'].append(rec)

print("=== LOOP ANALYSIS ===")
for loop in range(1, 9):
    w = loop_data[loop]['wins']
    l = loop_data[loop]['losses']
    total = len(w) + len(l)
    if total == 0: continue
    wr = len(w) / total * 100
    avg_sl_w = pd.DataFrame(w)['sl_dist'].mean() if w else 0
    avg_tp_w = pd.DataFrame(w)['tp_dist'].mean() if w else 0
    avg_rr_w = pd.DataFrame(w)['rr_theoretical'].mean() if w else 0
    avg_sl_l = pd.DataFrame(l)['sl_dist'].mean() if l else 0
    avg_tp_l = pd.DataFrame(l)['tp_dist'].mean() if l else 0
    avg_rr_l = pd.DataFrame(l)['rr_theoretical'].mean() if l else 0
    sl_pct_w = pd.DataFrame(w)['exit_type'].eq('SL').mean() * 100 if w else 0
    tp_pct_l = pd.DataFrame(l)['exit_type'].eq('TP').mean() * 100 if l else 0
    print(f"\nLoop {loop}: {total} tr, WR={wr:.1f}%")
    print(f"  Wins: {len(w)} | avg SL={avg_sl_w:.1f}p avg TP={avg_tp_w:.1f}p avg RR={avg_rr_w:.2f}")
    print(f"  Losses: {len(l)} | avg SL={avg_sl_l:.1f}p avg TP={avg_tp_l:.1f}p avg RR={avg_rr_l:.2f}")
    time_exits_l = sum(1 for x in l if 'TIME' in x['exit_type'])
    sl_exits_l = sum(1 for x in l if x['exit_type'] == 'SL')
    print(f"  Loss exits: SL={sl_exits_l} TIME={time_exits_l}")

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
[[Option A Confirmed 20260531]]
[[Cal]]
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
[[Blind Chain Debug]]
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
