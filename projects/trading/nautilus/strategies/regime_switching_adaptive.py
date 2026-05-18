"""
Regime-Switching Adaptive Strategy
====================================

Dynamically switches between trend-following and mean-reversion sub-strategies
based on detected market regime (Trending / Mean-Reverting / High-Volatility).

Sources:
  - arXiv:2509.14385 — "Adaptive and Regime-Aware RL for Portfolio Optimization"
  - arXiv:2601.19504 — "Hybrid AI-Driven Trading System with Market Regime Adaptation"
  - arXiv:2510.03236 — "Regime-Switching Volatility Forecasting"

REGIME DETECTION:
  Trending:      ADX > 25 + ATR ratio < 1.5  → Use EMA crossover (trend-follow)
  Mean-Reverting: ADX < 20 + BB width < avg   → Use RSI extremes (mean-reversion)
  High-Volatility: ATR ratio > 2.0            → Reduce exposure / stay flat

Author: Quant Lab — Algo Agent Research 2026-05-17
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

import pandas as pd
import numpy as np


class Regime(str, Enum):
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    HIGH_VOLATILITY = "high_volatility"


class RSATrade:
    def __init__(self, entry_time, direction, entry_price, sl_price, tp_price,
                 size_lots, regime, session):
        self.entry_time = entry_time
        self.direction = direction
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.size_lots = size_lots
        self.regime = regime
        self.session = session
        self.exit_time = None
        self.exit_price = None
        self.pnl_pips = 0.0
        self.result = ""
        self.exit_reason = ""


class RegimeSwitchingConfig:
    def __init__(self()):
        # Regime detection
        self.adx_trend_threshold = 25
        self.adx_mr_threshold = 20
        self.atr_vol_threshold = 2.0       # ATR ratio for high-vol
        self.atr_lookback = 14
        self.bb_lookback = 20
        self.adx_lookback = 14

        # Trend-following params (EMA crossover)
        self.fast_ema = 20
        self.slow_ema = 50
        self.trend_sl_atr_mult = 2.0
        self.trend_tp_atr_mult = 3.0

        # Mean-reversion params (RSI extremes)
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.mr_sl_atr_mult = 1.5
        self.mr_tp_atr_mult = 2.0

        # Session timing (EST = UTC - 5)
        self.entry_start_est = 2
        self.entry_end_est = 16
        self.hard_exit_est = 17

        # Risk
        self.position_size_lots = 0.1
        self.max_daily_trades = 5


class RegimeSwitchingStrategy:
    def __init__(self, config: RegimeSwitchingConfig = None):
        self.cfg = config or RegimeSwitchingConfig()

    @staticmethod
    def _utc_to_est(utc_hour: int) -> int:
        return (utc_hour - 5 + 24) % 24

    def _get_est_hour(self, ts) -> int:
        return self._utc_to_est(ts.hour)

    @staticmethod
    def _to_pips(price_diff: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return price_diff * 100
        return price_diff * 10000

    @staticmethod
    def _to_price(pips: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return pips / 100
        return pips / 10000

    def _compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # EMA
        df["ema_fast"] = close.ewm(span=self.cfg.fast_ema, adjust=False).mean()
        df["ema_slow"] = close.ewm(span=self.cfg.slow_ema, adjust=False).mean()

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(span=self.cfg.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.cfg.rsi_period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))

        # ATR
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.ewm(span=self.cfg.atr_lookback, adjust=False).mean()
        df["atr_ratio"] = df["atr"] / df["atr"].rolling(50).mean()

        # ADX
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        # Where plus_dm > minus_dm, keep plus_dm, else 0
        mask = plus_dm > minus_dm
        plus_dm = plus_dm * mask
        minus_dm = minus_dm * (~mask)
        atr_smooth = df["atr"]
        plus_di = 100 * (plus_dm.ewm(span=self.cfg.adx_lookback, adjust=False).mean() / atr_smooth)
        minus_di = 100 * (minus_dm.ewm(span=self.cfg.adx_lookback, adjust=False).mean() / atr_smooth)
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
        df["adx"] = dx.ewm(span=self.cfg.adx_lookback, adjust=False).mean()
        df["plus_di"] = plus_di
        df["minus_di"] = minus_di

        # Bollinger Band width
        bb_mid = close.rolling(self.cfg.bb_lookback).mean()
        bb_std = close.rolling(self.cfg.bb_lookback).std()
        df["bb_width"] = (bb_std * 2) / bb_mid
        df["bb_width_avg"] = df["bb_width"].rolling(50).mean()

        return df

    def _detect_regime(self, row) -> Regime:
        adx = row.get("adx", 0) or 0
        atr_ratio = row.get("atr_ratio", 1) or 1
        bb_width = row.get("bb_width", 0) or 0
        bb_width_avg = row.get("bb_width_avg", 0) or 0

        if atr_ratio > self.cfg.atr_vol_threshold:
            return Regime.HIGH_VOLATILITY
        elif adx > self.cfg.adx_trend_threshold:
            return Regime.TRENDING
        elif adx < self.cfg.adx_mr_threshold and bb_width < bb_width_avg:
            return Regime.MEAN_REVERTING
        else:
            # Default to previous or neutral — use trending as fallback
            return Regime.TRENDING

    def run_backtest(self, df: pd.DataFrame, pair: str = "EUR/USD") -> Dict:
        if df is None or len(df) < 200:
            return {"error": "Insufficient data", "total_trades": 0}

        df = self._compute_indicators(df)
        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)

        df["est_hour"] = df.index.hour.map(self._utc_to_est)
        df["date"] = df.index.date

        active_trade: Optional[RSATrade] = None
        all_trades: List[RSATrade] = []
        last_date = None
        daily_trade_count = 0
        last_regime = Regime.TRENDING

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = row["est_hour"]
            date = row["date"]
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]

            # New day reset
            if date != last_date:
                if active_trade is not None and active_trade.exit_time is None:
                    dm = 1 if active_trade.direction == "LONG" else -1
                    active_trade.pnl_pips = self._to_pips((c - active_trade.entry_price) * dm, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = c
                    active_trade.result = "win" if active_trade.pnl_pips > 0 else "loss"
                    active_trade.exit_reason = "new_day"
                    all_trades.append(active_trade)
                    active_trade = None
                daily_trade_count = 0
                last_date = date

            # Manage active trade
            if active_trade is not None and active_trade.exit_time is None:
                dm = 1 if active_trade.direction == "LONG" else -1

                # SL check
                if active_trade.direction == "LONG" and l <= active_trade.sl_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.sl_price - active_trade.entry_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.sl_price
                    active_trade.result = "loss"
                    active_trade.exit_reason = "sl"
                    all_trades.append(active_trade)
                    active_trade = None
                elif active_trade.direction == "SHORT" and h >= active_trade.sl_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.entry_price - active_trade.sl_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.sl_price
                    active_trade.result = "loss"
                    active_trade.exit_reason = "sl"
                    all_trades.append(active_trade)
                    active_trade = None
                # TP check
                elif active_trade.direction == "LONG" and h >= active_trade.tp_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.tp_price - active_trade.entry_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.tp_price
                    active_trade.result = "win"
                    active_trade.exit_reason = "tp"
                    all_trades.append(active_trade)
                    active_trade = None
                elif active_trade.direction == "SHORT" and l <= active_trade.tp_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.entry_price - active_trade.tp_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.tp_price
                    active_trade.result = "win"
                    active_trade.exit_reason = "tp"
                    all_trades.append(active_trade)
                    active_trade = None
                # Max hold (4 hours = 48 bars on M5)
                else:
                    bars_held = i - df.index.get_loc(active_trade.entry_time) if active_trade.entry_time in df.index else 48
                    if bars_held >= 48:
                        active_trade.pnl_pips = self._to_pips((c - active_trade.entry_price) * dm, pair)
                        active_trade.exit_time = ts
                        active_trade.exit_price = c
                        active_trade.result = "win" if active_trade.pnl_pips > 0 else "loss"
                        active_trade.exit_reason = "max_hold"
                        all_trades.append(active_trade)
                        active_trade = None

            # Hard exit
            if est_h >= self.cfg.hard_exit_est:
                if active_trade is not None and active_trade.exit_time is None:
                    dm = 1 if active_trade.direction == "LONG" else -1
                    active_trade.pnl_pips = self._to_pips((c - active_trade.entry_price) * dm, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = c
                    active_trade.result = "win" if active_trade.pnl_pips > 0 else "loss"
                    active_trade.exit_reason = "hard_exit"
                    all_trades.append(active_trade)
                    active_trade = None
                continue

            # Skip if outside entry window or max daily trades
            if not (self.cfg.entry_start_est <= est_h < self.cfg.entry_end_est):
                continue
            if daily_trade_count >= self.cfg.max_daily_trades:
                continue

            # Detect regime
            regime = self._detect_regime(row)
            if regime == Regime.HIGH_VOLATILITY:
                last_regime = regime
                continue  # Skip entries in high vol

            atr = row.get("atr", 0) or 0
            if atr <= 0:
                continue

            # Generate signals based on regime
            if active_trade is None:
                direction = None

                if regime == Regime.TRENDING:
                    # EMA crossover for trend following
                    ema_fast = row.get("ema_fast", 0) or 0
                    ema_slow = row.get("ema_slow", 0) or 0
                    prev_fast = df.iloc[i-1].get("ema_fast", 0) or 0
                    prev_slow = df.iloc[i-1].get("ema_slow", 0) or 0

                    if prev_fast <= prev_slow and ema_fast > ema_slow:
                        direction = "LONG"
                    elif prev_fast >= prev_slow and ema_fast < ema_slow:
                        direction = "SHORT"

                elif regime == Regime.MEAN_REVERTING:
                    rsi = row.get("rsi", 50) or 50
                    if rsi < self.cfg.rsi_oversold:
                        direction = "LONG"
                    elif rsi > self.cfg.rsi_overbought:
                        direction = "SHORT"

                if direction is not None:
                    sl_dist = atr * (self.cfg.trend_sl_atr_mult if regime == Regime.TRENDING else self.cfg.mr_sl_atr_mult)
                    tp_dist = atr * (self.cfg.trend_tp_atr_mult if regime == Regime.TRENDING else self.cfg.mr_tp_atr_mult)

                    if direction == "LONG":
                        sl_price = c - sl_dist
                        tp_price = c + tp_dist
                    else:
                        sl_price = c + sl_dist
                        tp_price = c - tp_dist

                    session = f"{est_h}"
                    trade = RSATrade(
                        entry_time=ts,
                        direction=direction,
                        entry_price=c,
                        sl_price=sl_price,
                        tp_price=tp_price,
                        size_lots=self.cfg.position_size_lots,
                        regime=regime.value,
                        session=session,
                    )
                    active_trade = trade
                    daily_trade_count += 1

            last_regime = regime

        return self._calc_results(all_trades, pair)

    def _calc_results(self, trades: List[RSATrade], pair: str) -> Dict:
        if not trades:
            return {"strategy": "Regime_Switching_Adaptive", "pair": pair, "total_trades": 0, "error": "No trades"}

        pnls = [t.pnl_pips for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_pnl = sum(pnls)
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        cumulative = [0]
        for p in pnls:
            cumulative.append(cumulative[-1] + p)
        peak = cumulative[0]
        max_dd = 0
        for v in cumulative:
            if v > peak:
                peak = v
            dd = v - peak
            if dd < max_dd:
                max_dd = dd

        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # By regime
        by_regime = {}
        for t in trades:
            r = t.regime
            if r not in by_regime:
                by_regime[r] = {"trades": 0, "wins": 0, "pnl": 0}
            by_regime[r]["trades"] += 1
            by_regime[r]["pnl"] += t.pnl_pips
            if t.pnl_pips > 0:
                by_regime[r]["wins"] += 1

        by_regime_summary = {}
        for r, data in by_regime.items():
            by_regime_summary[r] = {
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl_pips": round(data["pnl"], 2),
            }

        by_exit = {}
        for t in trades:
            er = t.exit_reason
            if er not in by_exit:
                by_exit[er] = 0
            by_exit[er] += 1

        return {
            "strategy": "Regime_Switching_Adaptive",
            "pair": pair,
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl_pips": round(total_pnl, 2),
            "avg_win_pips": round(avg_win, 2),
            "avg_loss_pips": round(avg_loss, 2),
            "max_drawdown_pips": round(max_dd, 2),
            "profit_factor": round(profit_factor, 2),
            "by_regime": by_regime_summary,
            "by_exit_reason": by_exit,
            "timeframe": "M5",
        }


if __name__ == "__main__":
    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading {data_path.name}...")
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import _parse_csv
    df = _parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    strategy = RegimeSwitchingStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")

    print(f"\n{'='*60}")
    print(f"REGIME-SWITCHING ADAPTIVE BACKTEST RESULTS")
    print(f"{'='*60}")
    for k, v in results.items():
        if k not in ("by_regime", "by_exit_reason"):
            print(f"  {k:25s}: {v}")
    if "by_regime" in results:
        print(f"\n  By Regime:")
        for r, data in results["by_regime"].items():
            print(f"    {r:20s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")
    if "by_exit_reason" in results:
        print(f"\n  By Exit Reason:")
        for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:25s}: {count}")
    print(f"{'='*60}")

    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"regime_switching_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")
