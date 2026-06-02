"""
Phase 4.1: Friction Filters
=============================
Real-time pre-trade filters that prevent execution during toxic conditions.
"""
from __future__ import annotations

from datetime import datetime

TIER_MAX_SPREAD = {
    "T1": 10.0,
    "T2": 15.0,
    "T3": 25.0,
}


class FrictionFilter:
    """Pre-trade friction gate. All checks must pass before an order is submitted."""

    def __init__(
        self,
        max_consecutive_losses: int = 2,
        daily_loss_limit_pct: float = 3.0,
        max_spread_override: float = None,
    ):
        self.max_consecutive_losses = max_consecutive_losses
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_spread_override = max_spread_override
        self._consecutive_losses = 0
        self._daily_pnl_pct = 0.0
        self._last_date = None

    def check_all(
        self,
        current_time_est: datetime,
        current_spread_pips: float,
        tier: str = "T2",
    ) -> tuple[bool, str]:
        """Run all friction filters. Returns (passed, reason)."""
        t = current_time_est

        # Time gate: hard exit at 12:00 PM
        if t.hour >= 12:
            return False, "TIME_GATE: Past 12:00 PM EST hard exit"

        # Time gate: before session start (3:00 AM)
        if t.hour < 3:
            return False, "TIME_GATE: Before 3:00 AM EST session start"

        # Spread gate
        max_spread = self.max_spread_override or TIER_MAX_SPREAD.get(tier, 15.0)
        if current_spread_pips > max_spread:
            return False, f"SPREAD_GATE: {current_spread_pips:.1f}p > max {max_spread:.1f}p for {tier}"

        # Reset daily counters on new day
        self._reset_daily_if_new_day(t)

        # Daily loss limit gate (checked first — most critical)
        if self._daily_pnl_pct <= -self.daily_loss_limit_pct:
            return False, f"DAILY_LIMIT: {self._daily_pnl_pct:.1f}% <= -{self.daily_loss_limit_pct}%"

        # Consecutive loss gate
        if self._consecutive_losses >= self.max_consecutive_losses:
            return False, f"LOSS_GATE: {self._consecutive_losses} consecutive losses (max {self.max_consecutive_losses})"

        return True, "ALL_FILTERS_PASSED"

    def record_trade(self, pnl_pct: float, trade_date=None):
        """Record trade outcome for loss tracking."""
        if trade_date is None:
            trade_date = datetime.utcnow().date()
        self._last_trade_date = trade_date
        if pnl_pct < 0:
            self._consecutive_losses += 1
            self._daily_pnl_pct += pnl_pct
        else:
            self._consecutive_losses = 0
            self._daily_pnl_pct += pnl_pct

    def _reset_daily_if_new_day(self, current_time: datetime):
        current_date = current_time.date()
        # Reset if the check date is different from the last trade date
        last_date = self._last_date or self._last_trade_date
        if last_date is not None and last_date != current_date:
            self._consecutive_losses = 0
            self._daily_pnl_pct = 0.0
        self._last_date = current_date
