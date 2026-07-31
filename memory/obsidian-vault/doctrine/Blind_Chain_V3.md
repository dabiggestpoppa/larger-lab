# Blind Chain V3

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""
CEREBUS FX v4 — EUR/USD Blind Chain (Zero-Buffer + Mirrored Move + Continuous Loop)
Exact specification from manual via MAD (2026-05-29)

State Machine: SEARCH → WAIT_OPP → IN_TRADE → RESET (loop)
Key differences from Symmetry Trap:
  - NO Goldilocks/32-50% filter — entry fires on first opposite close after impulse
  - Gear Shift Override: dynamic AU based on impulse size
  - SL = Exact OCC Extreme (zero buffer, close-only)
  - TP = dynamic AU from Gear Shift
"""
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from shared import load_data

PIP_SIZE = 0.0001
SESSION_START = 3
SESSION_END = 12
MAX_LOOPS = 8

TIERS = {
    'T1': {'ar_max': 20.0, 'au': 10.0, 'trig': 12.0},
    'T2': {'ar_max': 30.0, 'au': 12.0, 'trig': 15.0},
    'T3': {'ar_max': 45.0, 'au': 15.0, 'trig': 19.0},
}

# Gear Shift Override: impulse_pips -> (tier_label, au_pips)
GEAR_SHIFT = {
    'T1': {15.0: ('T2', 12.0), 19.0: ('T3', 15.0)},
    'T2': {19.0: ('T3', 15.0)},
    'T3': {25.0: ('MT25', 25.0)},
}


def get_gear_shift(tier, impulse_pips):
    """Return (au_label, au_pips) based on impulse size."""
    if tier in GEAR_SHIFT:
        for threshold, (label, au) in sorted(GEAR_SHIFT[tier].items()):
            if impulse_pips >= threshold:
                return label, au
    return tier, TIERS[tier]['au']


def run_blind_chain_day(day_bars, ar_info):
    """Run Blind Chain state machine for one session day."""
    trades = []
    tier_name = ar_info['tier']
    base_au = TIERS[tier_name]['au']
    trig = TIERS[tier_name]['trig']

    session = day_bars[(day_bars['est_hour'] >= SESSION_START) & (day_bars['est_hour'] < SESSION_END)]
    session = session.sort_values('timestamp').reset_index(drop=True)
    if session.empty:
        return trades

    state = 'SEARCH'
    swing_origin = None
    bias = 0
    imp_high = 0.0
    imp_low = 0.0
    imp_size = 0.0
    entry = sl = tp = None
    loop_count = 0
    risk_mult = 1.0
    current_au = base_au
    current_tier = tier_name

    i = 0
    while i < len(session):
        bar = session.iloc[i]
        bar_hour = bar['est_hour']

        # 9AM Regime Check
        if bar_hour == 9 and state != 'IN_TRADE':
            morning = session[(session['est_hour'] >= 3) & (session['est_hour'] < 9)]
            if len(morning) > 0:
                morn_range = (morning['high'].max() - morning['low'].min()) / PIP_SIZE
                ar_pips = ar_info['ar_pips']
                regime_ratio = morn_range / ar_pips if ar_pips > 0 else 99
                if regime_ratio < 1.5:
                    risk_mult = 0.5

        if state == 'SEARCH':
            if swing_origin is None:
                swing_origin = bar['close']

            up_move = (bar['high'] - swing_origin) / PIP_SIZE
            dn_move = (swing_origin - bar['low']) / PIP_SIZE

            if up_move >= trig:
                bias = 1; imp_high = bar['high']; imp_low = swing_origin
                imp_size = up_move
                # Gear Shift check
                current_tier, current_au = get_gear_shift(tier_name, imp_size)
                state = 'WAIT_OPP'
            elif dn_move >= trig:
                bias = -1; imp_low = bar['low']; imp_high = swing_origin
                imp_size = dn_move
                current_tier, current_au = get_gear_shift(tier_name, imp_size)
                state = 'WAIT_OPP'

        elif state == 'WAIT_OPP':
            if imp_size == 0:
                state = 'SEARCH'; swing_origin = bar['close']; i += 1; continue

            # 80% Kill Switch (close-only)
            if bias == 1:
                kill_zone = imp_high - imp_size * 0.80 * PIP_SIZE
                if bar['close'] < kill_zone:
                    state = 'SEARCH'; swing_origin = bar['close']; i += 1; continue
            else:
                kill_zone = imp_low + imp_size * 0.80 * PIP_SIZE
                if bar['close'] > kill_zone:
                    state = 'SEARCH'; swing_origin = bar['close']; i += 1; continue

            # Entry: First M5 close opposite to impulse direction
            opp_close = (bias == 1 and bar['close'] < bar['open']) or \
                        (bias == -1 and bar['close'] > bar['open'])
            if opp_close:
                entry = bar['close']
                # SL: Exact OCC Extreme (close-only)
                sl = imp_low if bias == 1 else imp_high
                # TP: 1 AU (dynamic from Gear Shift)
                tp = entry + (bias * current_au * PIP_SIZE)
                state = 'IN_TRADE'
                loop_count += 1

        elif state == 'IN_TRADE':
            exit_px = None
            exit_type = 'TIME'
            remaining = session.iloc[i+1:]

            for j_idx, nb in remaining.iterrows():
                nh = nb['est_hour']
                if nh >= 12:
                    exit_px = nb['close']; exit_type = 'TIME'; break

                if bias == 1:
                    if nb['high'] >= tp:
                        exit_px = tp; exit_type = 'TP'; break
                    if nb['close'] <= sl:  # Close-only SL
                        exit_px = sl; exit_type = 'SL'; break
                else:
                    if nb['low'] <= tp:
                        exit_px = tp; exit_type = 'TP'; break
                    if nb['close'] >= sl:
                        exit_px = sl; exit_type = 'SL'; break

            if exit_px is None:
                if len(remaining) > 0:
                    exit_px = remaining.iloc[-1]['close']
                    exit_type = 'TIME_EXIT'
                else:
                    exit_px = bar['close']
                    exit_type = 'TIME_EXIT'

            pnl_pips = (exit_px - entry) / PIP_SIZE * bias * risk_mult
            risk_pips = abs(entry - sl) / PIP_SIZE
            rr = pnl_pips / risk_pips if risk_pips > 0 else 0

            trades.append({
                'date_key': ar_info.get('date_key', ''),
                'tier': tier_name,
                'gear_tier': current_tier,
                'loop': loop_count,
                'bias': bias,
                'impulse_pips': round(imp_size, 1),
                'entry': entry, 'sl': sl, 'tp': tp, 'exit': exit_px,
                'pnl_pips': round(pnl_pips, 1),
                'rr': round(rr, 2),
                'type': exit_type,
                'risk_mult': risk_mult,
            })

            # LOOP RESET
            state = 'SEARCH'
            swing_origin = exit_px

            if loop_count >= MAX_LOOPS:
                break

            i += 1
            continue

        i += 1

    # Force close at end of session
    if state == 'IN_TRADE' and entry is not None:
        last_bar = session.iloc[-1]
        exit_px = last_bar['close']
        pnl_pips = (exit_px - entry) / PIP_SIZE * bias * risk_mult
        risk_pips = abs(entry - sl) / PIP_SIZE
        rr = pnl_pips / risk_pips if risk_pips > 0 else 0
        trades.append({
            'date_key': ar_info.get('date_key', ''),
            'tier': tier_name, 'gear_tier': current_tier,
            'loop': loop_count, 'bias': bias,
            'impulse_pips': round(imp_size, 1),
            'entry': entry, 'sl': sl, 'tp': tp, 'exit': exit_px,
            'pnl_pips': round(pnl_pips, 1),
            'rr': round(rr, 2), 'type': 'TIME_EXIT',
            'risk_mult': risk_mult,
        })

    return trades


def run_backtest():
    df = load_data()
    dates = sorted(df['est_date'].unique())
    print(f"Data: {len(df)} bars | {len(dates)} sessions")
    print("=" * 60)
    print("BLIND CHAIN v3 — Zero-Buffer + Gear Shift + Continuous Loop")
    print("=" * 60)

    from shared import compute_asian_range
    all_trades = []

    for dk in dates:
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        ar = compute_asian_range(db, dk)
        if ar is None or ar.get('tier') == 'NO_GO':
            continue
        ar['date_key'] = dk
        day_trades = run_blind_chain_day(db, ar)
        all_trades.extend(day_trades)

    if not all_trades:
        print("No trades generated")
        return

    tdf = pd.DataFrame(all_trades)
    total = len(tdf)
    wins = len(tdf[tdf['pnl_pips'] > 0])
    losses = len(tdf[tdf['pnl_pips'] <= 0])
    wr = wins / total * 100 if total > 0 else 0
    total_pnl = tdf['pnl_pips'].sum()
    avg_win = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].mean() if wins > 0 else 0
    avg_loss = tdf[tdf['pnl_pips'] <= 0]['pnl_pips'].mean() if losses > 0 else 0
    gross_win = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum() if wins > 0 else 0
    gross_loss = abs(tdf[tdf['pnl_pips'] <= 0]['pnl_pips'].sum()) if losses > 0 else 0
    pf = gross_win / gross_loss if gross_loss > 0 else float('inf')
    avg_rr = tdf['rr'].mean()

    tp_count = len(tdf[tdf['type'] == 'TP'])
    sl_count = len(tdf[tdf['type'] == 'SL'])
    time_count = len(tdf[tdf['type'].str.startswith('TIME')])

    print(f"\nTotal trades: {total}")
    print(f"Win Rate: {wr:.1f}% ({wins}/{total})")
    print(f"Total PnL: {total_pnl:.1f} pips")
    print(f"Avg Win: {avg_win:.1f}p | Avg Loss: {avg_loss:.1f}p")
    print(f"Profit Factor: {pf:.2f} | Avg R:R: {avg_rr:.2f}")
    print(f"\nExits: TP={tp_count} ({tp_count/total*100:.1f}%) | SL={sl_count} ({sl_count/total*100:.1f}%) | TIME={time_count} ({time_count/total*100:.1f}%)")

    # By tier
    print(f"\n--- By Tier ---")
    for tier in ['T1', 'T2', 'T3']:
        tt = tdf[tdf['tier'] == tier]
        if tt.empty: continue
        tw = len(tt[tt['pnl_pips'] > 0])
        ttl = len(tt)
        twr = tw / ttl * 100 if ttl > 0 else 0
        tpnl = tt['pnl_pips'].sum()
        tpf = tt[tt['pnl_pips'] > 0]['pnl_pips'].sum() / abs(tt[tt['pnl_pips'] <= 0]['pnl_pips'].sum()) if abs(tt[tt['pnl_pips'] <= 0]['pnl_pips'].sum()) > 0 else float('inf')
        print(f"  {tier}: {ttl} tr | WR:{twr:.1f}% | PnL:{tpnl:.1f}p | PF:{tpf:.2f}")

    # By loop
    print(f"\n--- By Loop Number ---")
    for loop in range(1, MAX_LOOPS + 1):
        lt = tdf[tdf['loop'] == loop]
        if lt.empty: continue
        tw = len(lt[lt['pnl_pips'] > 0])
        ttl = len(lt)
        twr = tw / ttl * 100 if ttl > 0 else 0
        print(f"  Loop {loop}: {ttl} tr | WR:{twr:.1f}% | PnL:{lt['pnl_pips'].sum():.1f}p")

    # Gear Shift stats
    print(f"\n--- Gear Shift Override ---")
    for gt in tdf['gear_tier'].unique():
        gt_trades = tdf[tdf['gear_tier'] == gt]
        if gt_trades.empty: continue
        gw = len(gt_trades[gt_trades['pnl_pips'] > 0])
        print(f"  {gt}: {len(gt_trades)} tr | WR:{gw/len(gt_trades)*100:.1f}% | avg impulse:{gt_trades['impulse_pips'].mean():.1f}p")

    # Regime filter
    failed = len(tdf[tdf['risk_mult'] == 0.5])
    if failed > 0:
        print(f"\nRegime filter: {failed} trades at 50% size ({failed/total*100:.1f}%)")

    date_trades = tdf.groupby('date_key').size()
    print(f"\nSessions with trades: {len(date_trades)}")
    print(f"Avg trades/session (when trading): {date_trades.mean():.1f}")
    print(f"Max loops in one session: {date_trades.max()}")

    return tdf


if __name__ == '__main__':
    run_backtest()

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
[[Backtest Campaign V3 Results]]
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
