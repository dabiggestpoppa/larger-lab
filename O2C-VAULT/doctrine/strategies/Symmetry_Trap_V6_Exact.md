# Symmetry Trap V6 Exact

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""
Symmetry Trap v6 — EXACT manual pseudocode translation
======================================================
Built line-by-line from page 145 of CEREBUS FX v4 Manual.

No interpretation. No "improvements". Just what the manual says.
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date, datetime
import pandas as pd

# ═══ CONFIG (from manual page 2 + page 145) ═══
# Tier config: ar_max, atomic, trigger
# atomic = Atomic Unit for target sizing
# trigger = Tier Threshold for impulse detection
TIERS = {
    'T1': {'ar_max': 20, 'atomic': 10, 'trigger': 12},
    'T2': {'ar_max': 30, 'atomic': 12, 'trigger': 15},
    'T3': {'ar_max': 45, 'atomic': 15, 'trigger': 19},
}

AU1 = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'


def run_session(day_bars, ah, al, ar_pips, date_key):
    """
    Exact implementation of manual's run_distribution_trap per-session loop.
    Session = 3AM to 12PM EST.
    """
    trades = []
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3:
        return trades

    params = TIERS[tier]
    atomic = params['atomic']
    ar_val = ar_pips / 10000.0

    # === Filter to session window ===
    # Manual: bias_window is 3AM-12PM
    session = day_bars[(day_bars['est_hour'] >= 3) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(session) < 5:
        return trades

    # === LAYER 1: LOCK BIAS ===
    # Manual: first M5 close outside Asian band
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

    asian_high = ah
    asian_low = al

    # === LAYER 2: ATOMIC ENTRY ===
    # Manual pseudocode (exact):
    # for idx, row in post_bias.iterrows():
    #   if bias==1 and row['close']>row['open'] and body>=atomic*0.5:
    #     if next_candle['close'] < next_candle['open']:
    #       entry = next_candle['close']; break
    #   if bias==-1 and row['close']<row['open'] and body>=atomic*0.5:
    #     if next_candle['close'] > next_candle['close']:
    #       entry = next_candle['close']; break

    entry = None
    entry_idx = None

    for j in range(bias_idx + 1, len(session)):
        row = session.iloc[j]
        body = abs(row['close'] - row['open']) * 10000.0  # pips

        if bias == 1 and row['close'] > row['open'] and body >= atomic * 0.5:
            if j + 1 < len(session):
                next_candle = session.iloc[j + 1]
                if next_candle['close'] < next_candle['open']:
                    entry = next_candle['close']
                    entry_idx = j + 1
                    break

        if bias == -1 and row['close'] < row['open'] and body >= atomic * 0.5:
            if j + 1 < len(session):
                next_candle = session.iloc[j + 1]
                if next_candle['close'] > next_candle['open']:
                    entry = next_candle['close']
                    entry_idx = j + 1
                    break

    if entry is None:
        return trades

    # === LAYER 3: DISTRIBUTION TARGETS ===
    # Manual:
    # t25  = asian_edge + ar * 0.25 * bias
    # t50  = asian_edge + ar * 0.50 * bias
    # t100 = asian_edge + ar * 1.00 * bias
    #
    # asian_edge = the band that was broken for bias
    # For LONG (bias=1): asian_edge = asian_high
    # For SHORT (bias=-1): asian_edge = asian_low

    if bias == 1:
        asian_edge = asian_high
        sl = asian_low  # Close back inside = exit
    else:
        asian_edge = asian_low
        sl = asian_high

    t25  = asian_edge + ar_val * 0.25 * bias
    t50  = asian_edge + ar_val * 0.50 * bias
    t100 = asian_edge + ar_val * 1.00 * bias

    # === MANAGEMENT ===
    # Manual: SL = M5 close back inside Asian band (81.2% rule — not wick, close only)
    # Hard exit = 12:00 PM EST
    # Partial closes: 50% at T25, 40% at T50, 10% runner at T100

    pos = 1.0
    pnl_pips = 0.0
    t25_hit = False
    t50_hit = False

    for k in range(entry_idx + 1, len(session)):
        row = session.iloc[k]
        c = row['close']
        h = row['high']
        l = row['low']

        # Hard exit 12PM
        if row['est_hour'] >= 12:
            if pos > 0:
                pnl_pips += (c - entry) * bias * 10000.0 * pos
                pos = 0
            break

        # SL: close back inside Asian band
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

        # Target management
        if bias == 1:
            if h >= t25 and not t25_hit:
                pnl_pips += (t25 - entry) * 10000.0 * 0.50
                pos -= 0.50
                t25_hit = True
            if h >= t50 and not t50_hit:
                pnl_pips += (t50 - entry) * 10000.0 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and h >= t100:
                pnl_pips += (t100 - entry) * 10000.0 * pos
                pos = 0
                break
        else:
            if l <= t25 and not t25_hit:
                pnl_pips += (entry - t25) * 10000.0 * 0.50
                pos -= 0.50
                t25_hit = True
            if l <= t50 and not t50_hit:
                pnl_pips += (entry - t50) * 10000.0 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and l <= t100:
                pnl_pips += (entry - t100) * 10000.0 * pos
                pos = 0
                break

    if pnl_pips != 0 or pos < 1.0:
        trades.append({
            'date': str(date_key), 'pnl_pips': pnl_pips,
            'tier': tier, 'ar': ar_pips, 'bias': bias,
            'asian_edge': asian_edge, 'entry': entry,
            't25': t25, 't50': t50, 't100': t100, 'sl': sl,
            't25_hit': t25_hit, 't50_hit': t50_hit,
        })

    return trades


def run_backtest(df, start_date=None, end_date=None):
    if start_date: df = df[df['est_date'] >= start_date]
    if end_date:   df = df[df['est_date'] <= end_date]

    all_trades = []
    days = 0

    for dk in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue

        ar = compute_asian_range(df, dk)
        if ar is None: continue

        tr = run_session(day_bars, ar['ah'], ar['al'], ar['ar_pips'], dk)
        if tr: all_trades.extend(tr)
        days += 1

    return all_trades, days


if __name__ == "__main__":
    print("=" * 60)
    print("SYMMETRY TRAP v6 — EXACT Manual Pseudocode")
    print("=" * 60)

    df = load_data()

    # First: trace a few individual days
    print(f"\n--- Individual Day Traces ---\n")
    trace_dates = [date(2024, 1, 15), date(2024, 1, 16), date(2024, 2, 1),
                   date(2024, 3, 1), date(2024, 4, 1), date(2024, 5, 1)]

    for dk in trace_dates:
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        tier = classify_tier(ar['ar_pips'])
        if tier == 'NO_GO': continue
        tr = run_session(db, ar['ah'], ar['al'], ar['ar_pips'], dk)
        if tr:
            t = tr[0]
            d = "LONG" if t['bias']==1 else "SHORT"
            print(f"{dk} {d} {tier} AR={t['ar']:.1f}p")
            print(f"  edge={t['asian_edge']:.5f} entry={t['entry']:.5f} sl={t['sl']:.5f}")
            print(f"  T25={t['t25']:.5f} T50={t['t50']:.5f} T100={t['t100']:.5f}")
            print(f"  Result: {t['pnl_pips']:.1f}p (T25={'Y' if t['t25_hit'] else 'N'} T50={'Y' if t['t50_hit'] else 'N'})")
        else:
            # Check what happened
            ah, al = ar['ah'], ar['al']
            window = db[(db['est_hour']>=3)&(db['est_hour']<12)].reset_index(drop=True)
            bias = 0
            for i in range(len(window)):
                if window.iloc[i]['close'] > ah: bias=1; break
                if window.iloc[i]['close'] < al: bias=-1; break
            if bias == 0:
                print(f"{dk} NO BIAS (AR={ar['ar_pips']:.1f}p)")
            else:
                print(f"{dk} bias={'LONG' if bias==1 else 'SHORT'} but no entry (AR={ar['ar_pips']:.1f}p)")
        print()

    # Full backtest
    print(f"\n--- Full Backtest ---")
    for pname, sd, ed in [("2024-2025", date(2024,1,1), date(2025,12,31)),
                            ("Full 2023H2-2026H1", date(2023,7,1), date(2026,5,31))]:
        tr, days = run_backtest(df, sd, ed)
        if not tr: print(f"{pname}: No trades"); continue
        tdf = pd.DataFrame(tr)
        n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins = tdf[tdf['pnl_pips']>0]['pnl_pips'].sum()
        losses = abs(tdf[tdf['pnl_pips']<0]['pnl_pips'].sum())
        pf = wins/losses if losses > 0 else 99

        print(f"\n{pname}: Days={days} Trades={n}")
        print(f"WR: {wr:.1f}% (manual 83-86%) | PF: {pf:.2f} (manual 3.82)")
        print(f"Total: {total:.1f}p | Avg: {total/n:.1f}p | Wins: {wins:.1f}p | Losses: {losses:.1f}p")

        for t in ['T1','T2','T3']:
            tf = tdf[tdf['tier']==t]
            if len(tf)==0: continue
            print(f"  {t}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, "
                  f"avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

        t25_rate = tdf['t25_hit'].mean() * 100
        t50_rate = tdf['t50_hit'].mean() * 100
        print(f"  T25 hit rate: {t25_rate:.1f}% | T50 hit rate: {t50_rate:.1f}%")

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
