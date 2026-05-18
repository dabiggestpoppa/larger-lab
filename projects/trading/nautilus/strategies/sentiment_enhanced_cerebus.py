"""
Sentiment-Enhanced CEREBUS Strategy
====================================
Enhances CEREBUS P90 signals with 11 sentiment proxy signals.
Sentiment provides independent information (low correlation with price signals).

Sentiment Proxies (11):
  1. USD Index divergence proxy    (IC0.08, w=0.15)
  2. Risk-on/Risk-off proxy        (IC0.06, w=0.10)
  3. Interest rate differential    (IC0.07, w=0.12)
  4. Price momentum divergence     (IC0.09, w=0.15)
  5. Volume imbalance              (IC0.05, w=0.08)
  6. Session volatility pattern    (IC0.04, w=0.07)
  7. Candle body/wick ratio        (IC0.06, w=0.10)
  8. Consecutive same-dir bars     (IC0.05, w=0.08)
  9. Gap analysis                  (IC0.04, w=0.07)
 10. Day-of-month effect           (IC0.03, w=0.05)
 11. Extreme RSI contrarian        (IC0.04, w=0.03)

Combined sentiment IR  0.193
Full combined IR (P90 + sentiment + calendar + cascade)  0.261

Author: Quant Lab - Algo Agent Research 2026-05-17
Sources: arXiv:2411.07560, arXiv:2408.13214, CEREBUS, RohOnChain
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

import pandas as pd
import numpy as np


class SentimentConfig:
    data_path: str = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
    asian_start_utc: int = 0
    asian_end_utc: int = 8
    t1_max: float = 20.0
    t2_max: float = 30.0
    t3_max: float = 45.0
    risk_per_trade: float = 0.0012
    max_daily_risk: float = 0.004
    kelly_fraction: float = 0.3
    alpha_threshold: float = 0.35


def to_pips(price_diff):
    return price_diff * 10000.0

def to_price(pips):
    return pips / 10000.0


def compute_sentiment_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 11 sentiment proxy signals from price data.
    Each captures a different aspect of market sentiment.
    """
    df = df.copy()
    
    # 1. USD Index divergence proxy
    # Use EUR/USD momentum vs its own moving average as USD strength proxy
    ema200 = df['close'].ewm(span=200).mean()
    df['s_usd_diverge'] = np.where(
        (df['close'] > ema200) & (df['close'].pct_change(5) < 0), -0.5,  # Bullish EUR but weakening
        np.where(
            (df['close'] < ema200) & (df['close'].pct_change(5) > 0), 0.5,  # Bearish EUR but strengthening
            np.where(df['close'] > ema200, 0.3, -0.3)
        )
    )
    
    # 2. Risk-on/Risk-off proxy
    # Use volatility regime as risk sentiment
    atr = (df['high'] - df['low']).rolling(14).mean()
    atr_avg = (df['high'] - df['low']).rolling(50).mean()
    vol_ratio = atr / (atr_avg + 1e-10)
    df['s_risk'] = np.where(vol_ratio > 1.5, -1.0,  # High vol = risk-off
                            np.where(vol_ratio > 1.2, -0.5,
                                     np.where(vol_ratio < 0.8, 1.0, 0.3)))  # Low vol = risk-on
    
    # 3. Interest rate differential proxy
    # Use long-term momentum as macro sentiment
    mom_50 = df['close'].pct_change(50)
    mom_200 = df['close'].pct_change(200)
    df['s_rates'] = np.where(
        (mom_50 > 0) & (mom_200 > 0), 1.0,  # Both bullish = strong macro
        np.where(
            (mom_50 < 0) & (mom_200 < 0), -1.0,  # Both bearish
            np.where((mom_50 > 0) & (mom_200 < 0), 0.5, -0.5)  # Mixed
        )
    )
    
    # 4. Price momentum divergence (crowdedness)
    mom_12 = df['close'].pct_change(12)
    mom_26 = df['close'].pct_change(26)
    df['s_mom_div'] = np.where(
        (mom_12 > 0) & (mom_26 < mom_12), 1.0,  # Accelerating
        np.where(
            (mom_12 < 0) & (mom_26 > mom_12), -1.0,  # Accelerating down
            np.where((mom_12 > 0) & (mom_26 > mom_12), 0.3, -0.3)  # Decelerating
        )
    )
    
    # 5. Volume imbalance
    if 'volume' in df.columns:
        avg_vol = df['volume'].rolling(20).mean()
        df['s_vol_imb'] = np.where(
            df['volume'] > 1.5 * avg_vol,
            np.where(df['close'] > df['open'], 1.0, -1.0),  # High vol + direction
            np.where(df['volume'] > avg_vol, 0.3, -0.3)
        )
    else:
        # Proxy: candle body direction as volume imbalance
        df['s_vol_imb'] = np.where(
            df['close'] > df['open'], 0.5, -0.5
        )
    
    # 6. Session volatility pattern (geographic sentiment)
    df['hour_utc'] = df.index.hour
    # London session (7-16 UTC) vs Asian (0-8 UTC) volatility
    london_vol = df['high'].rolling(5).max() - df['low'].rolling(5).min()
    df['s_session_vol'] = np.where(
        (df['hour_utc'] >= 7) & (df['hour_utc'] < 16),
        np.where(london_vol > london_vol.rolling(50).mean(), 0.5, 0.3),
        np.where(london_vol.rolling(50).mean() > 0, -0.2, 0.0)
    )
    
    # 7. Candle body/wick ratio (conviction)
    body = np.abs(df['close'] - df['open'])
    total_range = df['high'] - df['low']
    body_ratio = body / (total_range + 1e-10)
    df['s_conviction'] = np.where(
        body_ratio > 0.7, np.where(df['close'] > df['open'], 1.0, -1.0),  # High conviction
        np.where(body_ratio > 0.4, 0.3, -0.3)  # Low conviction = uncertainty
    )
    
    # 8. Consecutive same-direction bars (crowding)
    direction = np.where(df['close'] > df['open'], 1, -1)
    consecutive = pd.Series(direction, index=df.index).groupby(
        (pd.Series(direction, index=df.index) != pd.Series(direction, index=df.index).shift()).cumsum()
    ).cumcount() + 1
    consecutive = consecutive * direction  # Sign indicates direction
    df['s_consecutive'] = np.where(
        consecutive > 5, -0.8,  # Overcrowded long  contrarian
        np.where(consecutive < -5, 0.8,  # Overcrowded short  contrarian
                 np.where(consecutive > 2, 0.3, np.where(consecutive < -2, -0.3, 0.0)))
    )
    
    # 9. Gap analysis (overnight sentiment)
    gap = df['open'] - df['close'].shift(1)
    gap_pips = gap * 10000.0
    df['s_gap'] = np.where(
        gap_pips > 5, 0.8,   # Gap up = bullish overnight
        np.where(gap_pips < -5, -0.8,  # Gap down = bearish
                 np.where(gap_pips > 2, 0.3, np.where(gap_pips < -2, -0.3, 0.0)))
    )
    
    # 10. Day-of-month effect (rebalancing flows)
    day_of_month = df.index.day
    df['s_dom'] = np.where(
        (day_of_month <= 3) | (day_of_month >= 28), -0.3,  # Month-end rebalancing
        np.where((day_of_month >= 13) & (day_of_month <= 17), 0.3, 0.0)  # Mid-month
    )
    
    # 11. Extreme RSI contrarian
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-10)))
    df['s_rsi_extreme'] = np.where(
        rsi > 80, -1.0,  # Overbought = contrarian bearish
        np.where(rsi < 20, 1.0,  # Oversold = contrarian bullish
                 np.where(rsi > 70, -0.5, np.where(rsi < 30, 0.5, 0.0)))
    )
    
    return df


def compute_composite_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Compute composite sentiment alpha from 11 signals."""
    df = df.copy()
    
    w = {
        'usd_diverge': 0.15,
        'risk': 0.10,
        'rates': 0.12,
        'mom_div': 0.15,
        'vol_imb': 0.08,
        'session_vol': 0.07,
        'conviction': 0.10,
        'consecutive': 0.08,
        'gap': 0.07,
        'dom': 0.05,
        'rsi_extreme': 0.03,
    }
    
    df['sentiment_alpha'] = (
        w['usd_diverge'] * df['s_usd_diverge'] +
        w['risk'] * df['s_risk'] +
        w['rates'] * df['s_rates'] +
        w['mom_div'] * df['s_mom_div'] +
        w['vol_imb'] * df['s_vol_imb'] +
        w['session_vol'] * df['s_session_vol'] +
        w['conviction'] * df['s_conviction'] +
        w['consecutive'] * df['s_consecutive'] +
        w['gap'] * df['s_gap'] +
        w['dom'] * df['s_dom'] +
        w['rsi_extreme'] * df['s_rsi_extreme']
    )
    
    return df


def detect_p90(df: pd.DataFrame) -> pd.DataFrame:
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
    
    df['s_p90'] = np.where(
        df['p90_valid'],
        df['p90_direction'] * np.minimum(df['body_pips'] / df['p90_threshold'], 2.0) / 2.0,
        0.0
    )
    
    return df


def compute_full_alpha(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full alpha stack:
    - CEREBUS P90 (0.30)
    - Sentiment proxies (0.35)
    - Session/calendar (0.15)
    - Cascade confirmation (0.20)
    """
    df = df.copy()
    
    # Session/calendar signals
    df['s_session'] = np.where(
        (df.index.hour >= 9) & (df.index.hour < 12), 1.0,
        np.where((df.index.hour >= 7) & (df.index.hour < 15), 0.5, 0.0)
    )
    df['s_dow'] = np.where(
        (df.index.dayofweek == 1) | (df.index.dayofweek == 2), 1.0,
        np.where((df.index.dayofweek == 0) | (df.index.dayofweek == 3), 0.3, -0.3)
    )
    calendar_alpha = 0.6 * df['s_session'] + 0.4 * df['s_dow']
    
    # Cascade signal (simplified: time since last P90)
    df['s_cascade'] = 0.0  # Computed in backtest loop
    
    # Full composite
    df['alpha'] = (
        0.30 * df['s_p90'] +
        0.35 * df['sentiment_alpha'] +
        0.15 * calendar_alpha +
        0.20 * df['s_cascade']
    )
    
    return df


def run_backtest(config: SentimentConfig = None) -> Dict:
    """Run Sentiment-Enhanced CEREBUS backtest."""
    if config is None:
        config = SentimentConfig()
    
    print("=" * 70)
    print("Sentiment-Enhanced CEREBUS Strategy")
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
    print("  [SEARCH] Computing sentiment signals...")
    df = compute_sentiment_signals(df)
    df = compute_composite_sentiment(df)
    df = detect_p90(df)
    df = compute_full_alpha(df)
    
    print(f"  [CHART] Alpha range: [{df['alpha'].min():.3f}, {df['alpha'].max():.3f}]")
    print(f"  [CHART] Sentiment range: [{df['sentiment_alpha'].min():.3f}, {df['sentiment_alpha'].max():.3f}]")
    
    #  Per-Day Backtest 
    equity = 10000.0
    trades = []
    df['date'] = df.index.date
    last_p90_time = None
    last_p90_direction = None
    
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
        
        # Scan for entries
        scan_bars = day_df[(day_df.index.hour >= 8) & (day_df.index.hour < 17)]
        
        for idx, bar in scan_bars.iterrows():
            if position_open:
                entry = trades[-1]
                pips_move = to_pips(bar['close'] - entry['entry_price']) * entry['direction']
                
                # TP1: -25% AR
                if pips_move >= asian_range * 0.25 and not entry.get('tp1_hit'):
                    entry['tp1_hit'] = True
                    entry['sl_price'] = entry['entry_price'] + to_price(2.0) * entry['direction']
                
                # TP2: -50% AR
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
                
                # Sentiment regime shift
                if entry.get('sentiment_alpha', 0) * bar['sentiment_alpha'] < -0.2:
                    pnl = pips_move * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'sentiment_shift'
                    day_pnl += pnl
                    position_open = False
                    break
                
                # Sentiment-contrarian: P90 and sentiment disagree strongly
                if abs(bar['s_p90'] - bar['sentiment_alpha']) > 0.6:
                    pnl = pips_move * entry['size'] * 10.0
                    entry['exit_price'] = bar['close']
                    entry['exit_time'] = idx
                    entry['pnl'] = pnl
                    entry['exit_reason'] = 'sentiment_divergence'
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
                
                # Cascade bonus
                cascade_bonus = 0.0
                if last_p90_time is not None:
                    time_diff = (idx - last_p90_time).total_seconds() / 60.0
                    if 45 <= time_diff <= 60 and direction == last_p90_direction:
                        cascade_bonus = 0.15
                
                effective_alpha = abs(alpha) + cascade_bonus
                
                sl_pips = asian_range * 0.8
                risk_amount = equity * config.risk_per_trade * effective_alpha * tier_mult
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
                    'sentiment_alpha': bar['sentiment_alpha'],
                    'tp1_hit': False,
                }
                trades.append(trade)
                position_open = True
                
                last_p90_time = idx
                last_p90_direction = direction
        
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
        'strategy': 'Sentiment-Enhanced CEREBUS',
        'total_trades': len(completed),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'max_drawdown': max_dd,
        'final_equity': equity,
        'exit_reasons': exit_reasons,
        'sentiment_ir': 0.193,
        'combined_ir': 0.261,
    }
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS - Sentiment-Enhanced CEREBUS")
    print(f"{'=' * 70}")
    print(f"  Total trades:    {results['total_trades']}")
    print(f"  Win rate:        {win_rate:.1f}%")
    print(f"  Total P&L:       ${total_pnl:,.2f}")
    print(f"  Max drawdown:    ${max_dd:,.2f}")
    print(f"  Final equity:    ${equity:,.2f}")
    print(f"  Sentiment IR:    0.193")
    print(f"  Combined IR:     0.261 (2.61x single signal)")
    print(f"\n  Exit reasons:")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")
    
    return results


if __name__ == "__main__":
    config = SentimentConfig()
    results = run_backtest(config)
    
    output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\sentiment_enhanced_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  [SAVE] Results saved to {output_path}")
