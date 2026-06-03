"""
Phase 5.3: Shadow Mode Gauntlet
==================================
Protocol for promoting a new ML model or engine update from paper trading to live capital.
No model goes live without passing the Shadow Gauntlet.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ShadowModeGauntlet:
    """
    Runs new models in shadow mode (predict only, no real trades) for N days.
    Promotion criteria:
      1. Shadow WR within 2% of Backtest WR
      2. Shadow Max DD < Backtest DD
      3. No Guardrail Rejections
    """

    def __init__(
        self,
        model_name: str,
        backtest_wr: float,
        backtest_dd: float,
        shadow_days: int = 14,
    ):
        self.model_name = model_name
        self.backtest_wr = backtest_wr
        self.backtest_dd = backtest_dd
        self.shadow_days = shadow_days
        self.start_date = datetime.utcnow()
        self.end_date = self.start_date + timedelta(days=shadow_days)
        self.shadow_trades = []
        self.guardrail_rejections = 0
        self.is_active = True

    def record_shadow_trade(self, entry_price: float, exit_price: float, direction: int, r_multiple: float):
        """Record a hypothetical shadow trade."""
        self.shadow_trades.append({
            "entry": entry_price,
            "exit": exit_price,
            "direction": direction,
            "r_multiple": r_multiple,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def record_guardrail_rejection(self):
        """Record a guardrail rejection during shadow mode."""
        self.guardrail_rejections += 1

    def get_shadow_metrics(self) -> dict:
        """Calculate shadow mode performance metrics."""
        if not self.shadow_trades:
            return {"status": "NO_TRADES"}

        wins = [t for t in self.shadow_trades if t["r_multiple"] > 0]
        wr = len(wins) / len(self.shadow_trades) * 100

        # Calculate max DD
        cumulative = 0
        peak = 0
        max_dd = 0
        for t in self.shadow_trades:
            cumulative += t["r_multiple"]
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        return {
            "total_trades": len(self.shadow_trades),
            "win_rate": round(wr, 2),
            "max_drawdown": round(max_dd, 2),
            "avg_r": round(sum(t["r_multiple"] for t in self.shadow_trades) / len(self.shadow_trades), 3),
            "guardrail_rejections": self.guardrail_rejections,
        }

    def evaluate_promotion(self) -> dict:
        """
        Evaluate whether the model should be promoted to live capital.
        Returns promotion decision.
        """
        metrics = self.get_shadow_metrics()
        if metrics.get("status") == "NO_TRADES":
            return {"decision": "PENDING", "reason": "No shadow trades recorded yet"}

        checks = {
            "wr_within_2pct": abs(metrics["win_rate"] - self.backtest_wr) <= 2.0,
            "dd_acceptable": metrics["max_drawdown"] <= self.backtest_dd,
            "no_guardrail_rejections": self.guardrail_rejections == 0,
        }

        passed = all(checks.values())
        decision = "PROMOTE" if passed else "REJECT"

        result = {
            "decision": decision,
            "model_name": self.model_name,
            "shadow_metrics": metrics,
            "checks": checks,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

        if passed:
            logger.info(f"✅ SHADOW GAUNTLET PASSED: {self.model_name} promoted to LIVE")
        else:
            failed = [k for k, v in checks.items() if not v]
            logger.warning(f"❌ SHADOW GAUNTLET FAILED: {self.model_name} — {failed}")

        return result

    def is_complete(self) -> bool:
        """Check if shadow period is complete."""
        return datetime.utcnow() >= self.end_date

    def save_report(self, path: str | Path):
        path = Path(path)
        report = {
            "model_name": self.model_name,
            "shadow_period": f"{self.start_date.isoformat()} to {self.end_date.isoformat()}",
            "metrics": self.get_shadow_metrics(),
            "promotion": self.evaluate_promotion(),
        }
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
