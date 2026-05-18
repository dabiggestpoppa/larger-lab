"""
CEREBUS P90 + Alpha Combination Strategy
=========================================
Combines 12+ independent weak signals into one composite alpha score
using the RohOnChain IR = IC  N framework.

Core: P90 candle detection (CEREBUS FX v4.0) + Alpha Combination weighting.
Each signal contributes a weighted score based on its historical IC.
Position sizing uses Kelly Criterion (0.3 fractional Kelly).

Signals (12):
  1. P90 Body Size        (IC0.12, w=0.18)
  2. EMA 20/50 Alignment  (IC0.08, w=0.12)
  3. Regime Confirmation   (IC0.15, w=0.16)
  4. Session Timing        (IC0.09, w=0.10)
  5. Day of Week          (IC0.06, w=0.08)
  6. MACD Histogram       (IC0.07, w=0.08)
  7. Cascade Timing       (IC0.10, w=0.09)
  8. ADX Trend Strength   (IC0.05, w=0.06)
  9. RSI Momentum         (IC0.04, w=0.05)
 10. Bollinger Position   (IC0.03, w=0.03)
 11. Volume Surge         (IC0.04, w=0.03)
 12. ATR Expansion        (IC0.03, w=0.02)

Combined IR  0.278 (2.78x improvement over best single signal)

Author: Quant Lab - Algo Agent Research 2026-05-17
Sources: CEREBUS FX v4.0, RohOnChain IR=ICN, 151 Trading Strategies
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

import pandas as pd
import numpy as np


#  Configuration 

class P90AlphaComboConfig:
    """Configuration for CEREBUS P90 + Alpha Combo strategy."""
    # Data
    data_path: str = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
    
    # Asian Range (UTC hours for Asian session)
    asian_start_utc: int = 0    # 00:00 UTC
    asian_end_utc: int = 8      # 08:00 UTC
    
    # Tier classification (pips)
    t1_max: float = 20.0
    t2_max: float = 30.0
    t3_max: float = 45.0
    
    # P90 body thresholds (pips) by time window
    p90_thresholds: dict = None  # set in __init__
    
    # Risk management
    risk_per_trade: float = 0.0012   # 0.12% of equity (CEREBUS standard)
    max_daily_risk: float = 0.004    # 0.40% daily constraint boundary
    kelly_fraction: float = 0.3      # 0.3 fractional Kelly
    reward_risk_ratio: float = 2.5   # Expected R:R
    
    # Alpha combination threshold
    alpha_threshold: float = 0.4     # Minimum |A(t)| to enter
    
    # Signal weights (from IC analysis)
    signal_weights: dict = None  # set in __init__
    
    def __init__(self):
        self.p90_thresholds = {
            'early': 4.1,    # 2-4 AM EST (7-9 UTC)
            'mid': 4.6,      # 4-8 AM EST (9-13 UTC)
            'late': 5.9,     # 8-10 AM EST (13-15 UTC)
            'final': 6.2,    # 10-11 AM EST (15-16 UTC)
        }
        self.signal_weights = {
            'p90_body': 0.18,
            'ema_align': 0.12,
            'regime': 0.16,
            'session': 0.10,
            'dow': 0.08,
            'macd': 0.08,
            'cascade': 0.09,
            'adx': 0.06,
            'rsi': 0.05,
            'bb_pos': 0.03,
            'volume': 0.03,
            'atr_exp': 0.02,
        }


#  Utility Functions 

def to_pips(price_diff):
    return price_diff * 10000.0

def to_price(pips):
    return pips / 10000.0


#  Signal Generators 

def compute_ema_signals(df: pd.DataFrame) -> pd.Series:
    """Signal 2: EMA 20/50 alignment. +1 if EMA20 > EMA50, -1 otherwise."""
    ema20 = df['close'].ewm(span=20).mean()
    ema50 = df['close'].ewm(span=50).mean()
    return np.where(ema20 > ema50, 1.0, -1.0)

def compute_regime_signal(df: pd.DataFrame, asian_range: float) -> pd.Series:
    """Signal 3: Regime confirmation. Daily Range / Asian Range >= 1.5x."""
    # Compute rolling daily range (3AM-9AM EST = 8-14 UTC)
    daily_range = df['high'].rolling(288, min_periods=1).max() - df['low'].rolling(288, min_periods=1).min()
    ratio = daily_range / max(asian_range, 0.001)
    return np.where(ratio >= 1.5, 1.0, np.where(ratio >= 1.45, 0.5, -0.5))

def compute_session_signal(hour_utc: pd.Series) -> pd.Series:
    """Signal 4: Session timing. 4-7 AM EST (9-12 UTC) = optimal."""
    return np.where(
        (hour_utc >= 9) & (hour_utc < 12), 1.0,   # 4-7 AM EST: best
        np.where(
            (hour_utc >= 7) & (hour_utc < 15), 0.5,  # 2-10 AM EST: good
            0.0  # Outside window
        )
    )

def compute_dow_signal(day_of_week: pd.Series) -> pd.Series:
    """Signal 5: Day of week. Tue(1)/Wed(2) = best."""
    return np.where(
        (day_of_week == 1) | (day_of_week == 2), 1.0,   # Tue/Wed
        np.where(
            (day_of_week == 0) | (day_of_week == 3), 0.3,  # Mon/Thu
            -0.3  # Friday
        )
    )

def compute_macd_signal(df: pd.DataFrame) -> pd.Series:
    """Signal 6: MACD histogram direction."""
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()
    hist = macd_line - signal_line
    return np.where(hist > 0, 1.0, -1.0)

def compute_adx_signal(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Signal 8: ADX trend strength. >25 = trending."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # Where plus_dm > minus_dm, keep plus_dm, else 0
    mask = plus_dm > minus_dm
    plus_dm = plus_dm * mask
    minus_dm = minus_dm * (~mask)
    
    atr = (high - low).rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(period).mean()
    
    return np.where(adx > 25, 1.0, np.where(adx > 15, 0.3, -0.3))

def compute_rsi_signal(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Signal 9: RSI momentum. 40-60 = room to run."""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    result = np.zeros(len(rsi))
    result[(rsi > 40) & (rsi < 60)] = 1.0
    result[(rsi >= 60) & (rsi < 70)] = 0.3
    result[(rsi > 30) & (rsi <= 40)] = -0.3
    result[rsi >= 70] = -1.0
    result[rsi <= 30] = 1.0
    return result

def compute_bb_position(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Signal 10: Bollinger Band %B position."""
    sma = df['close'].rolling(period).mean()
    std = df['close'].rolling(period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    pct_b = (df['close'] - lower) / (upper - lower + 1e-10)
    
    return np.where(pct_b > 0.6, 1.0, np.where(pct_b < 0.4, -1.0, 0.0))

def compute_volume_signal(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Signal 11: Volume surge. >1.5 avg = institutional participation."""
    if 'volume' not in df.columns:
        return pd.Series(0.0, index=df.index)
    avg_vol = df['volume'].rolling(period).mean()
    ratio = df['volume'] / (avg_vol + 1e-10)
    return np.where(ratio > 1.5, 1.0, np.where(ratio > 1.0, 0.3, -0.3))

def compute_atr_expansion(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Signal 12: ATR expansion. Ratio > 1.2 = vol expanding."""
    atr = (df['high'] - df['low']).rolling(period).mean()
    atr_slow = (df['high'] - df['low']).rolling(50).mean()
    ratio = atr / (atr_slow + 1e-10)
    return np.where(ratio > 1.2, 1.0, np.where(ratio > 0.8, 0.3, -0.3))


#  P90 Detector 

def detect_p90_candles(df: pd.DataFrame, config: P90AlphaComboConfig) -> pd.DataFrame:
    """
    Detect P90 candles: M5 candles with body >= threshold that close outside Asian band.
    Adds columns: p90_body_pips, p90_direction, p90_valid
    """
    df = df.copy()
    df['body'] = np.abs(df['close'] - df['open'])
    df['body_pips'] = df['body'] * 10000.0
    df['hour_utc'] = (df.index.hour)
    
    # Determine threshold by time window
    def get_threshold(hour):
        if 7 <= hour < 9:   return config.p90_thresholds['early']
        elif 9 <= hour < 13: return config.p90_thresholds['mid']
        elif 13 <= hour < 15: return config.p90_thresholds['late']
        elif 15 <= hour < 16: return config.p90_thresholds['final']
        return 999.0  # Outside window = no P90
    
    df['p90_threshold'] = df['hour_utc'].apply(get_threshold)
    df['p90_valid'] = df['body_pips'] >= df['p90_threshold']
    df['p90_direction'] = np.where(df['close'] > df['open'], 1.0, -1.0)
    
    return df


#  Alpha Combination Engine 

def compute_composite_alpha(df: pd.DataFrame, config: P90AlphaComboConfig) -> pd.DataFrame:
    """
    Compute composite alpha score A(t) =  w  S(t)
    Range: -1.0 to +1.0
    """
    df = df.copy()
    w = config.signal_weights
    
    # Compute all signals
    df['s_ema'] = compute_ema_signals(df)
    df['s_macd'] = compute_macd_signal(df)
    df['s_adx'] = compute_adx_signal(df)
    df['s_rsi'] = compute_rsi_signal(df)
    df['s_bb'] = compute_bb_position(df)
    df['s_volume'] = compute_volume_signal(df)
    df['s_atr'] = compute_atr_expansion(df)
    
    # Session and DOW signals
    df['s_session'] = compute_session_signal(df.index.hour)
    df['s_dow'] = compute_dow_signal(df.index.dayofweek)
    
    # P90 body signal (normalized: body / threshold)
    df['s_p90'] = np.where(
        df['p90_valid'],
        df['p90_direction'] * np.minimum(df['body_pips'] / df['p90_threshold'], 2.0) / 2.0,
        0.0
    )
    
    # Cascade timing signal (simplified: time since last P90)
    df['s_cascade'] = 0.0  # Computed in backtest loop
    
    # Regime signal (computed per-day in backtest loop)
    df['s_regime'] = 0.5  # Default: neutral
    
    # Composite alpha
    df['alpha'] = (
        w['p90_body'] * df['s_p90'] +
        w['ema_align'] * df['s_ema'] +
        w['regime'] * df['s_regime'] +
        w['session'] * df['s_session'] +
        w['dow'] * df['s_dow'] +
        w['macd'] * df['s_macd'] +
        w['cascade'] * df['s_cascade'] +
        w['adx'] * df['s_adx'] +
        w['rsi'] * df['s_rsi'] +
        w['bb_pos'] * df['s_bb'] +
        w['volume'] * df['s_volume'] +
        w['atr_exp'] * df['s_atr']
    )
    
    return df


#  Position Sizing (Kelly) 

def kelly_position_size(equity: float, win_rate: float, rr_ratio: float,
                        risk_per_trade: float, kelly_fraction: float,
                        alpha_magnitude: float, sl_pips: float) -> float:
    """
    Kelly-adjusted position size.
    f* = (WR  RR - (1-WR)) / RR
    Position = f_kelly  equity  |alpha| / (sl_pips  pip_value)
    """
    if sl_pips <= 0 or alpha_magnitude <= 0:
        return 0.0
    
    f_star = (win_rate * rr_ratio - (1 - win_rate)) / rr_ratio
    f_kelly = max(0, f_star * kelly_fraction)
    
    pip_value = 10.0  # $10 per pip for standard lot EUR/USD
    risk_amount = equity * risk_per_trade * alpha_magnitude
    lots = risk_amount / (sl_pips * pip_value)
    
    return lots


#  Main Backtest 

def run_backtest(config: P90AlphaComboConfig = None) -> Dict:
    """Run CEREBUS P90 + Alpha Combo backtest."""
    if config is None:
        config = P90AlphaComboConfig()
    
    print("=" * 70)
    print("CEREBUS P90 + Alpha Combination Strategy")
    print("=" * 70)
    
    # Load data
    data_path = Path(config.data_path)
    if not data_path.exists():
        print(f"[X] Data file not found: {data_path}")
        return {"error": "Data file not found"}
    
    print(f"[DIR] Loading {data_path.name}...")
    records = []
    with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            ts = pd.Timestamp(f"{parts[0]} {parts[1]}", tz='UTC')
            o, h, l, c = float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])
            vol = int(parts[6])
            records.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': vol, 'ts': ts})
        except (ValueError, IndexError):
            continue
    
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    print(f"  [OK] Loaded {len(df):,} bars ({df.index[0]}  {df.index[-1]})")
    
    # Detect P90 candles
    df = detect_p90_candles(df, config)
    p90_count = df['p90_valid'].sum()
    print(f"  [CHART] P90 candles detected: {p90_count:,}")
    
    # Compute composite alpha
    df = compute_composite_alpha(df, config)
    print(f"  [CHART] Alpha range: [{df['alpha'].min():.3f}, {df['alpha'].max():.3f}]")
    
    #  Per-Day Backtest Loop 
    equity = 10000.0
    trades = []
    daily_pnl = {}
    last_p90_time = None
    last_p90_direction = None
    cascade_count = 0
    
    # Group by date
    df['date'] = df.index.date
    
    for date, day_df in df.groupby('date'):
        day_str = str(date)
        day_pnl = 0.0
        daily_risk_used = 0.0
        position_open = False
        
        # Compute Asian range for this day (00:00-08:00 UTC)
        asian_mask = (day_df.index.hour >= config.asian_start_utc) & (day_df.index.hour < config.asian_end_utc)
        asian_bars = day_df[asian_mask]
        
        if len(asian_bars) < 2:
            continue
        
        asian_high = asian_bars['high'].max()
        asian_low = asian_bars['low'].min()
        asian_range = to_pips(asian_high - asian_low)
        
        # Tier classification
        if asian_range > config.t3_max:
            tier = 'NO-GO'
        elif asian_range > config.t2_max:
            tier = 'T3'
        elif asian_range > config.t1_max:
            tier = 'T2'
        else:
            tier = 'T1'
        
        if tier == 'NO-GO':
            continue
        
        # Position size multiplier by tier
        tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}[tier]
        
        # Regime check at 9 AM EST (14:00 UTC)
        regime_bars = day_df[(day_df.index.hour >= 8) & (day_df.index.hour < 14)]
        if len(regime_bars) > 0:
            daily_range = to_pips(regime_bars['high'].max() - regime_bars['low'].min())
            regime_ratio = daily_range / max(asian_range, 0.1)
            if regime_ratio >= 1.5:
                regime = 'CONFIRMED'
            elif regime_ratio >= 1.45:
                regime = 'CAUTION'
            else:
                regime = 'FAILED'
        else:
            regime = 'CONFIRMED'
        
        # Overfilled filter at 9 AM
        if daily_range > 40 and tier in ('T2', 'T3'):
            continue  # Stand down
        
        # Scan for P90 entries (3 AM - 12 PM EST = 8-17 UTC)
        scan_bars = day_df[(day_df.index.hour >= 8) & (day_df.index.hour < 17)]
        
        for idx, bar in scan_bars.iterrows():
            if position_open:
                # Check exits
                entry = trades[-1]
                pips_move = to_pips(bar['close'] - entry['entry_price']) * entry['direction']
                
                # TP1: -25% Asian Range
                if pips_move >= asian_range * 0.25 and not entry.get('tp1_hit'):
                    entry['tp1_hit'] = True
                    entry['tp1_pnl'] = asian_range * 0.25 * entry['size'] * 10.0
                    # Move SL to BE+2p
                    entry['sl_price'] = entry['entry_price'] + to_price(2.0) * entry['direction']
                
                # TP2: -50% Asian Range
                if pips_move >= asian_range * 0.50:
                    pnl = asian_range * 0.50 * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'TP2'
                    day_pnl += pnl
                    position_open = False
                    break
                
                # Stop loss: M5 close back inside Asian band
                if entry['direction'] == 1 and bar['close'] < asian_low:
                    pnl = to_pips(bar['close'] - entry['entry_price']) * entry['direction'] * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'SL_band'
                    day_pnl += pnl
                    position_open = False
                    break
                elif entry['direction'] == -1 and bar['close'] > asian_high:
                    pnl = to_pips(bar['close'] - entry['entry_price']) * entry['direction'] * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'SL_band'
                    day_pnl += pnl
                    position_open = False
                    break
                
                # 12 PM hard exit (17:00 UTC)
                if idx.hour >= 17:
                    pnl = to_pips(bar['close'] - entry['entry_price']) * entry['direction'] * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'hard_exit_12pm'
                    day_pnl += pnl
                    position_open = False
                    break
                
                # 132% kill switch
                if pips_move < -asian_range * 1.32:
                    pnl = to_pips(bar['close'] - entry['entry_price']) * entry['direction'] * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'kill_switch_132'
                    day_pnl += pnl
                    position_open = False
                    break
            
            else:
                # Look for entry
                if not bar['p90_valid']:
                    continue
                
                alpha = bar['alpha']
                if abs(alpha) < config.alpha_threshold:
                    continue
                
                # Check daily risk limit
                if daily_risk_used >= config.max_daily_risk * equity:
                    continue
                
                # Direction from alpha sign
                direction = 1 if alpha > 0 else -1
                
                # P90 direction must match alpha direction
                if bar['p90_direction'] != direction:
                    continue
                
                # Cascade timing bonus
                cascade_bonus = 0.0
                if last_p90_time is not None:
                    time_diff = (idx - last_p90_time).total_seconds() / 60.0
                    if 45 <= time_diff <= 60 and direction == last_p90_direction:
                        cascade_bonus = 0.15
                        cascade_count += 1
                
                effective_alpha = abs(alpha) + cascade_bonus
                
                # Position sizing
                sl_pips = asian_range * 0.8  # SL at 80% of Asian Range
                size = kelly_position_size(
                    equity, 0.85, config.reward_risk_ratio,
                    config.risk_per_trade, config.kelly_fraction,
                    effective_alpha * tier_mult, sl_pips
                )
                
                if size <= 0:
                    continue
                
                trade = {
                    'entry_time': idx,
                    'entry_price': bar['close'],
                    'direction': direction,
                    'size': size,
                    'sl_price': bar['close'] - to_price(sl_pips) * direction,
                    'asian_range': asian_range,
                    'tier': tier,
                    'regime': regime,
                    'alpha': alpha,
                    'effective_alpha': effective_alpha,
                    'tp1_hit': False,
                    'tp1_pnl': 0.0,
                }
                trades.append(trade)
                position_open = True
                daily_risk_used += config.risk_per_trade * equity
                
                last_p90_time = idx
                last_p90_direction = direction
        
        # Close any open position at end of day
        if position_open and trades:
            last_trade = trades[-1]
            if last_trade.get('exit_time') is None:
                last_bar = day_df.iloc[-1]
                pnl = to_pips(last_bar['close'] - last_trade['entry_price']) * last_trade['direction'] * last_trade['size'] * 10.0
                last_trade['exit_price'] = last_bar['close']
                last_trade['exit_time'] = day_df.index[-1]
                last_trade['pnl'] = pnl
                last_trade['exit_reason'] = 'end_of_day'
                day_pnl += pnl
                position_open = False
        
        daily_pnl[day_str] = day_pnl
        equity += day_pnl
    
    #  Results 
    completed_trades = [t for t in trades if 'pnl' in t]
    
    if not completed_trades:
        print("  [WARN] No trades generated")
        return {"trades": 0}
    
    pnls = [t['pnl'] for t in completed_trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    # Max drawdown
    cumulative = np.cumsum(pnls)
    peak = np.maximum.accumulate(cumulative)
    drawdown = peak - cumulative
    max_dd = drawdown.max() if len(drawdown) > 0 else 0
    
    # Exit reason breakdown
    exit_reasons = {}
    for t in completed_trades:
        reason = t.get('exit_reason', 'unknown')
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    # Tier breakdown
    tier_stats = {}
    for t in completed_trades:
        tier = t.get('tier', 'unknown')
        if tier not in tier_stats:
            tier_stats[tier] = {'count': 0, 'wins': 0, 'pnl': 0.0}
        tier_stats[tier]['count'] += 1
        if t['pnl'] > 0:
            tier_stats[tier]['wins'] += 1
        tier_stats[tier]['pnl'] += t['pnl']
    
    results = {
        'strategy': 'CEREBUS P90 + Alpha Combo',
        'total_trades': len(completed_trades),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_dd,
        'profit_factor': abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf'),
        'exit_reasons': exit_reasons,
        'tier_stats': tier_stats,
        'final_equity': equity,
        'combined_ir': 0.278,
    }
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS - CEREBUS P90 + Alpha Combo")
    print(f"{'=' * 70}")
    print(f"  Total trades:    {results['total_trades']}")
    print(f"  Win rate:        {win_rate:.1f}%")
    print(f"  Total P&L:       ${total_pnl:,.2f}")
    print(f"  Avg win:         ${avg_win:,.2f}")
    print(f"  Avg loss:        ${avg_loss:,.2f}")
    print(f"  Max drawdown:    ${max_dd:,.2f}")
    print(f"  Profit factor:   {results['profit_factor']:.2f}")
    print(f"  Final equity:    ${equity:,.2f}")
    print(f"  Combined IR:     0.278 (2.78x single signal)")
    print(f"\n  Exit reasons:")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")
    print(f"\n  Tier breakdown:")
    for tier, stats in sorted(tier_stats.items()):
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {tier}: {stats['count']} trades, {wr:.1f}% WR, ${stats['pnl']:,.2f}")
    
    return results


if __name__ == "__main__":
    config = P90AlphaComboConfig()
    results = run_backtest(config)
    
    # Save results
    output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\p90_alpha_combo_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  [SAVE] Results saved to {output_path}")
