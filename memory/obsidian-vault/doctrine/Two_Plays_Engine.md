# Two Plays Engine

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
# -*- coding: utf-8 -*-
"""
Two Plays Engine (Strategy 6 — Simplified Execution Framework)
==============================================================
Play 1 (Base 80): T1/T2, P90 close → market entry, 80% body stop
  WR: 85-90%, simplified daily bread-and-butter

Play 2 (T3 Max Accuracy): T3 only, 2-hour hold, pullback entry
  WR: 76.7%, defensive edge for wider Asian ranges

MAD's framework: these are the SIMPLIFIED execution layer.
Two Plays = how you actually trade the atomic model day-to-day.
"""
import sys, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
from datetime import date

STRATEGY_NAME = "two_plays"
SPREAD_COST = 0.5
P90_THRESH = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def run_play1(day_bars, ar_info):
    """Play 1: Base 80 — T1/T2, P90 close → market entry"""
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info['date_key']

    if tier not in ('T1', 'T2'):
        return trades

    size = 1.0 if tier == 'T1' else 0.75

    for i, bar in day_bars.iterrows():
        eh = bar['est_hour']
        if eh < 2 or eh >= 11:
            continue

        o, h, l, c = bar['open'], bar['high'], bar['low'], bar['close']
        body_pips = abs(c - o) * 10000.0
        if body_pips < P90_THRESH.get(eh, 6.2):
            continue

        # LONG P90: close above Asian High
        if c > ah:
            direction = 1
            sl = c - body_pips * 0.80 / 10000.0
            tp1 = c + ar_pips * 0.25 / 10000.0
            tp2 = c + ar_pips * 0.50 / 10000.0
        # SHORT P90: close below Asian Low
        elif c < al:
            direction = -1
            sl = c + body_pips * 0.80 / 10000.0
            tp1 = c - ar_pips * 0.25 / 10000.0
            tp2 = c - ar_pips * 0.50 / 10000.0
        else:
            continue

        entry = c

        # Overfilled check
        bars_9am = day_bars[day_bars['est_hour'] <= 9]
        dr_9am = (bars_9am['high'].max() - bars_9am['low'].min()) * 10000.0 if len(bars_9am) > 0 else 0
        if dr_9am > 40.0 and tier == 'T2':
            return trades  # STAND DOWN

        tp1_hit = False
        for j, b2 in day_bars.iterrows():
            if b2['timestamp'] <= bar['timestamp']:
                continue
            eh2 = b2['est_hour']
            c2 = b2['close']

            # SL
            if direction == 1 and c2 <= sl:
                pnl = ((c2 - entry) * 10000.0 - SPREAD_COST) * size
                trades.append({'date': str(date_key), 'play': 'play1', 'direction': direction,
                    'entry_price': entry, 'exit_price': c2, 'pnl_pips': pnl,
                    'exit_reason': 'sl_80pct_body', 'tier': tier}); break
            if direction == -1 and c2 >= sl:
                pnl = ((entry - c2) * 10000.0 - SPREAD_COST) * size
                trades.append({'date': str(date_key), 'play': 'play1', 'direction': direction,
                    'entry_price': entry, 'exit_price': c2, 'pnl_pips': pnl,
                    'exit_reason': 'sl_80pct_body', 'tier': tier}); break

            # TP1
            if direction == 1 and c2 >= tp1: tp1_hit = True
            if direction == -1 and c2 <= tp1: tp1_hit = True

            # TP2 (or runner before 11AM)
            if tp1_hit:
                if direction == 1 and c2 >= tp2:
                    pnl = ((c2 - entry) * 10000.0 - SPREAD_COST) * size
                    trades.append({'date': str(date_key), 'play': 'play1', 'direction': direction,
                        'entry_price': entry, 'exit_price': c2, 'pnl_pips': pnl,
                        'exit_reason': 'tp2', 'tier': tier}); break
                if direction == -1 and c2 <= tp2:
                    pnl = ((entry - c2) * 10000.0 - SPREAD_COST) * size
                    trades.append({'date': str(date_key), 'play': 'play1', 'direction': direction,
                        'entry_price': entry, 'exit_price': c2, 'pnl_pips': pnl,
                        'exit_reason': 'tp2', 'tier': tier}); break

            # Hard exit
            if eh2 >= 12:
                pnl = ((c2 - entry) * direction * 10000.0 - SPREAD_COST) * size
                trades.append({'date': str(date_key), 'play': 'play1', 'direction': direction,
                    'entry_price': entry, 'exit_price': c2, 'pnl_pips': pnl,
                    'exit_reason': 'hard_exit', 'tier': tier}); break
        break  # one per session
    return trades


def run_play2(day_bars, ar_info):
    """Play 2: T3 Max Accuracy — 2-hour hold, pullback entry"""
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info['date_key']

    if tier != 'T3':
        return trades

    # Overfilled check
    bars_9am = day_bars[day_bars['est_hour'] <= 9]
    if len(bars_9am) > 0:
        dr_9am = (bars_9am['high'].max() - bars_9am['low'].min()) * 10000.0
        if dr_9am > 40.0:
            return trades  # STAND DOWN

    breakout_bar = None
    breakout_dir = 0
    breakout_time = None

    # Find first M5 close outside Asian band (body >= 4.6)
    for i, bar in day_bars.iterrows():
        eh = bar['est_hour']
        if eh < 3 or eh >= 11:
            continue
        o, h, l, c = bar['open'], bar['high'], bar['low'], bar['close']
        body_pips = abs(c - o) * 10000.0
        if body_pips < 4.6:
            continue
        if c > ah:
            breakout_bar = bar; breakout_dir = 1; breakout_time = bar['timestamp']; break
        elif c < al:
            breakout_bar = bar; breakout_dir = -1; breakout_time = bar['timestamp']; break

    if breakout_bar is None:
        return trades

    # 2-hour hold: price must stay outside Asian band for 2 full hours
    hold_confirmed = False
    hold_bars = day_bars[(day_bars['timestamp'] > breakout_time) &
                          (day_bars['timestamp'] <= breakout_time + pd.Timedelta(hours=2))]
    if len(hold_bars) > 0:
        if breakout_dir == 1:
            hold_confirmed = bool(hold_bars['close'].min() > ah)
        else:
            hold_confirmed = bool(hold_bars['close'].max() < al)

    if not hold_confirmed:
        return trades

    # Entry: pullback to 32-50% partial rebalancing zone
    # For LONG: between entry and entry - 32% to 50% of body
    # For SHORT: between entry and entry + 32% to 50% of body
    entry_price = breakout_bar['close']
    body = abs(entry_price - breakout_bar['open'])

    pullback_low = entry_price - body * 0.50 if breakout_dir == 1 else entry_price + body * 0.32
    pullback_high = entry_price - body * 0.32 if breakout_dir == 1 else entry_price + body * 0.50

    entry_filled = False
    entry_time = None
    for j, bar in day_bars.iterrows():
        if bar['timestamp'] <= breakout_time + pd.Timedelta(hours=2):
            continue
        if bar['est_hour'] >= 11:
            break
        if breakout_dir == 1 and pullback_low <= bar['close'] <= pullback_high:
            entry_filled = True; entry_price = bar['close']; entry_time = bar['timestamp']; break
        if breakout_dir == -1 and pullback_low <= bar['close'] <= pullback_high:
            entry_filled = True; entry_price = bar['close']; entry_time = bar['timestamp']; break

    if not entry_filled:
        return trades

    direction = breakout_dir
    # SL: Asian band edge (close back inside Asian band)
    sl_long = al if direction == 1 else ah
    # TP: 1x Asian Range extension
    tp = entry_price + direction * ar_pips / 10000.0
    size = 0.5  # T3 reduced

    for j, b2 in day_bars.iterrows():
        if entry_time is not None and b2['timestamp'] <= entry_time:
            continue
        c2 = b2['close']
        eh2 = b2['est_hour']

        # SL: close back inside Asian band
        if direction == 1 and c2 <= sl_long:
            pnl = ((c2 - entry_price) * 10000.0 - SPREAD_COST) * size
            trades.append({'date': str(date_key), 'play': 'play2', 'direction': 1,
                'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl,
                'exit_reason': 'sl_inside_band', 'tier': 'T3'}); break
        if direction == -1 and c2 >= sl_long:
            pnl = ((entry_price - c2) * 10000.0 - SPREAD_COST) * size
            trades.append({'date': str(date_key), 'play': 'play2', 'direction': -1,
                'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl,
                'exit_reason': 'sl_inside_band', 'tier': 'T3'}); break

        # TP: 1x AR
        if direction == 1 and c2 >= tp:
            pnl = ((c2 - entry_price) * 10000.0 - SPREAD_COST) * size
            trades.append({'date': str(date_key), 'play': 'play2', 'direction': 1,
                'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl,
                'exit_reason': 'tp_1xAR', 'tier': 'T3'}); break
        if direction == -1 and c2 <= tp:
            pnl = ((entry_price - c2) * 10000.0 - SPREAD_COST) * size
            trades.append({'date': str(date_key), 'play': 'play2', 'direction': -1,
                'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl,
                'exit_reason': 'tp_1xAR', 'tier': 'T3'}); break

        if eh2 >= 12:
            pnl = ((c2 - entry_price) * direction * 10000.0 - SPREAD_COST) * size
            trades.append({'date': str(date_key), 'play': 'play2', 'direction': direction,
                'entry_price': entry_price, 'exit_price': c2, 'pnl_pips': pnl,
                'exit_reason': 'hard_exit', 'tier': 'T3'}); break
    return trades


def run_day(day_bars, ar_info):
    # Play 2 has priority on T3 days
    if ar_info['tier'] == 'T3':
        return run_play2(day_bars, ar_info)
    return run_play1(day_bars, ar_info)


def run_backtest(df, start_date=None, end_date=None):
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]
    all_trades = []
    days = 0
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
    print("=" * 60); print("TWO PLAYS ENGINE — Backtest"); print("=" * 60)
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

    print(f"\nDays: {days}, Trades: {n}")
    print(f"WR: {wr:.1f}% (Play1 target: 85-90%, Play2 target: 76.7%)")
    print(f"PF: {pf:.2f} (target: 2.5)")
    print(f"Total: {total:.1f}p")

    for p in tdf['play'].unique():
        pf2 = tdf[tdf['play']==p]
        print(f"\n{p.upper()}: {len(pf2)} trades, WR {(pf2['pnl_pips']>0).mean()*100:.1f}%, total {pf2['pnl_pips'].sum():.1f}p")
        for r, c in pf2['exit_reason'].value_counts().items():
            avg = pf2[pf2['exit_reason']==r]['pnl_pips'].mean()
            print(f"  {r}: {c}, avg {avg:.1f}p")

    print("\nTiers:")
    for t in sorted(tdf['tier'].unique()):
        tf = tdf[tdf['tier']==t]
        print(f"  {t}: {len(tf)}, WR {(tf['pnl_pips']>0).mean()*100:.1f}%")

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
