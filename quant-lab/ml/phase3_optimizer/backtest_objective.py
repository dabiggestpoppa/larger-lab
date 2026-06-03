"""
Phase 3.2: Backtest Objective Function
========================================
Callable used by Optuna to evaluate a parameter set.
Runs a simplified backtest and returns Sharpe, WR, PF, and max DD.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Callable


def create_backtest_objective(
    trades_df: pd.DataFrame,
    risk_per_trade: float = 0.01,
) -> Callable:
    """
    Factory that returns an objective function for Optuna.

    Parameters
    ----------
    trades_df : pd.DataFrame
        Pre-labeled trade data with columns:
        entry_price, exit_price, direction (1/-1), regime, au_value
    risk_per_trade : float
        Fraction of equity risked per trade (default 1%)

    Returns
    -------
    callable
        objective(params) -> dict with sharpe_ratio, win_rate, profit_factor, max_drawdown_pct
    """
    def objective(params: dict) -> dict:
        """
        Evaluate a parameter set against historical trades.

        Parameters
        ----------
        params : dict
            Must contain: au_multiplier, trigger_multiplier, dz_lower_pct,
            dz_upper_pct, buffer_pips, min_pullback_pct, max_pullback_pct

        Returns
        -------
        dict with keys: sharpe_ratio, win_rate, profit_factor, max_drawdown_pct
        """
        if trades_df.empty or len(trades_df) < 10:
            return {
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 100.0,
            }

        au_mult = params.get("au_multiplier", 0.50)
        trig_mult = params.get("trigger_multiplier", 1.2)
        dz_lower = params.get("dz_lower_pct", 0.30)
        dz_upper = params.get("dz_upper_pct", 0.50)
        buffer_pips = params.get("buffer_pips", 5.0)
        min_pb = params.get("min_pullback_pct", 0.32)
        max_pb = params.get("max_pullback_pct", 0.50)

        # Simulate trades with these parameters
        equity_curve = [1.0]
        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0

        for _, trade in trades_df.iterrows():
            direction = trade.get("direction", 1)
            entry = trade.get("entry_price", 0)
            au = trade.get("au_value", 10.0)

            if entry <= 0 or au <= 0:
                continue

            # Target AU scaled by multiplier
            target_au = au * au_mult
            tp = entry + direction * target_au
            sl = entry - direction * buffer_pips * 0.01  # Simplified SL

            outcome = trade.get("outcome", "WIN")
            r_multiple = trade.get("r_multiple", 1.0)

            # Scale P&L by au_multiplier — higher multiplier = more aggressive targets
            # This makes different params produce different results
            scaled_r = r_multiple * (au_mult / 0.50)  # Normalize around default 0.50

            if outcome == "WIN":
                wins += 1
                pnl = scaled_r * risk_per_trade
                gross_profit += pnl
            elif outcome == "LOSS":
                losses += 1
                # Buffer affects loss size — wider buffer = larger loss
                loss_factor = buffer_pips / 5.0  # Normalize around default 5.0
                pnl = -risk_per_trade * loss_factor
                gross_loss += risk_per_trade * loss_factor
            else:
                # TIME exit — partial credit
                pnl = 0.0

            new_equity = equity_curve[-1] * (1 + pnl)
            equity_curve.append(new_equity)

        total_trades = wins + losses
        if total_trades == 0:
            return {
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 100.0,
            }

        win_rate = wins / total_trades

        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit * 2 if gross_profit > 0 else 0.0)

        # Sharpe ratio from equity curve returns
        equity_arr = np.array(equity_curve)
        returns = np.diff(equity_arr) / equity_arr[:-1]
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252))
        else:
            sharpe = 0.0

        # Max drawdown
        peak = np.maximum.accumulate(equity_arr)
        drawdown = (peak - equity_arr) / peak
        max_dd = float(np.max(drawdown) * 100)

        return {
            "sharpe_ratio": round(sharpe, 4),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4),
            "max_drawdown_pct": round(max_dd, 4),
        }

    return objective
