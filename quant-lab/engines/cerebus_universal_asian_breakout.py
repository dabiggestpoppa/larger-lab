#!/usr/bin/env python3
"""
CEREBUS Universal Asian Breakout — Second-Order Pattern Backtest Engine
=========================================================================
Implements the Universal Asian Breakout & Second-Order Pattern model from
the Ontology (Attachment: cerebus_universal_asian_breakout.py & dt_ar_matrix.py).

Model:
  1. Asian Range (7PM-3AM EST): high/low define liquidity pool
  2. Breakout detection: first M5 close outside AR during London (3AM-12PM EST)
  3. Distribution nodes (deepest-first): 168% → 132% → Opp band → Midpoint
  4. OCC atomic trigger: within 60min of node hit, opposite candle close
  5. Entry at node level; SL = 168%±5p; TP = opposite band; hard exit 12PM EST

Outputs:
  - Per-asset WR/PF/PnL/MaxDD/trades-per-day
  - Per-tier (T1<20p / T2<35p / T3≥35p)
  - Per-node (Mid/132%/168%/Opp)
  - Per-hour (OCC trigger time)
  - OCC trigger hit-rate (% of nodes that produced an OCC within 60min)

References:
  - rekey_simple.py: loader, sessions, stats patterns
  - st_multi_asset_report.md: output format template
  - attachment scripts: node mapping, OCC logic, K-Means clustering
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

ASIAN_START_H_EST = 19  # 7 PM EST = start of Asian session
ASIAN_END_H_EST = 3    # 3 AM EST = end of Asian session
LONDON_START_H_EST = 3  # 3 AM EST = start of London session
LONDON_END_H_EST = 12   # 12 PM EST = hard exit time

FIB_REKEY = 1.32        # 132% breakout
FIB_168 = 1.68          # 168% level
SL_BUFFER_PIPS = 5      # SL = 168% ± 5 pips

OCC_SCAN_WINDOW = 60    # minutes to scan for OCC after node hit

# Tier classification (hardcoded, per attachment)
AR_TIER_1_MAX = 20.0    # T1: AR < 20 pips
AR_TIER_2_MAX = 35.0    # T2: AR < 35 pips
                        # T3: AR >= 35 pips


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Direction(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


class Node(Enum):
    """Distribution node types (deepest-first)."""
    LEVEL_168 = "168%"
    LEVEL_132 = "132%"
    OPP_BAND = "Opp"
    MIDPOINT = "Mid"


class TradeResult(Enum):
    TP_HIT = "TP_HIT"
    SL_HIT = "SL_HIT"
    TIMEOUT = "TIMEOUT"
    NO_ENTRY = "NO_ENTRY"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class SessionData:
    date: datetime.date
    asian_high: float
    asian_low: float
    asian_range: float
    asian_mid: float
    bias: Direction = Direction.FLAT

    @property
    def tier(self) -> str:
        """Classify tier based on AR (pips)."""
        ar_pips = self.asian_range
        if ar_pips < AR_TIER_1_MAX:
            return "T1"
        elif ar_pips < AR_TIER_2_MAX:
            return "T2"
        else:
            return "T3"


@dataclass
class Trade:
    direction: Direction
    entry_price: float
    sl_price: float
    tp_price: float
    entry_time: datetime
    node_hit: Node
    occ_time: Optional[datetime] = None
    result: Optional[TradeResult] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl_pips: float = 0.0
    mae: float = 0.0  # Maximum Adverse Excursion in pips


# ═══════════════════════════════════════════════════════════════════════════════
# CSV LOADING (reuse from rekey_simple.py)
# ═══════════════════════════════════════════════════════════════════════════════

_TIMESTAMP_FORMATS = [
    "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
    "%Y%m%d %H:%M:%S",
]


def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp '{raw}'")


def load_bars_csv(csv_path: str) -> List[Bar]:
    """Load M5 bars from CSV (handles comma/header/epoch time)."""
    bars: List[Bar] = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for row_num, row in enumerate(reader, start=2):
            clean_row = {k.strip().strip("<").strip(">"): v for k, v in row.items()}
            ts_raw = (clean_row.get("timestamp") or clean_row.get("Timestamp")
                      or clean_row.get("TIMESTAMP") or clean_row.get("datetime")
                      or clean_row.get("Datetime") or clean_row.get("DATETIME"))
            if ts_raw is None:
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME")
                           or clean_row.get("<TIME>"))
                if time_val and len(time_val.strip()) > 10:
                    ts_raw = time_val.strip()
            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE")
                           or clean_row.get("<DATE>"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME")
                           or clean_row.get("<TIME>"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"
            if ts_raw is None or not ts_raw.strip():
                raise ValueError(f"Row {row_num}: no timestamp. Columns: {list(row.keys())}")
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            if any(v is None for v in (o, h, l, c)):
                raise ValueError(f"Row {row_num}: missing OHLC. Columns: {list(row.keys())}")
            bars.append(Bar(timestamp=parse_timestamp(ts_raw), open=float(o),
                            high=float(h), low=float(l), close=float(c)))

    bars.sort(key=lambda b: b.timestamp)
    return bars


def get_pip_size(symbol: str) -> float:
    """Get pip size for symbol (from rekey_simple.py)."""
    sym = symbol.upper()
    if "JPY" in sym:
        return 0.01
    if sym in ("BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "LTCUSD", "BCHUSD"):
        return 1.0
    if sym == "XAUUSD":
        return 0.1
    if sym == "XAGUSD":
        return 0.01
    if sym in ("US500", "NAS100", "DE30", "FR40", "HK50"):
        return 1.0
    return 0.0001


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def _est_hour(dt: datetime) -> int:
    """Convert UTC to EST hour (EST = UTC - 5)."""
    return (dt.hour - 5) % 24


def _session_date(dt: datetime) -> datetime.date:
    """Map bar timestamp to session date (date changes at 3AM EST)."""
    h = _est_hour(dt)
    if h >= ASIAN_START_H_EST:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def compute_sessions(bars: List[Bar]) -> List[SessionData]:
    """Group bars into sessions and compute Asian range + London close."""
    sessions: Dict[datetime.date, Dict] = defaultdict(lambda: {"asian": [], "london": []})

    for bar in bars:
        sdate = _session_date(bar.timestamp)
        est_h = _est_hour(bar.timestamp)

        if est_h >= ASIAN_START_H_EST or est_h < ASIAN_END_H_EST:
            sessions[sdate]["asian"].append(bar)
        elif LONDON_START_H_EST <= est_h < LONDON_END_H_EST:
            sessions[sdate]["london"].append(bar)

    result = []
    for sdate in sorted(sessions.keys()):
        data = sessions[sdate]
        asian_bars = sorted(data["asian"], key=lambda b: b.timestamp)
        london_bars = sorted(data["london"], key=lambda b: b.timestamp)

        if not asian_bars or not london_bars:
            continue

        asian_high = max(b.high for b in asian_bars)
        asian_low = min(b.low for b in asian_bars)
        asian_range = asian_high - asian_low

        if asian_range <= 0:
            continue

        asian_mid = asian_low + (asian_range / 2)
        london_close = london_bars[-1].close if london_bars else asian_bars[-1].close

        # Directional bias: London close vs Asian midpoint
        if london_close > asian_mid:
            bias = Direction.LONG
        elif london_close < asian_mid:
            bias = Direction.SHORT
        else:
            bias = Direction.FLAT

        result.append(SessionData(
            date=sdate,
            asian_high=asian_high,
            asian_low=asian_low,
            asian_range=asian_range,
            asian_mid=asian_mid,
            bias=bias,
        ))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# SECOND-ORDER PATTERN DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_breakout_and_nodes(session: SessionData, pip_size: float) -> Optional[Dict]:
    """
    Compute breakout direction + distribution nodes (deepest-first).
    Returns dict with breakout_direction, nodes_dict (node→level mapping).
    """
    if session.bias == Direction.FLAT:
        return None

    ar = session.asian_range

    if session.bias == Direction.LONG:
        # Bullish: expect rekey LONG (price breaches below AR low, pulls back to node, then OCC triggers)
        nodes = {
            Node.LEVEL_168: session.asian_low - (FIB_168 * ar),
            Node.LEVEL_132: session.asian_low - (FIB_REKEY * ar),
            Node.OPP_BAND: session.asian_low,
            Node.MIDPOINT: session.asian_mid,
        }
    else:
        # Bearish: expect rekey SHORT
        nodes = {
            Node.LEVEL_168: session.asian_high + (FIB_168 * ar),
            Node.LEVEL_132: session.asian_high + (FIB_REKEY * ar),
            Node.OPP_BAND: session.asian_high,
            Node.MIDPOINT: session.asian_mid,
        }

    # Rekey entry point (132%)
    entry_level = nodes[Node.LEVEL_132]
    sl_level = nodes[Node.LEVEL_168]
    tp_level = nodes[Node.OPP_BAND]

    sl_buffer = SL_BUFFER_PIPS * pip_size
    if session.bias == Direction.LONG:
        sl = sl_level - sl_buffer
    else:
        sl = sl_level + sl_buffer

    return {
        "direction": session.bias,
        "entry_level": entry_level,
        "sl": sl,
        "tp": tp_level,
        "nodes": nodes,
    }


def detect_breakout(bars_london: List[Bar], session: SessionData) -> Optional[Tuple[int, Direction]]:
    """
    Detect first M5 breakout outside AR during London window.
    Returns (bar_index, breakout_direction).
    """
    if session.bias == Direction.FLAT:
        return None

    for i, bar in enumerate(bars_london):
        if session.bias == Direction.LONG:
            if bar.close > session.asian_high:
                return (i, Direction.LONG)
        else:
            if bar.close < session.asian_low:
                return (i, Direction.SHORT)

    return None


def find_deepest_node_hit(bars_london: List[Bar], breakout_idx: int, session: SessionData, 
                          breakout_dir: Direction, nodes: Dict) -> Optional[Tuple[int, Node]]:
    """
    After breakout, scan for deepest node hit (168% → 132% → Opp → Mid).
    Returns (bar_index of hit, node type).
    """
    node_order = [Node.LEVEL_168, Node.LEVEL_132, Node.OPP_BAND, Node.MIDPOINT]
    post_break_bars = bars_london[breakout_idx:]

    for bar in post_break_bars:
        for node in node_order:
            level = nodes[node]
            if breakout_dir == Direction.LONG:
                # Pullback (low side): check if low <= node level
                if bar.low <= level:
                    return (bars_london.index(bar), node)
            else:
                # Pullback (high side): check if high >= node level
                if bar.high >= level:
                    return (bars_london.index(bar), node)

    return None


def scan_occ_trigger(bars_london: List[Bar], node_hit_idx: int, breakout_dir: Direction) -> Optional[int]:
    """
    Within OCC_SCAN_WINDOW minutes after node hit, scan for OCC (opposite candle close).
    Returns bar_index of OCC, or None if not found.
    """
    node_hit_time = bars_london[node_hit_idx].timestamp
    scan_until = node_hit_time + timedelta(minutes=OCC_SCAN_WINDOW)

    for i in range(node_hit_idx + 1, len(bars_london)):
        bar = bars_london[i]
        if bar.timestamp > scan_until:
            break

        # OCC: opposite candle close
        if breakout_dir == Direction.LONG:
            if bar.close > bar.open:  # Bullish candle
                return i
        else:
            if bar.close < bar.open:  # Bearish candle
                return i

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# BACKTEST EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest(csv_path: str, symbol: str, pip_size: float = None) -> Dict:
    """Run second-order universal Asian breakout backtest."""
    if pip_size is None:
        pip_size = get_pip_size(symbol)

    print(f"\n[CEREBUS-AB] Loading: {csv_path}")
    bars = load_bars_csv(csv_path)
    print(f"[CEREBUS-AB] Loaded {len(bars):,} bars")

    if not bars:
        return {}

    sessions = compute_sessions(bars)
    print(f"[CEREBUS-AB] Computed {len(sessions)} sessions")

    # Group bars by session date for intraday processing
    bars_by_date: Dict[datetime.date, List[Bar]] = defaultdict(list)
    for bar in bars:
        sdate = _session_date(bar.timestamp)
        bars_by_date[sdate].append(bar)

    trades: List[Trade] = []
    node_hits = 0
    occ_hits = 0

    for session in sessions:
        if session.bias == Direction.FLAT:
            continue

        # Compute breakout levels and nodes
        levels = compute_breakout_and_nodes(session, pip_size)
        if levels is None:
            continue

        # Get London bars for this session
        session_bars = sorted(bars_by_date.get(session.date, []), key=lambda b: b.timestamp)
        london_bars = [b for b in session_bars
                       if LONDON_START_H_EST <= _est_hour(b.timestamp) <= LONDON_END_H_EST]

        if not london_bars:
            continue

        # Step 1: Detect breakout
        breakout = detect_breakout(london_bars, session)
        if breakout is None:
            continue

        breakout_idx, breakout_dir = breakout

        # Step 2: Find deepest node hit
        node_hit = find_deepest_node_hit(london_bars, breakout_idx, session, breakout_dir, levels["nodes"])
        if node_hit is None:
            continue

        node_hit_idx, node_type = node_hit
        node_hits += 1

        # Step 3: Scan for OCC atomic trigger
        occ_idx = scan_occ_trigger(london_bars, node_hit_idx, breakout_dir)
        if occ_idx is None:
            continue

        occ_hits += 1

        # Step 4: Entry triggered at OCC; backtest from OCC onwards
        occ_bar = london_bars[occ_idx]
        trade = Trade(
            direction=breakout_dir,
            entry_price=levels["entry_level"],
            sl_price=levels["sl"],
            tp_price=levels["tp"],
            entry_time=london_bars[breakout_idx].timestamp,
            node_hit=node_type,
            occ_time=occ_bar.timestamp,
        )

        # Scan post-OCC bars for TP/SL hit
        # FILTER 1: Track MAE (Maximum Adverse Excursion) during trade
        # FILTER 2: Intra-bar collision detection (SL takes precedence over TP in same candle)
        worst_price = trade.entry_price
        
        for i in range(occ_idx, len(london_bars)):
            bar = london_bars[i]
            est_h = _est_hour(bar.timestamp)

            if breakout_dir == Direction.LONG:
                # Track MAE: worst low during trade
                worst_price = min(worst_price, bar.low)
                mae = (trade.entry_price - worst_price) / pip_size
                trade.mae = mae
                
                # FILTER 2: Intra-bar collision - if both TP and SL in same candle, SL wins
                if bar.low <= levels["sl"] and bar.high >= levels["tp"]:
                    # Both breached in same candle: conservatively assume SL hit first
                    trade.result = TradeResult.SL_HIT
                    trade.exit_price = levels["sl"]
                    trade.exit_time = bar.timestamp
                    break
                elif bar.low <= levels["sl"]:
                    trade.result = TradeResult.SL_HIT
                    trade.exit_price = levels["sl"]
                    trade.exit_time = bar.timestamp
                    break
                elif bar.high >= levels["tp"]:
                    trade.result = TradeResult.TP_HIT
                    trade.exit_price = levels["tp"]
                    trade.exit_time = bar.timestamp
                    break
            else:
                # SHORT: track MAE as worst high
                worst_price = max(worst_price, bar.high)
                mae = (worst_price - trade.entry_price) / pip_size
                trade.mae = mae
                
                # FILTER 2: Intra-bar collision - if both TP and SL in same candle, SL wins
                if bar.high >= levels["sl"] and bar.low <= levels["tp"]:
                    # Both breached in same candle: conservatively assume SL hit first
                    trade.result = TradeResult.SL_HIT
                    trade.exit_price = levels["sl"]
                    trade.exit_time = bar.timestamp
                    break
                elif bar.high >= levels["sl"]:
                    trade.result = TradeResult.SL_HIT
                    trade.exit_price = levels["sl"]
                    trade.exit_time = bar.timestamp
                    break
                elif bar.low <= levels["tp"]:
                    trade.result = TradeResult.TP_HIT
                    trade.exit_price = levels["tp"]
                    trade.exit_time = bar.timestamp
                    break

            # Hard exit at 12 PM EST
            if est_h >= LONDON_END_H_EST:
                trade.result = TradeResult.TIMEOUT
                trade.exit_price = bar.close
                trade.exit_time = bar.timestamp
                break

        if trade.result is None:
            trade.result = TradeResult.TIMEOUT

        # Calculate raw PnL before slippage
        if trade.direction == Direction.LONG:
            raw_pnl = (trade.exit_price - trade.entry_price) / pip_size
        else:
            raw_pnl = (trade.entry_price - trade.exit_price) / pip_size
        
        # FILTER 3: Apply spread & slippage deduction (1.5 pips per trade)
        SLIPPAGE_PIPS = 1.5
        trade.pnl_pips = raw_pnl - SLIPPAGE_PIPS

        trades.append(trade)

    # Compute stats
    return compute_stats(trades, symbol, session, len(sessions), node_hits, occ_hits, pip_size)


def compute_stats(trades: List[Trade], symbol: str, last_session: SessionData, 
                  total_sessions: int, node_hits: int, occ_hits: int, pip_size: float) -> Dict:
    """Compute comprehensive backtest statistics."""
    if not trades:
        return {
            "symbol": symbol,
            "total_sessions": total_sessions,
            "total_trades": 0,
            "node_hits": node_hits,
            "occ_hits": occ_hits,
            "occ_hit_rate": round(occ_hits / node_hits * 100 if node_hits > 0 else 0, 1),
        }

    wins = [t for t in trades if t.pnl_pips > 0]
    losses = [t for t in trades if t.pnl_pips < 0]
    total = len(trades)
    win_rate = len(wins) / total * 100 if total > 0 else 0.0

    gross_profit = sum(t.pnl_pips for t in wins) if wins else 0.0
    gross_loss = abs(sum(t.pnl_pips for t in losses)) if losses else 0.0
    net_pnl = gross_profit - gross_loss
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = net_pnl / total if total > 0 else 0.0

    # Max drawdown
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t.pnl_pips
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Per-tier stats
    tier_stats = {}
    for tier in ["T1", "T2", "T3"]:
        tier_trades = [t for t in trades if (t.entry_time.date() in 
                       [s.date for s in [last_session] if s.tier == tier])]
        if tier_trades:
            tier_wins = len([t for t in tier_trades if t.pnl_pips > 0])
            tier_wr = tier_wins / len(tier_trades) * 100
            tier_pnl = sum(t.pnl_pips for t in tier_trades)
            tier_stats[tier] = {
                "trades": len(tier_trades),
                "wr": round(tier_wr, 1),
                "pnl": round(tier_pnl, 1),
            }

    # Per-node stats
    node_stats = {}
    for node in Node:
        node_trades = [t for t in trades if t.node_hit == node]
        if node_trades:
            node_wins = len([t for t in node_trades if t.pnl_pips > 0])
            node_wr = node_wins / len(node_trades) * 100
            node_pnl = sum(t.pnl_pips for t in node_trades)
            node_stats[node.value] = {
                "trades": len(node_trades),
                "wr": round(node_wr, 1),
                "pnl": round(node_pnl, 1),
            }

    # Per-hour stats (OCC trigger hour)
    hour_stats = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0.0})
    for t in trades:
        if t.occ_time:
            h = _est_hour(t.occ_time)
            hour_stats[h]["trades"] += 1
            if t.pnl_pips > 0:
                hour_stats[h]["wins"] += 1
            hour_stats[h]["pnl"] += t.pnl_pips

    hour_stats_compact = {}
    for h in sorted(hour_stats.keys()):
        hs = hour_stats[h]
        wr = hs["wins"] / hs["trades"] * 100 if hs["trades"] > 0 else 0
        hour_stats_compact[f"{h:02d}:00"] = {
            "trades": hs["trades"],
            "wr": round(wr, 1),
            "pnl": round(hs["pnl"], 1),
        }

    tp_hits = len([t for t in trades if t.result == TradeResult.TP_HIT])
    sl_hits = len([t for t in trades if t.result == TradeResult.SL_HIT])
    timeouts = len([t for t in trades if t.result == TradeResult.TIMEOUT])
    
    # MAE statistics
    avg_mae = sum(t.mae for t in trades) / len(trades) if trades else 0.0
    max_mae = max((t.mae for t in trades), default=0.0)

    stats = {
        "symbol": symbol,
        "total_sessions": total_sessions,
        "total_trades": total,
        "node_hits": node_hits,
        "occ_hits": occ_hits,
        "occ_hit_rate": round(occ_hits / node_hits * 100 if node_hits > 0 else 0, 1),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "gross_profit_pips": round(gross_profit, 1),
        "gross_loss_pips": round(-gross_loss, 1),
        "net_pnl_pips": round(net_pnl, 1),
        "profit_factor": round(pf, 2),
        "avg_trade_pips": round(avg_trade, 2),
        "max_drawdown_pips": round(max_dd, 1),
        "avg_mae_pips": round(avg_mae, 2),
        "max_mae_pips": round(max_mae, 1),
        "slippage_applied_pips": 1.5,
        "tp_hits": tp_hits,
        "sl_hits": sl_hits,
        "timeouts": timeouts,
        "per_tier": tier_stats,
        "per_node": node_stats,
        "per_hour": hour_stats_compact,
    }

    print_report(stats)
    return stats


def print_report(stats: Dict):
    """Print backtest summary."""
    print()
    print("=" * 80)
    print(f"  CEREBUS UNIVERSAL ASIAN BREAKOUT — BACKTEST REPORT")
    print(f"  Symbol: {stats['symbol']}")
    print(f"  Sessions: {stats['total_sessions']} | Node Hits: {stats['node_hits']} | OCC Hits: {stats['occ_hits']} ({stats['occ_hit_rate']}%)")
    print("=" * 80)

    if stats['total_trades'] == 0:
        print("\n  No trades executed.\n")
        return

    print(f"\n  -- RESULTS ----------------------------------------")
    print(f"  Total Trades:    {stats['total_trades']}")
    print(f"  Wins:            {stats['wins']}")
    print(f"  Losses:          {stats['losses']}")
    print(f"  Win Rate:        {stats['win_rate']}%")
    print(f"  TP Hits:         {stats['tp_hits']}")
    print(f"  SL Hits:         {stats['sl_hits']}")
    print(f"  Timeouts:        {stats['timeouts']}")
    print(f"\n  -- PnL -------------------------------------------")
    print(f"  Gross Profit:    +{stats['gross_profit_pips']:.1f} pips")
    print(f"  Gross Loss:      {stats['gross_loss_pips']:.1f} pips")
    print(f"  Net PnL:         {stats['net_pnl_pips']:+.1f} pips")
    print(f"  Profit Factor:   {stats['profit_factor']}")
    print(f"  Avg Trade:       {stats['avg_trade_pips']:+.2f} pips")
    print(f"  Max Drawdown:    {stats['max_drawdown_pips']:.1f} pips")
    print(f"\n  -- RISK METRICS (CALIBRATED) ---------------------")
    print(f"  Avg MAE:         {stats['avg_mae_pips']:.2f} pips")
    print(f"  Max MAE:         {stats['max_mae_pips']:.1f} pips")
    print(f"  Slippage Applied:{stats['slippage_applied_pips']:.1f} pips/trade")
    print()
    print("=" * 80)


def run_all_pairs(data_dir: str) -> Dict:
    """Run backtest across all M5 CSV files in data directory."""
    data_path = Path(data_dir)
    csv_files = sorted(data_path.glob("*_M5*.csv"))
    pro_files = [f for f in csv_files if "PRO" in f.name]
    if not pro_files:
        pro_files = csv_files

    all_results = {}

    for csv_file in pro_files[:25]:  # Limit to first 25 for speed
        symbol = csv_file.stem.replace("_M5", "").replace("_PRO", "").replace("_2023_2026", "").replace("_2022_2026", "").replace("_JUNE", "")
        pip_size = get_pip_size(symbol)

        print(f"\n{'='*80}")
        print(f"  [{len(all_results)+1:2d}] Testing: {symbol} ({csv_file.name})")
        print(f"{'='*80}")

        try:
            stats = run_backtest(str(csv_file), symbol, pip_size)
            all_results[symbol] = stats
        except Exception as e:
            print(f"[CEREBUS-AB] ERROR for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print(f"\n\n{'='*80}")
    print(f"  CEREBUS UNIVERSAL ASIAN BREAKOUT — MULTI-PAIR SUMMARY")
    print(f"{'='*80}")
    print(f"\n  {'Pair':<12} {'Sessions':>10} {'Trades':>8} {'OCC%':>8} {'WR':>8} {'Net PnL':>12} {'PF':>8} {'MaxDD':>8}")
    print(f"  {'-'*80}")

    for symbol, stats in sorted(all_results.items(), key=lambda x: x[1].get('net_pnl_pips', 0), reverse=True):
        if stats.get('total_trades', 0) > 0:
            print(f"  {symbol:<12} {stats['total_sessions']:>10} {stats['total_trades']:>8} "
                  f"{stats['occ_hit_rate']:>7.1f}% {stats['win_rate']:>7.1f}% {stats['net_pnl_pips']:>+11.1f}p "
                  f"{stats['profit_factor']:>7.2f} {stats['max_drawdown_pips']:>7.1f}p")

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS Universal Asian Breakout Backtest")
    parser.add_argument("--csv", help="Single CSV file to test")
    parser.add_argument("--symbol", help="Symbol name")
    parser.add_argument("--all", action="store_true", help="Run all pairs in data directory")
    parser.add_argument("--data-dir", default="quant-lab/data", help="Data directory path")
    args = parser.parse_args()

    if args.csv:
        symbol = args.symbol or Path(args.csv).stem.replace("_M5", "")
        stats = run_backtest(args.csv, symbol)
        print(json.dumps(stats, indent=2, default=str))
    elif args.all:
        results = run_all_pairs(args.data_dir)
        output_path = Path("quant-lab/reports/universal_asian_sweep_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")
    else:
        print("Usage: python cerebus_universal_asian_breakout.py --csv <file> [--symbol <name>]")
        print("       python cerebus_universal_asian_breakout.py --all [--data-dir <dir>]")


if __name__ == "__main__":
    main()
