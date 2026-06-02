# P90 Usdchf Backtest

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #engines

```python
"""
P90 CASCADE Backtest — USDCHF.PRO
Runs P90 engine (CASCADE variant) on USDCHF 3Y data for verification.
"""
import sys, os, csv
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
os.environ['PYTHONPATH'] = 'quant-lab'
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from p90_engine import (
    P90Engine, P90Variant, TradeDirection, Bar,
    DEFAULT_P90_THRESHOLDS, DEFAULT_TIER_CONFIG,
)

DATA_FILE = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5.csv'
SYMBOL = 'USDCHF.PRO'
PIP_SIZE = 0.0001

def price_to_pips(price_diff):
    return round(price_diff / PIP_SIZE, 1)

def pips_to_price(pips):
    return pips * PIP_SIZE

def load_bars(path):
    bars = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bars.append({
                'ts': int(row['timestamp']),
                'dt': datetime.fromtimestamp(int(row['timestamp'])),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            })
    bars.sort(key=lambda x: x['ts'])
    return bars

def get_est_offset(dt):
    return (dt.hour + (-5)) % 24

def run_backtest(bars, max_ar=45.0, min_ar=3.0):
    trades = []
    total_bars = len(bars)
    
    # Group bars by EST date
    days = {}
    for b in bars:
        est_h = get_est_offset(b['dt'])
        # EST date: if hour < 5, it's previous calendar day
        if est_h < 5:
            est_date = (b['dt'] - timedelta(days=1)).date()
        else:
            est_date = b['dt'].date()
        if est_date not in days:
            days[est_date] = []
        days[est_date].append(b)
    
    for day_date, day_bars in sorted(days.items()):
        # Find Asian Range (19:00-2:59 EST = 00:00 to 07:59 UTC)
        asian_bars = [b for b in day_bars if get_est_offset(b['dt']) >= 19 or get_est_offset(b['dt']) < 3]
        if not asian_bars:
            continue
        
        asian_high = max(b['high'] for b in asian_bars)
        asian_low = min(b['low'] for b in asian_bars)
        ar_pips = price_to_pips(asian_high - asian_low)
        
        if ar_pips < min_ar or ar_pips > max_ar:
            continue
        
        # Trading window: 2AM-11:59AM EST
        trading_bars = [b for b in day_bars if 2 <= get_est_offset(b['dt']) < 12]
        if not trading_bars:
            continue
        
        engine = P90Engine(
            pip_size=PIP_SIZE,
            p90_config=DEFAULT_P90_THRESHOLDS,
            tier_config=DEFAULT_TIER_CONFIG,
            symbol=SYMBOL,
        )
        engine.initialize_session(asian_high, asian_low)
        if not engine.session_active:
            continue
        
        in_trade = False
        entry_price = sl_price = tp_price = None
        current_direction = current_variant = None
        
        for b in trading_bars:
            bar = Bar(timestamp=b['dt'], open=b['open'], high=b['high'], low=b['low'], close=b['close'])
            signal = engine.process_bar(bar)
            
            if in_trade and current_direction is not None:
                # Check exit conditions using locally stored values
                if current_direction == TradeDirection.LONG:
                    if b['high'] >= tp_price:
                        pnl = price_to_pips(tp_price - entry_price)
                        trades.append({
                            'date': day_date, 'direction': 'LONG', 'variant': current_variant.value if current_variant else 'UNKNOWN',
                            'entry': entry_price, 'exit': tp_price, 'pnl_pips': pnl,
                            'result': 'TP', 'ar': ar_pips, 'tier': engine.tier_name,
                        })
                        in_trade = False; entry_price = sl_price = tp_price = None
                        current_direction = current_variant = None
                    elif b['low'] <= sl_price:
                        pnl = price_to_pips(sl_price - entry_price)
                        trades.append({
                            'date': day_date, 'direction': 'LONG', 'variant': current_variant.value if current_variant else 'UNKNOWN',
                            'entry': entry_price, 'exit': sl_price, 'pnl_pips': pnl,
                            'result': 'SL', 'ar': ar_pips, 'tier': engine.tier_name,
                        })
                        in_trade = False; entry_price = sl_price = tp_price = None
                        current_direction = current_variant = None
                elif current_direction == TradeDirection.SHORT:
                    if b['low'] <= tp_price:
                        pnl = price_to_pips(entry_price - tp_price)
                        trades.append({
                            'date': day_date, 'direction': 'SHORT', 'variant': current_variant.value if current_variant else 'UNKNOWN',
                            'entry': entry_price, 'exit': tp_price, 'pnl_pips': pnl,
                            'result': 'TP', 'ar': ar_pips, 'tier': engine.tier_name,
                        })
                        in_trade = False; entry_price = sl_price = tp_price = None
                        current_direction = current_variant = None
                    elif b['high'] >= sl_price:
                        pnl = price_to_pips(entry_price - sl_price)
                        trades.append({
                            'date': day_date, 'direction': 'SHORT', 'variant': current_variant.value if current_variant else 'UNKNOWN',
                            'entry': entry_price, 'exit': sl_price, 'pnl_pips': pnl,
                            'result': 'SL', 'ar': ar_pips, 'tier': engine.tier_name,
                        })
                        in_trade = False; entry_price = sl_price = tp_price = None
                        current_direction = current_variant = None
            
            if signal and signal.event == 'ENTRY' and not in_trade:
                entry_price = signal.entry_price
                sl_price = signal.sl_price
                tp_price = signal.tp_price
                current_direction = signal.direction
                current_variant = signal.variant
                in_trade = True
    
    return trades


def print_report(trades):
    if not trades:
        print("NO TRADES")
        return
    
    total = len(trades)
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    wr = len(wins) / total * 100 if total > 0 else 0
    
    total_pips = sum(t['pnl_pips'] for t in trades)
    gross_profit = sum(t['pnl_pips'] for t in wins)
    gross_loss = abs(sum(t['pnl_pips'] for t in losses))
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    avg_win = gross_profit / len(wins) if wins else 0
    avg_loss = gross_loss / len(losses) if losses else 0
    
    # Variant breakdown
    variants = {}
    for t in trades:
        v = t['variant']
        if v not in variants:
            variants[v] = {'trades': 0, 'wins': 0, 'pips': 0}
        variants[v]['trades'] += 1
        variants[v]['pips'] += t['pnl_pips']
        if t['pnl_pips'] > 0:
            variants[v]['wins'] += 1
    
    # Direction breakdown
    longs = [t for t in trades if t['direction'] == 'LONG']
    shorts = [t for t in trades if t['direction'] == 'SHORT']
    
    # Max DD
    cumulative = [0]
    for t in trades:
        cumulative.append(cumulative[-1] + t['pnl_pips'])
    peak = cumulative[0]
    max_dd = 0
    for c in cumulative:
        if c > peak:
            peak = c
        dd = peak - c
        if dd > max_dd:
            max_dd = dd
    
    print("=" * 60)
    print(f"  P90 CASCADE BACKTEST — {SYMBOL}")
    print("=" * 60)
    print(f"  Total Trades:     {total}")
    print(f"  Win Rate:         {wr:.1f}% ({len(wins)}W / {len(losses)}L)")
    print(f"  Total P&L:        {total_pips:+.1f} pips")
    print(f"  Gross Profit:     +{gross_profit:.1f} pips")
    print(f"  Gross Loss:       -{gross_loss:.1f} pips")
    print(f"  Profit Factor:    {pf:.2f}")
    print(f"  Avg Win:          {avg_win:.1f} pips")
    print(f"  Avg Loss:         -{avg_loss:.1f} pips")
    print(f"  Max Drawdown:     -{max_dd:.1f} pips")
    print(f"  Avg R:R:          {total_pips/total:.2f}R" if total > 0 else "")
    
    print(f"\n  ── Variant Breakdown ──")
    for v, d in sorted(variants.items()):
        vwr = d['wins']/d['trades']*100 if d['trades'] > 0 else 0
        print(f"  {v:12s}: {d['trades']:4d} trades | {vwr:.1f}% WR | {d['pips']:+.1f}p")
    
    print(f"\n  ── Direction ──")
    long_wr = sum(1 for t in longs if t['pnl_pips']>0)/len(longs)*100 if longs else 0
    short_wr = sum(1 for t in shorts if t['pnl_pips']>0)/len(shorts)*100 if shorts else 0
    print(f"  LONG:  {len(longs):4d} trades | {long_wr:.1f}% WR | {sum(t['pnl_pips'] for t in longs):+.1f}p")
    print(f"  SHORT: {len(shorts):4d} trades | {short_wr:.1f}% WR | {sum(t['pnl_pips'] for t in shorts):+.1f}p")
    print("=" * 60)


if __name__ == '__main__':
    print(f"Loading {DATA_FILE}...")
    bars = load_bars(DATA_FILE)
    print(f"Loaded {len(bars)} bars")
    print(f"Date range: {bars[0]['dt']} to {bars[-1]['dt']}")
    
    trades = run_backtest(bars)
    print_report(trades)
    
    # Save trades CSV
    out = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\P90_CASCADE_USDCHF_trades.csv'
    with open(out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date','direction','variant','entry','exit','pnl_pips','result','ar','tier'])
        writer.writeheader()
        writer.writerows(trades)
    print(f"\nTrades saved: {out}")

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
[[Backtest Campaign Status 20260531]]
[[Backtest Campaign V3 Results]]
[[Backtest Phase Status]]
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
