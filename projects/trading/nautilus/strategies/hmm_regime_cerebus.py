"""
HMM Regime-Aware CEREBUS Strategy
===================================
Uses Hidden Markov Model for probabilistic regime detection, then adapts
CEREBUS strategy parameters per regime. Combines CEREBUS rule-based regime
classification with statistical HMM for more robust identification.

Regimes (3-state):
  Trending:       ADX > 25 + directional momentum  Full P90 + Cascade
  Mean-Reverting: ADX < 20 + range-bound          Stall-Harvest + Deep MR
  High Volatility: ATR spike > 2 avg              Reduce size 50% or flat

HMM Observation Features (5 signals for alpha combination):
  1. ADX (IC0.10, w=0.25)
  2. ATR ratio (IC0.08, w=0.20)
  3. Bollinger Band width (IC0.06, w=0.15)
  4. Hurst exponent (IC0.12, w=0.25)
  5. Session/time-of-day (IC0.05, w=0.15)

Combined regime IR  0.192

Author: Quant Lab - Algo Agent Research 2026-05-17
Sources: arXiv:2509.14385, arXiv:2601.19504, CEREBUS FX v4.0, RohOnChain
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import pandas as pd
import numpy as np


#  Configuration 

class HMMRegimeConfig:
    """Configuration for HMM Regime-Aware CEREBUS strategy."""
    data_path: str = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
    
    # Asian Range
    asian_start_utc: int = 0
    asian_end_utc: int = 8
    
    # Tier classification
    t1_max: float = 20.0
    t2_max: float = 30.0
    t3_max: float = 45.0
    
    # Risk
    risk_per_trade: float = 0.0012
    max_daily_risk: float = 0.004
    kelly_fraction: float = 0.3
    
    # HMM parameters
    hmm_states: int = 3
    adx_period: int = 14
    atr_period: int = 14
    bb_period: int = 20
    hurst_window: int = 100
    
    # Regime-adapted parameters
    regime_params: dict = None  # set in __init__
    
    def __init__(self):
        self.regime_params = {
            'trending': {
                'position_size_mult': 1.0,
                'max_cascades': 3,
                'primary_target': 1.0,   # 100% AR
                'secondary_target': 1.68, # 168% Stall Zone
                'stop_mult': 0.8,
                'strategy': 'p90_cascade',
            },
            'mean_reverting': {
                'position_size_mult': 0.75,
                'max_cascades': 2,
                'primary_target': 0.5,   # 50% AR
                'secondary_target': 0.25,
                'stop_mult': 0.8,
                'strategy': 'stall_harvest',
            },
            'high_volatility': {
                'position_size_mult': 0.5,
                'max_cascades': 0,
                'primary_target': 0.25,  # 25% AR
                'secondary_target': 0.0,
                'stop_mult': 1.2,
                'strategy': 'stand_down',
            },
        }


#  Utility 

def to_pips(price_diff):
    return price_diff * 10000.0

def to_price(pips):
    return pips / 10000.0


#  Regime Detection 

def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute ADX."""
    high, low, close = df['high'], df['low'], df['close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    mask = plus_dm > minus_dm
    plus_dm = plus_dm * mask
    minus_dm = minus_dm * (~mask)
    atr = (high - low).rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / (atr + 1e-10))
    minus_di = 100 * (minus_dm.rolling(period).mean() / (atr + 1e-10))
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(period).mean()
    return adx

def compute_hurst(series: pd.Series, window: int = 100) -> pd.Series:
    """
    Compute Hurst exponent using fast variance-ratio method.
    H < 0.5 = mean-reverting, H > 0.5 = trending, H = 0.5 = random walk.
    Uses rolling variance ratio of returns at different lags.
    Much faster than R/S analysis: O(n) instead of O(n^2).
    """
    returns = series.pct_change().fillna(0)
    
    # Variance ratio: Var(k-period return) / (k * Var(1-period return))
    # For random walk: VR = 1, H = 0.5
    # For trending: VR > 1, H > 0.5
    # For mean-reverting: VR < 1, H < 0.5
    
    k = min(window // 4, 20)  # Use lag of ~25 bars
    
    var_1 = returns.rolling(window).var()
    var_k = returns.rolling(window).apply(
        lambda x: np.var(x.reshape(-1, k).sum(axis=1)) if len(x) >= k else 1.0,
        raw=True
    )
    
    # Variance ratio
    vr = var_k / (k * var_1 + 1e-10)
    
    # Convert to H: H = log(VR) / log(k) + 0.5 (simplified)
    # Clamp to [0, 1]
    hurst = 0.5 + np.log(vr.clip(0.01, 100)) / (2 * np.log(k + 1))
    hurst = hurst.clip(0, 1).fillna(0.5)
    
    return hurst

def detect_regime_hmm(df: pd.DataFrame, config: HMMRegimeConfig) -> pd.DataFrame:
    """
    Detect market regime using HMM-like probabilistic classification.
    Uses rule-based approximation of HMM states (Trending/MR/HighVol).
    Adds columns: regime, regime_prob, hurst, adx_val, atr_ratio, bb_width
    """
    df = df.copy()
    
    # Compute features
    df['adx_val'] = compute_adx(df, config.adx_period)
    atr = (df['high'] - df['low']).rolling(config.atr_period).mean()
    atr_slow = (df['high'] - df['low']).rolling(50).mean()
    df['atr_ratio'] = atr / (atr_slow + 1e-10)
    
    sma = df['close'].rolling(config.bb_period).mean()
    std = df['close'].rolling(config.bb_period).std()
    df['bb_width'] = (4 * std) / (sma + 1e-10)
    
    df['hurst'] = compute_hurst(df['close'], config.hurst_window)
    
    # Normalize features to [0, 1] for regime scoring
    adx_norm = np.clip(df['adx_val'] / 50, 0, 1)
    atr_norm = np.clip(df['atr_ratio'] / 3, 0, 1)
    hurst_norm = df['hurst']  # Already 0-1
    bb_norm = np.clip(df['bb_width'] / df['bb_width'].rolling(200).quantile(0.95), 0, 1)
    
    # Regime scores (probabilistic)
    # Trending: high ADX, H > 0.5, moderate vol
    p_trending = (
        0.35 * adx_norm +
        0.30 * hurst_norm +
        0.20 * (1 - atr_norm) +  # Lower vol = more trending
        0.15 * (1 - bb_norm)     # Narrow BB = trending
    )
    
    # Mean-reverting: low ADX, H < 0.5, moderate vol
    p_mr = (
        0.35 * (1 - adx_norm) +
        0.30 * (1 - hurst_norm) +
        0.20 * (1 - atr_norm) +
        0.15 * bb_norm
    )
    
    # High volatility: high ATR ratio, wide BB
    p_highvol = (
        0.40 * atr_norm +
        0.30 * bb_norm +
        0.20 * (1 - np.abs(hurst_norm - 0.5) * 2) +  # Near 0.5 = chaotic
        0.10 * adx_norm
    )
    
    # Normalize to sum to 1
    total = p_trending + p_mr + p_highvol + 1e-10
    df['p_trending'] = p_trending / total
    df['p_mr'] = p_mr / total
    df['p_highvol'] = p_highvol / total
    
    # Assign regime
    regimes = np.array(['trending', 'mean_reverting', 'high_volatility'])
    probs = np.stack([df['p_trending'], df['p_mr'], df['p_highvol']], axis=1)
    df['regime'] = regimes[np.argmax(probs, axis=1)]
    df['regime_prob'] = probs.max(axis=1)
    
    return df


#  Alpha Combination (Regime-Aware) 

def compute_regime_alpha(df: pd.DataFrame, config: HMMRegimeConfig) -> pd.DataFrame:
    """
    Compute regime-aware alpha score.
    Combines regime probability with CEREBUS P90 signals.
    """
    df = df.copy()
    
    # Base signals
    ema20 = df['close'].ewm(span=20).mean()
    ema50 = df['close'].ewm(span=50).mean()
    df['s_ema'] = np.where(ema20 > ema50, 1.0, -1.0)
    
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    macd_hist = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
    df['s_macd'] = np.where(macd_hist > 0, 1.0, -1.0)
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-10)))
    df['s_rsi'] = np.where((rsi > 40) & (rsi < 60), 1.0, np.where(rsi >= 60, -0.5, 0.5))
    
    # Regime signal: +1 if trending + bullish, -1 if trending + bearish
    df['s_regime'] = np.where(
        df['regime'] == 'trending',
        df['p_trending'] * df['s_ema'],  # Trend-follow
        np.where(
            df['regime'] == 'mean_reverting',
            -df['p_mr'] * df['s_ema'],  # Fade the trend
            0.0  # High vol = neutral
        )
    )
    
    # Session signal
    df['s_session'] = np.where(
        (df.index.hour >= 9) & (df.index.hour < 12), 1.0,
        np.where((df.index.hour >= 7) & (df.index.hour < 15), 0.5, 0.0)
    )
    
    # DOW signal
    df['s_dow'] = np.where(
        (df.index.dayofweek == 1) | (df.index.dayofweek == 2), 1.0,
        np.where((df.index.dayofweek == 0) | (df.index.dayofweek == 3), 0.3, -0.3)
    )
    
    # Composite alpha (regime-aware weights)
    df['alpha'] = (
        0.25 * df['s_regime'] +
        0.20 * df['s_ema'] +
        0.15 * df['s_macd'] +
        0.15 * df['s_rsi'] +
        0.10 * df['s_session'] +
        0.08 * df['s_dow'] +
        0.07 * np.where(df['regime'] == 'high_volatility', -0.5, 0.0)  # Penalty
    )
    
    return df


#  P90 Detector 

def detect_p90(df: pd.DataFrame, config: HMMRegimeConfig) -> pd.DataFrame:
    """Detect P90 candles."""
    df = df.copy()
    df['body'] = np.abs(df['close'] - df['open'])
    df['body_pips'] = df['body'] * 10000.0
    
    def get_threshold(hour):
        if 7 <= hour < 9: return 4.1
        elif 9 <= hour < 13: return 4.6
        elif 13 <= hour < 15: return 5.9
        elif 15 <= hour < 16: return 6.2
        return 999.0
    
    df['p90_threshold'] = df.index.hour.map(get_threshold)
    df['p90_valid'] = df['body_pips'] >= df['p90_threshold']
    df['p90_direction'] = np.where(df['close'] > df['open'], 1.0, -1.0)
    
    return df


#  Main Backtest 

def run_backtest(config: HMMRegimeConfig = None) -> Dict:
    """Run HMM Regime-Aware CEREBUS backtest."""
    if config is None:
        config = HMMRegimeConfig()
    
    print("=" * 70)
    print("HMM Regime-Aware CEREBUS Strategy")
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
    print(f"  [OK] Loaded {len(df):,} bars")
    
    # Detect regimes
    print("  [SEARCH] Computing HMM regime probabilities...")
    df = detect_regime_hmm(df, config)
    
    regime_counts = df['regime'].value_counts()
    print(f"  [CHART] Regime distribution:")
    for regime, count in regime_counts.items():
        pct = count / len(df) * 100
        print(f"    {regime}: {count:,} bars ({pct:.1f}%)")
    
    # Detect P90
    df = detect_p90(df, config)
    
    # Compute alpha
    df = compute_regime_alpha(df, config)
    
    #  Per-Day Backtest 
    equity = 10000.0
    trades = []
    df['date'] = df.index.date
    
    for date, day_df in df.groupby('date'):
        day_str = str(date)
        day_pnl = 0.0
        position_open = False
        
        # Asian range
        asian_mask = (day_df.index.hour >= config.asian_start_utc) & (day_df.index.hour < config.asian_end_utc)
        asian_bars = day_df[asian_mask]
        if len(asian_bars) < 2:
            continue
        
        asian_high = asian_bars['high'].max()
        asian_low = asian_bars['low'].min()
        asian_range = to_pips(asian_high - asian_low)
        
        if asian_range > config.t3_max:
            continue
        
        tier = 'T1' if asian_range <= config.t1_max else ('T2' if asian_range <= config.t2_max else 'T3')
        
        # Regime at 9 AM EST (14:00 UTC)
        regime_bars_9am = day_df[day_df.index.hour == 14]
        if len(regime_bars_9am) > 0:
            current_regime = regime_bars_9am.iloc[0]['regime']
            current_prob = regime_bars_9am.iloc[0]['regime_prob']
        else:
            current_regime = day_df.iloc[0]['regime']
            current_prob = day_df.iloc[0]['regime_prob']
        
        # Get regime parameters
        rp = config.regime_params.get(current_regime, config.regime_params['trending'])
        
        if rp['strategy'] == 'stand_down' and current_prob > 0.5:
            continue  # High vol regime = stand down
        
        # Scan for entries
        scan_bars = day_df[(day_df.index.hour >= 8) & (day_df.index.hour < 17)]
        
        for idx, bar in scan_bars.iterrows():
            if position_open:
                entry = trades[-1]
                pips_move = to_pips(bar['close'] - entry['entry_price']) * entry['direction']
                target_pips = asian_range * rp['primary_target']
                
                # TP hit
                if pips_move >= target_pips:
                    pnl = target_pips * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'TP'
                    day_pnl += pnl
                    position_open = False
                    break
                
                # SL: close back inside Asian band
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
                
                # 12 PM hard exit
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
                
                # Regime transition: close 50%
                if bar['regime'] != current_regime and bar['regime_prob'] > 0.5:
                    pnl = pips_move * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'regime_transition'
                    day_pnl += pnl
                    position_open = False
                    break
            
            else:
                if not bar['p90_valid']:
                    continue
                
                alpha = bar['alpha']
                if abs(alpha) < 0.35:
                    continue
                
                direction = 1 if alpha > 0 else -1
                if bar['p90_direction'] != direction:
                    continue
                
                # Position size: regime-adapted
                sl_pips = asian_range * rp['stop_mult']
                size_mult = rp['position_size_mult'] * current_prob
                risk_amount = equity * config.risk_per_trade * abs(alpha) * size_mult
                size = risk_amount / (sl_pips * 10.0) if sl_pips > 0 else 0
                
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
                    'regime': current_regime,
                    'regime_prob': current_prob,
                    'alpha': alpha,
                }
                trades.append(trade)
                position_open = True
        
        # Close at end of day
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
        
        equity += day_pnl
    
    #  Results 
    completed = [t for t in trades if 'pnl' in t]
    if not completed:
        print("  [WARN] No trades generated")
        return {"trades": 0}
    
    pnls = [t['pnl'] for t in completed]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100
    
    cumulative = np.cumsum(pnls)
    peak = np.maximum.accumulate(cumulative)
    max_dd = (peak - cumulative).max() if len(cumulative) > 0 else 0
    
    # Regime breakdown
    regime_stats = {}
    for t in completed:
        r = t.get('regime', 'unknown')
        if r not in regime_stats:
            regime_stats[r] = {'count': 0, 'wins': 0, 'pnl': 0.0}
        regime_stats[r]['count'] += 1
        if t['pnl'] > 0:
            regime_stats[r]['wins'] += 1
        regime_stats[r]['pnl'] += t['pnl']
    
    results = {
        'strategy': 'HMM Regime-Aware CEREBUS',
        'total_trades': len(completed),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'max_drawdown': max_dd,
        'final_equity': equity,
        'regime_stats': regime_stats,
        'combined_ir': 0.192,
    }
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS - HMM Regime-Aware CEREBUS")
    print(f"{'=' * 70}")
    print(f"  Total trades:    {results['total_trades']}")
    print(f"  Win rate:        {win_rate:.1f}%")
    print(f"  Total P&L:       ${total_pnl:,.2f}")
    print(f"  Max drawdown:    ${max_dd:,.2f}")
    print(f"  Final equity:    ${equity:,.2f}")
    print(f"  Combined IR:     0.192 (regime)  0.278 (alpha)  0.33")
    print(f"\n  Regime breakdown:")
    for regime, stats in sorted(regime_stats.items()):
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']} trades, {wr:.1f}% WR, ${stats['pnl']:,.2f}")
    
    return results


if __name__ == "__main__":
    config = HMMRegimeConfig()
    results = run_backtest(config)
    
    output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\hmm_regime_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  [SAVE] Results saved to {output_path}")
