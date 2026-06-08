"""7_multiscale.weekly_engine

Weekly Timeframe Data Engine — aggregates and analyzes weekly-scale data.

Processes weekly OHLCV bars, computes weekly indicators (SMA, EMA, RSI),
detects weekly-level patterns, and provides trend analysis at the
weekly timeframe for multi-scale field operations.
"""

import logging
import math
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Deque, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.weekly_engine")


class WeeklyBar(BaseModel):
    """A single weekly OHLCV bar."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    symbol: str = ""


class WeeklyIndicator(BaseModel):
    """Computed weekly indicator values."""
    sma_10: float = 0.0
    sma_20: float = 0.0
    sma_50: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    rsi_14: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_middle: float = 0.0
    bollinger_lower: float = 0.0
    atr_14: float = 0.0


class WeeklyEngineConfig(BaseModel):
    """Configuration for weekly_engine."""
    enabled: bool = True
    max_bars: int = 500
    sma_periods: List[int] = Field(default_factory=lambda: [10, 20, 50])
    ema_periods: List[int] = Field(default_factory=lambda: [12, 26])
    rsi_period: int = 14
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    atr_period: int = 14


class WeeklyEngineModule:
    """Weekly timeframe data engine — weekly bar processing and analysis."""

    def __init__(self):
        self.config = WeeklyEngineConfig()
        self.running = False
        self._lock = Lock()
        self._bars: Dict[str, Deque[WeeklyBar]] = defaultdict(lambda: deque(maxlen=500))
        self._indicators: Dict[str, WeeklyIndicator] = {}
        self._patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._trend_state: Dict[str, str] = {}  # symbol -> trend direction
        self._total_bars: int = 0

    def start(self) -> None:
        self.running = True
        logger.info("WeeklyEngine started")

    def stop(self) -> None:
        self.running = False
        logger.info("WeeklyEngine stopped (%d total bars processed)", self._total_bars)

    def ingest_bar(self, bar: WeeklyBar) -> Optional[WeeklyIndicator]:
        """Ingest a weekly bar and compute indicators.

        Args:
            bar: Weekly OHLCV bar data.

        Returns:
            Updated WeeklyIndicator after processing, or None if insufficient data.
        """
        with self._lock:
            symbol = bar.symbol or "default"
            bars = self._bars[symbol]
            bars.append(bar)
            self._total_bars += 1

            if len(bars) < 5:
                return None

            indicator = self._compute_indicators(list(bars))
            self._indicators[symbol] = indicator
            self._update_trend(symbol, indicator)
            self._detect_patterns(symbol, list(bars), indicator)

            logger.debug("Weekly bar ingested for %s: close=%.4f, rsi=%.2f",
                         symbol, bar.close, indicator.rsi_14)
            return indicator

    def _compute_indicators(self, bars: List[WeeklyBar]) -> WeeklyIndicator:
        """Compute all weekly indicators from bar data."""
        closes = [b.close for b in bars]
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]

        # SMAs
        sma_10 = self._sma(closes, 10)
        sma_20 = self._sma(closes, 20)
        sma_50 = self._sma(closes, 50)

        # EMAs
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)

        # RSI
        rsi = self._rsi(closes, self.config.rsi_period)

        # MACD
        macd = ema_12 - ema_26
        # Signal line: EMA of MACD (approximate from available data)
        macd_values = []
        for i in range(max(0, len(closes) - 30), len(closes)):
            sub_closes = closes[:i + 1]
            if len(sub_closes) >= 26:
                m_12 = self._ema(sub_closes, 12)
                m_26 = self._ema(sub_closes, 26)
                macd_values.append(m_12 - m_26)
        macd_signal = self._ema(macd_values, 9) if len(macd_values) >= 9 else macd
        macd_histogram = macd - macd_signal

        # Bollinger Bands
        period = self.config.bollinger_period
        if len(closes) >= period:
            recent = closes[-period:]
            bb_middle = sum(recent) / len(recent)
            variance = sum((c - bb_middle) ** 2 for c in recent) / len(recent)
            std = math.sqrt(variance)
            bb_upper = bb_middle + self.config.bollinger_std * std
            bb_lower = bb_middle - self.config.bollinger_std * std
        else:
            bb_middle = closes[-1] if closes else 0
            bb_upper = bb_middle
            bb_lower = bb_middle

        # ATR
        atr = self._atr(highs, lows, closes, self.config.atr_period)

        return WeeklyIndicator(
            sma_10=round(sma_10, 6),
            sma_20=round(sma_20, 6),
            sma_50=round(sma_50, 6),
            ema_12=round(ema_12, 6),
            ema_26=round(ema_26, 6),
            rsi_14=round(rsi, 4),
            macd=round(macd, 6),
            macd_signal=round(macd_signal, 6),
            macd_histogram=round(macd_histogram, 6),
            bollinger_upper=round(bb_upper, 6),
            bollinger_middle=round(bb_middle, 6),
            bollinger_lower=round(bb_lower, 6),
            atr_14=round(atr, 6),
        )

    def _sma(self, values: List[float], period: int) -> float:
        """Simple Moving Average."""
        if len(values) < period:
            return sum(values) / len(values) if values else 0.0
        return sum(values[-period:]) / period

    def _ema(self, values: List[float], period: int) -> float:
        """Exponential Moving Average."""
        if not values:
            return 0.0
        if len(values) < period:
            return sum(values) / len(values)
        multiplier = 2.0 / (period + 1)
        ema = sum(values[:period]) / period
        for val in values[period:]:
            ema = (val - ema) * multiplier + ema
        return ema

    def _rsi(self, closes: List[float], period: int) -> float:
        """Relative Strength Index."""
        if len(closes) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(len(closes) - period, len(closes)):
            change = closes[i] - closes[i - 1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _atr(self, highs: List[float], lows: List[float],
             closes: List[float], period: int) -> float:
        """Average True Range."""
        if len(highs) < 2:
            return 0.0
        trs = []
        start = max(1, len(highs) - period)
        for i in range(start, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            trs.append(tr)
        return sum(trs) / len(trs) if trs else 0.0

    def _update_trend(self, symbol: str, indicator: WeeklyIndicator) -> None:
        """Update trend state based on indicator values."""
        if indicator.sma_10 > indicator.sma_20 > indicator.sma_50:
            new_trend = "strong_uptrend"
        elif indicator.sma_10 > indicator.sma_20:
            new_trend = "uptrend"
        elif indicator.sma_10 < indicator.sma_20 < indicator.sma_50:
            new_trend = "strong_downtrend"
        elif indicator.sma_10 < indicator.sma_20:
            new_trend = "downtrend"
        elif indicator.rsi_14 > 70:
            new_trend = "overbought"
        elif indicator.rsi_14 < 30:
            new_trend = "oversold"
        else:
            new_trend = "neutral"

        old_trend = self._trend_state.get(symbol)
        if old_trend != new_trend:
            logger.info("Weekly trend change for %s: %s -> %s", symbol, old_trend, new_trend)
        self._trend_state[symbol] = new_trend

    def _detect_patterns(self, symbol: str, bars: List[WeeklyBar],
                         indicator: WeeklyIndicator) -> None:
        """Detect weekly chart patterns."""
        if len(bars) < 5:
            return
        patterns = self._patterns[symbol]
        closes = [b.close for b in bars]

        # Golden cross / Death cross
        if indicator.sma_10 > indicator.sma_50 and len(closes) > 2:
            prev_closes = closes[:-1]
            prev_sma10 = sum(prev_closes[-10:]) / min(10, len(prev_closes))
            prev_sma50 = sum(prev_closes[-50:]) / min(50, len(prev_closes))
            if prev_sma10 <= prev_sma50:
                patterns.append({
                    "type": "golden_cross",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "description": "SMA10 crossed above SMA50 on weekly",
                })
                logger.info("Weekly golden cross detected for %s", symbol)

        if indicator.sma_10 < indicator.sma_50 and len(closes) > 2:
            prev_closes = closes[:-1]
            prev_sma10 = sum(prev_closes[-10:]) / min(10, len(prev_closes))
            prev_sma50 = sum(prev_closes[-50:]) / min(50, len(prev_closes))
            if prev_sma10 >= prev_sma50:
                patterns.append({
                    "type": "death_cross",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "description": "SMA10 crossed below SMA50 on weekly",
                })
                logger.info("Weekly death cross detected for %s", symbol)

        # Bollinger squeeze
        if indicator.bollinger_middle > 0:
            bandwidth = (indicator.bollinger_upper - indicator.bollinger_lower) / indicator.bollinger_middle
            if bandwidth < 0.05:
                patterns.append({
                    "type": "bollinger_squeeze",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "description": f"Bollinger squeeze (bandwidth={bandwidth:.4f})",
                })

        # Trim patterns
        if len(patterns) > 200:
            self._patterns[symbol] = patterns[-200:]

    def get_trend(self, symbol: str = "default") -> str:
        """Get the current weekly trend for a symbol."""
        return self._trend_state.get(symbol, "unknown")

    def get_indicators(self, symbol: str = "default") -> Optional[Dict]:
        """Get current weekly indicators for a symbol."""
        ind = self._indicators.get(symbol)
        return ind.model_dump() if ind else None

    def get_patterns(self, symbol: str = "default", limit: int = 50) -> List[Dict]:
        """Get detected weekly patterns for a symbol."""
        return self._patterns.get(symbol, [])[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics."""
        with self._lock:
            return {
                "total_bars_processed": self._total_bars,
                "symbols_tracked": len(self._bars),
                "total_patterns_detected": sum(len(p) for p in self._patterns.values()),
                "trend_states": dict(self._trend_state),
            }
