# Constraint Anchor Engine

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
# -*- coding: utf-8 -*-
"""
Constraint Anchor Engine (Strategy 9 — Atomic Pure Structural)
=============================================================
Manual claims: 91.7% WR, 2.8 PF

CONCEPT:
- Purest form of CEREBUS thesis — Asian constraint band is the anchor
- ANY M5 close outside Asian band = structural signal
- NO P90 filter, no cascade — just the raw structural break
- Direction: WITH the breakout (expansion of constraint deficit)

ENTRY: M5 candle CLOSES outside Asian High/Low, body >= 4.6p
TIME: 3AM - 12PM EST
SL: Opposite Asian extreme (Asian Low for LONG, Asian High for SHORT)
TP1: entry + 25% AR in trade direction (close 50%, move SL to BE)
TP2: entry + 50% AR in trade direction (close remaining)
HARD EXIT: 12PM EST

TIER RULES:
- T1 (<20p AR): Full size
- T2 (20-30p): Normal size
- T3 (30-45p): 50-75% size, no normal deployment
- Overfilled (>40p by 9AM): T2/T3 STAND DOWN, T1 anchor only at 50%
"""
import sys, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
from datetime import date

STRATEGY_NAME = "constraint_anchor"
SPREAD_COST = 0.5  # pips

def run_day(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info['date_key']

    if tier == 'NO_GO':
        return trades

    # Overfilled check at 9AM
    mult = 1.0
    if tier == 'T3':
        mult = 0.5
    bars_to_9am = day_bars[day_bars['est_hour'] <= 9]
    if len(bars_to_9am) > 0:
        dr_9am = (bars_to_9am['high'].max() - bars_to_9am['low'].min()) * 10000.0
        if dr_9am > 40.0:
            if tier in ('T2', 'T3'):
                return trades  # STAND DOWN
            mult = 0.5  # T1 anchor only, half size

    base_size = {'T1': 1.0, 'T2': 1.0, 'T3': 0.5}.get(tier, 0)
    size = base_size * mult

    if size <= 0:
        return trades

    # Look for first valid breakout
    for i, bar in day_bars.iterrows():
        eh = bar['est_hour']
        if eh < 3 or eh >= 11:
            continue

        o, h, l, c = bar['open'], bar['high'], bar['low'], bar['close']
        body_pips = abs(c - o) * 10000.0
        if body_pips < 4.6:
            continue

        # LONG breakout: close above Asian High
        if c > ah:
            direction = 1
            sl = al
            tp1 = c + ar_pips * 0.25 / 10000.0
            tp2 = c + ar_pips * 0.50 / 10000.0
        # SHORT breakout: close below Asian Low
        elif c < al:
            direction = -1
            sl = ah
            tp1 = c - ar_pips * 0.25 / 10000.0
            tp2 = c - ar_pips * 0.50 / 10000.0
        else:
            continue

        entry_price = c
        risk = abs(entry_price - sl) * 10000.0
        if risk < 2 or risk > 100:
            continue

        # Track trade
        tp1_hit = False
        for j, b2 in day_bars.iterrows():
            if b2['timestamp'] <= bar['timestamp']:
                continue
            eh2 = b2['est_hour']
            c2 = b2['close']

            # SL hit
            if direction == 1 and c2 <= sl:
                pnl = (c2 - entry_price) * 10000.0 - SPREAD_COST
                trades.append({'date': str(date_key), 'direction': direction,
                    'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl * size,
                    'exit_reason': 'sl', 'tier': tier, 'size': size})
                break
            if direction == -1 and c2 >= sl:
                pnl = (entry_price - c2) * 10000.0 - SPREAD_COST
                trades.append({'date': str(date_key), 'direction': direction,
                    'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl * size,
                    'exit_reason': 'sl', 'tier': tier, 'size': size})
                break

            # TP1
            if direction == 1 and c2 >= tp1:
                tp1_hit = True
            if direction == -1 and c2 <= tp1:
                tp1_hit = True

            # TP2
            if tp1_hit:
                if direction == 1 and c2 >= tp2:
                    pnl = (c2 - entry_price) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'direction': direction,
                        'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl * size,
                        'exit_reason': 'tp2', 'tier': tier, 'size': size})
                    break
                if direction == -1 and c2 <= tp2:
                    pnl = (entry_price - c2) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'direction': direction,
                        'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl * size,
                        'exit_reason': 'tp2', 'tier': tier, 'size': size})
                    break

            # Hard exit 12PM
            if eh2 >= 12:
                pnl = (c2 - entry_price) * direction * 10000.0 - SPREAD_COST
                trades.append({'date': str(date_key), 'direction': direction,
                    'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl * size,
                    'exit_reason': 'hard_exit_12pm', 'tier': tier, 'size': size})
                break
        break  # one trade per session

    return trades


def run_backtest(df, start_date=None, end_date=None):
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]
    all_trades = []
    days = 0
    for dk in sorted(df['est_date'].unique()):
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(db) < 10:
            continue
        ar = compute_asian_range(df, dk)
        if ar is None:
            continue
        ar['date_key'] = dk
        tr = run_day(db, ar)
        if tr:
            all_trades.extend(tr)
        days += 1
    return all_trades, days


if __name__ == "__main__":
    print("=" * 60)
    print("CONSTRAINT ANCHOR ENGINE — Backtest (Atomic)")
    print("=" * 60)
    df = load_data()
    print("\nRunning 2024-2025...")
    tr, days = run_backtest(df, date(2024, 1, 1), date(2025, 12, 31))
    if not tr:
        print("No trades!"); sys.exit(1)

    tdf = pd.DataFrame(tr)
    n = len(tdf)
    wr = (tdf['pnl_pips'] > 0).mean() * 100
    total = tdf['pnl_pips'].sum()
    wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
    losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
    pf = wins / losses if losses > 0 else float('inf')

    print(f"\nDays: {days}, Trades: {n}")
    print(f"WR: {wr:.1f}% (target: 91.7%)")
    print(f"PF: {pf:.2f} (target: 2.8)")
    print(f"Total: {total:.1f}p, Avg: {total/n:.1f}p/trade")

    print("\nExits:")
    for r, c in tdf['exit_reason'].value_counts().items():
        avg = tdf[tdf['exit_reason']==r]['pnl_pips'].mean()
        print(f"  {r}: {c}, avg {avg:.1f}p, WR {(tdf[tdf['exit_reason']==r]['pnl_pips']>0).mean()*100:.0f}%")

    print("\nTiers:")
    for t in sorted(tdf['tier'].unique()):
        tf = tdf[tdf['tier']==t]
        print(f"  {t}: {len(tf)}, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

    tdf['year'] = pd.to_datetime(tdf['date']).dt.year
    print("\nYearly:")
    for y in sorted(tdf['year'].unique()):
        yf = tdf[tdf['year']==y]
        print(f"  {y}: {len(yf)}, WR {(yf['pnl_pips']>0).mean()*100:.1f}%, {yf['pnl_pips'].sum():.1f}p")

    # Session-level (one trade per day max = already session-level)
    print(f"\nSession WR: {wr:.1f}% ({n} sessions)")
    print(f"Winning sessions: {(tdf['pnl_pips']>0).sum()}/{n}")

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
