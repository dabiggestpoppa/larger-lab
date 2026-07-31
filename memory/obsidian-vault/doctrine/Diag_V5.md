# Diag V5

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
﻿import sys
from datetime import datetime, timedelta
import MetaTrader5 as mt5

EST_OFFSET = -5
def est_hour(dt): return (dt.hour + EST_OFFSET) % 24

if not mt5.initialize(): print('MT5 fail'); sys.exit()
bars = mt5.copy_rates_from_pos('USDCHF.PRO', mt5.TIMEFRAME_M5, 0, 50000)
mt5.shutdown()
if bars is None or len(bars) == 0: print('No bars'); sys.exit()

result = []
for bar in bars:
    dt = datetime.fromtimestamp(bar['time'])
    result.append({'dt': dt, 'est_h': est_hour(dt), 'o': bar['open'], 'h': bar['high'], 'l': bar['low'], 'c': bar['close']})

sessions = {}
for bar in result:
    d = bar['dt'].date()
    if bar['est_h'] < 3: d = (bar['dt'] + timedelta(hours=EST_OFFSET)).date()
    sessions.setdefault(str(d), []).append(bar)

pm = 10000
def ppip(price): return price * pm
def ppt(pips): return pips / pm

dates = sorted(sessions.keys())
count = 0
for d in dates[100:200]:
    db = sessions[d]
    asian = [b for b in db if b['est_h'] >= 19 or b['est_h'] < 3]
    if len(asian) < 2: continue
    ah = max(b['h'] for b in asian)
    al = min(b['l'] for b in asian)
    ar = ppip(ah - al)
    if ar < 13 or ar > 60: continue
    au = 11 if ar < 18 else (15 if ar < 24 else 18)
    bw = [b for b in db if 3 <= b['est_h'] < 11]
    bias = 0
    bi = -1
    for i, b in enumerate(bw):
        if b['c'] > ah: bias = 1; bi = i; break
        if b['c'] < al: bias = -1; bi = i; break
    if bias == 0: continue
    post = bw[bi:]
    for i in range(len(post)-1):
        b = post[i]
        body = abs(b['c'] - b['o'])
        bp = ppip(body)
        is_bull = b['c'] > b['o']
        is_bear = b['c'] < b['o']
        nb = post[i+1]
        if bias == 1 and is_bull and bp >= au * 0.5 and nb['c'] < nb['o']:
            entry = nb['c']
            t25 = ah + ppt(ar * -0.25)
            t50 = ah + ppt(ar * -0.50)
            reward25 = ppip(entry - t25)
            risk = ppip(ah - entry)
            count += 1
            arrow = '<-' if entry >= ah else '  '
            print(f'{d} SHORT entry={entry:.5f} t25={t25:.5f} reward25={reward25:+.1f}p risk={risk:+.1f}p RR={reward25/max(risk,0.01):.1f} {arrow}ah={ah:.5f}')
            break
        if bias == -1 and is_bear and bp >= au * 0.5 and nb['c'] > nb['o']:
            entry = nb['c']
            t25 = al + ppt(ar * 0.25)
            t50 = al + ppt(ar * 0.50)
            reward25 = ppip(t25 - entry)
            risk = ppip(entry - al)
            count += 1
            arrow = '->' if entry <= al else '  '
            print(f'{d} LONG  entry={entry:.5f} t25={t25:.5f} reward25={reward25:+.1f}p risk={risk:+.1f}p RR={reward25/max(risk,0.01):.1f} {arrow}al={al:.5f}')
            break
    if count >= 8: break

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
