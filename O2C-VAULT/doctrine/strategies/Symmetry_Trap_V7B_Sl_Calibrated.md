# Symmetry Trap V7B Sl Calibrated

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""
Symmetry Trap v7b — Strategy-Level Calibration for M5
=======================================================
Findings from v7a (SL calibration):
- Changing SL distance does NOT fix the edge — WR stays ~25-36% across ALL SL modes
- Only 26% of losses come from SL hits. 74% come from 12PM hard exit or T25-only partials.
- Root cause: After 50% T25 partial, remaining 50% often never reaches T50 (67% hit).
  The remaining position gets closed at session end at a loss.

NEW APPROACH: Rethink the entire trade management on M5:

v7b_1: Move to breakeven after T25 hit (SL = entry after T25 partial)
v7b_2: Trailing SL to T25 level after T25 hit (lock in 50% profit as min)
v7b_3: Full position at T25 (100% exit, no runner) — reduce avg win but increase WR
v7b_4: 70/30 split instead of 50/40/10 (more at T25, less runner)
v7b_5: Wider targets — T25=0.33*AR, T50=0.66*AR, T100=1.0*AR
v7b_6: Combination: v7b_2 (trailing to entry) + wider AR targets

The thesis: the 50/40/10 target structure gives large losses on the runner.
If we can ensure T25+partial breakeven, losses shrink dramatically.
"""
import sys, io
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TIERS = {
    'T1': {'ar_max': 20, 'atomic': 10, 'trigger': 12},
    'T2': {'ar_max': 30, 'atomic': 12, 'trigger': 15},
    'T3': {'ar_max': 45, 'atomic': 15, 'trigger': 19},
}

SPREAD = 0.3  # EURUSD spread cost per trade in pips


def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'


def run_session_v7b(day_bars, ah, al, ar_pips, date_key, mode):
    """
    Variants:
      'baseline'   — v6 exact: 50/40/10, SL=opposite band
      'breakeven'  — After T25, move SL to entry. After T50, move SL to T25.
      'trail_t25'  — After T25 hit, move SL to T25 price level (lock partial)
      'full_t25'   — 100% exit at T25, no runner
      '70_30'      — 70% T25, 30% runner (no T50)
      'wide_tgts'  — T33/T66/T100 instead of T25/T50/T100
      'combined'   — breakeven + wider targets + 70/20/10
    """
    trades = []
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3:
        return trades

    params = TIERS[tier]
    atomic = params['atomic']
    ar_val = ar_pips / 10000.0

    session = day_bars[(day_bars['est_hour'] >= 3) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(session) < 5:
        return trades

    # LAYER 1: BIAS
    bias = 0
    bias_idx = -1
    for i in range(len(session)):
        row = session.iloc[i]
        if row['close'] > ah:
            bias = 1; bias_idx = i; break
        if row['close'] < al:
            bias = -1; bias_idx = i; break
    if bias == 0:
        return trades

    # LAYER 2: ATOMIC ENTRY (same as v6)
    entry = None
    entry_idx = None
    for j in range(bias_idx + 1, len(session)):
        row = session.iloc[j]
        body = abs(row['close'] - row['open']) * 10000.0
        if bias == 1 and row['close'] > row['open'] and body >= atomic * 0.5:
            if j + 1 < len(session):
                next_c = session.iloc[j + 1]
                if next_c['close'] < next_c['open']:
                    entry = next_c['close']; entry_idx = j + 1; break
        if bias == -1 and row['close'] < row['open'] and body >= atomic * 0.5:
            if j + 1 < len(session):
                next_c = session.iloc[j + 1]
                if next_c['close'] > next_c['open']:
                    entry = next_c['close']; entry_idx = j + 1; break
    if entry is None:
        return trades

    # LAYER 3: TARGETS
    if bias == 1:
        asian_edge = ah
    else:
        asian_edge = al

    if mode == 'wide_tgts' or mode == 'combined':
        t33 = asian_edge + ar_val * 0.33 * bias
        t66 = asian_edge + ar_val * 0.66 * bias
        t100 = asian_edge + ar_val * 1.00 * bias
        use_t25 = False
    else:
        t33 = asian_edge + ar_val * 0.25 * bias
        t66 = asian_edge + ar_val * 0.50 * bias
        t100 = asian_edge + ar_val * 1.00 * bias
        use_t25 = True

    # Original SL
    if bias == 1:
        sl = al
    else:
        sl = ah

    # MANAGEMENT
    pos = 1.0
    pnl_pips = 0.0
    t33_hit = False
    t66_hit = False
    be_moved = False

    for k in range(entry_idx + 1, len(session)):
        row = session.iloc[k]
        c = row['close']
        h = row['high']
        l = row['low']

        if row['est_hour'] >= 12:
            if pos > 0:
                pnl_pips += (c - entry) * bias * 10000.0 * pos
                pos = 0
            break

        # SL check
        if bias == 1 and c < sl:
            if pos > 0:
                pnl_pips += (c - entry) * 10000.0 * pos
                pos = 0
            break
        if bias == -1 and c > sl:
            if pos > 0:
                pnl_pips += (entry - c) * 10000.0 * pos
                pos = 0
            break

        # Target management by mode
        if use_t25:
            t25 = t33; t50 = t66
        else:
            t25 = t33; t50 = t66

        if bias == 1:
            if h >= t25 and not t33_hit:
                if mode == 'full_t25':
                    pnl_pips += (t25 - entry) * 10000.0 * pos
                    pos = 0
                    t33_hit = True
                    break
                elif mode == '70_30':
                    pnl_pips += (t25 - entry) * 10000.0 * 0.70
                    pos -= 0.70
                    t33_hit = True
                    # No T50 — runner to T100
                elif mode in ('breakeven', 'combined'):
                    pnl_pips += (t25 - entry) * 10000.0 * 0.50
                    pos -= 0.50
                    t33_hit = True
                    sl = entry  # move SL to breakeven
                elif mode == 'trail_t25':
                    pnl_pips += (t25 - entry) * 10000.0 * 0.50
                    pos -= 0.50
                    t33_hit = True
                    sl = t25  # trail SL to T25 level
                else:  # baseline
                    pnl_pips += (t25 - entry) * 10000.0 * 0.50
                    pos -= 0.50
                    t33_hit = True

            elif (mode not in ('70_30', 'full_t25')) and h >= t50 and not t66_hit:
                if mode == 'breakeven':
                    pnl_pips += (t50 - entry) * 10000.0 * 0.40
                    pos -= 0.40
                    t66_hit = True
                    sl = t25  # trail SL to T25 after T50
                elif mode == 'combined':
                    pnl_pips += (t50 - entry) * 10000.0 * 0.20
                    pos -= 0.20
                    t66_hit = True
                    sl = entry  # tighter trail
                elif mode == 'trail_t25':
                    pnl_pips += (t50 - entry) * 10000.0 * 0.40
                    pos -= 0.40
                    t66_hit = True
                    sl = t25
                else:
                    pnl_pips += (t50 - entry) * 10000.0 * 0.40
                    pos -= 0.40
                    t66_hit = True

            if pos > 0 and h >= t100:
                pnl_pips += (t100 - entry) * 10000.0 * pos
                pos = 0
                break

        else:  # bias == -1
            if l <= t25 and not t33_hit:
                if mode == 'full_t25':
                    pnl_pips += (entry - t25) * 10000.0 * pos
                    pos = 0
                    t33_hit = True
                    break
                elif mode == '70_30':
                    pnl_pips += (entry - t25) * 10000.0 * 0.70
                    pos -= 0.70
                    t33_hit = True
                elif mode in ('breakeven', 'combined'):
                    pnl_pips += (entry - t25) * 10000.0 * 0.50
                    pos -= 0.50
                    t33_hit = True
                    sl = entry
                elif mode == 'trail_t25':
                    pnl_pips += (entry - t25) * 10000.0 * 0.50
                    pos -= 0.50
                    t33_hit = True
                    sl = t25
                else:
                    pnl_pips += (entry - t25) * 10000.0 * 0.50
                    pos -= 0.50
                    t33_hit = True

            elif (mode not in ('70_30', 'full_t25')) and l <= t50 and not t66_hit:
                if mode == 'breakeven':
                    pnl_pips += (entry - t50) * 10000.0 * 0.40
                    pos -= 0.40
                    t66_hit = True
                    sl = t25
                elif mode == 'combined':
                    pnl_pips += (entry - t50) * 10000.0 * 0.20
                    pos -= 0.20
                    t66_hit = True
                    sl = entry
                elif mode == 'trail_t25':
                    pnl_pips += (entry - t50) * 10000.0 * 0.40
                    pos -= 0.40
                    t66_hit = True
                    sl = t25
                else:
                    pnl_pips += (entry - t50) * 10000.0 * 0.40
                    pos -= 0.40
                    t66_hit = True

            if pos > 0 and l <= t100:
                pnl_pips += (entry - t100) * 10000.0 * pos
                pos = 0
                break

    if pnl_pips != 0 or pos < 1.0:
        trades.append({
            'date': str(date_key), 'pnl_pips': pnl_pips,
            'tier': tier, 'ar': ar_pips, 'bias': bias,
            't33_hit': t33_hit, 't66_hit': t66_hit, 'mode': mode,
        })
    return trades


def run_backtest_mode(df, mode, start_date=None, end_date=None):
    if start_date: df = df[df['est_date'] >= start_date]
    if end_date:   df = df[df['est_date'] <= end_date]
    all_trades = []
    days = 0
    for dk in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        tr = run_session_v7b(day_bars, ar['ah'], ar['al'], ar['ar_pips'], dk, mode)
        if tr: all_trades.extend(tr)
        days += 1
    return all_trades, days


if __name__ == "__main__":
    print("=" * 70)
    print("SYMMETRY TRAP v7b — Strategy-Level Management Calibration")
    print("=" * 70)
    df = load_data()
    start_date = date(2024, 1, 1)
    end_date = date(2025, 12, 31)

    modes = [
        ('baseline',  'v6 exact: 50/40/10 + SL=opposite band'),
        ('breakeven', '50/40/10, move SL to entry after T25'),
        ('trail_t25', '50/40/10, trail SL to T25 after hit'),
        ('full_t25',  '100% exit at T25 (no runner)'),
        ('70_30',     '70% T25, 30% runner (skip T50)'),
        ('wide_tgts', '50/40/10, targets at 33/66/100% of AR'),
        ('combined',  '70/20/10 + wider targets + SL=entry after T33'),
    ]

    results = []
    for mode, desc in modes:
        tr, days = run_backtest_mode(df, mode, start_date, end_date)
        if not tr:
            print(f"{mode}: No trades"); continue
        tdf = pd.DataFrame(tr)
        n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins / losses if losses > 0 else 99
        avg = total / n
        avg_win = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].mean() if (tdf['pnl_pips'] > 0).any() else 0
        avg_loss = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].mean()) if (tdf['pnl_pips'] < 0).any() else 0
        t33_rate = tdf['t33_hit'].mean() * 100
        t66_rate = tdf['t66_hit'].mean() * 100

        print(f"\nMode: {mode} — {desc}")
        print(f"  Tr={n} WR={wr:.1f}% PF={pf:.2f} Total={total:.1f}p Avg={avg:.1f}p")
        print(f"  AvgW={avg_win:.1f}p AvgL={avg_loss:.1f}p T33={t33_rate:.1f}% T66={t66_rate:.1f}%")

        for t in ['T1', 'T2', 'T3']:
            tf = tdf[tdf['tier'] == t]
            if len(tf) == 0: continue
            print(f"    {t}: {len(tf)} tr WR {(tf['pnl_pips'] > 0).mean()*100:.1f}% "
                  f"avg {tf['pnl_pips'].mean():.1f}p")

        results.append({
            'mode': mode, 'desc': desc, 'trades': n, 'days': days,
            'wr': wr, 'pf': pf, 'total': total, 'avg': avg,
            'avg_win': avg_win, 'avg_loss': avg_loss,
            't33_rate': t33_rate, 't66_rate': t66_rate,
        })

    print(f"\n{'='*70}")
    print("CALIBRATION SUMMARY")
    print(f"{'='*70}")
    print(f"{'Mode':<14} {'Tr':>4} {'WR%':>6} {'PF':>6} {'Total':>8} {'AvgW':>7} {'AvgL':>7}")
    for r in results:
        print(f"{r['mode']:<14} {r['trades']:>4} {r['wr']:>5.1f}% {r['pf']:>6.2f} "
              f"{r['total']:>7.1f}p {r['avg_win']:>6.1f}p {r['avg_loss']:>6.1f}p")

    if results:
        best = max(results, key=lambda x: x['pf'])
        print(f"\nBest: {best['mode']} — {best['desc']}")
        print(f"WR={best['wr']:.1f}% PF={best['pf']:.2f} Total={best['total']:.1f}p")

        # Full dataset run with best
        print(f"\n{'='*70}")
        print("WINNER — FULL DATASET RUN")
        for pname, sd, ed in [("2024-2025", date(2024,1,1), date(2025,12,31)),
                                ("Full 2023H2-2026H1", date(2023,7,1), date(2026,6,30))]:
            tr, days = run_backtest_mode(df, best['mode'], sd, ed)
            if not tr: print(f"{pname}: No trades"); continue
            tdf = pd.DataFrame(tr)
            n = len(tdf)
            wr = (tdf['pnl_pips'] > 0).mean() * 100
            total = tdf['pnl_pips'].sum()
            wins_g = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
            losses_g = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
            pf = wins_g / losses_g if losses_g > 0 else 99
            print(f"\n{pname}: Days={days} Trades={n}")
            print(f"WR: {wr:.1f}% (v6=37%, manual=83-86%) | PF: {pf:.2f} (v6=0.29, manual=3.82)")
            print(f"Total: {total:.1f}p | Avg: {total/n:.1f}p")

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
[[Dramatic]]
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
