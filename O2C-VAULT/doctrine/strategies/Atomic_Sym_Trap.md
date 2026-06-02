# Atomic Sym Trap

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
﻿"""
Atomic Symmetry Trap — OCC Extreme / OAU Engine
=================================================
Pure implementation of MAD's state machine spec.
SL = exact OCC extreme (zero buffer, close-only invalidation)
TP = 1 AU (OAU — Opposite Atomic Unit)
Fib confluence: 38.2%-50% retracement for entry confirmation
Gear Shift Override for intraday tier reclassification
"""
import sys
from datetime import datetime, timedelta
import numpy as np

ASSET_CONFIG = {
    'USDCHF.PRO': {
        'pip_mult': 10000,
        't1_max_ar': 18, 't2_max_ar': 24, 't3_max_ar': 36,
        't1_trig': 13, 't2_trig': 18, 't3_trig': 24, 'mt25_trig': 36,
        't1_au': 11, 't2_au': 15, 't3_au': 18, 'mt25_au': 25,
        'gear_t1_t2': 13, 'gear_t1_t3': 24, 'gear_t2_t3': 24, 'gear_t3_mt25': 25,
        'min_ar': 5, 'max_ar': 60,
    },
    'EURUSD.PRO': {
        'pip_mult': 10000,
        't1_max_ar': 20, 't2_max_ar': 30, 't3_max_ar': 45,
        't1_trig': 12, 't2_trig': 15, 't3_trig': 19, 'mt25_trig': 45,
        't1_au': 10, 't2_au': 12, 't3_au': 15, 'mt25_au': 25,
        'gear_t1_t2': 15, 'gear_t1_t3': 19, 'gear_t2_t3': 19, 'gear_t3_mt25': 25,
        'min_ar': 3, 'max_ar': 45,
    },
}

EST_OFFSET = -5
HARD_EXIT = 17
def eh(dt): return (dt.hour + EST_OFFSET) % 24

def pt(pips, pm): return pips / pm
def pp(price, pm): return price * pm


def run_session(db, symbol='USDCHF.PRO'):
    cfg = ASSET_CONFIG.get(symbol, ASSET_CONFIG['USDCHF.PRO'])
    pm = cfg['pip_mult']
    trades = []

    # Asian Range
    asian = [b for b in db if b['est_h'] >= 19 or b['est_h'] < 3]
    if len(asian) < 2: return trades
    ah = max(b['h'] for b in asian)
    al = min(b['l'] for b in asian)
    ar = pp(ah - al, pm)
    if ar < cfg['min_ar'] or ar > cfg['max_ar']: return trades

    # Classify tier
    if ar <= cfg['t1_max_ar']: tier, au, trig = 'T1', cfg['t1_au'], cfg['t1_trig']
    elif ar <= cfg['t2_max_ar']: tier, au, trig = 'T2', cfg['t2_au'], cfg['t2_trig']
    elif ar <= cfg['t3_max_ar']: tier, au, trig = 'T3', cfg['t3_au'], cfg['t3_trig']
    else: return trades

    bias_win = [b for b in db if 3 <= b['est_h'] < 11]
    bias, bi = 0, -1
    for i, b in enumerate(bias_win):
        if b['c'] > ah: bias, bi = 1, i; break
        if b['c'] < al: bias, bi = -1, i; break
    if bias == 0: return trades

    post = bias_win[bi:]
    if not post: return trades

    # State machine variables
    state = 'SEARCH'
    swing_origin = post[0]['c']
    impulse_dir = 0
    impulse_ext = None
    impulse_size = 0.0
    kill_switch = None
    fib_low = fib_high = None
    active_au = au
    base_tier = tier
    shifted_tier = None
    loop = 0

    i = 0
    while i < len(post) and loop < 50:
        b = post[i]
        if b['est_h'] >= HARD_EXIT: break

        up_move = pp(b['h'] - swing_origin, pm)
        dn_move = pp(swing_origin - b['l'], pm)

        if state == 'SEARCH':
            trig_pm = trig * pm / pm  # trig in pips
            if up_move >= trig:
                impulse_dir = 1
                impulse_ext = b['h']
                impulse_size = up_move
                kill_switch = impulse_ext - pt(up_move * 0.80, pm) * pm / pm
                fib_low = min(swing_origin, impulse_ext)
                fib_high = max(swing_origin, impulse_ext)
                fib_range = fib_high - fib_low
                fib_382 = fib_low + fib_range * 0.382
                fib_500 = fib_low + fib_range * 0.50
                fl, fh = min(fib_382, fib_500), max(fib_382, fib_500)
                # Gear shift
                shifted = base_tier
                if base_tier == 'T1':
                    if up_move >= cfg['gear_t1_t3']: shifted = 'T3'
                    elif up_move >= cfg['gear_t1_t2']: shifted = 'T2'
                elif base_tier == 'T2' and up_move >= cfg['gear_t2_t3']: shifted = 'T3'
                elif base_tier == 'T3' and up_move >= cfg['gear_t3_mt25']: shifted = 'MT25'
                shifted_tier = shifted if shifted != base_tier else None
                active_au = {'T1': cfg['t1_au'], 'T2': cfg['t2_au'], 'T3': cfg['t3_au'], 'MT25': cfg['mt25_au']}[shifted]
                state = 'WAIT_RETRACE'
                i += 1; continue

            if dn_move >= trig:
                impulse_dir = -1
                impulse_ext = b['l']
                impulse_size = dn_move
                kill_switch = impulse_ext + pt(dn_move * 0.80, pm) * pm / pm
                fib_low = min(swing_origin, impulse_ext)
                fib_high = max(swing_origin, impulse_ext)
                fib_range = fib_high - fib_low
                fib_382 = fib_low + fib_range * 0.382
                fib_500 = fib_low + fib_range * 0.50
                fl, fh = min(fib_382, fib_500), max(fib_382, fib_500)
                shifted = base_tier
                if base_tier == 'T1':
                    if dn_move >= cfg['gear_t1_t3']: shifted = 'T3'
                    elif dn_move >= cfg['gear_t1_t2']: shifted = 'T2'
                elif base_tier == 'T2' and dn_move >= cfg['gear_t2_t3']: shifted = 'T3'
                elif base_tier == 'T3' and dn_move >= cfg['gear_t3_mt25']: shifted = 'MT25'
                shifted_tier = shifted if shifted != base_tier else None
                active_au = {'T1': cfg['t1_au'], 'T2': cfg['t2_au'], 'T3': cfg['t3_au'], 'MT25': cfg['mt25_au']}[shifted]
                state = 'WAIT_RETRACE'
                i += 1; continue

        elif state == 'WAIT_RETRACE':
            # Kill switch
            if impulse_dir == 1 and b['c'] < kill_switch:
                state = 'SEARCH'; swing_origin = b['c']; loop += 1; i += 1; continue
            if impulse_dir == -1 and b['c'] > kill_switch:
                state = 'SEARCH'; swing_origin = b['c']; loop += 1; i += 1; continue

            # Retrace check: 1 AU or fib zone
            if impulse_dir == 1:
                pullback = pp(impulse_ext - b['l'], pm)
            else:
                pullback = pp(b['h'] - impulse_ext, pm)

            retrace_pct = pullback / impulse_size if impulse_size > 0 else 0
            au_penetrated = pullback >= active_au * 0.8
            fib_penetrated = 0.382 <= retrace_pct <= 0.500

            if au_penetrated or fib_penetrated:
                state = 'WAIT_OCC'

        elif state == 'WAIT_OCC':
            is_bull = b['c'] > b['o']
            is_bear = b['c'] < b['o']
            trade_dir = None

            # OCC: candle closing in direction of the original bias (confirming reversal)
            if impulse_dir == 1 and is_bear:
                trade_dir = 'SHORT'  # Bull impulse, bear close = SHORT
            elif impulse_dir == -1 and is_bull:
                trade_dir = 'LONG'   # Bear impulse, bull close = LONG

            if trade_dir:
                entry = b['c']
                sl = impulse_ext  # exact OCC extreme
                tp_val = pt(active_au, pm)
                if trade_dir == 'LONG':
                    tp = entry + tp_val
                else:
                    tp = entry - tp_val

                # Validate geometry
                if trade_dir == 'LONG' and (sl >= entry or tp <= entry):
                    state = 'SEARCH'; swing_origin = b['c']; loop += 1; i += 1; continue
                if trade_dir == 'SHORT' and (sl <= entry or tp >= entry):
                    state = 'SEARCH'; swing_origin = b['c']; loop += 1; i += 1; continue

                # Scan for exit
                for rb in post[i+1:]:
                    if rb['est_h'] >= HARD_EXIT:
                        ep = rb['c']
                        pnl = pp(ep - entry, pm) if trade_dir == 'LONG' else pp(entry - ep, pm)
                        trades.append({'dir': trade_dir, 'entry': round(entry,5), 'exit': round(ep,5),
                                       'sl': round(sl,5), 'tp': round(tp,5), 'pnl_pips': round(pnl,1),
                                       'reason': 'EOD', 'tier': base_tier, 'shift': shifted_tier,
                                       'au': active_au, 'loop': loop})
                        break
                    if trade_dir == 'LONG':
                        if rb['h'] >= tp:
                            pnl = pp(tp - entry, pm)
                            trades.append({'dir': trade_dir, 'entry': round(entry,5), 'exit': round(tp,5),
                                           'sl': round(sl,5), 'tp': round(tp,5), 'pnl_pips': round(pnl,1),
                                           'reason': 'TP', 'tier': base_tier, 'shift': shifted_tier,
                                           'au': active_au, 'loop': loop}); break
                        if rb['c'] <= sl:
                            pnl = pp(rb['c'] - entry, pm)
                            trades.append({'dir': trade_dir, 'entry': round(entry,5), 'exit': round(rb['c'],5),
                                           'sl': round(sl,5), 'tp': round(tp,5), 'pnl_pips': round(pnl,1),
                                           'reason': 'SL', 'tier': base_tier, 'shift': shifted_tier,
                                           'au': active_au, 'loop': loop}); break
                    else:
                        if rb['l'] <= tp:
                            pnl = pp(entry - tp, pm)
                            trades.append({'dir': trade_dir, 'entry': round(entry,5), 'exit': round(tp,5),
                                           'sl': round(sl,5), 'tp': round(tp,5), 'pnl_pips': round(pnl,1),
                                           'reason': 'TP', 'tier': base_tier, 'shift': shifted_tier,
                                           'au': active_au, 'loop': loop}); break
                        if rb['c'] >= sl:
                            pnl = pp(entry - rb['c'], pm)
                            trades.append({'dir': trade_dir, 'entry': round(entry,5), 'exit': round(rb['c'],5),
                                           'sl': round(sl,5), 'tp': round(tp,5), 'pnl_pips': round(pnl,1),
                                           'reason': 'SL', 'tier': base_tier, 'shift': shifted_tier,
                                           'au': active_au, 'loop': loop}); break

                state = 'SEARCH'
                swing_origin = trades[-1]['exit'] if trades else b['c']
                loop += 1
                i += 1
                continue

        i += 1

    return trades


def load_bars(symbol, count=250000):
    import MetaTrader5 as mt5
    if not mt5.initialize(): return None
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    mt5.shutdown()
    if bars is None or len(bars) == 0: return None
    result = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        result.append({'dt': dt, 'est_h': eh(dt), 'o': bar['open'], 'h': bar['high'], 'l': bar['low'], 'c': bar['close']})
    return result


def group_sessions(bars):
    sessions = {}
    for bar in bars:
        d = bar['dt'].date()
        if bar['est_h'] < 3: d = (bar['dt'] + timedelta(hours=EST_OFFSET)).date()
        sessions.setdefault(str(d), []).append(bar)
    return sessions


def run_backtest(symbol='USDCHF.PRO'):
    print('=' * 60)
    print('ATOMIC SYMMETRY TRAP — OCC Extreme/OAU Engine')
    print('SL=OCC extreme (zero buffer) | TP=1 AU | Fib 38.2-50% confluence')
    print(f'Symbol: {symbol}')
    print('=' * 60)

    bars = load_bars(symbol, 250000)
    if not bars: print('No data'); return []
    print(f'Bars: {len(bars):,}')
    sessions = group_sessions(bars)
    dates = sorted(sessions.keys())
    print(f'Sessions: {len(dates)}')

    all_trades = []
    for idx, d in enumerate(dates):
        trades = run_session(sessions[d], symbol)
        all_trades.extend(trades)
        if (idx+1) % 100 == 0:
            wr, pnl, n = _stats(all_trades)
            print(f'  [{idx+1}/{len(dates)}] {n} tr, {wr:.1f}% WR, {pnl:+.0f}p')

    _print_results(all_trades, symbol)
    return all_trades


def _stats(trades):
    if not trades: return 0, 0, 0
    wins = sum(1 for t in trades if t['pnl_pips'] > 0)
    return wins/len(trades)*100, sum(t['pnl_pips'] for t in trades), len(trades)


def _print_results(trades, symbol):
    if not trades: print('No trades'); return
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    total = sum(t['pnl_pips'] for t in trades)
    wr = len(wins)/len(trades)*100
    avg_w = np.mean([t['pnl_pips'] for t in wins]) if wins else 0
    avg_l = np.mean([t['pnl_pips'] for t in losses]) if losses else 0
    pf = abs(sum(t['pnl_pips'] for t in wins)/sum(t['pnl_pips'] for t in losses)) if losses and sum(t['pnl_pips'] for t in losses) != 0 else 0
    exp = total/len(trades)
    tp_t = [t for t in trades if t['reason'] == 'TP']
    sl_t = [t for t in trades if t['reason'] == 'SL']
    eod_t = [t for t in trades if t['reason'] == 'EOD']
    longs = [t for t in trades if t['dir'] == 'LONG']
    shorts = [t for t in trades if t['dir'] == 'SHORT']
    tiers = {}
    for t in trades: tiers.setdefault(t['tier'], []).append(t)
    loops = {}
    for t in trades: loops.setdefault(t.get('loop',0), []).append(t)

    print(f'\n{"="*60}\nRESULTS\n{"="*60}')
    print(f'  Trades:        {len(trades)} ({len(wins)}W / {len(losses)}L)')
    print(f'  Win Rate:      {wr:.1f}%')
    print(f'  Total PnL:     {total:+.1f} pips')
    print(f'  Avg Win:       {avg_w:+.1f}p  |  Avg Loss: {avg_l:+.1f}p')
    print(f'  Payoff:        {abs(avg_w/max(avg_l,0.01)):.2f}')
    print(f'  Profit Factor: {pf:.2f}')
    print(f'  Expectancy:    {exp:+.2f} pips/trade')
    print(f'  TP:  {len(tp_t)} ({len(tp_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in tp_t):+.0f}p')
    print(f'  SL:  {len(sl_t)} ({len(sl_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in sl_t):+.0f}p')
    print(f'  EOD: {len(eod_t)} ({len(eod_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in eod_t):+.0f}p')
    print(f'  Long:  {len(longs)} tr  WR={sum(1 for t in longs if t["pnl_pips"]>0)/max(len(longs),1)*100:.1f}%')
    print(f'  Short: {len(shorts)} tr  WR={sum(1 for t in shorts if t["pnl_pips"]>0)/max(len(shorts),1)*100:.1f}%')
    print(f'  ---')
    for ti in sorted(tiers.keys()):
        tt = tiers[ti]; tw = sum(1 for t in tt if t['pnl_pips'] > 0)
        print(f'  {ti}: {len(tt)} tr  WR={tw/len(tt)*100:.1f}%  PnL={sum(t["pnl_pips"] for t in tt):+.0f}p')
    print(f'  ---')
    for lo in sorted(loops.keys()):
        lt = loops[lo]; lw = sum(1 for t in lt if t['pnl_pips'] > 0)
        print(f'  Loop {lo}: {len(lt)} tr  WR={lw/len(lt)*100:.1f}%  PnL={sum(t["pnl_pips"] for t in lt):+.0f}p')


if __name__ == '__main__':
    sym = sys.argv[1] if len(sys.argv) > 1 else 'USDCHF.PRO'
    run_backtest(sym)

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
