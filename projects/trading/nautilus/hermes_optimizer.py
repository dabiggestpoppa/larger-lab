#!/usr/bin/env python3
"""
Hermes Strategy Optimizer v1 — Target: <15% Max Drawdown, >30% Return
======================================================================
Iteratively tests parameter combinations for CEREBUS strategies
on real EURUSD M5 data until targets are met.

Targets:
  - Max Drawdown: < 15%
  - Total Return: >= 30%
  - Min Trades: >= 50 (statistical significance)

Strategies optimized:
  1. Symmetry Trap (CEREBUS manual p.141-143)
  2. P90 CFD Expansion (CEREBUS manual p.5-6)
  3. EMA Cross (baseline)
  4. CEREBUS WMA Crossover

Usage:
    python -m nautilus.hermes_optimizer
    python -m nautilus.hermes_optimizer --strategy symmetry_trap
    python -m nautilus.hermes_optimizer --max-iterations 200
"""
import os
import sys
import json
import time
import itertools
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Paths ────────────────────────────────────────────────────────────────────
LAB_ROOT = Path(__file__).parent.parent
NAUTILUS_DIR = Path(__file__).parent
DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = NAUTILUS_DIR / "results"
REPORTS_DIR = NAUTILUS_DIR / "reports"
RESULTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

INITIAL_EQUITY = 10000.0

# ── Target Criteria ──────────────────────────────────────────────────────────
TARGETS = {
    "max_drawdown_pct": 15.0,    # Must be LESS than this
    "min_return_pct": 30.0,      # Must be GREATER than this
    "min_trades": 50,            # Minimum trades for significance
}


# ── Result Dataclass ─────────────────────────────────────────────────────────
@dataclass
class BacktestResult:
    strategy: str
    params: dict
    total_return_pct: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    avg_trade_pnl: float
    max_consecutive_losses: int
    equity_curve: list = field(default_factory=list)
    trades: list = field(default_factory=list)
    is_winner: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        self.is_winner = (
            self.max_drawdown_pct < TARGETS["max_drawdown_pct"]
            and self.total_return_pct >= TARGETS["min_return_pct"]
            and self.total_trades >= TARGETS["min_trades"]
        )


# ── Data Loading ─────────────────────────────────────────────────────────────
def _parse_csv_direct(filepath: Path) -> pd.DataFrame:
    """Parse forex.com CSV directly without nautilus_trader dependency."""
    import re
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()

    data_lines = [l for l in raw_lines[1:] if l.strip()]

    # Fix OX Securities line wrapping
    fixed = []
    i = 0
    while i < len(data_lines):
        line = data_lines[i]
        if i + 1 < len(data_lines) and re.match(r'^\d{4}\.\d{2}\.\d{2}', data_lines[i + 1]):
            parts = line.strip().split()
            if len(parts) >= 8:
                fixed.append(line)
            else:
                merged = line.strip() + " " + data_lines[i + 1].strip()
                fixed.append(merged)
                i += 1
        else:
            fixed.append(line)
        i += 1

    records = []
    for line in fixed:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            date_str, time_str = parts[0], parts[1]
            open_val, high_val = float(parts[2]), float(parts[3])
            low_val, close_val = float(parts[4]), float(parts[5])
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            records.append({
                'timestamp': ts, 'open': open_val, 'high': high_val,
                'low': low_val, 'close': close_val,
            })
        except (ValueError, IndexError):
            continue

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    return df


def load_eurusd_m5(limit: int = 50000) -> pd.DataFrame:
    """Load EURUSD M5 data from Downloads."""
    filepath = DOWNLOADS_DIR / "EURUSD!_M5_202301020000_202605061250.csv"
    if not filepath.exists():
        print(f"❌ Data file not found: {filepath}")
        return generate_synthetic_data(limit)

    print(f"📂 Loading EURUSD M5 data from {filepath.name}...")
    df = _parse_csv_direct(filepath)
    if df.empty:
        print("❌ Failed to parse CSV. Using synthetic data.")
        return generate_synthetic_data(limit)
    if limit and len(df) > limit:
        df = df.tail(limit).copy()
    print(f"  ✅ Loaded {len(df)} bars | {df.index[0]} → {df.index[-1]}")
    return df


def generate_synthetic_data(n: int = 30000) -> pd.DataFrame:
    """Generate synthetic EURUSD data for testing."""
    print(f"⚠️  Generating synthetic data ({n} bars)...")
    idx = pd.date_range('2023-01-01', periods=n, freq='5T')
    np.random.seed(42)
    base = 1.1000
    prices = [base]
    for i in range(1, n):
        if i % 200 == 0:
            change = np.random.randn() * 0.0012
        else:
            change = np.random.randn() * 0.0002
        prices.append(prices[-1] + change)
    prices = np.array(prices)
    df = pd.DataFrame({
        'open': prices + np.random.randn(n) * 0.0001,
        'high': prices + np.abs(np.random.randn(n)) * 0.0004,
        'low': prices - np.abs(np.random.randn(n)) * 0.0004,
        'close': prices + np.random.randn(n) * 0.0001,
    }, index=idx)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    return df


# ── Performance Metrics ──────────────────────────────────────────────────────
def calc_max_drawdown(equity_curve: list) -> float:
    """Calculate max drawdown percentage from equity curve."""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    equity = np.array(equity_curve)
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak * 100
    return abs(float(np.min(drawdown)))


def calc_sharpe_ratio(equity_curve: list, risk_free_rate: float = 0.0) -> float:
    """Calculate annualized Sharpe ratio from equity curve."""
    if not equity_curve or len(equity_curve) < 10:
        return 0.0
    equity = np.array(equity_curve)
    returns = np.diff(equity) / equity[:-1]
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    # Annualize: ~78 five-min bars per day, ~252 trading days
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 78)
    return float(sharpe)


def calc_profit_factor(trades: list) -> float:
    """Calculate profit factor (gross profit / gross loss)."""
    gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def calc_max_consecutive_losses(trades: list) -> int:
    """Calculate maximum consecutive losing trades."""
    max_streak = 0
    current_streak = 0
    for t in trades:
        if t['pnl'] < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


# ── Position Sizing ──────────────────────────────────────────────────────────
def calc_position_size(equity: float, risk_pct: float, sl_pips: float, pip_value: float = 10.0) -> float:
    """
    Calculate position size based on risk percentage.
    risk_pct: fraction of equity to risk (e.g., 0.0025 = 0.25%)
    sl_pips: stop loss distance in pips
    pip_value: $ per pip per standard lot (~$10 for EURUSD)
    Returns: lot size
    """
    if sl_pips <= 0:
        return 0.01
    risk_amount = equity * risk_pct
    lot_size = risk_amount / (sl_pips * pip_value)
    return round(max(0.01, min(lot_size, 10.0)), 2)  # Clamp between 0.01 and 10.0


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 1: Symmetry Trap (CEREBUS manual p.141-143)
# ═══════════════════════════════════════════════════════════════════════════════
def run_symmetry_trap(
    df: pd.DataFrame,
    risk_pct: float = 0.0025,
    tp_factor: float = 1.0,       # TP = atomic_unit * tp_factor
    sl_buffer_pips: float = 4.0,  # SL buffer beyond Asian band
    max_loops: int = 8,
    bias_delay_bars: int = 0,     # Bars to wait after bias lock before entry
    atr_multiplier_sl: float = 0, # If > 0, use ATR-based SL instead of fixed
) -> BacktestResult:
    """
    Symmetry Trap — CEREBUS Distribution Symmetry Trap.

    Three-Layer Model:
      Layer 1: BIAS LOCK — First M5 close outside Asian Range
      Layer 2: ATOMIC ENTRY — Impulse in bias direction + opposite close pullback
      Layer 3: DISTRIBUTION TARGETS — TP at atomic unit from entry

    Tier System:
      T1: AR < 20p  | Atomic = 10p
      T2: AR 20-30p  | Atomic = 12p
      T3: AR 30-45p  | Atomic = 15p
      NO-GO: AR > 45p
    """
    df = df.copy()
    df['hour_utc'] = df.index.hour
    df['minute'] = df.index.minute
    df['date'] = df.index.date

    # Pre-calculate ATR(14) for adaptive SL
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(14).mean()

    equity = INITIAL_EQUITY
    equity_curve = [equity]
    trades = []
    position = None
    bias_locked = False
    bias_direction = 0
    asian_high = None
    asian_low = None
    asian_range_pips = 0
    tier = None
    loop_count = 0
    last_date = None
    bars_since_bias = 0

    for i in range(50, len(df)):
        row = df.iloc[i]
        hour = row['hour_utc']
        date = row['date']
        o, h, l, c = row['open'], row['high'], row['low'], row['close']

        # New day reset
        if date != last_date:
            # Close any open position at day boundary
            if position is not None:
                exit_price = c
                pnl = (exit_price - position['entry']) * position['size'] * 100000 * position['direction']
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': exit_price, 'pnl': round(pnl, 2),
                               'side': 'long' if position['direction'] > 0 else 'short', 'reason': 'new_day'})
                position = None
                equity_curve.append(equity)

            asian_high = None
            asian_low = None
            asian_range_pips = 0
            tier = None
            bias_locked = False
            bias_direction = 0
            loop_count = 0
            bars_since_bias = 0
            last_date = date

        # ── Asian Session: Measure Range (19:00-03:00 UTC) ──
        if hour >= 19 or hour < 3:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            continue

        # ── End of Asian: Classify Tier ──
        if asian_high is not None and tier is None:
            mid_price = (asian_high + asian_low) / 2
            asian_range_pips = (asian_high - asian_low) / (mid_price * 0.0001)
            if asian_range_pips < 20:
                tier = 'T1'
            elif asian_range_pips <= 30:
                tier = 'T2'
            elif asian_range_pips <= 45:
                tier = 'T3'
            else:
                tier = 'NO_GO'

        if tier == 'NO_GO' or tier is None:
            continue

        atomic_unit = {'T1': 10, 'T2': 12, 'T3': 15}[tier]
        tp_pips = atomic_unit * tp_factor

        # ── Hard Exit at 17:00 UTC (12PM EST) ──
        if hour >= 17:
            if position is not None:
                exit_price = c
                pnl = (exit_price - position['entry']) * position['size'] * 100000 * position['direction']
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': exit_price, 'pnl': round(pnl, 2),
                               'side': 'long' if position['direction'] > 0 else 'short', 'reason': 'hard_exit'})
                position = None
                equity_curve.append(equity)
            bias_locked = False
            loop_count = 0
            continue

        # ── Bias Lock Window: 08:00-17:00 UTC ──
        if hour < 8:
            continue

        # Track bars since bias lock
        if bias_locked:
            bars_since_bias += 1

        # ── Layer 1: Bias Lock ──
        if not bias_locked and asian_high is not None:
            if c > asian_high:
                bias_direction = 1
                bias_locked = True
                bars_since_bias = 0
            elif c < asian_low:
                bias_direction = -1
                bias_locked = True
                bars_since_bias = 0

        # ── Layer 2: Atomic Entry ──
        if bias_locked and position is None and loop_count < max_loops and bars_since_bias >= bias_delay_bars:
            # Entry: close beyond Asian range in bias direction
            if bias_direction > 0 and c > asian_high:
                sl_dist = (sl_buffer_pips * 0.0001) + (row['atr'] * atr_multiplier_sl if atr_multiplier_sl > 0 and not pd.isna(row['atr']) else 0)
                lot_size = calc_position_size(equity, risk_pct, sl_dist * 10000)
                position = {
                    'direction': 1, 'entry': c,
                    'sl': c - sl_dist,
                    'tp': c + tp_pips * 0.0001,
                    'size': lot_size,
                }
                loop_count += 1
            elif bias_direction < 0 and c < asian_low:
                sl_dist = (sl_buffer_pips * 0.0001) + (row['atr'] * atr_multiplier_sl if atr_multiplier_sl > 0 and not pd.isna(row['atr']) else 0)
                lot_size = calc_position_size(equity, risk_pct, sl_dist * 10000)
                position = {
                    'direction': -1, 'entry': c,
                    'sl': c + sl_dist,
                    'tp': c - tp_pips * 0.0001,
                    'size': lot_size,
                }
                loop_count += 1

        # ── Layer 3: Position Management ──
        if position is not None:
            # Check SL
            if position['direction'] > 0 and l <= position['sl']:
                pnl = (position['sl'] - position['entry']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['sl'], 'pnl': round(pnl, 2),
                               'side': 'long', 'reason': 'sl'})
                position = None
                equity_curve.append(equity)
            elif position['direction'] < 0 and h >= position['sl']:
                pnl = (position['entry'] - position['sl']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['sl'], 'pnl': round(pnl, 2),
                               'side': 'short', 'reason': 'sl'})
                position = None
                equity_curve.append(equity)
            # Check TP
            elif position['direction'] > 0 and h >= position['tp']:
                pnl = (position['tp'] - position['entry']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['tp'], 'pnl': round(pnl, 2),
                               'side': 'long', 'reason': 'tp'})
                position = None
                equity_curve.append(equity)
            elif position['direction'] < 0 and l <= position['tp']:
                pnl = (position['entry'] - position['tp']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['tp'], 'pnl': round(pnl, 2),
                               'side': 'short', 'reason': 'tp'})
                position = None
                equity_curve.append(equity)

    # ── Calculate Metrics ──
    total_return = ((equity - INITIAL_EQUITY) / INITIAL_EQUITY) * 100
    max_dd = calc_max_drawdown(equity_curve)
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] <= 0]
    win_rate = len(winning) / max(1, len(trades)) * 100
    pf = calc_profit_factor(trades)
    sharpe = calc_sharpe_ratio(equity_curve)
    avg_trade = np.mean([t['pnl'] for t in trades]) if trades else 0
    max_cons_loss = calc_max_consecutive_losses(trades)

    return BacktestResult(
        strategy="Symmetry_Trap",
        params={
            "risk_pct": risk_pct, "tp_factor": tp_factor,
            "sl_buffer_pips": sl_buffer_pips, "max_loops": max_loops,
            "bias_delay_bars": bias_delay_bars, "atr_multiplier_sl": atr_multiplier_sl,
        },
        total_return_pct=round(total_return, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(win_rate, 1),
        profit_factor=round(pf, 2),
        sharpe_ratio=round(sharpe, 2),
        avg_trade_pnl=round(avg_trade, 2),
        max_consecutive_losses=max_cons_loss,
        equity_curve=equity_curve[::max(1, len(equity_curve)//500)],  # Downsample for storage
        trades=trades,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 2: P90 CFD Expansion (CEREBUS manual p.5-6)
# ═══════════════════════════════════════════════════════════════════════════════
def run_p90_strategy(
    df: pd.DataFrame,
    risk_pct: float = 0.0025,
    tp1_factor: float = 0.25,     # TP1 at 25% of Asian Range
    tp2_factor: float = 0.50,     # TP2 at 50% of Asian Range
    tp3_factor: float = 1.00,     # TP3 at 100% of Asian Range
    pyramid_delay_min: int = 45,  # Minutes before adding position 3
    sl_atr_mult: float = 1.5,     # SL = ATR * multiplier
    entry_start_hour: int = 7,    # Entry window start (UTC)
    entry_end_hour: int = 15,     # Entry window end (UTC)
) -> BacktestResult:
    """
    P90 CFD Expansion Engine.

    1. Asian Range → Tier classification
    2. P90 candle (body >= threshold) → Entry
    3. 3-position pyramid: 40%/40%/20%
    4. TP at -25%, -50%, -100% of Asian Range
    """
    df = df.copy()
    df['hour_utc'] = df.index.hour
    df['date'] = df.index.date

    # ATR for SL
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(14).mean()

    equity = INITIAL_EQUITY
    equity_curve = [equity]
    trades = []
    positions = []  # List of open positions
    asian_high = None
    asian_low = None
    asian_range = 0
    tier = None
    last_date = None
    entry_time = None

    for i in range(50, len(df)):
        row = df.iloc[i]
        hour = row['hour_utc']
        date = row['date']
        o, h, l, c = row['open'], row['high'], row['low'], row['close']

        # New day reset
        if date != last_date:
            # Close all open positions
            for pos in positions:
                pnl = (c - pos['entry']) * pos['size'] * 100000 * pos['direction']
                equity += pnl
                trades.append({'entry': pos['entry'], 'exit': c, 'pnl': round(pnl, 2),
                               'side': 'long' if pos['direction'] > 0 else 'short', 'reason': 'new_day'})
            if positions:
                equity_curve.append(equity)
            positions = []
            asian_high = None
            asian_low = None
            asian_range = 0
            tier = None
            entry_time = None
            last_date = date

        # Asian Session
        if hour >= 19 or hour < 3:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            continue

        # End of Asian: classify tier
        if asian_high is not None and tier is None:
            asian_range = asian_high - asian_low
            mid = (asian_high + asian_low) / 2
            ar_pips = asian_range / (mid * 0.0001)
            if ar_pips < 20:
                tier = 'T1'
            elif ar_pips <= 30:
                tier = 'T2'
            elif ar_pips <= 45:
                tier = 'T3'
            else:
                tier = 'NO_GO'

        if tier == 'NO_GO' or tier is None:
            continue

        # Hard exit at 17:00 UTC
        if hour >= 17:
            for pos in positions:
                pnl = (c - pos['entry']) * pos['size'] * 100000 * pos['direction']
                equity += pnl
                trades.append({'entry': pos['entry'], 'exit': c, 'pnl': round(pnl, 2),
                               'side': 'long' if pos['direction'] > 0 else 'short', 'reason': 'hard_exit'})
            if positions:
                equity_curve.append(equity)
            positions = []
            continue

        if hour < entry_start_hour or hour >= entry_end_hour:
            continue

        # Check existing positions for SL/TP
        new_positions = []
        for pos in positions:
            exited = False
            # Check SL
            if pos['direction'] > 0 and l <= pos['sl']:
                pnl = (pos['sl'] - pos['entry']) * pos['size'] * 100000
                equity += pnl
                trades.append({'entry': pos['entry'], 'exit': pos['sl'], 'pnl': round(pnl, 2),
                               'side': 'long', 'reason': 'sl'})
                exited = True
            elif pos['direction'] < 0 and h >= pos['sl']:
                pnl = (pos['entry'] - pos['sl']) * pos['size'] * 100000
                equity += pnl
                trades.append({'entry': pos['entry'], 'exit': pos['sl'], 'pnl': round(pnl, 2),
                               'side': 'short', 'reason': 'sl'})
                exited = True
            # Check TP
            elif pos['direction'] > 0 and h >= pos['tp']:
                pnl = (pos['tp'] - pos['entry']) * pos['size'] * 100000
                equity += pnl
                trades.append({'entry': pos['entry'], 'exit': pos['tp'], 'pnl': round(pnl, 2),
                               'side': 'long', 'reason': 'tp'})
                exited = True
            elif pos['direction'] < 0 and l <= pos['tp']:
                pnl = (pos['entry'] - pos['tp']) * pos['size'] * 100000
                equity += pnl
                trades.append({'entry': pos['entry'], 'exit': pos['tp'], 'pnl': round(pnl, 2),
                               'side': 'short', 'reason': 'tp'})
                exited = True

            if not exited:
                new_positions.append(pos)
            else:
                equity_curve.append(equity)
        positions = new_positions

        # P90 Entry: candle body >= threshold
        body = abs(c - o)
        body_pips = body / (c * 0.0001)

        # Time-dependent thresholds
        if 7 <= hour < 9:
            threshold = 4.1
        elif 9 <= hour < 11:
            threshold = 4.6
        elif 11 <= hour < 13:
            threshold = 4.6
        elif 13 <= hour < 15:
            threshold = 5.9
        else:
            threshold = 6.2

        if body_pips >= threshold and len(positions) < 3:
            direction = 1 if c > o else -1
            atr_val = row['atr'] if not pd.isna(row['atr']) else 0.0010
            sl_dist = atr_val * sl_atr_mult

            # Position sizing: 40%, 40%, 20%
            if len(positions) == 0:
                pos_pct = 0.40
            elif len(positions) == 1:
                pos_pct = 0.40
            else:
                pos_pct = 0.20

            risk_amount = equity * risk_pct * (pos_pct / 0.40)
            lot_size = max(0.01, risk_amount / (sl_dist * 100000))

            # TP based on Asian Range
            if len(positions) == 0:
                tp_dist = asian_range * tp1_factor
            elif len(positions) == 1:
                tp_dist = asian_range * tp2_factor
            else:
                tp_dist = asian_range * tp3_factor

            if direction > 0:
                entry_price = c
                sl = entry_price - sl_dist
                tp = entry_price + tp_dist
            else:
                entry_price = c
                sl = entry_price + sl_dist
                tp = entry_price - tp_dist

            positions.append({
                'direction': direction, 'entry': entry_price,
                'sl': sl, 'tp': tp, 'size': round(lot_size, 2),
            })
            if entry_time is None:
                entry_time = i

    # Metrics
    total_return = ((equity - INITIAL_EQUITY) / INITIAL_EQUITY) * 100
    max_dd = calc_max_drawdown(equity_curve)
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] <= 0]
    win_rate = len(winning) / max(1, len(trades)) * 100
    pf = calc_profit_factor(trades)
    sharpe = calc_sharpe_ratio(equity_curve)
    avg_trade = np.mean([t['pnl'] for t in trades]) if trades else 0
    max_cons_loss = calc_max_consecutive_losses(trades)

    return BacktestResult(
        strategy="P90_CFD_Expansion",
        params={
            "risk_pct": risk_pct, "tp1_factor": tp1_factor,
            "tp2_factor": tp2_factor, "tp3_factor": tp3_factor,
            "pyramid_delay_min": pyramid_delay_min, "sl_atr_mult": sl_atr_mult,
            "entry_start_hour": entry_start_hour, "entry_end_hour": entry_end_hour,
        },
        total_return_pct=round(total_return, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(win_rate, 1),
        profit_factor=round(pf, 2),
        sharpe_ratio=round(sharpe, 2),
        avg_trade_pnl=round(avg_trade, 2),
        max_consecutive_losses=max_cons_loss,
        equity_curve=equity_curve[::max(1, len(equity_curve)//500)],
        trades=trades,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 3: EMA Cross with ATR Trailing Stop
# ═══════════════════════════════════════════════════════════════════════════════
def run_ema_cross(
    df: pd.DataFrame,
    risk_pct: float = 0.0025,
    fast_ema: int = 8,
    slow_ema: int = 21,
    atr_mult_sl: float = 1.5,
    atr_mult_tp: float = 3.0,
    trend_filter_ema: int = 0,  # 0 = disabled, else use as trend filter
) -> BacktestResult:
    """EMA Cross with ATR-based SL/TP and optional trend filter."""
    df = df.copy()
    df['ema_fast'] = df['close'].ewm(span=fast_ema).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_ema).mean()

    if trend_filter_ema > 0:
        df['ema_trend'] = df['close'].ewm(span=trend_filter_ema).mean()

    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(14).mean()

    equity = INITIAL_EQUITY
    equity_curve = [equity]
    trades = []
    position = None

    for i in range(max(slow_ema, trend_filter_ema) + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        h, l, c = row['high'], row['low'], row['close']

        # Check existing position
        if position is not None:
            exited = False
            if position['direction'] > 0:
                # Update trailing SL
                new_sl = c - row['atr'] * atr_mult_sl if not pd.isna(row['atr']) else position['sl']
                position['sl'] = max(position['sl'], new_sl)
                if l <= position['sl']:
                    pnl = (position['sl'] - position['entry']) * position['size'] * 100000
                    equity += pnl
                    trades.append({'entry': position['entry'], 'exit': position['sl'], 'pnl': round(pnl, 2),
                                   'side': 'long', 'reason': 'sl'})
                    position = None
                    equity_curve.append(equity)
                    exited = True
                elif h >= position['tp']:
                    pnl = (position['tp'] - position['entry']) * position['size'] * 100000
                    equity += pnl
                    trades.append({'entry': position['entry'], 'exit': position['tp'], 'pnl': round(pnl, 2),
                                   'side': 'long', 'reason': 'tp'})
                    position = None
                    equity_curve.append(equity)
                    exited = True
            else:
                new_sl = c + row['atr'] * atr_mult_sl if not pd.isna(row['atr']) else position['sl']
                position['sl'] = min(position['sl'], new_sl)
                if h >= position['sl']:
                    pnl = (position['entry'] - position['sl']) * position['size'] * 100000
                    equity += pnl
                    trades.append({'entry': position['entry'], 'exit': position['sl'], 'pnl': round(pnl, 2),
                                   'side': 'short', 'reason': 'sl'})
                    position = None
                    equity_curve.append(equity)
                    exited = True
                elif l <= position['tp']:
                    pnl = (position['entry'] - position['tp']) * position['size'] * 100000
                    equity += pnl
                    trades.append({'entry': position['entry'], 'exit': position['tp'], 'pnl': round(pnl, 2),
                                   'side': 'short', 'reason': 'tp'})
                    position = None
                    equity_curve.append(equity)
                    exited = True

            if exited:
                continue

        # Entry signals
        if position is None:
            fast_prev, slow_prev = prev['ema_fast'], prev['ema_slow']
            fast_curr, slow_curr = row['ema_fast'], row['ema_slow']

            # Trend filter
            trend_ok = True
            if trend_filter_ema > 0:
                trend_ok = c > row['ema_trend']  # Only long above trend

            atr_val = row['atr'] if not pd.isna(row['atr']) else 0.0010
            sl_dist = atr_val * atr_mult_sl
            tp_dist = atr_val * atr_mult_tp

            if fast_prev <= slow_prev and fast_curr > slow_curr and trend_ok:
                lot_size = calc_position_size(equity, risk_pct, sl_dist * 10000)
                position = {
                    'direction': 1, 'entry': c,
                    'sl': c - sl_dist, 'tp': c + tp_dist,
                    'size': lot_size,
                }
            elif fast_prev >= slow_prev and fast_curr < slow_curr:
                lot_size = calc_position_size(equity, risk_pct, sl_dist * 10000)
                position = {
                    'direction': -1, 'entry': c,
                    'sl': c + sl_dist, 'tp': c - tp_dist,
                    'size': lot_size,
                }

    total_return = ((equity - INITIAL_EQUITY) / INITIAL_EQUITY) * 100
    max_dd = calc_max_drawdown(equity_curve)
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] <= 0]
    win_rate = len(winning) / max(1, len(trades)) * 100
    pf = calc_profit_factor(trades)
    sharpe = calc_sharpe_ratio(equity_curve)
    avg_trade = np.mean([t['pnl'] for t in trades]) if trades else 0
    max_cons_loss = calc_max_consecutive_losses(trades)

    return BacktestResult(
        strategy="EMA_Cross",
        params={
            "risk_pct": risk_pct, "fast_ema": fast_ema, "slow_ema": slow_ema,
            "atr_mult_sl": atr_mult_sl, "atr_mult_tp": atr_mult_tp,
            "trend_filter_ema": trend_filter_ema,
        },
        total_return_pct=round(total_return, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(win_rate, 1),
        profit_factor=round(pf, 2),
        sharpe_ratio=round(sharpe, 2),
        avg_trade_pnl=round(avg_trade, 2),
        max_consecutive_losses=max_cons_loss,
        equity_curve=equity_curve[::max(1, len(equity_curve)//500)],
        trades=trades,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 4: CEREBUS WMA Crossover
# ═══════════════════════════════════════════════════════════════════════════════
def run_wma_crossover(
    df: pd.DataFrame,
    risk_pct: float = 0.0025,
    wma_period: int = 7,
    atr_mult_sl: float = 1.5,
    rr_ratio: float = 3.0,        # Risk:Reward ratio
    daily_dd_limit_pct: float = 3.0,  # Max daily drawdown before stopping
) -> BacktestResult:
    """CEREBUS WMA Crossover with ATR stops and daily drawdown limit."""
    df = df.copy()
    df['hour_utc'] = df.index.hour
    df['date'] = df.index.date

    weights = np.arange(1, wma_period + 1)
    df['wma'] = df['close'].rolling(wma_period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(14).mean()

    equity = INITIAL_EQUITY
    equity_curve = [equity]
    trades = []
    position = None
    day_start_equity = INITIAL_EQUITY
    last_date = None

    for i in range(wma_period + 14, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        h, l, c = row['high'], row['low'], row['close']

        # Daily reset
        if row['date'] != last_date:
            day_start_equity = equity
            last_date = row['date']

        # Daily drawdown check
        daily_dd = abs((equity - day_start_equity) / day_start_equity * 100) if day_start_equity > 0 else 0
        dd_triggered = daily_dd >= daily_dd_limit_pct

        # Manage existing position
        if position is not None:
            exited = False
            if position['direction'] > 0 and l <= position['sl']:
                pnl = (position['sl'] - position['entry']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['sl'], 'pnl': round(pnl, 2),
                               'side': 'long', 'reason': 'sl'})
                position = None
                equity_curve.append(equity)
                exited = True
            elif position['direction'] < 0 and h >= position['sl']:
                pnl = (position['entry'] - position['sl']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['sl'], 'pnl': round(pnl, 2),
                               'side': 'short', 'reason': 'sl'})
                position = None
                equity_curve.append(equity)
                exited = True
            elif position['direction'] > 0 and h >= position['tp']:
                pnl = (position['tp'] - position['entry']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['tp'], 'pnl': round(pnl, 2),
                               'side': 'long', 'reason': 'tp'})
                position = None
                equity_curve.append(equity)
                exited = True
            elif position['direction'] < 0 and l <= position['tp']:
                pnl = (position['entry'] - position['tp']) * position['size'] * 100000
                equity += pnl
                trades.append({'entry': position['entry'], 'exit': position['tp'], 'pnl': round(pnl, 2),
                               'side': 'short', 'reason': 'tp'})
                position = None
                equity_curve.append(equity)
                exited = True

            if exited:
                continue

        # Entry
        if position is None and not dd_triggered:
            wma = row['wma']
            prev_wma = prev['wma']
            atr_val = row['atr'] if not pd.isna(row['atr']) else 0.0010
            sl_dist = atr_val * atr_mult_sl
            tp_dist = sl_dist * rr_ratio

            if pd.isna(wma) or pd.isna(prev_wma):
                continue

            is_long = c > wma and prev['close'] <= prev_wma and c > prev['close']
            is_short = c < wma and prev['close'] >= prev_wma and c < prev['close']

            if is_long:
                lot_size = calc_position_size(equity, risk_pct, sl_dist * 10000)
                position = {
                    'direction': 1, 'entry': c,
                    'sl': c - sl_dist, 'tp': c + tp_dist,
                    'size': lot_size,
                }
            elif is_short:
                lot_size = calc_position_size(equity, risk_pct, sl_dist * 10000)
                position = {
                    'direction': -1, 'entry': c,
                    'sl': c + sl_dist, 'tp': c - tp_dist,
                    'size': lot_size,
                }

    total_return = ((equity - INITIAL_EQUITY) / INITIAL_EQUITY) * 100
    max_dd = calc_max_drawdown(equity_curve)
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] <= 0]
    win_rate = len(winning) / max(1, len(trades)) * 100
    pf = calc_profit_factor(trades)
    sharpe = calc_sharpe_ratio(equity_curve)
    avg_trade = np.mean([t['pnl'] for t in trades]) if trades else 0
    max_cons_loss = calc_max_consecutive_losses(trades)

    return BacktestResult(
        strategy="WMA_Crossover",
        params={
            "risk_pct": risk_pct, "wma_period": wma_period,
            "atr_mult_sl": atr_mult_sl, "rr_ratio": rr_ratio,
            "daily_dd_limit_pct": daily_dd_limit_pct,
        },
        total_return_pct=round(total_return, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(win_rate, 1),
        profit_factor=round(pf, 2),
        sharpe_ratio=round(sharpe, 2),
        avg_trade_pnl=round(avg_trade, 2),
        max_consecutive_losses=max_cons_loss,
        equity_curve=equity_curve[::max(1, len(equity_curve)//500)],
        trades=trades,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMETER GRID DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
PARAM_GRIDS = {
    "Symmetry_Trap": {
        "risk_pct": [0.0012, 0.0025, 0.005],
        "tp_factor": [0.8, 1.0, 1.2, 1.5],
        "sl_buffer_pips": [2, 4, 6, 8],
        "max_loops": [4, 6, 8],
        "bias_delay_bars": [0, 1, 3],
        "atr_multiplier_sl": [0, 0.5, 1.0],
    },
    "P90_CFD_Expansion": {
        "risk_pct": [0.0012, 0.0025, 0.005],
        "tp1_factor": [0.20, 0.25, 0.30],
        "tp2_factor": [0.40, 0.50, 0.60],
        "tp3_factor": [0.80, 1.00, 1.20],
        "sl_atr_mult": [1.0, 1.5, 2.0],
        "entry_start_hour": [6, 7, 8],
        "entry_end_hour": [14, 15, 16],
    },
    "EMA_Cross": {
        "risk_pct": [0.0012, 0.0025, 0.005],
        "fast_ema": [5, 8, 10, 12],
        "slow_ema": [15, 21, 30, 50],
        "atr_mult_sl": [1.0, 1.5, 2.0],
        "atr_mult_tp": [2.0, 3.0, 4.0],
        "trend_filter_ema": [0, 50, 100, 200],
    },
    "WMA_Crossover": {
        "risk_pct": [0.0012, 0.0025, 0.005],
        "wma_period": [5, 7, 10, 14],
        "atr_mult_sl": [1.0, 1.5, 2.0],
        "rr_ratio": [2.0, 3.0, 4.0],
        "daily_dd_limit_pct": [2.0, 3.0, 5.0],
    },
}

# Strategy function mapping
STRATEGY_FUNCS = {
    "Symmetry_Trap": run_symmetry_trap,
    "P90_CFD_Expansion": run_p90_strategy,
    "EMA_Cross": run_ema_cross,
    "WMA_Crossover": run_wma_crossover,
}


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class HermesOptimizer:
    """
    Iterates through parameter combinations for each strategy,
    tracking the best results and stopping when targets are met.
    """

    def __init__(self, strategy_filter: str = None, max_iterations: int = 500):
        self.strategy_filter = strategy_filter
        self.max_iterations = max_iterations
        self.all_results: List[BacktestResult] = []
        self.winners: List[BacktestResult] = []
        self.best_by_strategy: Dict[str, BacktestResult] = {}
        self.iteration = 0
        self.df = None

    def _smart_param_sample(self, strategy_name: str, n_samples: int = 50) -> List[dict]:
        """
        Generate smart parameter combinations using Latin Hypercube-style sampling.
        Instead of full grid (which explodes), sample intelligently.
        """
        grid = PARAM_GRIDS[strategy_name]
        keys = list(grid.keys())
        values = [grid[k] for k in keys]

        # If total combinations is manageable, do full grid
        total = 1
        for v in values:
            total *= len(v)

        if total <= n_samples:
            # Full grid
            combos = list(itertools.product(*values))
        else:
            # Random sample from grid
            np.random.seed(42 + self.iteration)
            combos = []
            for _ in range(n_samples):
                combo = tuple(np.random.choice(v) for v in values)
                combos.append(combo)

        return [dict(zip(keys, combo)) for combo in combos]

    def run_optimization(self):
        """Main optimization loop."""
        print("=" * 70)
        print("🔬 HERMES STRATEGY OPTIMIZER v1")
        print("=" * 70)
        print(f"  Targets: Return >= {TARGETS['min_return_pct']}% | Max DD < {TARGETS['max_drawdown_pct']}%")
        print(f"  Min Trades: {TARGETS['min_trades']}")
        print(f"  Max Iterations: {self.max_iterations}")
        print("=" * 70)

        # Load data once
        self.df = load_eurusd_m5(limit=50000)
        if self.df is None or len(self.df) < 1000:
            print("❌ Insufficient data. Exiting.")
            return

        strategies_to_test = (
            [self.strategy_filter] if self.strategy_filter
            else list(STRATEGY_FUNCS.keys())
        )

        start_time = time.time()

        for strategy_name in strategies_to_test:
            if strategy_name not in STRATEGY_FUNCS:
                print(f"⚠️  Unknown strategy: {strategy_name}")
                continue

            print(f"\n{'─' * 50}")
            print(f"🎯 Optimizing: {strategy_name}")
            print(f"{'─' * 50}")

            func = STRATEGY_FUNCS[strategy_name]
            param_sets = self._smart_param_sample(strategy_name, n_samples=60)

            best_return = -999
            best_dd = 999

            for params in param_sets:
                if self.iteration >= self.max_iterations:
                    break

                self.iteration += 1

                try:
                    result = func(self.df, **params)
                    self.all_results.append(result)

                    # Track best
                    if result.strategy not in self.best_by_strategy:
                        self.best_by_strategy[strategy_name] = result
                    else:
                        current_best = self.best_by_strategy[strategy_name]
                        # Prefer: meets DD target, then highest return
                        if (result.max_drawdown_pct < TARGETS["max_drawdown_pct"]
                                and result.total_return_pct > current_best.total_return_pct):
                            self.best_by_strategy[strategy_name] = result
                        elif (result.max_drawdown_pct < current_best.max_drawdown_pct
                              and result.total_return_pct >= current_best.total_return_pct * 0.9):
                            self.best_by_strategy[strategy_name] = result

                    # Track winners
                    if result.is_winner:
                        self.winners.append(result)
                        print(f"  🏆 WINNER #{len(self.winners)} | "
                              f"Return: {result.total_return_pct}% | "
                              f"DD: {result.max_drawdown_pct}% | "
                              f"Trades: {result.total_trades} | "
                              f"WR: {result.win_rate}% | "
                              f"PF: {result.profit_factor}")
                        print(f"     Params: {result.params}")

                    # Progress indicator
                    if self.iteration % 10 == 0:
                        elapsed = time.time() - start_time
                        print(f"  ... iter {self.iteration} | "
                              f"Best Return: {best_return:.1f}% | "
                              f"Best DD: {best_dd:.1f}% | "
                              f"Elapsed: {elapsed:.0f}s")

                except Exception as e:
                    print(f"  ⚠️  Error at iter {self.iteration}: {e}")
                    continue

        elapsed = time.time() - start_time
        self._print_final_report(elapsed)
        self._save_results()

    def _print_final_report(self, elapsed: float):
        """Print comprehensive final report."""
        print(f"\n{'=' * 70}")
        print(f"📊 OPTIMIZATION COMPLETE — {elapsed:.1f}s | {self.iteration} iterations")
        print(f"{'=' * 70}")

        # Winners
        print(f"\n🏆 WINNERS FOUND: {len(self.winners)}")
        print(f"   (Return >= {TARGETS['min_return_pct']}% AND Max DD < {TARGETS['max_drawdown_pct']}%)")
        for i, w in enumerate(self.winners[:10], 1):
            print(f"  {i}. {w.strategy}")
            print(f"     Return: {w.total_return_pct}% | DD: {w.max_dd}% | "
                  f"Trades: {w.total_trades} | WR: {w.win_rate}% | PF: {w.profit_factor} | "
                  f"Sharpe: {w.sharpe_ratio}")
            print(f"     Params: {w.params}")

        # Best by strategy
        print(f"\n📈 BEST RESULTS BY STRATEGY:")
        for name, result in sorted(self.best_by_strategy.items()):
            status = "✅" if result.is_winner else "❌"
            print(f"  {status} {name}:")
            print(f"     Return: {result.total_return_pct}% | DD: {result.max_drawdown_pct}% | "
                  f"Trades: {result.total_trades} | WR: {result.win_rate}% | PF: {result.profit_factor}")
            print(f"     Params: {result.params}")

        # Summary stats
        if self.all_results:
            returns = [r.total_return_pct for r in self.all_results]
            dds = [r.max_drawdown_pct for r in self.all_results]
            print(f"\n📊 OVERALL STATS:")
            print(f"  Total tests: {len(self.all_results)}")
            print(f"  Return range: {min(returns):.1f}% to {max(returns):.1f}%")
            print(f"  DD range: {min(dds):.1f}% to {max(dds):.1f}%")
            print(f"  Profitable tests: {sum(1 for r in returns if r > 0)}/{len(returns)}")
            print(f"  Winners (meeting targets): {len(self.winners)}")

    def _save_results(self):
        """Save all results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save summary
        summary = {
            "timestamp": timestamp,
            "targets": TARGETS,
            "total_iterations": self.iteration,
            "winners_count": len(self.winners),
            "winners": [asdict(w) for w in self.winners[:20]],
            "best_by_strategy": {
                name: asdict(result) for name, result in self.best_by_strategy.items()
            },
        }

        summary_file = REPORTS_DIR / f"optimization_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n💾 Summary saved: {summary_file}")

        # Save winners separately for easy access
        if self.winners:
            winners_file = REPORTS_DIR / "winning_strategies.json"
            with open(winners_file, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "winners": [asdict(w) for w in self.winners]
                }, f, indent=2, default=str)
            print(f"💾 Winners saved: {winners_file}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Strategy Optimizer")
    parser.add_argument("--strategy", type=str, default=None,
                        choices=["Symmetry_Trap", "P90_CFD_Expansion", "EMA_Cross", "WMA_Crossover"],
                        help="Optimize a specific strategy (default: all)")
    parser.add_argument("--max-iterations", type=int, default=500,
                        help="Maximum iterations (default: 500)")
    args = parser.parse_args()

    optimizer = HermesOptimizer(
        strategy_filter=args.strategy,
        max_iterations=args.max_iterations,
    )
    optimizer.run_optimization()
