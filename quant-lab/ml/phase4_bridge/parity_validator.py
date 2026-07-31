"""
Phase 4.4: Parity Validator
=============================
Compares live simulation metrics against backtest baseline.
"""
from __future__ import annotations

import numpy as np

DEFAULT_TOLERANCE = 0.05

BENCHMARKS = {
    "EURUSD": {"wr": 88.4, "r": 1.18, "pf": 4.18, "dd": 0.8, "trades_yr": 3842},
    "GBPUSD": {"wr": 86.2, "r": 1.35, "pf": 3.82, "dd": 0.9, "trades_yr": 4120},
    "USDCHF": {"wr": 87.9, "r": 1.21, "pf": 4.82, "dd": 0.6, "trades_yr": 3710},
    "USDJPY": {"wr": 85.8, "r": 1.42, "pf": 4.58, "dd": 0.7, "trades_yr": 3950},
    "AUDUSD": {"wr": 87.5, "r": 1.25, "pf": 4.42, "dd": 0.75, "trades_yr": 3620},
    "NZDUSD": {"wr": 85.7, "r": 1.25, "pf": 4.18, "dd": 0.85, "trades_yr": 3620},
    "CHFJPY": {"wr": 84.8, "r": 1.55, "pf": 4.82, "dd": 4.8, "trades_yr": 4210},
    "GBPJPY": {"wr": 82.9, "r": 1.75, "pf": 4.82, "dd": 5.4, "trades_yr": 4850},
    "GBPAUD": {"wr": 83.5, "r": 1.62, "pf": 4.82, "dd": 5.6, "trades_yr": 4450},
    "GBPNZD": {"wr": 85.8, "r": 1.48, "pf": 4.82, "dd": 5.2, "trades_yr": 4380},
    "GBPCHF": {"wr": 88.1, "r": 1.38, "pf": 4.82, "dd": 4.6, "trades_yr": 3890},
    "US500": {"wr": 92.3, "r": 0.92, "pf": 4.82, "dd": 3.8, "trades_yr": 2650},
    "DE30": {"wr": 91.4, "r": 0.98, "pf": 4.82, "dd": 4.1, "trades_yr": 2890},
    "FR40": {"wr": 91.1, "r": 1.01, "pf": 4.82, "dd": 4.2, "trades_yr": 2910},
    "USTEC100": {"wr": 90.2, "r": 1.08, "pf": 4.82, "dd": 4.8, "trades_yr": 3120},
    "HK50": {"wr": 89.2, "r": 1.12, "pf": 4.82, "dd": 5.1, "trades_yr": 3450},
    "XAUUSD": {"wr": 87.6, "r": 1.38, "pf": 4.82, "dd": 5.0, "trades_yr": 3800},
    "XAGUSD": {"wr": 85.4, "r": 1.52, "pf": 4.82, "dd": 5.8, "trades_yr": 3400},
    "BTCUSD": {"wr": 94.9, "r": 1.82, "pf": 4.82, "dd": 3.4, "trades_yr": 2847},
    "ETHUSD": {"wr": 79.2, "r": 2.05, "pf": 4.82, "dd": 7.8, "trades_yr": 3150},
}

TOLERANCES = {"wr": 2.0, "r": 0.2, "pf_min": 2.5, "dd_buffer": 2.0, "trades_min_pct": 0.80}


def validate_parity(backtest_metrics: dict, live_metrics: dict, tolerance: float = 0.05) -> dict:
    """Compare live metrics against backtest baseline."""
    issues = []

    baseline_wr = backtest_metrics.get("win_rate", 0)
    live_wr = live_metrics.get("win_rate", 0)
    if baseline_wr > 0:
        wr_drift = abs(live_wr - baseline_wr) / baseline_wr
        if wr_drift > tolerance:
            issues.append(f"Win Rate drift: {wr_drift:.1%} exceeds {tolerance:.1%} tolerance")

    baseline_r = backtest_metrics.get("avg_r", 0)
    live_r = live_metrics.get("avg_r", 0)
    if baseline_r > 0:
        r_drift = abs(live_r - baseline_r) / baseline_r
        if r_drift > tolerance:
            issues.append(f"R-Multiple drift: {r_drift:.1%} exceeds {tolerance:.1%} tolerance")

    if issues:
        return {"status": "DRIFT_DETECTED", "issues": issues}
    return {"status": "PARITY_CONFIRMED", "message": "Live matches backtest"}


class ParityValidator:
    """Stateful parity validator for live trading."""

    def __init__(self, backtest_metrics: dict, tolerance: float = DEFAULT_TOLERANCE):
        self.baseline = backtest_metrics
        self.tolerance = tolerance
        self.live_trades = []

    def record_live_trade(self, pnl_r: float):
        self.live_trades.append({"pnl_r": pnl_r})

    def validate(self) -> dict:
        if len(self.live_trades) < 10:
            return {"status": "INSUFFICIENT_DATA", "message": f"Need >=10 trades, have {len(self.live_trades)}"}

        live_wr = sum(1 for t in self.live_trades if t["pnl_r"] > 0) / len(self.live_trades)
        live_avg_r = float(np.mean([t["pnl_r"] for t in self.live_trades]))

        issues = []
        baseline_wr = self.baseline.get("win_rate", 0)
        if baseline_wr > 0:
            # Only flag drift when live is worse than baseline
            wr_diff = baseline_wr - live_wr  # Positive means live is worse
            if wr_diff > 0:
                wr_drift = wr_diff / baseline_wr if baseline_wr <= 1 else wr_diff / 100
                if wr_drift > self.tolerance:
                    issues.append(f"Win Rate drift: {wr_drift:.1%}")

        baseline_r = self.baseline.get("avg_r", 0)
        if baseline_r > 0:
            # Only flag drift when live avg R is worse
            r_diff = baseline_r - live_avg_r
            if r_diff > 0:
                r_drift = r_diff / abs(baseline_r)
                if r_drift > self.tolerance:
                    issues.append(f"R-Multiple drift: {r_drift:.1%}")

        if issues:
            return {"status": "DRIFT_DETECTED", "issues": issues, "live_trades": len(self.live_trades)}

        return {"status": "PARITY_CONFIRMED", "live_trades": len(self.live_trades),
                "live_win_rate": round(live_wr, 4), "live_avg_r": round(live_avg_r, 4)}

    def reset(self):
        self.live_trades = []
