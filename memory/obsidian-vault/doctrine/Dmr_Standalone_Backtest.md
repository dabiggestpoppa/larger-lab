# Dmr Standalone Backtest

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #engines

```python
"""
DMR Standalone Backtest — CSV-Based
====================================
Mean Reversion strategy: enters at 200% Deep State, TP at origin, SL at 220%.
Operates independently from P90 engine (no nesting).
Uses CSV bar data — no MT5 connection required.
"""
import csv, sys, os
from datetime import datetime, timedelta, time
from collections import defaultdict
from pathlib import Path

ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENGINES_DIR)
from p90_engine import Bar, classify_tier, DEFAULT_TIER_CONFIG, get_p90_threshold

PIP_SIZE = 0.0001
EST_OFFSET = -5

ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 2
TRADING_END_H = 11
HARD_EXIT_H = 17

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%Y.%m.%d %H:%M",
    "%Y.%m.%d %H:%M:%S",
]

def parse_ts(raw):
    raw = raw.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None

def load_csv(path):
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_raw = (row.get("timestamp") or row.get("Timestamp") or row.get("time")
                      or row.get("Time") or row.get("date") or row.get("Date")
                      or row.get("datetime") or row.get("Datetime"))
            if not ts_raw:
                continue
            ts = parse_ts(ts_raw)
            if ts is None:
                continue
            o = row.get("open") or row.get("Open") or row.get("OPEN")
            h = row.get("high") or row.get("High") or row.get("HIGH")
            l = row.get("low") or row.get("Low") or row.get("LOW")
            c = row.get("close") or row.get("Close") or row.get("CLOSE")
            if any(v is None for v in (o,h,l,c)):
                continue
            bars.append(Bar(timestamp=ts, open=float(o), high=float(h),
                           low=float(l), close=float(c)))
    bars.sort(key=lambda b: b.timestamp)
    return bars

def est_hour(dt):
    return (dt.hour + EST_OFFSET) % 24

def session_date(dt):
    h = est_hour(dt)
    if h >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()

def group_sessions(bars):
    sessions = defaultdict(lambda: {"asian": [], "trading": []})
    for bar in bars:
        sd = session_date(bar.timestamp)
        h = est_hour(bar.timestamp)
        if h >= ASIAN_START_H or h < ASIAN_END_H:
            sessions[sd]["asian"].append(bar)
        elif TRADING_START_H <= h < HARD_EXIT_H:
            sessions[sd]["trading"].append(bar)
    for sd in sessions:
        sessions[sd]["asian"].sort(key=lambda b: b.timestamp)
        sessions[sd]["trading"].sort(key=lambda b: b.timestamp)
    return dict(sorted(sessions.items()))

def run_backtest(bars):
    sessions = group_sessions(bars)
    trades = []
    total_bars = 0

    for sd, sess in sessions.items():
        asian = sess["asian"]
        trading = sess["trading"]
        total_bars += len(trading)

        if len(trading) < 5:
            continue

        # Asian Range
        ah = max(b.high for b in asian) if asian else 0
        al = min(b.low for b in asian) if asian else 99999
        if ah <= 0 or al >= 99999:
            continue
        ar_pips = (ah - al) / PIP_SIZE

        # Tier classification
        tier_name, au_pips, trigger_pips = classify_tier(ar_pips, DEFAULT_TIER_CONFIG)
        if tier_name == "NO_GO":
            continue

        # DMR: Find first P90 impulse in trading window
        p90_found = False
        p90_close = 0.0
        p90_body = 0.0
        p90_body_abs = 0.0
        p90_direction = 0  # 1=bull, -1=bear
        p90_hour = 0

        for bar in trading:
            eh = est_hour(bar.timestamp)
            if eh < TRADING_START_H or eh >= TRADING_END_H:
                continue

            body = bar.close - bar.open
            body_abs = abs(body)
            threshold = get_p90_threshold(eh) * PIP_SIZE

            if body_abs >= threshold:
                p90_found = True
                p90_close = bar.close
                p90_body = body
                p90_body_abs = body_abs
                p90_direction = 1 if body > 0 else -1
                p90_hour = eh
                break

        if not p90_found:
            continue

        # Deep State = 200% of P90 body from activation (close)
        deep_state = p90_close + p90_direction * 2.0 * p90_body_abs

        # Kill Switch SL = 220% of P90 body from activation
        # DMR enters AGAINST P90 direction at DS
        # For bull P90: DMR SHORT at DS. SL = activation + 220% body (above DS)
        # For bear P90: DMR LONG at DS. SL = activation - 220% body (below DS)
        sl_distance = 2.2 * p90_body_abs
        if p90_direction == 1:  # Bull P90 -> DMR SHORT
            dmr_sl = p90_close + sl_distance  # above
            dmr_tp = p90_close  # return to origin (entry of P90)
            dmr_entry = deep_state
            direction_str = "SHORT"
        else:  # Bear P90 -> DMR LONG
            dmr_sl = p90_close - sl_distance  # below
            dmr_tp = p90_close  # return to origin
            dmr_entry = deep_state
            direction_str = "LONG"

        # Scan for DMR trigger (price reaching DS) and outcome
        dmr_triggered = False
        trade_result = None
        exit_price = 0.0
        exit_time = None

        for bar in trading:
            # Skip bars before P90 candle
            if not dmr_triggered:
                if p90_direction == 1:
                    # Bull P90 -> DS above -> check if HIGH reaches DS
                    if bar.high >= deep_state:
                        dmr_triggered = True
                        continue
                else:
                    # Bear P90 -> DS below -> check if LOW reaches DS
                    if bar.low <= deep_state:
                        dmr_triggered = True
                        continue

            if dmr_triggered:
                # Check TP hit first (price returns to origin)
                if p90_direction == 1:  # SHORT -> TP when price falls to origin
                    if bar.low <= dmr_tp:
                        trade_result = "TP"
                        exit_price = dmr_tp
                        exit_time = bar.timestamp
                        break
                    # SL hit (price rises above SL)
                    if bar.high >= dmr_sl:
                        trade_result = "SL"
                        exit_price = dmr_sl
                        exit_time = bar.timestamp
                        break
                else:  # LONG -> TP when price rises to origin
                    if bar.high >= dmr_tp:
                        trade_result = "TP"
                        exit_price = dmr_tp
                        exit_time = bar.timestamp
                        break
                    # SL hit (price falls below SL)
                    if bar.low <= dmr_sl:
                        trade_result = "SL"
                        exit_price = dmr_sl
                        exit_time = bar.timestamp
                        break

                # Hard exit at trading end
                eh = est_hour(bar.timestamp)
                if eh >= HARD_EXIT_H:
                    trade_result = "HARD_EXIT"
                    exit_price = bar.close
                    exit_time = bar.timestamp
                    break

        if trade_result is None:
            # Trade still open at end of data — skip
            continue

        # Calculate PnL
        if direction_str == "SHORT":
            pnl_pips = (dmr_entry - exit_price) / PIP_SIZE
        else:
            pnl_pips = (exit_price - dmr_entry) / PIP_SIZE

        trades.append({
            "date": str(sd),
            "direction": direction_str,
            "result": trade_result,
            "pnl_pips": round(pnl_pips, 1),
            "p90_hour": p90_hour,
            "tier": tier_name,
            "ar_pips": round(ar_pips, 1),
            "p90_body_pips": round(p90_body_abs / PIP_SIZE, 1),
            "entry": dmr_entry,
            "sl": dmr_sl,
            "tp": dmr_tp,
            "entry_time": sd,
            "exit_time": str(exit_time),
        })

    return trades, len(sessions), total_bars

def compute_stats(trades):
    if not trades:
        return {}
    pnls = [t["pnl_pips"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = len(pnls)
    wr = len(wins)/total*100 if total > 0 else 0
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0.001
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = sum(pnls)/total if total > 0 else 0

    # Max DD
    eq = peak = max_dd = 0
    for p in pnls:
        eq += p
        if eq > peak: peak = eq
        dd = peak - eq
        if dd > max_dd: max_dd = dd

    # Per-year
    yearly = defaultdict(list)
    for t in trades:
        year = t["date"][:4]
        yearly[year].append(t["pnl_pips"])

    # Per-hour
    hourly = defaultdict(list)
    for t in trades:
        hourly[t["p90_hour"]].append(t["pnl_pips"])

    # Per-tier
    by_tier = defaultdict(list)
    for t in trades:
        by_tier[t["tier"]].append(t["pnl_pips"])

    # Long/Short
    lt = [t["pnl_pips"] for t in trades if t["direction"]=="LONG"]
    st = [t["pnl_pips"] for t in trades if t["direction"]=="SHORT"]

    # Streaks
    cw = cl = mcw = mcl = 0
    for p in pnls:
        if p > 0: cw += 1; cl = 0; mcw = max(mcw, cw)
        elif p < 0: cl += 1; cw = 0; mcl = max(mcl, cl)

    # Sharpe
    from statistics import mean, stdev
    m = mean(pnls)
    s = stdev(pnls)
    sharpe = (m/s * (252**0.5)) if s > 0 else 0

    avg_win = mean(wins) if wins else 0
    avg_loss = abs(mean(losses)) if losses else 0
    r_mult = avg_win/avg_loss if avg_loss > 0 else 0

    return {
        "total": total, "wins": len(wins), "losses": len(losses),
        "wr": round(wr,1), "gross_profit": round(gross_profit,1),
        "gross_loss": round(-gross_loss,1), "pf": round(pf,2),
        "sharpe": round(sharpe,2), "avg_trade": round(avg_trade,2),
        "r_mult": round(r_mult,2), "max_dd": round(max_dd,1),
        "avg_win": round(avg_win,1), "avg_loss": round(avg_loss,1),
        "long_trades": len(lt), "long_wr": round(sum(1 for p in lt if p>0)/len(lt)*100,1) if lt else 0,
        "long_pnl": round(sum(lt),1),
        "short_trades": len(st), "short_wr": round(sum(1 for p in st if p>0)/len(st)*100,1) if st else 0,
        "short_pnl": round(sum(st),1),
        "max_consec_wins": mcw, "max_consec_losses": mcl,
        "yearly": {y: {"trades": len(v), "pnl": round(sum(v),1),
                       "wr": round(sum(1 for p in v if p>0)/len(v)*100,1)} for y,v in yearly.items()},
        "hourly": {h: {"trades": len(v), "pnl": round(sum(v),1),
                       "wr": round(sum(1 for p in v if p>0)/len(v)*100,1)} for h,v in hourly.items()},
        "tier": {t: {"trades": len(v), "pnl": round(sum(v),1),
                     "wr": round(sum(1 for p in v if p>0)/len(v)*100,1)} for t,v in by_tier.items()},
    }

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else r"quant-lab\data\EURUSDPRO_M5_2023_2026.csv"
    print(f"[DMR BT] Loading: {csv_path}")
    bars = load_csv(csv_path)
    print(f"[DMR BT] Loaded {len(bars):,} bars")
    trades, n_sessions, n_bars = run_backtest(bars)
    print(f"[DMR BT] Sessions: {n_sessions} | Bars processed: {n_bars:,}")
    print(f"[DMR BT] DMR trades: {len(trades)}")

    stats = compute_stats(trades)
    print()
    print("=" * 60)
    print("DMR (DEEP MEAN REVERSION) — STANDALONE BACKTEST")
    print("=" * 60)
    for k, v in stats.items():
        if isinstance(v, dict):
            print(f"\n  --- {k.upper()} ---")
            for k2, v2 in v.items():
                print(f"  {k2}: {v2}")
        else:
            print(f"  {k}: {v}")

    # Save trades CSV
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(out_dir, exist_ok=True)
    trades_csv = os.path.join(out_dir, "dmr_standalone_trades.csv")
    with open(trades_csv, "w", newline="") as f:
        if trades:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
    print(f"\nTrades saved: {trades_csv}")

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
