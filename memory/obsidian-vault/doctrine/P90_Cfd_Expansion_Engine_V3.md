# P90 Cfd Expansion Engine V3

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
# -*- coding: utf-8 -*-
"""
P90 CFD Expansion Engine v3 (Strategy #1 — Calibrated)
======================================================
Manual Reference: CEREBUS FX v4 Part 1, Section 3 + P90_STRATEGY_GUIDE.md
Target Stats: 85-90% WR, ~1.78 PF

CHANGES FROM v2 (calibration fixes):
1. Kill switch: 132% of Asian Range measured from the ENTRY PRICE in trade direction,
   NOT from Asian band edges. This prevents premature kills on normal expansion.
   - LONG kill: entry_price + (AR * 1.32)
   - SHORT kill: entry_price - (AR * 1.32)
   
2. Opposite P90 handling: FIRST opposite P90 → trim 50% (not exit all).
   SECOND opposite P90 → exit all remaining.
   Only if TP1 hasn't been hit yet. If TP1 already hit, first opposite P90 exits all.

3. Tier-specific cascade limits: T1/T2 max=3, T3 max=0 (NO cascades).
   Cascade count spans all same-direction P90s after the initial.

4. Monday size reduction: 25% (multiply tier_mult by 0.75 on Mondays).

5. Signal 3 size: manual says 20% (not 30% as in strategy guide table which sums to 130%;
   the guide notes "When ONLY 45-Min triggers: split 50/50" for signals 1+2 → 50% total, 
   then 45-min add takes 20% → combined 70%; but initial is 80% with s1+s2.
   We use: S1=40%, S2=40%, S3=20%, C1=20%, C2=10% → matching manual table).

6. Improved 45-min add: fires at 40-50 min window, needs +8p favorable move, SL=BE.

7. Overfilled filter: at 9AM, if daily range > 40p:
   - T1: reduce to 50% size (anchor only)
   - T2/T3: STAND DOWN (skip day)

8. Hard exit: 12PM EST close ALL.

9. Regime confirmation at 8AM (not 8:45): if daily range so far < 1.5x AR, reduce 50%.

Entry Logic (MOMENTUM):
- P90 close above Asian High → LONG (ride expansion upward)
- P90 close below Asian Low → SHORT (ride expansion downward)
- Signal 1 (40%): SL = 80% of P90 body behind entry
- Signal 2 (40%): SL = 1.5x P90 body behind entry
- Both fire simultaneously at P90 close

TP Management:
- TP1: entry + 25% of Asian Range (in trade direction) → close 50%, move SL to BE
- TP2: entry + 50% of Asian Range → close remaining
"""
import sys, json, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import *
import pandas as pd
import numpy as np
from datetime import date, datetime

STRATEGY_NAME = "p90_cfd_expansion_v3"
TARGET_STATS = {
    'win_rate_pct': 87.5,  # midpoint of 85-90%
    'profit_factor': 1.78,
    'note': '85-90% WR, ~1.78 PF, EURUSD.PRO 2024-2025'
}

SPREAD_COST = 0.5  # pips


def run_day(day_bars, ar_info):
    """Process one trading day. Returns list of closed trade dicts."""
    trades = []

    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    tier = ar_info['tier']
    date_key = ar_info.get('date_key', None)

    if tier == 'NO_GO' or ar_pips < 3:
        return trades

    # Tier multiplier
    tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}.get(tier, 0.0)
    if tier_mult == 0:
        return trades

    # Monday reduction: 25%
    is_monday = False
    if date_key is not None:
        from datetime import date as dt_date
        if isinstance(date_key, str):
            date_key = dt_date.fromisoformat(date_key)
        is_monday = date_key.weekday() == 0
    monday_mult = 0.75 if is_monday else 1.0

    # TP price moves
    tp1_move = (ar_pips * 0.25) / 10000.0
    tp2_move = (ar_pips * 0.50) / 10000.0

    # Kill switch: 132% of Asian Range from ENTRY (in trade direction)
    kill_move = (ar_pips * 1.32) / 10000.0

    # Max cascades by tier
    max_cascades = {'T1': 3, 'T2': 3, 'T3': 0}.get(tier, 0)

    # --- Full-day pre-scan for overfilled check ---
    # Overfilled: bars up to 9AM, daily range > 40p
    bars_to_9am = day_bars[day_bars['est_hour'] <= 9]
    overfilled = False
    if len(bars_to_9am) > 0:
        dr_9am = (bars_to_9am['high'].max() - bars_to_9am['low'].min()) * 10000.0
        if dr_9am > 40.0:
            if tier in ('T2', 'T3'):
                return trades  # STAND DOWN
            elif tier == 'T1':
                tier_mult *= 0.5  # reduce to 50%

    # State variables
    direction = 0
    entry_price = 0.0
    p90_body_pips = 0.0
    p90_time = None
    signals_fired = 0
    tp1_hit = False
    active_lots = []
    cascade_count = 0
    add45_fired = False
    opposite_p90_count = 0
    regime_mult = 1.0

    for _, bar in day_bars.iterrows():
        eh = int(bar['est_hour'])
        bar_close = bar['close']
        bar_high = bar['high']
        bar_low = bar['low']

        # --- Regime check at 8AM EST ---
        if eh == 8 and direction == 0:
            bars_so_far = day_bars[day_bars['est_hour'] <= 8]
            if len(bars_so_far) > 0:
                dr = (bars_so_far['high'].max() - bars_so_far['low'].min()) * 10000.0
                if ar_pips > 0 and dr / ar_pips < 1.5:
                    regime_mult = 0.5

        # --- STAND DOWN for T2/T3 overfilled already handled above ---

        # --- Hard Exit at 12PM EST ---
        if eh >= HARD_EXIT_EST and active_lots:
            for lot in active_lots:
                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                trades.append({
                    'date': str(bar['est_date']),
                    'direction': direction,
                    'entry_price': lot['price'],
                    'exit_price': bar_close,
                    'pnl_pips': pnl,
                    'exit_reason': 'hard_exit_12pm',
                    'signal_type': lot['signal_type'],
                    'tier': tier,
                })
            active_lots = []
            direction = 0
            continue

        # --- Kill Switch: 132% of AR from entry price in trade direction ---
        if active_lots and direction != 0:
            if direction == 1:
                kill_level = entry_price + kill_move
                if bar_close > kill_level:
                    for lot in active_lots:
                        pnl = (kill_level - lot['price']) * 10000.0 - SPREAD_COST
                        trades.append({
                            'date': str(bar['est_date']),
                            'direction': 1,
                            'entry_price': lot['price'],
                            'exit_price': kill_level,
                            'pnl_pips': pnl,
                            'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'],
                            'tier': tier,
                        })
                    active_lots = []
                    direction = 0
                    continue
            elif direction == -1:
                kill_level = entry_price - kill_move
                if bar_close < kill_level:
                    for lot in active_lots:
                        pnl = (lot['price'] - kill_level) * 10000.0 - SPREAD_COST
                        trades.append({
                            'date': str(bar['est_date']),
                            'direction': -1,
                            'entry_price': lot['price'],
                            'exit_price': kill_level,
                            'pnl_pips': pnl,
                            'exit_reason': 'kill_switch_132',
                            'signal_type': lot['signal_type'],
                            'tier': tier,
                        })
                    active_lots = []
                    direction = 0
                    continue

        # --- TP Management ---
        if active_lots and not tp1_hit:
            tp1 = entry_price + direction * tp1_move
            if (direction == 1 and bar_high >= tp1) or \
               (direction == -1 and bar_low <= tp1):
                tp1_hit = True
                # Close 50% of lots
                n_close = max(1, len(active_lots) // 2)
                for lot in active_lots[:n_close]:
                    pnl = (tp1 - lot['price']) * direction * 10000.0 - SPREAD_COST
                    trades.append({
                        'date': str(bar['est_date']),
                        'direction': direction,
                        'entry_price': lot['price'],
                        'exit_price': tp1,
                        'pnl_pips': pnl,
                        'exit_reason': 'tp1_ar25',
                        'signal_type': lot['signal_type'],
                        'tier': tier,
                    })
                active_lots = active_lots[n_close:]
                # Move SL to breakeven+2p for remaining
                for lot in active_lots:
                    lot['sl'] = entry_price + direction * (2.0 / 10000.0)

        if tp1_hit and active_lots:
            tp2 = entry_price + direction * tp2_move
            if (direction == 1 and bar_high >= tp2) or \
               (direction == -1 and bar_low <= tp2):
                for lot in active_lots:
                    pnl = (tp2 - lot['price']) * direction * 10000.0 - SPREAD_COST
                    trades.append({
                        'date': str(bar['est_date']),
                        'direction': direction,
                        'entry_price': lot['price'],
                        'exit_price': tp2,
                        'pnl_pips': pnl,
                        'exit_reason': 'tp2_ar50',
                        'signal_type': lot['signal_type'],
                        'tier': tier,
                    })
                active_lots = []
                direction = 0
                continue

        # --- SL Check ---
        if active_lots and not tp1_hit:
            lots_to_keep = []
            for lot in active_lots:
                triggered = False
                if direction == 1 and bar_low <= lot['sl']:
                    triggered = True
                    exit_p = lot['sl']
                elif direction == -1 and bar_high >= lot['sl']:
                    triggered = True
                    exit_p = lot['sl']

                if triggered:
                    pnl = (exit_p - lot['price']) * direction * 10000.0 - SPREAD_COST
                    trades.append({
                        'date': str(bar['est_date']),
                        'direction': direction,
                        'entry_price': lot['price'],
                        'exit_price': exit_p,
                        'pnl_pips': pnl,
                        'exit_reason': 'sl_' + lot['signal_type'],
                        'signal_type': lot['signal_type'],
                        'tier': tier,
                    })
                else:
                    lots_to_keep.append(lot)
            active_lots = lots_to_keep
            if not active_lots and direction != 0:
                direction = 0
                continue

        # --- Opposite P90 detection (trim/exit logic) ---
        if direction != 0 and P90_WINDOW_START_EST <= eh < P90_WINDOW_END_EST:
            is_p90, p90_dir, body_pips_check = detect_p90(bar)
            if is_p90 and p90_dir == -direction:
                bar_status = classify_p90_relative_to_barrier(bar, ah, al)
                if bar_status in ('above', 'below'):
                    opposite_p90_count += 1
                    if tp1_hit:
                        # If TP1 already hit, first opposite P90 exits all remaining
                        for lot in active_lots:
                            pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                            trades.append({
                                'date': str(bar['est_date']),
                                'direction': direction,
                                'entry_price': lot['price'],
                                'exit_price': bar_close,
                                'pnl_pips': pnl,
                                'exit_reason': 'opposite_p90_exit_tp1done',
                                'signal_type': lot['signal_type'],
                                'tier': tier,
                            })
                        active_lots = []
                        direction = 0
                        continue
                    else:
                        # TP1 not hit yet
                        if opposite_p90_count == 1:
                            # FIRST opposite P90: trim 50%
                            if active_lots:
                                n_close = max(1, len(active_lots) // 2)
                                for lot in active_lots[:n_close]:
                                    pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                                    trades.append({
                                        'date': str(bar['est_date']),
                                        'direction': direction,
                                        'entry_price': lot['price'],
                                        'exit_price': bar_close,
                                        'pnl_pips': pnl,
                                        'exit_reason': 'opposite_p90_trim50',
                                        'signal_type': lot['signal_type'],
                                        'tier': tier,
                                    })
                                active_lots = active_lots[n_close:]
                                # Move SL to BE for remaining
                                for lot in active_lots:
                                    lot['sl'] = entry_price + direction * (2.0 / 10000.0)
                        elif opposite_p90_count >= 2:
                            # SECOND opposite P90: exit all
                            for lot in active_lots:
                                pnl = (bar_close - lot['price']) * direction * 10000.0 - SPREAD_COST
                                trades.append({
                                    'date': str(bar['est_date']),
                                    'direction': direction,
                                    'entry_price': lot['price'],
                                    'exit_price': bar_close,
                                    'pnl_pips': pnl,
                                    'exit_reason': 'opposite_p90_exit_all',
                                    'signal_type': lot['signal_type'],
                                    'tier': tier,
                                })
                            active_lots = []
                            direction = 0
                            continue

        # --- Skip P90 entry logic if already exited or no direction ---
        if direction == 0 and eh < P90_WINDOW_END_EST:
            pass  # Reset state for potential new entry later in day

        # --- P90 Detection & Entry ---
        if eh < P90_WINDOW_START_EST or eh >= P90_WINDOW_END_EST:
            continue
        if signals_fired >= 5:
            continue

        is_p90, p90_dir, body_pips = detect_p90(bar)
        if not is_p90:
            continue

        bar_status = classify_p90_relative_to_barrier(bar, ah, al)
        if bar_status not in ('above', 'below'):
            continue

        signal_dir = 1 if bar_status == 'above' else -1

        if direction == 0:
            # === INITIAL P90 ===
            direction = signal_dir
            entry_price = bar_close
            p90_body_pips = body_pips
            p90_time = bar['timestamp']
            tp1_hit = False
            cascade_count = 0
            opposite_p90_count = 0

            size_mult = tier_mult * regime_mult * monday_mult

            # Signal 1 (40%): SL = 80% of body
            sl1 = bar_close - signal_dir * (body_pips * 0.80 / 10000.0)
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

            signals_fired = 2

        elif signal_dir == direction and cascade_count < max_cascades:
            # === CASCADE P90 (same direction) ===
            if p90_time is not None:
                elapsed = (bar['timestamp'] - p90_time).total_seconds() / 60.0
                if 30 <= elapsed <= 90:
                    cascade_count += 1
                    size_mult = tier_mult * regime_mult * monday_mult

                    if cascade_count == 1:
                        c_size = 0.2
                    elif cascade_count == 2:
                        c_size = 0.1
                    else:
                        c_size = 0.05

                    sl_c = bar_close - signal_dir * (body_pips * 1.68 / 10000.0)
                    active_lots.append({
                        'price': bar_close, 'size_pct': c_size * size_mult,
                        'sl': sl_c, 'signal_type': f'cascade_{cascade_count}'
                    })
                    signals_fired += 1

        # --- 45-Min Add ---
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
                    signals_fired = max(signals_fired, 3)

    return trades


def run_p90_backtest_v3(df, start_date=None, end_date=None):
    """Run P90 CFD Expansion v3 backtest"""
    if start_date:
        df = df[df['est_date'] >= start_date]
    if end_date:
        df = df[df['est_date'] <= end_date]

    all_trades = []
    days_processed = 0

    for date_key in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == date_key].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10:
            continue

        ar_info = compute_asian_range(df, date_key)
        if ar_info is None:
            continue
        ar_info['date_key'] = date_key

        trades = run_day(day_bars, ar_info)
        if trades:
            all_trades.extend(trades)
        days_processed += 1

    return all_trades, days_processed


if __name__ == "__main__":
    print("=" * 60)
    print("P90 CFD EXPANSION ENGINE v3 — Backtest (Calibrated)")
    print("=" * 60)

    df = load_data()

    print("\nRunning 2023H2-2026H1 (full dataset)...")
    all_trades, days = run_p90_backtest_v3(df, date(2023, 7, 1), date(2026, 5, 31))

    if not all_trades:
        print("No trades generated!")
        sys.exit(1)

    trades_df = pd.DataFrame(all_trades)
    stats = compute_stats(trades_df, STRATEGY_NAME)

    print(f"\nDays processed: {days}")
    print(f"Total trades (lots): {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate_pct']}% (target: 85-90%)")
    print(f"Profit Factor: {stats['profit_factor']} (target: ~1.78)")
    print(f"Total Pips: {stats['total_pips']}")
    print(f"Avg pips/trade: {stats['avg_pips_per_trade']}")

    # Exit reason breakdown
    print("\nExit Reason Breakdown:")
    for reason, count in trades_df['exit_reason'].value_counts().items():
        avg = trades_df[trades_df['exit_reason'] == reason]['pnl_pips'].mean()
        wr = (trades_df[trades_df['exit_reason'] == reason]['pnl_pips'] > 0).mean() * 100
        print(f"  {reason}: {count} trades, avg {avg:.1f}p, WR {wr:.0f}%")

    # Tier breakdown
    print("\nTier Breakdown:")
    for t in sorted(trades_df['tier'].unique()):
        tf = trades_df[trades_df['tier'] == t]
        print(f"  {t}: {len(tf)} trades, WR {((tf['pnl_pips'] > 0).mean() * 100):.1f}%, "
              f"avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

    # Signal type breakdown
    print("\nSignal Type Breakdown:")
    for sig in sorted(trades_df['signal_type'].unique()):
        sf = trades_df[trades_df['signal_type'] == sig]
        print(f"  {sig}: {len(sf)} trades, WR {((sf['pnl_pips'] > 0).mean() * 100):.1f}%, "
              f"avg {sf['pnl_pips'].mean():.1f}p")

    # Yearly
    trades_df['year'] = pd.to_datetime(trades_df['date']).dt.year
    print("\nYearly:")
    for y in sorted(trades_df['year'].unique()):
        yf = trades_df[trades_df['year'] == y]
        print(f"  {y}: {len(yf)} lots, WR {((yf['pnl_pips'] > 0).mean() * 100):.1f}%, "
              f"total {yf['pnl_pips'].sum():.1f}p")

    # Session-based win rate (per-day aggregated)
    print("\nPer-Day Session WR (aggregating all lots per day):")
    daily = trades_df.groupby('date').agg(
        day_pnl=('pnl_pips', 'sum'),
        n_lots=('pnl_pips', 'count')
    ).reset_index()
    daily['win'] = daily['day_pnl'] > 0
    session_wr = daily['win'].mean() * 100
    n_days = len(daily)
    n_win_days = daily['win'].sum()
    print(f"  {n_win_days}/{n_days} winning days = {session_wr:.1f}% session WR")
    print(f"  Total session pips: {daily['day_pnl'].sum():.1f}")

    report_path = write_report(STRATEGY_NAME, stats, TARGET_STATS, trades_df)
    print(f"\nReport: {report_path}")

```

LINKS:
[[Codemap]]
[[V3 Architecture]]
[[V3 Cognitive Field]]
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
[[2026 05 18]]
[[Backtest Campaign V3 Results]]
[[Errors And Solutions]]
[[Oc2 Gateway Failures]]
[[Cal]]
[[Citation Workflow]]
[[Pitfalls]]
[[Template Integrity]]
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
