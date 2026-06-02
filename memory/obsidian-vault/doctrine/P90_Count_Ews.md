# P90 Count Ews

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #engines

```python
"""Count EWS variant trades vs INITIAL+CASCADE."""
import sys, os, csv
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
os.environ['PYTHONPATH'] = 'quant-lab'
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from collections import defaultdict
from p90_engine import P90Engine, P90Variant, TradeDirection, Bar

DATA_FILE = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv'
PIP_SIZE = 0.0001

def load_bars(path):
    bars = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            bars.append({'dt': dt, 'o': float(row['open']), 'h': float(row['high']),
                         'l': float(row['low']), 'c': float(row['close'])})
    bars.sort(key=lambda x: x['dt'])
    return bars

def est_hour(dt): return (dt.hour - 5) % 24

bars = load_bars(DATA_FILE)
sessions = defaultdict(lambda: {"asian": [], "trading": []})
for b in bars:
    sd = (b['dt'] + timedelta(days=1)).date() if est_hour(b['dt']) >= 19 else b['dt'].date()
    h = est_hour(b['dt'])
    sessions[sd]["asian" if (h >= 19 or h < 3) else "trading"].append(b)

all_signals = []
for sdate in sorted(sessions.keys()):
    sbars = sessions[sdate]
    if not sbars["asian"] or not sbars["trading"]: continue
    ah = max(b['h'] for b in sbars["asian"])
    al = min(b['l'] for b in sbars["asian"])
    if (ah - al) / PIP_SIZE < 3.0 or (ah - al) / PIP_SIZE > 45.0: continue
    engine = P90Engine(pip_size=PIP_SIZE, symbol='USDCHF')
    engine.initialize_session(ah, al)
    if not engine.session_active: continue
    for b in sbars["trading"]:
        bar = Bar(timestamp=b['dt'], open=b['o'], high=b['h'], low=b['l'], close=b['c'])
        sig = engine.process_bar(bar)
        if sig:
            all_signals.append(sig)

# Count exits by variant
exit_by_variant = defaultdict(int)
for s in all_signals:
    if s.event in ("TP_HIT", "SL_HIT", "EWS_EXIT"):
        v = s.variant.value if s.variant else "NONE"
        exit_by_variant[f"{v}_{s.event}"] += 1

print("EXIT signals by variant + type:")
for k, v in sorted(exit_by_variant.items(), key=lambda x: -x[1]):
    print(f"  {k:25s}: {v}")

print()
for variant_name in ["INITIAL", "CASCADE", "EWS", "NONE"]:
    entries = sum(1 for s in all_signals if s.event == "ENTRY" and s.variant and s.variant.value == variant_name)
    exits = sum(1 for s in all_signals if s.event in ("TP_HIT","SL_HIT","EWS_EXIT") and s.variant and s.variant.value == variant_name)
    print(f"{variant_name}: {entries} entries, {exits} exits")

total_entries = sum(1 for s in all_signals if s.event == "ENTRY")
total_exits = sum(1 for s in all_signals if s.event in ("TP_HIT","SL_HIT","EWS_EXIT"))
print(f"\nTOTAL: {total_entries} entries, {total_exits} exits")
print(f"EWS exits as % of total: {sum(v for k,v in exit_by_variant.items() if 'EWS_' in k) / total_exits * 100:.1f}%")

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
