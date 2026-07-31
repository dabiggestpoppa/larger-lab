# P90 Cfd Expansion Engine V5

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
# -*- coding: utf-8 -*-
"""
P90 CFD Expansion Engine v5 — Honest Assessment
=================================================
v5 is an honest attempt to get as close as possible to manual's 85-90% claim.

Key insights from v4:
- T1 sessions: 63.2% WR (380 sessions), +1880p — this where the edge is
- T2/T3 sessions: negative EV — wider AR = harder to expand
- TP1 hits ~60% of sessions, and when it does → 87% go to TP2
- Main losses: stop-outs (-12.5p avg), hard exits (-5.7p)

v5 changes:
1. T-ONLY: Trade T1 only (<20p AR). This is the gold tier.
2. Tighter TP1: 25% AR for T1 = avg ~4.7p target — very achievable.
3. TP1 close 50%, TP2 = 50% AR = avg ~9.4p target.
4. STR requirements: P90 must be in 2-6AM window (optimal cascade window per manual).
   - Manual says: "First P90 in 2-6 AM EST Window → Sets direction of constraint resolution"
   - PART 3: "2:00-6:00 AM EST — Initial Bias Window (First Resolution Signal)"
5. No cascades in T1 for v5 simplicity — just S1+S2+optional 45-min add.
6. If no P90 by 6AM, skip the day (resolution window opening is missed).
7. SL widened: S1 = body (100%, not 80%), S2 = 1.5x body (unchanged — already safe).
8. Minimum body filter: skip if P90 body < 4.1p (minimum threshold) OR body > 30p
   (too big = likely already extended).

CRITICAL: The manual's 85-90% WR is per-session. A session wins if total PnL > 0.

We'll run this honestly and see what number we actually get.
"""
import sys, json, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
import numpy as np
from datetime import date, datetime

STRATEGY_NAME = "p90_cfd_expansion_v5"
TARGET_STATS = {
    'win_rate_pct': 87.5,
    'profit_factor': 1.78,
    'note': '85-90% WR per-session T1-only, ~1.78 PF, EURUSD.PRO 2024-2025'
}

SPREAD_COST = 0.5  # pips


def run_day(day_bars, ar_info):
    """Process one trading day. Returns (session_trade_or_None, lot_trades)."""
    lots = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info.get('date_key', None)

    if tier != 'T1':  # T1 only
        return None, lots

    tier_mult = 1.0

    # Monday reduction
    monday_mult = 1.0
    if date_key is not None:
        from datetime import date as dt_date
        if isinstance(date_key, str):
            date_key = dt_date.fromisoformat(date_key)
        if date_key.weekday() == 0:
            monday_mult = 0.75

    tp1_move = (ar_pips * 0.25) / 10000.0
    tp2_move = (ar_pips * 0.50) / 10000.0
    kill_move = (ar_pips * 1.32) / 10000.0

    # Overfilled check
    bars_to_9am = day_bars[day_bars['est_hour'] <= 9]
    if len(bars_to_9am) > 0:
        dr_9am = (bars_to_9am['high'].max() - bars_to_9am['low'].min()) * 10000.0
        if dr_9am > 40.0:
            tier_mult *= 0.5

    direction = 0
    entry_price = 0.0
    p90_body_pips = 0.0
    p90_time = None
    tp1_hit = False
    active_lots = []
    add45_fired = False
    opposite_p90_count = 0
    regime_mult = 1.0
    initial_p90_bar_time = None

    for _, bar in day_bars.iterrows():
        eh = int(bar['est_hour'])
        bar_close = bar['close']
        bar_high = bar['high']
        bar_low = bar['low']

        # Regime check at 8AM
        if eh == 8 and direction == 0:
            bars_so_far = day_bars[day_bars['est_hour'] <= 8]
            if len(bars_so_far) > 0:
                dr = (bars_so_far['high'].max() - bars_so_far['low'].min()) * 10000.0
                if ar_pips > 0 and dr / ar_pips < 1.5:
                    regime_mult = 0.5

        # Hard Exit at 12PM
        if eh >= HARD_EXIT_EST and active_lots:
            for lot in active_lots:
                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                lots.append({
                    'date': str(bar['est_date']), 'direction': direction,
                    'entry_price': lot['price'], 'exit_price': bar_close,
                    'pnl_pips': pnl, 'exit_reason': 'hard_exit_12pm',
                    'signal_type': lot['signal_type'], 'tier': tier,
                })
            direction = 0
            active_lots = []
            continue

        # Kill Switch
        if active_lots and direction != 0:
            if direction == 1:
                kill_level = entry_price + kill_move
                if bar_close > kill_level:
                    for lot in active_lots:
                        pnl = (kill_level - lot['price']) * 10000.0 - SPREAD_COST
                        lots.append({
                            'date': str(bar['est_date']), 'direction': 1,
                            'entry_price': lot['price'], 'exit_price': kill_level,
                            'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'], 'tier': tier,
                        })
                    direction = 0
                    active_lots = []
                    continue
            elif direction == -1:
                kill_level = entry_price - kill_move
                if bar_close < kill_level:
                    for lot in active_lots:
                        pnl = (lot['price'] - kill_level) * 10000.0 - SPREAD_COST
                        lots.append({
                            'date': str(bar['est_date']), 'direction': -1,
                            'entry_price': lot['price'], 'exit_price': kill_level,
                            'pnl_pips': pnl, 'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'], 'tier': tier,
                        })
                    direction = 0
                    active_lots = []
                    continue

        # TP Management
        if active_lots and not tp1_hit:
            tp1 = entry_price + direction * tp1_move
            if (direction == 1 and bar_high >= tp1) or \
               (direction == -1 and bar_low <= tp1):
                tp1_hit = True
                n_close = max(1, len(active_lots) // 2)
                for lot in active_lots[:n_close]:
                    pnl = (tp1 - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': tp1,
                        'pnl_pips': pnl, 'exit_reason': 'tp1', 'signal_type': lot['signal_type'], 'tier': tier,
                    })
                active_lots = active_lots[n_close:]
                for lot in active_lots:
                    lot['sl'] = entry_price + direction * (2.0 / 10000.0)

        if tp1_hit and active_lots:
            tp2 = entry_price + direction * tp2_move
            if (direction == 1 and bar_high >= tp2) or \
               (direction == -1 and bar_low <= tp2):
                for lot in active_lots:
                    pnl = (tp2 - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': tp2,
                        'pnl_pips': pnl, 'exit_reason': 'tp2', 'signal_type': lot['signal_type'], 'tier': tier,
                    })
                active_lots = []
                direction = 0
                continue

        # SL Check
        if active_lots and not tp1_hit:
            lots_to_keep = []
            for lot in active_lots:
                triggered = False
                exit_p = 0.0
                if direction == 1 and bar_low <= lot['sl']:
                    triggered = True
                    exit_p = lot['sl']
                elif direction == -1 and bar_high >= lot['sl']:
                    triggered = True
                    exit_p = lot['sl']
                if triggered:
                    pnl = (exit_p - lot['price']) * direction * 10000.0 - SPREAD_COST
                    lots.append({
                        'date': str(bar['est_date']), 'direction': direction,
                        'entry_price': lot['price'], 'exit_price': exit_p,
                        'pnl_pips': pnl, 'exit_reason': 'sl_' + lot['signal_type'],
                        'signal_type': lot['signal_type'], 'tier': tier,
                    })
                else:
                    lots_to_keep.append(lot)
            active_lots = lots_to_keep
            if not active_lots and direction != 0:
                direction = 0
                continue

        # Opposite P90
        if direction != 0 and P90_WINDOW_START_EST <= eh < P90_WINDOW_END_EST:
            is_p90, p90_dir, _ = detect_p90(bar)
            if is_p90 and p90_dir == -direction:
                bar_status = classify_p90_relative_to_barrier(bar, ah, al)
                if bar_status in ('above', 'below'):
                    opposite_p90_count += 1
                    if tp1_hit:
                        for lot in active_lots:
                            pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                            lots.append({
                                'date': str(bar['est_date']), 'direction': direction,
                                'entry_price': lot['price'], 'exit_price': bar_close,
                                'pnl_pips': pnl, 'exit_reason': 'opposite_p90_exit',
                                'signal_type': lot['signal_type'], 'tier': tier,
                            })
                        active_lots = []
                        direction = 0
                        continue
                    else:
                        if opposite_p90_count == 1 and active_lots:
                            n_close = max(1, len(active_lots) // 2)
                            for lot in active_lots[:n_close]:
                                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                                lots.append({
                                    'date': str(bar['est_date']), 'direction': direction,
                                    'entry_price': lot['price'], 'exit_price': bar_close,
                                    'pnl_pips': pnl, 'exit_reason': 'opposite_p90_trim',
                                    'signal_type': lot['signal_type'], 'tier': tier,
                                })
                            active_lots = active_lots[n_close:]
                            for lot in active_lots:
                                lot['sl'] = entry_price + direction * (2.0 / 10000.0)
                        elif opposite_p90_count >= 2:
                            for lot in active_lots:
                                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                                lots.append({
                                    'date': str(bar['est_date']), 'direction': direction,
                                    'entry_price': lot['price'], 'exit_price': bar_close,
                                    'pnl_pips': pnl, 'exit_reason': 'opposite_p90_exit',
                                    'signal_type': lot['signal_type'], 'tier': tier,
                                })
                            active_lots = []
                            direction = 0
                            continue

        # P90 Entry: ONLY in 2-6AM window (Initial Bias Window)
        if eh < P90_WINDOW_START_EST or eh > 6:
            continue

        is_p90, p90_dir, body_pips = detect_p90(bar)
        if not is_p90:
            continue

        bar_status = classify_p90_relative_to_barrier(bar, ah, al)
        if bar_status not in ('above', 'below'):
            continue

        signal_dir = 1 if bar_status == 'above' else -1
        if signal_dir == 0:
            continue

        # Body size filter
        if body_pips > 30.0:
            continue

        if direction == 0:
            direction = signal_dir
            entry_price = bar_close
            p90_body_pips = body_pips
            p90_time = bar['timestamp']
            initial_p90_bar_time = bar['timestamp']
            tp1_hit = False
            opposite_p90_count = 0
            add45_fired = False

            size_mult = tier_mult * regime_mult * monday_mult

            # Signal 1 (40%): SL = 100% of body (widened from 80%)
            sl1 = bar_close - signal_dir * (body_pips * 1.00 / 10000.0)
            active_lots.append({
                'price': bar_close, 'size_pct': 0.4 * size_mult,
                'sl': sl1, 'signal_type': 'signal1'
            })

            # Signal 2 (40%): SL = 1.5x body
            sl2 = bar_close - signal_dir * (body_pips * 1.50 / 10000.0)
            active_lots.append({
                'price': bar_close, 'size_pct': 0.4 * size_mult,
                'sl': sl2, 'signal_type': 'signal2'
            })

        # 45-Min Add (fires at 40-50 min from initial P90)
        if direction != 0 and p90_time is not None and not add45_fired:
            elapsed = (bar['timestamp'] - p90_time).total_seconds() / 60.0
            if 40 <= elapsed <= 50:
                current_move = (bar_close - entry_price) * direction * 10000.0
                if current_move >= 8.0:
                    size_mult = tier_mult * regime_mult * monday_mult
                    active_lots.append({
                        'price': bar_close, 'size_pct': 0.2 * size_mult,
                        'sl': entry_price + direction * (2.0 / 10000.0),
                        'signal_type': 'add45min'
                    })
                    add45_fired = True

    # End of day — compute session summary
    if lots:
        day_date = lots[0]['date']
        session_pnl = sum(l['pnl_pips'] for l in lots)
        directions = [l['direction'] for l in lots]
        session_dir = directions[0] if directions else 0
        return {
            'date': day_date,
            'direction': session_dir,
            'session_pnl_pips': session_pnl,
            'n_lots': len(lots),
            'tier': tier,
            'exit_reason': lots[-1].get('exit_reason', 'end_of_day'),
        }, lots

    return None, lots


def run_p90_backtest_v5(df, start_date=None, end_date=None):
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]

    all_sessions = []
    all_lots = []
    days_processed = 0

    for date_key in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == date_key].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10:
            continue

        ar_info = compute_asian_range(df, date_key)
        if ar_info is None:
            continue
        ar_info['date_key'] = date_key

        sess, lots = run_day(day_bars, ar_info)
        if sess:
            all_sessions.append(sess)
        if lots:
            all_lots.extend(lots)
        days_processed += 1

    return all_sessions, all_lots, days_processed


def compute_session_stats(sessions, strategy_name):
    if not sessions:
        return {'error': 'no sessions'}
    df = pd.DataFrame(sessions)
    wins = df[df['session_pnl_pips'] > 0]
    losses = df[df['session_pnl_pips'] <= 0]
    total = len(df)
    win_rate = len(wins) / total * 100.0
    gross_profit = wins['session_pnl_pips'].sum() if len(wins) > 0 else 0
    gross_loss = abs(losses['session_pnl_pips'].sum()) if len(losses) > 0 else 0.001
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    total_pips = df['session_pnl_pips'].sum()
    avg_r = df['session_pnl_pips'].mean()
    return {
        'strategy': strategy_name,
        'total_sessions': total,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': round(win_rate, 1),
        'profit_factor': round(pf, 2),
        'total_pips': round(total_pips, 1),
        'avg_pips_per_session': round(avg_r, 2),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("P90 CFD EXPANSION ENGINE v5 — T1 Only, 2-6AM Initial Window")
    print("=" * 60)

    df = load_data()
    print("\nRunning 2024-2025...")
    sessions, lots, days = run_p90_backtest_v5(df, date(2024, 1, 1), date(2025, 12, 31))

    if not lots:
        print("No trades!")
        sys.exit(1)

    lot_df = pd.DataFrame(lots)
    lot_stats = compute_stats(lot_df, STRATEGY_NAME)
    print(f"\n--- LOT-LEVEL ---")
    print(f"Days: {days}, Lots: {lot_stats['total_trades']}, WR: {lot_stats['win_rate_pct']}%, "
          f"Pips: {lot_stats['total_pips']}")

    if sessions:
        sess_stats = compute_session_stats(sessions, STRATEGY_NAME)
        print(f"\n--- SESSION-LEVEL ---")
        print(f"Sessions: {sess_stats['total_sessions']}")
        print(f"Win Rate: {sess_stats['win_rate_pct']}% (target: 85-90%)")
        print(f"PF: {sess_stats['profit_factor']} (target: 1.78)")
        print(f"Total Pips: {sess_stats['total_pips']}")
        print(f"Avg pips/session: {sess_stats['avg_pips_per_session']}")

        sess_df = pd.DataFrame(sessions)
        print("\nSession Exit Breakdown:")
        for reason, count in sess_df['exit_reason'].value_counts().items():
            avg = sess_df[sess_df['exit_reason'] == reason]['session_pnl_pips'].mean()
            wr = (sess_df[sess_df['exit_reason'] == reason]['session_pnl_pips'] > 0).mean() * 100
            print(f"  {reason}: {count}, avg {avg:.1f}p, WR {wr:.0f}%")

        sess_df['year'] = pd.to_datetime(sess_df['date']).dt.year
        print("\nSession Yearly:")
        for y in sorted(sess_df['year'].unique()):
            yf = sess_df[sess_df['year'] == y]
            wr = (yf['session_pnl_pips'] > 0).mean() * 100
            print(f"  {y}: {len(yf)} sessions, WR {wr:.1f}%, total {yf['session_pnl_pips'].sum():.1f}p")

        report_path = write_report(STRATEGY_NAME, sess_stats, TARGET_STATS, lot_df)
        print(f"\nReport: {report_path}")
        sess_path = REPORTS_DIR / f"{STRATEGY_NAME}_sessions.csv"
        sess_df.to_csv(sess_path, index=False)
    else:
        print("No sessions!")

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
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
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
