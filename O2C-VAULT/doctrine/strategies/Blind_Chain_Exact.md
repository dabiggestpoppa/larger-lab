# Blind Chain Exact

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""
BLIND STRUCTURAL CHAIN ENGINE — Exact Manual Specification (Pages 95-104)
===========================================================================
Blind Chain Law: Impulse → Partial Rebalancing (32-50% Goldilocks) → Continuation

KEY: This is NOT a P90 strategy. P90 is the CASCADE ADD protocol, not the core.
The previous engines (v1, v2) were WRONG — they tried to fit micro-P90 inside
Goldilocks. Manual says: Impulse breaks band → pullback to 32-50% → continuation.

MANUAL FORMULA (Page 98):
  SUCCESS = (Impulse > Tier Threshold) AND (32-50% rebalancing) AND (no close >80%)
  Impulse thresholds: T1=10-12p, T2=14-16p, T3=18-20p (from 3AM)
  Target: 1 AU from entry
  SL: close past impulse baseline (81.2% rule)
  12PM hard exit
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np

sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range

TIER_PARAMS = {
    'T1': {'ar_max': 20, 'au': 10, 'trigger': 12},
    'T2': {'ar_max': 30, 'au': 12, 'trigger': 15},
    'T3': {'ar_max': 45, 'au': 15, 'trigger': 19},
}

IMPULSE_MIN = {'T1': 10, 'T2': 14, 'T3': 18}
IMPULSE_MAX_TRIGGER = {'T1': 12, 'T2': 15, 'T3': 19}

def classify_tier(ar_pips):
    if ar_pips < 20: return 'T1'
    elif ar_pips < 30: return 'T2'
    elif ar_pips <= 45: return 'T3'
    return 'NO_GO'

def run_blind_chain_day(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    date_key = ar_info['date_key']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3:
        return trades

    au = TIER_PARAMS[tier]['au']
    trigger = TIER_PARAMS[tier]['trigger']

    # Window: 2AM-12PM EST
    window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].copy()
    if len(window) < 15:
        return trades

    # === LAYER 1: IMPULSE (first M5 close outside Asian band >= trigger) ===
    # The first close beyond the Asian band that meets the tier trigger IS the impulse.
    # Manual: "WHEN price moves the Tier Threshold from 3 AM"
    bias = None
    baseline = None
    impulse_extreme = None
    impulse_idx = None
    for i in range(len(window)):
        row = window.iloc[i]
        if row['est_hour'] < 2: continue
        if bias is None:
            # Look for first close outside band that meets trigger
            if row['close'] > ah:
                dist = (row['close'] - ah) * 10000
                if dist >= trigger:
                    bias = 1; baseline = ah
                    impulse_extreme = row['close']
                    impulse_idx = i
                    break
            elif row['close'] < al:
                dist = (al - row['close']) * 10000
                if dist >= trigger:
                    bias = -1; baseline = al
                    impulse_extreme = row['close']
                    impulse_idx = i
                    break
    if bias is None or impulse_extreme is None:
        return trades

    impulse_range = abs(impulse_extreme - baseline) * 10000  # total move in pips

    # === LAYER 3: GOLDILOCKS PARTIAL REBALANCING ===
    # Pullback to 32-50% of impulse, with 80% close invalidation check
    p80_level = baseline + (impulse_extreme - baseline) * 0.80
    p32_level = baseline + (impulse_extreme - baseline) * 0.32
    p50_level = baseline + (impulse_extreme - baseline) * 0.50

    entry = None
    invalidated = False
    for i in range(impulse_idx + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 12: break

        # 80% close invalidation
        if bias == 1 and row['close'] < p80_level:
            invalidated = True; break
        if bias == -1 and row['close'] > p80_level:
            invalidated = True; break

        # Goldilocks entry: pullback into 32-50% zone
        if bias == 1:
            if p32_level <= row['close'] <= p50_level:
                pullback_pct = (impulse_extreme - row['close']) * 10000 / impulse_range * 100 if impulse_range > 0 else 50
                entry = {'price': row['close'], 'idx': i, 'pullback_pct': pullback_pct}
                break
        else:
            if p50_level <= row['close'] <= p32_level:
                pullback_pct = (row['close'] - impulse_extreme) * 10000 / impulse_range * 100 if impulse_range > 0 else 50
                entry = {'price': row['close'], 'idx': i, 'pullback_pct': pullback_pct}
                break

    if invalidated or entry is None:
        return trades

    # === CONTINUATION CHECK ===
    entry_price = entry['price']
    if bias == 1:
        target = entry_price + (au / 10000)
        sl_level = baseline  # close past baseline = invalidated
    else:
        target = entry_price - (au / 10000)
        sl_level = baseline

    result = None
    for i in range(entry['idx'] + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 12:
            result = ('TIME', row['close']); break
        if bias == 1:
            if row['close'] >= target:
                result = ('TP', target); break
            if row['close'] <= sl_level:
                result = ('SL', row['close']); break
        else:
            if row['close'] <= target:
                result = ('TP', target); break
            if row['close'] >= sl_level:
                result = ('SL', row['close']); break

    if result is None:
        result = ('TIME', window.iloc[-1]['close'])

    exit_price = result[1]
    pnl = (exit_price - entry_price) * 10000 * bias

    trades.append({
        'date': date_key, 'tier': tier, 'bias': bias,
        'impulse_pips': impulse_range,
        'pullback_pct': entry['pullback_pct'],
        'entry_price': entry_price,
        'result': result[0],
        'pnl_pnl': pnl,
    })

    return trades


def run_backtest():
    df = load_data()
    if df is None or len(df) == 0:
        print("No data"); return

    all_dates = sorted(df['est_date'].unique())
    print(f"{'='*60}")
    print(f"BLIND STRUCTURAL CHAIN — Exact Manual Spec")
    print(f"{'='*60}")
    print(f"Data: {len(df)} bars | {len(all_dates)} sessions")
    print(f"Law: Impulse → 32-50% Goldilocks → Continuation (93.7%)")
    print(f"{'='*60}")

    all_trades = []
    for dk in all_dates:
        day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue
        ar_info = compute_asian_range(day_bars, dk)
        if ar_info is None: continue
        ar_info['date_key'] = dk
        trades = run_blind_chain_day(day_bars, ar_info)
        all_trades.extend(trades)

    if not all_trades:
        print("No trades"); return

    wins = [t for t in all_trades if t['pnl_pnl'] > 0]
    losses = [t for t in all_trades if t['pnl_pnl'] <= 0]
    wr = len(wins) / len(all_trades) * 100
    total = sum(t['pnl_pnl'] for t in all_trades)
    avg = total / len(all_trades)

    tp_count = len([t for t in all_trades if t['result'] == 'TP'])
    sl_count = len([t for t in all_trades if t['result'] == 'SL'])
    time_count = len([t for t in all_trades if t['result'] == 'TIME'])

    print(f"\nTotal trades: {len(all_trades)}")
    print(f"WR: {wr:.1f}% ({len(wins)}W/{len(losses)}L)")
    print(f"Total PnL: {total:.1f}p | Avg: {avg:.2f}p")
    print(f"Results: TP={tp_count} ({tp_count/len(all_trades)*100:.0f}%) SL={sl_count} ({sl_count/len(all_trades)*100:.0f}%) TIME={time_count}")

    gold = [t for t in all_trades if 32 <= t.get('pullback_pct', 0) <= 50]
    if gold:
        gw = len([t for t in gold if t['pnl_pnl'] > 0])
        print(f"\nGoldilocks (32-50%): {len(gold)} trades | WR: {gw/len(gold)*100:.0f}%")

    for tn in ['T1','T2','T3']:
        tt = [t for t in all_trades if t['tier']==tn]
        if not tt: continue
        tw = len([t for t in tt if t['pnl_pnl'] > 0])
        print(f"  {tn}: {len(tt)} tr | WR:{tw/len(tt)*100:.1f}% | PnL:{sum(t['pnl_pnl'] for t in tt):.1f}p")

    print(f"\nMANUAL: Goldilocks=93.7% | T1=84% 1-cycle | T2=69+26% | T3=multi")
    return all_trades

if __name__ == '__main__':
    run_backtest()

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
