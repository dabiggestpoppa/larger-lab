"""
Phase 5.1: Execution Guardrail Interceptor
=============================================
Final safety net. Intercepts every order before broker submission.
Validates that SL/TP distances respect the asset's structural physics.
"""
from __future__ import annotations

import logging
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Minimum structural bounds per asset (derived from Phase 1 Tier Configs)
STRUCTURAL_BOUNDS = {
    "EURUSD":   {"min_sl_pips": 5.0,  "min_tp_pips": 10.0},
    "GBPUSD":   {"min_sl_pips": 5.0,  "min_tp_pips": 13.0},
    "USDCHF":   {"min_sl_pips": 5.0,  "min_tp_pips": 11.0},
    "USDJPY":   {"min_sl_pips": 6.0,  "min_tp_pips": 16.0},
    "AUDUSD":   {"min_sl_pips": 5.0,  "min_tp_pips": 11.0},
    "NZDUSD":   {"min_sl_pips": 6.0,  "min_tp_pips": 14.0},
    "CHFJPY":   {"min_sl_pips": 5.0,  "min_tp_pips": 14.0},
    "GBPJPY":   {"min_sl_pips": 8.0,  "min_tp_pips": 19.0},
    "GBPAUD":   {"min_sl_pips": 6.0,  "min_tp_pips": 14.0},
    "GBPNZD":   {"min_sl_pips": 6.0,  "min_tp_pips": 15.0},
    "GBPCHF":   {"min_sl_pips": 5.0,  "min_tp_pips": 13.0},
    "US500":    {"min_sl_pips": 8.0,  "min_tp_pips": 21.0},
    "DE30":     {"min_sl_pips": 8.0,  "min_tp_pips": 19.0},
    "FR40":     {"min_sl_pips": 8.0,  "min_tp_pips": 19.0},
    "USTEC100": {"min_sl_pips": 12.0, "min_tp_pips": 34.0},
    "HK50":     {"min_sl_pips": 37.0, "min_tp_pips": 92.0},
    "XAUUSD":   {"min_sl_pips": 12.0, "min_tp_pips": 16.0},
    "XAGUSD":   {"min_sl_pips": 5.0,  "min_tp_pips": 7.0},
    "BTCUSD":   {"min_sl_pips": 25.0, "min_tp_pips": 205.0},
    "ETHUSD":   {"min_sl_pips": 5.0,  "min_tp_pips": 35.0},
}


class ExecutionGuardrailInterceptor:
    """
    Phase 5 Safety Net. Intercepts every order before broker submission.
    Validates that SL/TP distances respect the asset's structural physics.
    """

    def __init__(self, symbol: str, pip_size: float = 1.0):
        self.symbol = symbol
        self.pip_size = pip_size
        self.bounds = STRUCTURAL_BOUNDS.get(symbol, {"min_sl_pips": 5.0, "min_tp_pips": 10.0})
        self.rejection_log = []

    def validate_order(
        self,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        current_spread_pips: float = 0.0,
    ) -> tuple[bool, str]:
        """
        Returns (is_valid, reason).
        If False, the order is KILLED locally and never reaches the broker.
        """
        sl_dist_pips = abs(entry_price - sl_price) / self.pip_size
        tp_dist_pips = abs(tp_price - entry_price) / self.pip_size

        # 1. Check SL Structural Integrity (0.1 pip tolerance for floating point)
        if sl_dist_pips < self.bounds["min_sl_pips"] - 0.1:
            msg = f"🛑 REJECTED: SL distance {sl_dist_pips:.1f}p below minimum {self.bounds['min_sl_pips']}p"
            self._log_rejection(msg)
            return False, msg

        # 2. Check TP Structural Integrity (0.1 pip tolerance for floating point)
        if tp_dist_pips < self.bounds["min_tp_pips"] - 0.1:
            msg = f"🛑 REJECTED: TP distance {tp_dist_pips:.1f}p below minimum {self.bounds['min_tp_pips']}p"
            self._log_rejection(msg)
            return False, msg

        # 3. Check Spread
        max_spread = self.bounds["min_sl_pips"] * 0.5
        if current_spread_pips > max_spread:
            msg = f"🛑 REJECTED: Spread {current_spread_pips:.1f}p exceeds max {max_spread:.1f}p"
            self._log_rejection(msg)
            return False, msg

        return True, "✅ CLEAR: Order passes structural guardrails"

    def _log_rejection(self, reason: str):
        """Log a guardrail rejection."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": self.symbol,
            "reason": reason,
        }
        self.rejection_log.append(entry)
        logger.warning(f"GUARDRAIL: {reason}")

    def get_rejection_log(self) -> list[dict]:
        return self.rejection_log

    def save_rejection_log(self, path: str | Path):
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self.rejection_log, f, indent=2)
