"""
Phase 4.1: Friction Filters
=============================
Real-time pre-trade filters that prevent execution during toxic conditions.
Filters: spread gate, time gate, consecutive loss gate, daily loss limit.
"""
from __future__ import annotations

import logging
from datetime import datetime, time as dt_time
from typing import Optional

logger = logging.getLogger(__name__)

# Max spread per tier (in pips)
TIER_MAX_SPREAD = {
    "T1": 15.0,
    "T2": 20.0,
    "T3": 30.0,
}

# Trading session boundaries (EST)
SESSION_START = dt_time(3, 0)   # 3:00 AM EST
SESSION_END = dt_time(12, 0)    # 12:00 PM EST hard exit


class FrictionFilter:
    """
    Pre-trade friction gate. All checks must pass before an order is submitted.
    """

    def __init__(
        self,
        max_consecutive_losses: int = 2,
        daily_loss_limit_pct: float = 3.0,
        max_spread_override: Optional[float] = None,
    ):
        self.max_consecutive_losses = max_consecutive_losses
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_spread_override = max_spread_override
        self._consecutive_losses = 0
        self._daily_pnl_pct = 0.0
        self._last_date: Optional[datetime] = None

    def check_all(
        self,
        current_time_est: datetime,
        current_spread_pips: float,
        tier: str = "T2",
    ) -> tuple[bool, str]:
        """
        Run all friction filters.

        Returns
        -------
        (passed: bool, reason: str)
        """
        # 1. Time gate
        t = current_time_est.time()
        if t < SESSION_START:
            return False, f"TIME_GATE: {t} before session start {SESSION_START}"
        if t >= SESSION_END:
            return False, f"TIME_GATE: {t} at/after hard exit {SESSION_END}"

        # 2. Spread gate
        max_spread = self.max_spread_override or TIER_MAX_SPREAD.get(tier, 20.0)
        if current_spread_pips > max_spread:
            return False, f"SPREAD_GATE: {current_spread_pips:.1f}p > max {max_spread:.1f}p for {tier}"

        # 3. Consecutive loss gate
        self._reset_daily_if_new_day(current_time_est)
        if self._consecutive_losses >= self.max_consecutive_losses:
            return False, f"LOSS_GATE: {self._consecutive_losses} consecutive losses (max {self.max_consecutive_losses})"

        # 4. Daily loss limit gate
        if self._daily_pnl_pct <= -self.daily_loss_limit_pct:
            return False, f"DAILY_LIMIT: {self._daily_pnl_pct:.1f}% <= -{self.daily_loss_limit_pct}%"

        return True, "ALL_FILTERS_PASSED"

    def record_trade(self, pnl_pct: float):
        """Record trade outcome for loss tracking."""
        if pnl_pct < 0:
            self._consecutive_losses += 1
            self._daily_pnl_pct += pnl_pct
        else:
            self._consecutive_losses = 0
            self._daily_pnl_pct += pnl_pct

    def _reset_daily_if_new_day(self, current_time: datetime):
        current_date = current_time.date()
        if self._last_date != current_date:
            self._consecutive_losses = 0
            self._daily_pnl_pct = 0.0
            self._last_date = current_date

    @property
    def consecutive_losses(self) -> int:
        return self._consecutive_losses

    @property
    def daily_pnl_pct(self) -> float:
        return self._daily_pnl_pct
