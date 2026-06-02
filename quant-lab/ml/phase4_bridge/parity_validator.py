"""
Phase 4.4: Parity Validator
=============================
Compares live simulation metrics against backtest baseline.
Detects execution drift (spread spikes, slippage, logic bugs).
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_TOLERANCE = 0.05  # 5% drift tolerance


class ParityValidator:
    """
    Validates that live/paper trading matches backtest expectations.
    """

    def __init__(
        self,
        backtest_metrics: dict,
        tolerance: float = DEFAULT_TOLERANCE,
    ):
        """
        Parameters
        ----------
        backtest_metrics : dict
            Baseline metrics from backtest with keys:
            win_rate, avg_r, profit_factor, max_drawdown_pct, total_trades
        tolerance : float
            Max acceptable drift (e.g., 0.05 = 5%)
        """
        self.baseline = backtest_metrics
        self.tolerance = tolerance
        self.live_trades: list[dict] = []

    def record_live_trade(self, pnl_r: float):
        """Record a live/paper trade outcome (R-multiple)."""
        self.live_trades.append({"pnl_r": pnl_r})

    def validate(self) -> dict:
        """
        Compare live metrics against backtest baseline.

        Returns
        -------
        dict with status (PASS/FAIL), drift details, and recommendations
        """
        if len(self.live_trades) < 10:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Need ≥10 trades, have {len(self.live_trades)}",
            }

        live_wr = sum(1 for t in self.live_trades if t["pnl_r"] > 0) / len(self.live_trades)
        live_avg_r = np.mean([t["pnl_r"] for t in self.live_trades])

        issues = []

        # Win rate drift
        baseline_wr = self.baseline.get("win_rate", 0.0)
        if baseline_wr > 0:
            wr_drift = abs(live_wr - baseline_wr) / baseline_wr
            if wr_drift > self.tolerance:
                issues.append(
                    f"WR drift: {wr_drift:.1%} (live={live_wr:.1%} vs baseline={baseline_wr:.1%})"
                )

        # Avg R drift
        baseline_r = self.baseline.get("avg_r", 0.0)
        if baseline_r > 0:
            r_drift = abs(live_avg_r - baseline_r) / baseline_r
            if r_drift > self.tolerance:
                issues.append(
                    f"Avg R drift: {r_drift:.1%} (live={live_avg_r:.2f} vs baseline={baseline_r:.2f})"
                )

        if issues:
            return {
                "status": "DRIFT_DETECTED",
                "live_trades": len(self.live_trades),
                "live_win_rate": round(live_wr, 4),
                "live_avg_r": round(live_avg_r, 4),
                "issues": issues,
                "recommendation": "Investigate spread spikes, slippage, or logic bugs",
            }

        return {
            "status": "PARITY_CONFIRMED",
            "live_trades": len(self.live_trades),
            "live_win_rate": round(live_wr, 4),
            "live_avg_r": round(live_avg_r, 4),
            "message": "Live simulation matches backtest expectations",
        }

    def reset(self):
        """Reset live trade history."""
        self.live_trades = []
