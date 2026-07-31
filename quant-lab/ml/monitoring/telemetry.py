"""
Phase 5: Telemetry & Metrics Exporter
========================================
Pushes metrics to Prometheus-compatible endpoint.
"""
from __future__ import annotations

import time
import logging
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class CerebusTelemetry:
    """
    Collects and exports CEREBUS ML metrics.
    Compatible with Prometheus / Grafana.
    """

    def __init__(self, pushgateway_url: str = None, db_path: str = None):
        self.pushgateway_url = pushgateway_url
        self.db_path = db_path or str(
            Path(__file__).resolve().parent.parent / "data" / "telemetry.db"
        )
        self.metrics = {}
        self.trade_log = []

    def record_trade(self, symbol: str, regime: str, direction: str,
                     entry: float, exit_price: float, r_multiple: float,
                     quality_score: float):
        """Record a completed trade."""
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "regime": regime,
            "direction": direction,
            "entry": entry,
            "exit": exit_price,
            "r_multiple": r_multiple,
            "quality_score": quality_score,
        }
        self.trade_log.append(trade)

    def record_regime_prediction(self, symbol: str, regime: str, confidence: float):
        """Record a regime prediction."""
        key = f"regime_{regime.lower()}"
        self.metrics[key] = self.metrics.get(key, 0) + 1
        self.metrics["regime_total"] = self.metrics.get("regime_total", 0) + 1

    def record_guardrail_rejection(self, symbol: str, reason: str):
        """Record a guardrail rejection."""
        self.metrics["guardrail_rejections"] = self.metrics.get("guardrail_rejections", 0) + 1

    def record_kill_switch(self, symbol: str, reason: str):
        """Record a kill switch event."""
        self.metrics["kill_switches"] = self.metrics.get("kill_switches", 0) + 1

    def get_rolling_win_rate(self, window: int = 50) -> float:
        """Calculate rolling win rate over last N trades."""
        if not self.trade_log:
            return 0.0
        recent = self.trade_log[-window:]
        wins = sum(1 for t in recent if t["r_multiple"] > 0)
        return wins / len(recent) * 100

    def get_cumulative_pnl_r(self) -> float:
        """Calculate cumulative P&L in R-multiples."""
        return sum(t["r_multiple"] for t in self.trade_log)

    def get_regime_distribution(self) -> dict:
        """Get regime distribution."""
        total = self.metrics.get("regime_total", 0)
        if total == 0:
            return {}
        return {
            regime: count / total
            for regime, count in self.metrics.items()
            if regime.startswith("regime_") and regime != "regime_total"
        }

    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        timestamp_ms = int(time.time() * 1000)

        # Rolling WR
        wr = self.get_rolling_win_rate()
        lines.append(f"cerebus_rolling_win_rate_50 {wr} {timestamp_ms}")

        # Cumulative P&L
        pnl = self.get_cumulative_pnl_r()
        lines.append(f"cerebus_cumulative_pnl_r {pnl} {timestamp_ms}")

        # Guardrail rejections
        lines.append(f"cerebus_guardrail_rejection_total {self.metrics.get('guardrail_rejections', 0)} {timestamp_ms}")

        # Kill switches
        lines.append(f"cerebus_kill_switch_total {self.metrics.get('kill_switches', 0)} {timestamp_ms}")

        return "\n".join(lines)

    def save_state(self, path: str | Path = None):
        """Save telemetry state to JSON."""
        if path is None:
            path = Path(__file__).resolve().parent.parent / "data" / "telemetry_state.json"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "metrics": self.metrics,
            "trade_log": self.trade_log,
            "saved_at": datetime.utcnow().isoformat(),
        }
        with open(path, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def load_state(self, path: str | Path = None):
        """Load telemetry state from JSON."""
        if path is None:
            path = Path(__file__).resolve().parent.parent / "data" / "telemetry_state.json"
        path = Path(path)
        if path.exists():
            with open(path) as f:
                state = json.load(f)
            self.metrics = state.get("metrics", {})
            self.trade_log = state.get("trade_log", [])
