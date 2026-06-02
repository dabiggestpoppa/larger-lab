"""
Phase 4.2: Close-Only Guard
=============================
Enforces the CEREBUS close-only invalidation rule.
Only M5 candle CLOSE beyond SL triggers exit. Wicks are ignored.
Also enforces the 81.2% rule kill switch and 12PM hard exit.
"""
from __future__ import annotations

import logging
from datetime import datetime, time as dt_time
from typing import Optional

logger = logging.getLogger(__name__)

HARD_EXIT_TIME = dt_time(12, 0)  # 12:00 PM EST


class CloseOnlyGuard:
    """
    Position exit manager. Runs every bar close.
    Enforces close-only SL, 81.2% rule, and 12PM hard exit.
    """

    def __init__(self):
        self.position: Optional[dict] = None

    def open_position(
        self,
        direction: int,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        origin_price: float,
    ):
        """
        Open a tracked position.

        Parameters
        ----------
        direction : 1 for LONG, -1 for SHORT
        entry_price : float
        sl_price : OCC extreme (zero buffer)
        tp_price : 1 AU target (or gear-shifted AU)
        origin_price : Asian band extreme (for 81.2% rule)
        """
        self.position = {
            "direction": direction,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "origin_price": origin_price,
            "open_time": datetime.utcnow(),
        }
        logger.info(
            f"GUARD: Opened {'LONG' if direction == 1 else 'SHORT'} @ {entry_price} | "
            f"SL={sl_price} | TP={tp_price} | Origin={origin_price}"
        )

    def check_exit(
        self,
        bar_close: float,
        bar_high: float,
        bar_low: float,
        current_time_est: datetime,
    ) -> tuple[bool, str]:
        """
        Check if position should be exited.

        Parameters
        ----------
        bar_close : float — M5 candle close price
        bar_high : float — M5 candle high
        bar_low : float — M5 candle low
        current_time_est : datetime — current time in EST

        Returns
        -------
        (should_exit: bool, reason: str)
        """
        if self.position is None:
            return False, "NO_POSITION"

        direction = self.position["direction"]
        sl_price = self.position["sl_price"]
        tp_price = self.position["tp_price"]
        origin_price = self.position["origin_price"]

        # 1. 12PM Hard Exit (absolute priority)
        if current_time_est.time() >= HARD_EXIT_TIME:
            self.position = None
            return True, "HARD_EXIT_12PM"

        # 2. Take Profit — wick OR close triggers
        if direction == 1 and bar_high >= tp_price:
            self.position = None
            return True, "TP_HIT"
        if direction == -1 and bar_low <= tp_price:
            self.position = None
            return True, "TP_HIT"

        # 3. Stop Loss — CLOSE ONLY (wicks ignored)
        if direction == 1 and bar_close <= sl_price:
            self.position = None
            return True, "SL_CLOSE_ONLY"
        if direction == -1 and bar_close >= sl_price:
            self.position = None
            return True, "SL_CLOSE_ONLY"

        # 4. 81.2% Rule — close back inside Asian band
        if direction == 1 and bar_close < origin_price:
            self.position = None
            return True, "81PCT_RULE_KILL"
        if direction == -1 and bar_close > origin_price:
            self.position = None
            return True, "81PCT_RULE_KILL"

        return False, "HOLD"

    def close_position(self):
        """Force close position."""
        self.position = None

    @property
    def has_position(self) -> bool:
        return self.position is not None
