# Dual Engine

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
# -*- coding: utf-8 -*-
"""
Dual-Engine Execution Model (Strategy 4 — Atomic Hybrid)
=========================================================
Manual claims: 89.4% WR, 3.42 PF

CONCEPT:
Two complementary layers:
1. CONSTRAINT ANCHOR (70% capital): M5 close outside Asian band → structural entry
2. RESOLUTION AMPLIFIERS (30% capital): P90 activations in Anchor direction → momentum adds

KEY: Amplifiers ONLY fire if direction matches Anchor. No opposite amps.
Capital split: 70% Anchor / 30% Amplifiers

AMP RULES:
- T1: partial rebalancing at 32% or 50%, max 2 amps, 20% each, target 20p fixed
- T2: partial rebalancing at 50% ONLY, max 1 amp, 30%, target 20p fixed
- T3: NO AMPLIFIERS

OVERFILLED:
- T1 overfilled (>40p by 9AM): Anchor ONLY, 50% size
- T2/T3 overfilled: STAND DOWN
"""
import sys, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
from datetime import date

STRATEGY_NAME = "dual_engine"
SPREAD_COST = 0.5
P90_THRESH = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def run_day(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info['date_key']

    if tier == 'NO_GO':
        return trades

    # Overfilled check
    anchor_size = 0.70  # 70% to anchor
    amp_size = 0.30     # 30% to amps
    bars_9am = day_bars[day_bars['est_hour'] <= 9]
    dr_9am = (bars_9am['high'].max() - bars_9am['low'].min()) * 10000.0 if len(bars_9am) > 0 else 0

    if dr_9am > 40.0:
        if tier in ('T2', 'T3'):
            return trades  # STAND DOWN
        anchor_size = 0.35  # T1 anchor only, half
        amp_size = 0.0

    if tier == 'T3':
        amp_size = 0.0  # NO amps on T3

    # ── PHASE 1: Find Anchor entry ──
    anchor_entry = None
    anchor_dir = 0
    anchor_bar_idx = None

    for i, bar in day_bars.iterrows():
        eh = bar['est_hour']
        if eh < 3 or eh >= 11:
            continue
        o, h, l, c = bar['open'], bar['high'], bar['low'], bar['close']
        body_pips = abs(c - o) * 10000.0
        if body_pips < 4.6:
            continue
        if c > ah:
            anchor_entry = c; anchor_dir = 1; anchor_bar_idx = i; break
        elif c < al:
            anchor_entry = c; anchor_dir = -1; anchor_bar_idx = i; break

    if anchor_entry is None:
        return trades

    # Track anchor trade
    anchor_sl = al if anchor_dir == 1 else ah
    anchor_tp1 = anchor_entry + anchor_dir * ar_pips * 0.25 / 10000.0
    anchor_tp2 = anchor_entry + anchor_dir * ar_pips * 0.50 / 10000.0
    anchor_active = True
    anchor_tp1_hit = False
    anchor_pnl = 0

    # Amp tracking
    amps_fired = 0
    max_amps = {'T1': 2, 'T2': 1, 'T3': 0}.get(tier, 0)
    amp_size_each = {'T1': 0.20, 'T2': 0.30, 'T3': 0.0}.get(tier, 0)
    amp_target = 20.0  # pips fixed
    amp_entries = []

    # ── Track both anchor and amps through the day ──
    for j, bar in day_bars.iterrows():
        if anchor_bar_idx is not None and j <= anchor_bar_idx:
            continue
        eh = bar['est_hour']
        if eh >= 12:
            # Hard exit everything
            if anchor_active:
                pnl = (bar['close'] - anchor_entry) * anchor_dir * 10000.0 - SPREAD_COST
                trades.append({'date': str(date_key), 'engine': 'anchor', 'direction': anchor_dir,
                    'entry_price': anchor_entry, 'exit_price': bar['close'], 'pnl_pips': pnl * anchor_size,
                    'exit_reason': 'hard_exit', 'tier': tier})
            for ae in amp_entries:
                if ae['active']:
                    pnl = (bar['close'] - ae['entry']) * ae['dir'] * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'amp', 'direction': ae['dir'],
                        'entry_price': ae['entry'], 'exit_price': bar['close'], 'pnl_pips': pnl * amp_size_each,
                        'exit_reason': 'hard_exit', 'tier': tier})
            break

        c = bar['close']

        # ── Anchor management ──
        if anchor_active:
            # SL
            if anchor_dir == 1 and c <= anchor_sl:
                pnl = (c - anchor_entry) * 10000.0 - SPREAD_COST
                trades.append({'date': str(date_key), 'engine': 'anchor', 'direction': anchor_dir,
                    'entry_price': anchor_entry, 'exit_price': c, 'pnl_pips': pnl * anchor_size,
                    'exit_reason': 'sl', 'tier': tier})
                anchor_active = False
            elif anchor_dir == -1 and c >= anchor_sl:
                pnl = (anchor_entry - c) * 10000.0 - SPREAD_COST
                trades.append({'date': str(date_key), 'engine': 'anchor', 'direction': anchor_dir,
                    'entry_price': anchor_entry, 'exit_price': c, 'pnl_pips': pnl * anchor_size,
                    'exit_reason': 'sl', 'tier': tier})
                anchor_active = False

            # TP1
            if anchor_dir == 1 and c >= anchor_tp1:
                anchor_tp1_hit = True
            if anchor_dir == -1 and c <= anchor_tp1:
                anchor_tp1_hit = True

            # TP2
            if anchor_tp1_hit:
                if anchor_dir == 1 and c >= anchor_tp2:
                    pnl = (c - anchor_entry) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'anchor', 'direction': anchor_dir,
                        'entry_price': anchor_entry, 'exit_price': c, 'pnl_pips': pnl * anchor_size,
                        'exit_reason': 'tp2', 'tier': tier})
                    anchor_active = False
                if anchor_dir == -1 and c <= anchor_tp2:
                    pnl = (anchor_entry - c) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'anchor', 'direction': anchor_dir,
                        'entry_price': anchor_entry, 'exit_price': c, 'pnl_pips': pnl * anchor_size,
                        'exit_reason': 'tp2', 'tier': tier})
                    anchor_active = False

        # ── Amplifier detection ──
        if amps_fired < max_amps and amp_size > 0 and anchor_active:
            o = bar['open']
            body_pips = abs(c - o) * 10000.0
            if body_pips >= P90_THRESH.get(eh, 6.2):
                is_long_p90 = (c > ah) and (c > o)
                is_short_p90 = (c < al) and (c < o)
                p90_dir = 1 if is_long_p90 else (-1 if is_short_p90 else 0)

                if p90_dir == anchor_dir:
                    # Partial rebalancing zone
                    if anchor_dir == 1:
                        rebal_low = anchor_entry - ar_pips * 0.32 / 10000.0
                        rebal_high = anchor_entry - ar_pips * 0.50 / 10000.0
                    else:
                        rebal_low = anchor_entry + ar_pips * 0.32 / 10000.0
                        rebal_high = anchor_entry + ar_pips * 0.50 / 10000.0

                    if rebal_low <= c <= rebal_high:
                        amps_fired += 1
                        amp_entries.append({
                            'entry': c, 'dir': p90_dir, 'active': True,
                            'sl': c - p90_dir * body_pips * 0.80 / 10000.0,
                            'tp': c + p90_dir * amp_target / 10000.0
                        })

        # ── Amp management ──
        for ae in amp_entries:
            if not ae['active']:
                continue
            if ae['dir'] == 1:
                if c <= ae['sl']:
                    pnl = (c - ae['entry']) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'amp', 'direction': ae['dir'],
                        'entry_price': ae['entry'], 'exit_price': c, 'pnl_pips': pnl * amp_size_each,
                        'exit_reason': 'sl', 'tier': tier}); ae['active'] = False
                elif c >= ae['tp']:
                    pnl = (c - ae['entry']) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'amp', 'direction': ae['dir'],
                        'entry_price': ae['entry'], 'exit_price': c, 'pnl_pips': pnl * amp_size_each,
                        'exit_reason': 'tp_20p', 'tier': tier}); ae['active'] = False
            else:
                if c >= ae['sl']:
                    pnl = (ae['entry'] - c) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'amp', 'direction': ae['dir'],
                        'entry_price': ae['entry'], 'exit_price': c, 'pnl_pips': pnl * amp_size_each,
                        'exit_reason': 'sl', 'tier': tier}); ae['active'] = False
                elif c <= ae['tp']:
                    pnl = (ae['entry'] - c) * 10000.0 - SPREAD_COST
                    trades.append({'date': str(date_key), 'engine': 'amp', 'direction': ae['dir'],
                        'entry_price': ae['entry'], 'exit_price': c, 'pnl_pips': pnl * amp_size_each,
                        'exit_reason': 'tp_20p', 'tier': tier}); ae['active'] = False

    return trades


def run_backtest(df, start_date=None, end_date=None):
    if start_date: df = df[df['est_date'] >= start_date]
    if end_date: df = df[df['est_date'] <= end_date]
    all_trades = []; days = 0
    for dk in sorted(df['est_date'].unique()):
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(db) < 10: continue
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        ar['date_key'] = dk
        tr = run_day(db, ar)
        if tr: all_trades.extend(tr)
        days += 1
    return all_trades, days


if __name__ == "__main__":
    print("=" * 60); print("DUAL-ENGINE — Backtest (Atomic Hybrid)"); print("=" * 60)
    df = load_data()
    print("\nRunning 2024-2025...")
    tr, days = run_backtest(df, date(2024, 1, 1), date(2025, 12, 31))
    if not tr: print("No trades!"); sys.exit(1)

    tdf = pd.DataFrame(tr)
    n = len(tdf)
    wr = (tdf['pnl_pips'] > 0).mean() * 100
    total = tdf['pnl_pips'].sum()
    wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
    losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
    pf = wins / losses if losses > 0 else float('inf')

    print(f"\nDays: {days}, Total trades: {n}")
    print(f"WR: {wr:.1f}% (target: 89.4%)")
    print(f"PF: {pf:.2f} (target: 3.42)")
    print(f"Total: {total:.1f}p")

    for eng in tdf['engine'].unique():
        ef = tdf[tdf['engine']==eng]
        print(f"\n{eng.upper()}: {len(ef)} trades, WR {(ef['pnl_pips']>0).mean()*100:.1f}%, total {ef['pnl_pips'].sum():.1f}p")
        for r, c in ef['exit_reason'].value_counts().items():
            avg = ef[ef['exit_reason']==r]['pnl_pips'].mean()
            print(f"  {r}: {c}, avg {avg:.1f}p")

    print("\nTiers:")
    for t in sorted(tdf['tier'].unique()):
        tf = tdf[tdf['tier']==t]
        print(f"  {t}: {len(tf)}, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, total {tf['pnl_pips'].sum():.1f}p")

    tdf['year'] = pd.to_datetime(tdf['date']).dt.year
    print("\nYearly:")
    for y in sorted(tdf['year'].unique()):
        yf = tdf[tdf['year']==y]
        print(f"  {y}: {len(yf)}, WR {(yf['pnl_pips']>0).mean()*100:.1f}%, {yf['pnl_pips'].sum():.1f}p")

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
[[Diag V5]]
[[Dmr Strategy]]
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
