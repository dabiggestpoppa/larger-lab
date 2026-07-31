"""7_multiscale.daily_engine

Daily Timeframe Data Engine
============================
Aggregates and manages daily-resolution market data for multiscale analysis.
Provides daily OHLCV bars, session summaries, and day-over-day comparisons.

Integrates with the scale_router for cross-timeframe data flow and the
scale_bridge for translating daily signals to other resolutions.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.daily_engine")


class DailyBar(BaseModel):
    """A single daily OHLCV bar."""
    date: str  # YYYY-MM-DD
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    source: str = "unknown"


class DailySessionSummary(BaseModel):
    """Summary of a single trading day."""
    date: str
    bars_count: int = 0
    total_volume: float = 0.0
    vwap: float = 0.0
    open_price: float = 0.0
    close_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    range: float = 0.0  # high - low
    body: float = 0.0   # abs(close - open)
    direction: str = "neutral"  # bullish, bearish, neutral


class DailyEngineConfig(BaseModel):
    """Configuration for daily_engine."""
    enabled: bool = True
    max_bars: int = 5000
    vwap_enabled: bool = True
    gap_detection: bool = True
    gap_threshold_pct: float = 2.0


class DailyEngineModule:
    """Daily timeframe data engine for multiscale field operations."""

    def __init__(self):
        self.config = DailyEngineConfig()
        self.running = False
        self._lock = Lock()
        self._bars: Dict[str, DailyBar] = {}  # date -> DailyBar
        self._ordered_dates: List[str] = []  # sorted dates
        self._summaries: Dict[str, DailySessionSummary] = {}
        self._last_close: Optional[float] = None

    def start(self) -> None:
        self.running = True
        logger.info("DailyEngine started (gap_detection=%s)", self.config.gap_detection)

    def stop(self) -> None:
        self.running = False
        logger.info("DailyEngine stopped (%d bars stored)", len(self._bars))

    def add_bar(self, date: str, open_p: float, high: float, low: float,
                close: float, volume: float = 0.0, source: str = "unknown") -> DailyBar:
        """Add a daily OHLCV bar.

        Args:
            date: Date string YYYY-MM-DD.
            open_p: Open price.
            high: High price.
            low: Low price.
            close: Close price.
            volume: Volume.
            source: Data source identifier.

        Returns:
            The created DailyBar.
        """
        with self._lock:
            bar = DailyBar(
                date=date, open=open_p, high=high, low=low,
                close=close, volume=volume, source=source,
            )
            is_new = date not in self._bars
            self._bars[date] = bar

            if is_new:
                self._ordered_dates.append(date)
                self._ordered_dates.sort()

            # Enforce max bars
            while len(self._ordered_dates) > self.config.max_bars:
                old_date = self._ordered_dates.pop(0)
                del self._bars[old_date]
                self._summaries.pop(old_date, None)

            # Build summary
            summary = self._build_summary(bar)
            self._summaries[date] = summary

            # Gap detection
            if self.config.gap_detection and self._last_close is not None and self._last_close > 0:
                gap_pct = abs(open_p - self._last_close) / self._last_close * 100
                if gap_pct >= self.config.gap_threshold_pct:
                    direction = "up" if open_p > self._last_close else "down"
                    logger.info("GAP detected on %s: %.2f%% %s (prev_close=%.4f, open=%.4f)",
                                date, gap_pct, direction, self._last_close, open_p)

            self._last_close = close
            return bar

    def _build_summary(self, bar: DailyBar) -> DailySessionSummary:
        """Build a session summary from a daily bar."""
        direction = "neutral"
        if bar.close > bar.open:
            direction = "bullish"
        elif bar.close < bar.open:
            direction = "bearish"

        vwap = 0.0
        if self.config.vwap_enabled and bar.volume > 0:
            # Simplified VWAP: (high + low + close) / 3
            vwap = round((bar.high + bar.low + bar.close) / 3, 6)

        return DailySessionSummary(
            date=bar.date,
            bars_count=1,
            total_volume=bar.volume,
            vwap=vwap,
            open_price=bar.open,
            close_price=bar.close,
            high_price=bar.high,
            low_price=bar.low,
            range=round(bar.high - bar.low, 6),
            body=round(abs(bar.close - bar.open), 6),
            direction=direction,
        )

    def get_bar(self, date: str) -> Optional[DailyBar]:
        """Get a specific daily bar by date."""
        with self._lock:
            return self._bars.get(date)

    def get_latest(self, n: int = 1) -> List[DailyBar]:
        """Get the N most recent daily bars."""
        with self._lock:
            dates = self._ordered_dates[-n:]
            return [self._bars[d] for d in dates if d in self._bars]

    def get_range(self, start_date: str, end_date: str) -> List[DailyBar]:
        """Get daily bars within a date range (inclusive)."""
        with self._lock:
            return [
                self._bars[d] for d in self._ordered_dates
                if start_date <= d <= end_date and d in self._bars
            ]

    def get_summary(self, date: str) -> Optional[DailySessionSummary]:
        """Get the session summary for a specific date."""
        with self._lock:
            return self._summaries.get(date)

    def get_trend(self, lookback: int = 5) -> Dict[str, Any]:
        """Analyze the recent trend over the last N days.

        Returns:
            Dict with trend direction, strength, and statistics.
        """
        with self._lock:
            recent = self._ordered_dates[-lookback:]
            bars = [self._bars[d] for d in recent if d in self._bars]
            if len(bars) < 2:
                return {"trend": "insufficient_data", "strength": 0.0}

            first_close = bars[0].close
            last_close = bars[-1].close
            if first_close == 0:
                return {"trend": "insufficient_data", "strength": 0.0}

            total_change = (last_close - first_close) / first_close * 100
            bullish_days = sum(1 for b in bars if b.close > b.open)
            bearish_days = sum(1 for b in bars if b.close < b.open)
            avg_volume = sum(b.volume for b in bars) / len(bars)
            avg_range = sum(b.high - b.low for b in bars) / len(bars)

            if total_change > 1.0:
                trend = "bullish"
            elif total_change < -1.0:
                trend = "bearish"
            else:
                trend = "neutral"

            strength = min(1.0, abs(total_change) / 5.0)  # 5% move = max strength

            return {
                "trend": trend,
                "strength": round(strength, 4),
                "total_change_pct": round(total_change, 4),
                "bullish_days": bullish_days,
                "bearish_days": bearish_days,
                "neutral_days": len(bars) - bullish_days - bearish_days,
                "avg_volume": round(avg_volume, 2),
                "avg_range": round(avg_range, 6),
                "lookback": len(bars),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        with self._lock:
            bullish = sum(1 for s in self._summaries.values() if s.direction == "bullish")
            bearish = sum(1 for s in self._summaries.values() if s.direction == "bearish")
            neutral = sum(1 for s in self._summaries.values() if s.direction == "neutral")
            total_vol = sum(s.total_volume for s in self._summaries.values())
            return {
                "total_bars": len(self._bars),
                "date_range": f"{self._ordered_dates[0]}..{self._ordered_dates[-1]}" if self._ordered_dates else "empty",
                "bullish_days": bullish,
                "bearish_days": bearish,
                "neutral_days": neutral,
                "total_volume": round(total_vol, 2),
            }
