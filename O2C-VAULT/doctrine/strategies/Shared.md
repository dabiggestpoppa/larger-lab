# Shared

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #strategies

```python
﻿"""
CEREBUS Strategy Reconstruction - Shared Infrastructure
========================================================
Common utilities: Asian Range calc, P90 detection, data loading, backtest runner
"""
import sys, json, time
from datetime import datetime, timedelta, date
from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# CONSTANTS (from manual quick reference card)
# ============================================================
P90_THRESHOLDS = {
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9,
    9: 6.2, 10: 6.2,
}

# Tier parameters for EUR/USD
TIERS = {
    'T1': {'max_ar': 20, 'au': 10, 'trigger': 12, 'sl_buffer': 5},
    'T2': {'max_ar': 30, 'au': 12, 'trigger': 15, 'sl_buffer': 6},
    'T3': {'max_ar': 45, 'au': 15, 'trigger': 19, 'sl_buffer': 8},
}

ASIAN_START_EST = 19   # 7PM EST
ASIAN_END_EST = 3      # 3AM EST (lock time)
P90_WINDOW_START_EST = 2   # 2AM EST
P90_WINDOW_END_EST = 11    # 11AM EST
HARD_EXIT_EST = 12     # 12PM EST
EST_OFFSET = -5

DATA_PATH = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2026.csv")
REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
STRATEGIES_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
TRACKER_PATH = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategy_reconstruction_tracker.md")

REPORTS_DIR.mkdir(exist_ok=True)
STRATEGIES_DIR.mkdir(exist_ok=True)


def load_data():
    """Load and preprocess M5 data"""
    df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])
    df['est_hour'] = (df['timestamp'].dt.hour + EST_OFFSET) % 24
    df['est_date'] = (df['timestamp'] - pd.Timedelta(hours=5)).dt.date
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['bar_id'] = range(len(df))
    df['body'] = abs(df['close'] - df['open'])
    df['body_dir'] = np.sign(df['close'] - df['open'])  # +1 bullish, -1 bearish
    df['range'] = df['high'] - df['low']
    print(f"Loaded {len(df):,} bars | {df['timestamp'].min()} to {df['timestamp'].max()}")
    return df


def compute_asian_range(df, date_key):
    """
    Compute Asian Range for a given EST trading date.
    Asian session: 7PM EST (prev calendar day) to 3AM EST (current calendar day).
    
    For trading date D, the Asian range is:
    - Previous day (D-1): bars with est_hour >= 19 (7PM-11:59PM EST)
    - Current day (D):   bars with est_hour < 3 (12AM-2:59AM EST)
    
    Returns: dict with ah, al, ar_pips, tier
    """
    from datetime import date, timedelta
    
    if isinstance(date_key, str):
        date_key = date.fromisoformat(date_key)
    
    prev_key = date_key - timedelta(days=1)
    
    # Previous evening 7PM+ and current morning <3AM
    asian_bars = df[
        ((df['est_date'] == prev_key) & (df['est_hour'] >= ASIAN_START_EST)) |
        ((df['est_date'] == date_key) & (df['est_hour'] < ASIAN_END_EST))
    ]
    
    if len(asian_bars) == 0:
        return None
    
    ah = asian_bars['high'].max()
    al = asian_bars['low'].min()
    ar_pips = (ah - al) * 10000.0
    
    # Classify tier
    if ar_pips < 20:
        tier = 'T1'
    elif ar_pips < 30:
        tier = 'T2'
    elif ar_pips <= 45:
        tier = 'T3'
    else:
        tier = 'NO_GO'
    
    return {'ah': ah, 'al': al, 'ar_pips': ar_pips, 'tier': tier}


def detect_p90(bar_row, threshold_lookup=None):
    """
    Check if a bar qualifies as a P90 candle.
    P90 = body >= threshold for that EST hour, close outside Asian band
    Returns: True/False, direction (+1/-1), body_pips
    """
    if threshold_lookup is None:
        threshold_lookup = P90_THRESHOLDS
    
    eh = int(bar_row['est_hour'])
    if eh not in threshold_lookup:
        return False, 0, 0.0
    
    body_pips = bar_row['body'] * 10000.0
    threshold = threshold_lookup[eh]
    
    if body_pips < threshold:
        return False, 0, body_pips
    
    direction = int(bar_row['body_dir'])
    return True, direction, body_pips


def classify_p90_relative_to_barrier(row, ah, al):
    """
    Check if P90 closed outside Asian barrier.
    Manual rule: CLOSES ONLY — wicks do not count.
    Returns: 'above' (bullish break), 'below' (bearish break), or 'inside'
    """
    if row['close'] > ah:
        return 'above'
    elif row['close'] < al:
        return 'below'
    return 'inside'


def compute_fib_levels(activation_price, direction, ar_pips):
    """
    Compute key Fibonacci extension levels based on manual.
    direction: +1 for LONG, -1 for SHORT
    Returns dict of level_name -> price
    """
    ar_price = ar_pips / 10000.0
    levels = {}
    
    # Asian range targets
    levels['ar_25'] = activation_price + direction * ar_price * 0.25
    levels['ar_50'] = activation_price + direction * ar_price * 0.50
    
    # Fib extension states (from manual)
    for fib_pct in [0.68, 1.00, 1.27, 1.38, 1.50, 1.618, 1.68, 2.00, 2.61, 3.00]:
        key = f'fib_{str(fib_pct).replace(".", "_")}'
        levels[key] = activation_price + direction * ar_price * fib_pct
    
    return levels


def run_backtest_for_days(df, strategy_func, strategy_name, start_date=None, end_date=None):
    """
    Generic backtest runner.
    strategy_func: function(df_day_bars, asian_info, day_state) -> list of trade dicts
    Returns: DataFrame of trades
    """
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
        
        # Compute Asian range
        ar_info = compute_asian_range(df, date_key)
        if ar_info is None:
            continue
        
        trades = strategy_func(day_bars, ar_info)
        if trades:
            all_trades.extend(trades)
        days_processed += 1
    
    if not all_trades:
        return pd.DataFrame()
    
    trades_df = pd.DataFrame(all_trades)
    return trades_df, days_processed


def compute_stats(trades_df, strategy_name):
    """Compute summary statistics matching manual's metrics"""
    if len(trades_df) == 0:
        return {'error': 'no trades'}
    
    wins = trades_df[trades_df['pnl_pips'] > 0]
    losses = trades_df[trades_df['pnl_pips'] <= 0]
    
    total_trades = len(trades_df)
    win_rate = len(wins) / total_trades * 100.0
    gross_profit = wins['pnl_pips'].sum() if len(wins) > 0 else 0
    gross_loss = abs(losses['pnl_pips'].sum()) if len(losses) > 0 else 0.001
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    total_pips = trades_df['pnl_pips'].sum()
    avg_r = trades_df['pnl_pips'].mean()
    
    return {
        'strategy': strategy_name,
        'total_trades': total_trades,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': round(win_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'total_pips': round(total_pips, 1),
        'avg_pips_per_trade': round(avg_r, 2),
        'gross_profit_pips': round(gross_profit, 1),
        'gross_loss_pips': round(gross_loss, 1),
    }


def write_report(strategy_name, stats, target_stats, trades_df):
    """Write reconstruction report comparing to manual stats"""
    report_path = REPORTS_DIR / f"{strategy_name}_reconstruction_report.md"
    
    comparison = []
    if 'win_rate_pct' in target_stats and 'win_rate_pct' in stats:
        diff = stats['win_rate_pct'] - target_stats['win_rate_pct']
        comparison.append(f"| Win Rate | {target_stats['win_rate_pct']}% | {stats['win_rate_pct']}% | {diff:+.1f}% |")
    
    if 'profit_factor' in target_stats and 'profit_factor' in stats:
        diff = stats['profit_factor'] - target_stats['profit_factor']
        comparison.append(f"| Profit Factor | {target_stats['profit_factor']} | {stats['profit_factor']} | {diff:+.2f} |")
    
    if 'total_pips' in target_stats and 'total_pips' in stats:
        diff = stats['total_pips'] - target_stats['total_pips']
        comparison.append(f"| Total Pips | {target_stats['total_pips']} | {stats['total_pips']} | {diff:+.1f} |")
    
    report = f"""# {strategy_name} - Reconstruction Report

## Target Stats (from Manual)
{json.dumps(target_stats, indent=2)}

## Backtest Results
{json.dumps(stats, indent=2)}

## Comparison
| Metric | Target | Actual | Delta |
|--------|--------|--------|-------|
{chr(10).join(comparison) if comparison else '| N/A | N/A | N/A |'}

## Verdict
"""
    # 5% tolerance check
    passed = True
    if 'win_rate_pct' in target_stats and 'win_rate_pct' in stats:
        if abs(stats['win_rate_pct'] - target_stats['win_rate_pct']) > 5.0:
            passed = False
            report += f"- **FAIL**: Win rate off by {abs(stats['win_rate_pct'] - target_stats['win_rate_pct']):.1f}% (tolerance: 5%)\n"
    
    if passed:
        report += "**PASS**: All metrics within 5% tolerance\n"
    else:
        report += "**NEEDS CALIBRATION**: Some metrics outside 5% tolerance\n"
    
    report += f"\nGenerated: {datetime.now().isoformat()}\n"
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Also save trades CSV
    trades_path = REPORTS_DIR / f"{strategy_name}_trades.csv"
    trades_df.to_csv(trades_path, index=False)
    
    # Save stats JSON  
    stats_path = REPORTS_DIR / f"{strategy_name}_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    return report_path

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
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
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
