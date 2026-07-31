# Blind Chain V2 Debug

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
"""Quick debug: run v1 and v2 on same data and compare"""
import sys, io
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TIERS = {
    'T1': {'ar_max': 20, 'trigger': 12, 'au': 10},
    'T2': {'ar_max': 30, 'trigger': 15, 'au': 12},
    'T3': {'ar_max': 45, 'trigger': 19, 'au': 15},
}
AU1 = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'


def get_p90_thresh(est_hour):
    h = int(est_hour)
    if h < 2: return 4.1
    if h > 11: return 6.2
    return AU1.get(h, 4.6)


# Run v1-like logic (exactly from blind_chain_engine.py)
def run_v1(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']; al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    date_key = ar_info['date_key']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3: return trades
    params = TIERS[tier]
    window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(window) < 10: return trades

    anchor = None
    for i in range(len(window)):
        row = window.iloc[i]
        eh = row['est_hour']
        if eh < 2 or eh >= 11: continue
        body = abs(row['close'] - row['open']) * 10000
        if body >= get_p90_thresh(eh):
            if row['close'] > ah or row['close'] < al:
                anchor = {'idx': i, 'row': row, 'body': body,
                          'dir': 1 if row['close'] > row['open'] else -1}
                break
    if anchor is None: return trades

    anchor_dir = anchor['dir']
    anchor_close = anchor['row']['close']
    impulse_extreme = anchor_close; impulse_idx = anchor['idx']
    for i in range(anchor['idx'] + 1, len(window)):
        row = window.iloc[i]
        if anchor_dir == 1:
            if row['high'] > impulse_extreme:
                impulse_extreme = row['high']; impulse_idx = i
        else:
            if row['low'] < impulse_extreme:
                impulse_extreme = row['low']; impulse_idx = i

    impulse_distance = abs(impulse_extreme - anchor_close) * 10000
    if impulse_distance < params['trigger']: return trades

    if anchor_dir == 1:
        gold_high = impulse_extreme - (impulse_distance * 0.32 / 10000)
        gold_low = impulse_extreme - (impulse_distance * 0.50 / 10000)
    else:
        gold_low = impulse_extreme + (impulse_distance * 0.32 / 10000)
        gold_high = impulse_extreme + (impulse_distance * 0.50 / 10000)

    cascade_entry = None; cascade_idx = None; cascade_body = None

    for i in range(impulse_idx + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 11: break
        in_gold = gold_low <= row['close'] <= gold_high
        if not in_gold:
            in_gold = (gold_low <= row['high'] and row['low'] <= gold_high)
        if not in_gold: continue
        body = abs(row['close'] - row['open']) * 10000
        is_bullish = row['close'] > row['open']
        is_bearish = row['close'] < row['open']
        if body >= 4.5:
            if anchor_dir == 1 and is_bullish:
                cascade_entry = row['close']; cascade_idx = i; cascade_body = body; break
            elif anchor_dir == -1 and is_bearish:
                cascade_entry = row['close']; cascade_idx = i; cascade_body = body; break

    if cascade_entry is None: return trades
    sl_dist = cascade_body * 1.68 / 10000
    if anchor_dir == 1:
        sl = cascade_entry - sl_dist
        target = cascade_entry + (impulse_distance / 10000)
    else:
        sl = cascade_entry + sl_dist
        target = cascade_entry - (impulse_distance / 10000)

    pos = 1.0; pnl = 0.0
    for i in range(cascade_idx + 1, len(window)):
        row = window.iloc[i]; c = row['close']; h = row['high']; l = row['low']
        if row['est_hour'] >= 12:
            if pos > 0: pnl += (c - cascade_entry) * anchor_dir * 10000 * pos - 0.5 * pos; pos = 0
            break
        if anchor_dir == 1:
            if c < sl:
                if pos > 0: pnl += (c - cascade_entry) * 10000 * pos - 0.5 * pos; pos = 0
                break
            if h >= target and pos > 0: pnl += (target - cascade_entry) * 10000 * pos - 0.5 * pos; pos = 0; break
        else:
            if c > sl:
                if pos > 0: pnl += (cascade_entry - c) * 10000 * pos - 0.5 * pos; pos = 0
                break
            if l <= target and pos > 0: pnl += (cascade_entry - target) * 10000 * pos - 0.5 * pos; pos = 0; break
    if pnl != 0 or pos < 1.0:
        trades.append({'date': str(date_key), 'pnl_pips': pnl, 'tier': tier, 'version': 'v1'})
    return trades


# Run v2-like logic 
def run_v2(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']; al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    date_key = ar_info['date_key']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3: return trades
    params = TIERS[tier]
    window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(window) < 10: return trades

    anchor = None
    for i in range(len(window)):
        row = window.iloc[i]
        eh = row['est_hour']
        if eh < 2 or eh >= 11: continue
        body = abs(row['close'] - row['open']) * 10000
        if body >= get_p90_thresh(eh):
            if row['close'] > ah or row['close'] < al:
                anchor = {'idx': i, 'row': row, 'body': body,
                          'dir': 1 if row['close'] > row['open'] else -1}
                break
    if anchor is None: return trades

    anchor_dir = anchor['dir']
    anchor_close = anchor['row']['close']
    impulse_extreme = anchor_close; impulse_idx = anchor['idx']
    for i in range(anchor['idx'] + 1, len(window)):
        row = window.iloc[i]
        if anchor_dir == 1:
            if row['high'] > impulse_extreme:
                impulse_extreme = row['high']; impulse_idx = i
        else:
            if row['low'] < impulse_extreme:
                impulse_extreme = row['low']; impulse_idx = i

    impulse_distance = abs(impulse_extreme - anchor_close) * 10000
    if impulse_distance < params['trigger']: return trades

    # Goldilocks with percentage params (32, 50)
    g_low_pct, g_high_pct = 32, 50
    if anchor_dir == 1:
        gold_high = impulse_extreme - (impulse_distance * g_low_pct / 100 / 10000)
        gold_low  = impulse_extreme - (impulse_distance * g_high_pct / 100 / 10000)
    else:
        gold_low  = impulse_extreme + (impulse_distance * g_low_pct / 100 / 10000)
        gold_high = impulse_extreme + (impulse_distance * g_high_pct / 100 / 10000)

    cascade_entry = None; cascade_idx = None; cascade_body = None

    for i in range(impulse_idx + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 11: break
        in_gold = gold_low <= row['close'] <= gold_high
        if not in_gold:
            in_gold = (gold_low <= row['high'] and row['low'] <= gold_high)
        if not in_gold: continue
        body = abs(row['close'] - row['open']) * 10000
        is_bullish = row['close'] > row['open']
        is_bearish = row['close'] < row['open']
        if body >= 4.5:
            if anchor_dir == 1 and is_bullish:
                cascade_entry = row['close']; cascade_idx = i; cascade_body = body; break
            elif anchor_dir == -1 and is_bearish:
                cascade_entry = row['close']; cascade_idx = i; cascade_body = body; break

    if cascade_entry is None: return trades
    
    # Just return a diagnostic trade
    trades.append({'date': str(date_key), 'pnl_pips': 0, 'tier': tier, 'version': 'v2', 
                   'impulse': impulse_distance, 'gold_low': gold_low, 'gold_high': gold_high})
    return trades


if __name__ == "__main__":
    df = load_data()
    print("Running v1 and v2 comparison...")
    
    v1_trades = []; v2_trades = []
    v1_days_with_cascade = 0; v2_days_with_cascade = 0
    
    for dk in sorted(df['est_date'].unique()):
        if dk < date(2024,1,1) or dk > date(2024,12,31): continue
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(db) < 10: continue
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        ar['date_key'] = dk
        
        t1 = run_v1(db, ar)
        t2 = run_v2(db, ar)
        if t1: v1_trades.extend(t1); v1_days_with_cascade += 1
        if t2: v2_trades.extend(t2); v2_days_with_cascade += 1
    
    print(f"\n2024: v1 cascade days = {v1_days_with_cascade}, v2 cascade days = {v2_days_with_cascade}")
    
    if v1_trades:
        v1df = pd.DataFrame([t for t in v1_trades if t.get('version')=='v1'])
        print(f"v1 trades with PnL: {len(v1df)}")
        if len(v1df) > 0 and 'pnl_pips' in v1df.columns:
            print(f"v1 WR: {(v1df['pnl_pips']>0).mean()*100:.1f}%")
    
    if v2_trades:
        v2df = pd.DataFrame(v2_trades)
        print(f"\nV2 diagnostic trades (found cascade):")
        print(f"Total: {len(v2df)}")
        if len(v2df) > 0:
            print("Sample:")
            for _, r in v2df.head(5).iterrows():
                print(f"  {r['date']} impulse={r.get('impulse',0):.1f}p "
                      f"gold=[{r.get('gold_low',0):.5f}, {r.get('gold_high',0):.5f}] "
                      f"width={(r.get('gold_high',0)-r.get('gold_low',0))*10000:.1f}p")

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
[[Sage Audit 20260531 Environment Utilization V2]]
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
