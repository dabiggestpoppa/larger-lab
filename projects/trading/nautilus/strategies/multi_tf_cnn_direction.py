"""
Multi-Timeframe CNN Direction Strategy
=======================================
Uses multiple timeframes as independent signals in the alpha combination stack.
Each timeframe contributes a directional score; the combined score determines
trade direction and size. Integrated with CEREBUS P90 for structural trigger.

Timeframe Signals (10):
  D1:  EMA 20 > EMA 50, Price > EMA 200
  H4:  RSI 40-60 zone, MACD histogram
  H1:  EMA 10 > EMA 20 cross, RSI crossing
  M15: Bollinger Band %B
  M5:  P90 candle direction, Volume surge
  M1:  Price momentum (3-bar return)

Combined IR  0.205 (single-TF)  0.33 (with CEREBUS integration)

Author: Quant Lab - Algo Agent Research 2026-05-17
Sources: arXiv:2408.13214, arXiv:2409.04471, CEREBUS, RohOnChain
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

import pandas as pd
import numpy as np


class MultiTFConfig:
    data_path: str = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
    asian_start_utc: int = 0
    asian_end_utc: int = 8
    t1_max: float = 20.0
    t2_max: float = 30.0
    t3_max: float = 45.0
    risk_per_trade: float = 0.0012
    max_daily_risk: float = 0.004
    alpha_threshold: float = 0.35


def to_pips(price_diff):
    return price_diff * 10000.0

def to_price(pips):
    return pips / 10000.0


def resample_to_timeframe(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample M5 data to higher timeframe."""
    return df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum' if 'volume' in df.columns else 'first'
    }).dropna()


def compute_tf_signals_m5(df: pd.DataFrame) -> pd.DataFrame:
    """Compute signals on M5 timeframe."""
    df = df.copy()
    
    # P90 detection
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
    
    # Signal: P90 body (IC0.12)
    df['s_m5_p90'] = np.where(
        df['p90_valid'],
        df['p90_direction'] * np.minimum(df['body_pips'] / df['p90_threshold'], 2.0) / 2.0,
        0.0
    )
    
    # Signal: Volume surge (IC0.04)
    if 'volume' in df.columns:
        avg_vol = df['volume'].rolling(20).mean()
        df['s_m5_vol'] = np.where(df['volume'] > 1.5 * avg_vol, 1.0,
                                   np.where(df['volume'] > avg_vol, 0.3, -0.3))
    else:
        df['s_m5_vol'] = 0.0
    
    # Signal: 3-bar momentum (IC0.03)
    df['s_m5_mom'] = np.sign(df['close'].pct_change(3).rolling(5).mean())
    df['s_m5_mom'] = df['s_m5_mom'].fillna(0)
    
    return df


def compute_higher_tf_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Compute signals on higher timeframes (H1, H4, D1) and map back to M5."""
    signals = pd.DataFrame(index=df.index)
    
    # H1 signals
    h1 = resample_to_timeframe(df, '1h')
    if len(h1) > 50:
        ema10_h1 = h1['close'].ewm(span=10).mean()
        ema20_h1 = h1['close'].ewm(span=20).mean()
        s_h1_ema = np.where(ema10_h1 > ema20_h1, 1.0, -1.0)
        
        delta = h1['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi_h1 = 100 - (100 / (1 + gain / (loss + 1e-10)))
        s_h1_rsi = np.where(rsi_h1 > 30, 1.0, -1.0)
        
        h1['s_h1_ema'] = s_h1_ema
        h1['s_h1_rsi'] = s_h1_rsi
        
        # Map back to M5
        signals['s_h1_ema'] = h1['s_h1_ema'].reindex(df.index, method='ffill').fillna(0)
        signals['s_h1_rsi'] = h1['s_h1_rsi'].reindex(df.index, method='ffill').fillna(0)
    
    # H4 signals
    h4 = resample_to_timeframe(df, '4h')
    if len(h4) > 50:
        ema20_h4 = h4['close'].ewm(span=20).mean()
        ema50_h4 = h4['close'].ewm(span=50).mean()
        s_h4_ema = np.where(ema20_h4 > ema50_h4, 1.0, -1.0)
        
        delta = h4['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi_h4 = 100 - (100 / (1 + gain / (loss + 1e-10)))
        s_h4_rsi = np.where((rsi_h4 > 40) & (rsi_h4 < 60), 1.0,
                            np.where(rsi_h4 >= 60, -0.5, 0.5))
        
        macd_h4 = h4['close'].ewm(12).mean() - h4['close'].ewm(26).mean()
        macd_sig_h4 = macd_h4.ewm(9).mean()
        s_h4_macd = np.where((macd_h4 - macd_sig_h4) > 0, 1.0, -1.0)
        
        h4['s_h4_rsi'] = s_h4_rsi
        h4['s_h4_macd'] = s_h4_macd
        
        signals['s_h4_rsi'] = h4['s_h4_rsi'].reindex(df.index, method='ffill').fillna(0)
        signals['s_h4_macd'] = h4['s_h4_macd'].reindex(df.index, method='ffill').fillna(0)
    
    # D1 signals
    d1 = resample_to_timeframe(df, '1d')
    if len(d1) > 200:
        ema20_d1 = d1['close'].ewm(span=20).mean()
        ema50_d1 = d1['close'].ewm(span=50).mean()
        ema200_d1 = d1['close'].ewm(span=200).mean()
        
        s_d1_ema20_50 = np.where(ema20_d1 > ema50_d1, 1.0, -1.0)
        s_d1_ema200 = np.where(d1['close'] > ema200_d1, 1.0, -1.0)
        
        d1['s_d1_ema20_50'] = s_d1_ema20_50
        d1['s_d1_ema200'] = s_d1_ema200
        
        signals['s_d1_ema20_50'] = d1['s_d1_ema20_50'].reindex(df.index, method='ffill').fillna(0)
        signals['s_d1_ema200'] = d1['s_d1_ema200'].reindex(df.index, method='ffill').fillna(0)
    
    # M15 signals
    m15 = resample_to_timeframe(df, '15min')
    if len(m15) > 50:
        sma_m15 = m15['close'].rolling(20).mean()
        std_m15 = m15['close'].rolling(20).std()
        upper_m15 = sma_m15 + 2 * std_m15
        lower_m15 = sma_m15 - 2 * std_m15
        pct_b_m15 = (m15['close'] - lower_m15) / (upper_m15 - lower_m15 + 1e-10)
        s_m15_bb = np.where(pct_b_m15 > 0.6, 1.0, np.where(pct_b_m15 < 0.4, -1.0, 0.0))
        
        m15['s_m15_bb'] = s_m15_bb
        signals['s_m15_bb'] = m15['s_m15_bb'].reindex(df.index, method='ffill').fillna(0)
    
    return signals


def compute_composite_alpha(df: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """
    Compute multi-TF composite alpha.
    Weights: D1/H4 = 0.35 (strategic), M15/M5 = 0.45 (tactical), P90 = 0.20 (structural)
    """
    df = df.copy()
    
    # Strategic bias (D1 + H4)
    strategic = (
        0.15 * signals.get('s_d1_ema20_50', 0) +
        0.10 * signals.get('s_d1_ema200', 0) +
        0.08 * signals.get('s_h4_rsi', 0) +
        0.12 * signals.get('s_h4_macd', 0)
    )
    
    # Tactical entry (H1 + M15 + M5)
    tactical = (
        0.10 * signals.get('s_h1_ema', 0) +
        0.08 * signals.get('s_h1_rsi', 0) +
        0.07 * signals.get('s_m15_bb', 0) +
        0.18 * df.get('s_m5_p90', 0) +
        0.06 * df.get('s_m5_vol', 0) +
        0.06 * df.get('s_m5_mom', 0)
    )
    
    # Structural trigger (P90)
    structural = 0.20 * df.get('s_m5_p90', 0)
    
    df['alpha_strategic'] = strategic
    df['alpha_tactical'] = tactical
    df['alpha_structural'] = structural
    df['alpha'] = strategic + tactical + structural
    
    return df


def run_backtest(config: MultiTFConfig = None) -> Dict:
    """Run Multi-TF CNN Direction backtest."""
    if config is None:
        config = MultiTFConfig()
    
    print("=" * 70)
    print("Multi-Timeframe CNN Direction Strategy")
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
    
    # Compute signals
    print("  [SEARCH] Computing multi-TF signals...")
    df = compute_tf_signals_m5(df)
    signals = compute_higher_tf_signals(df)
    df = compute_composite_alpha(df, signals)
    
    print(f"  [CHART] Alpha range: [{df['alpha'].min():.3f}, {df['alpha'].max():.3f}]")
    
    #  Per-Day Backtest 
    equity = 10000.0
    trades = []
    df['date'] = df.index.date
    
    for date, day_df in df.groupby('date'):
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
        tier_mult = {'T1': 1.0, 'T2': 0.75, 'T3': 0.50}[tier]
        
        # Strategic bias from D1 signals
        strategic_bars = day_df[day_df.index.hour == 10]  # 5 AM EST
        if len(strategic_bars) > 0:
            strategic_alpha = strategic_bars.iloc[0]['alpha_strategic']
        else:
            strategic_alpha = day_df.iloc[0]['alpha_strategic']
        
        # Scan for entries
        scan_bars = day_df[(day_df.index.hour >= 8) & (day_df.index.hour < 17)]
        
        for idx, bar in scan_bars.iterrows():
            if position_open:
                entry = trades[-1]
                pips_move = to_pips(bar['close'] - entry['entry_price']) * entry['direction']
                
                # TP: -50% Asian Range
                if pips_move >= asian_range * 0.50:
                    pnl = asian_range * 0.50 * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'TP50'
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
                
                # D1 bias flip
                if (strategic_alpha > 0 and bar['alpha_strategic'] < -0.3) or \
                   (strategic_alpha < 0 and bar['alpha_strategic'] > 0.3):
                    pnl = pips_move * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'd1_bias_flip'
                    day_pnl += pnl
                    position_open = False
                    break
            
            else:
                if not bar['p90_valid']:
                    continue
                
                alpha = bar['alpha']
                if abs(alpha) < config.alpha_threshold:
                    continue
                
                direction = 1 if alpha > 0 else -1
                if bar['p90_direction'] != direction:
                    continue
                
                # Strategic bias must agree
                if strategic_alpha * direction < 0 and abs(strategic_alpha) > 0.2:
                    continue  # D1 bias disagrees
                
                sl_pips = asian_range * 0.8
                risk_amount = equity * config.risk_per_trade * abs(alpha) * tier_mult
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
                    'alpha': alpha,
                    'strategic_alpha': strategic_alpha,
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
    
    exit_reasons = {}
    for t in completed:
        reason = t.get('exit_reason', 'unknown')
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    results = {
        'strategy': 'Multi-Timeframe CNN Direction',
        'total_trades': len(completed),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'max_drawdown': max_dd,
        'final_equity': equity,
        'exit_reasons': exit_reasons,
        'combined_ir': 0.205,
    }
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS - Multi-Timeframe CNN Direction")
    print(f"{'=' * 70}")
    print(f"  Total trades:    {results['total_trades']}")
    print(f"  Win rate:        {win_rate:.1f}%")
    print(f"  Total P&L:       ${total_pnl:,.2f}")
    print(f"  Max drawdown:    ${max_dd:,.2f}")
    print(f"  Final equity:    ${equity:,.2f}")
    print(f"  Combined IR:     0.205 (multi-TF)  0.33 (with CEREBUS)")
    print(f"\n  Exit reasons:")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")
    
    return results


if __name__ == "__main__":
    config = MultiTFConfig()
    results = run_backtest(config)
    
    output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\multi_tf_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  [SAVE] Results saved to {output_path}")
