"""
7.1 Bar Engine — Multi-Scale Bar Aggregation
=============================================
Aggregates raw ticks into OHLCV bars at configurable intervals.

Supports multiple bar sizes simultaneously (1m, 5m, 15m, 1h, etc.).
Maintains a rolling window of bars per symbol per scale.
"""

import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.bar_engine")


class Bar(BaseModel):
    """OHLCV bar."""
    symbol: str
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    tick_count: int = 0
    timestamp: str = ""


class BarEngineConfig(BaseModel):
    """Configuration for bar_engine."""
    enabled: bool = True
    default_bar_size_sec: int = 60
    max_bars_per_symbol: int = 10000
    max_symbols: int = 500


class BarEngineModule:
    """Multi-scale bar aggregation engine."""

    def __init__(self):
        self.config = BarEngineConfig()
        self.running = False
        self._lock = threading.Lock()
        # symbol -> bar_size_sec -> deque[Bar]
        self._bars: Dict[str, Dict[int, Deque[Bar]]] = defaultdict(
            lambda: defaultdict(deque)
        )
        self._current_bar: Dict[str, Dict[int, Optional[Bar]]] = defaultdict(dict)
        self._tick_counts: Dict[str, int] = defaultdict(int)
        self._total_bars_formed: int = 0

    def start(self) -> None:
        """Start the bar engine."""
        self.running = True
        logger.info("BarEngine started")

    def stop(self) -> None:
        """Stop the bar engine."""
        self.running = False
        logger.info("BarEngine stopped")

    def on_tick(self, symbol: str, price: float, volume: float = 0.0,
                timestamp: str = "", bar_sizes: Optional[List[int]] = None) -> Dict[int, Optional[Bar]]:
        """
        Process a tick for a symbol. Closes bars when interval elapses.

        Args:
            symbol: Instrument symbol.
            price: Tick price.
            volume: Tick volume.
            timestamp: Tick timestamp (ISO format).
            bar_sizes: Bar sizes in seconds to aggregate into (default: [60]).

        Returns:
            Dict of bar_size -> Bar (only for bars that closed on this tick).
        """
        if not self.running:
            return {}

        ts = timestamp or datetime.now(timezone.utc).isoformat()
        sizes = bar_sizes or [self.config.default_bar_size_sec]
        closed_bars: Dict[int, Optional[Bar]] = {}

        with self._lock:
            self._tick_counts[symbol] += 1

            for bar_size in sizes:
                current = self._current_bar[symbol].get(bar_size)

                if current is None or self._should_close(current, ts, bar_size):
                    # Close existing bar
                    if current is not None:
                        bar_deque = self._bars[symbol][bar_size]
                        bar_deque.append(current)
                        if len(bar_deque) > self.config.max_bars_per_symbol:
                            bar_deque.popleft()
                        self._total_bars_formed += 1
                        closed_bars[bar_size] = current

                    # Start new bar
                    self._current_bar[symbol][bar_size] = Bar(
                        symbol=symbol,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=volume,
                        tick_count=1,
                        timestamp=ts,
                    )
                else:
                    # Update current bar
                    current.high = max(current.high, price)
                    current.low = min(current.low, price)
                    current.close = price
                    current.volume += volume
                    current.tick_count += 1

        if closed_bars:
            logger.debug("Bars closed for %s: %s", symbol, list(closed_bars.keys()))
        return closed_bars

    def _should_close(self, bar: Bar, current_ts: str, bar_size_sec: int) -> bool:
        """Check if a bar should be closed based on time."""
        try:
            bar_time = datetime.fromisoformat(bar.timestamp)
            current_time = datetime.fromisoformat(current_ts)
            return (current_time - bar_time).total_seconds() >= bar_size_sec
        except (ValueError, TypeError):
            return False

    def get_bars(self, symbol: str, bar_size: int, count: int = 100) -> List[Dict]:
        """
        Get recent bars for a symbol at a given bar size.

        Args:
            symbol: Instrument symbol.
            bar_size: Bar size in seconds.
            count: Number of bars to return.

        Returns:
            List of bar dicts, newest first.
        """
        with self._lock:
            bars = self._bars.get(symbol, {}).get(bar_size, deque())
            result = [b.model_dump() for b in list(bars)[-count:]]
            return result

    def get_current_bar(self, symbol: str, bar_size: int) -> Optional[Dict]:
        """Get the currently forming bar for a symbol."""
        with self._lock:
            bar = self._current_bar.get(symbol, {}).get(bar_size)
            return bar.model_dump() if bar else None

    def get_stats(self) -> Dict[str, Any]:
        """Get bar engine statistics."""
        with self._lock:
            total_bars = sum(
                sum(len(d) for d in sizes.values())
                for sizes in self._bars.values()
            )
            return {
                "symbols_tracked": len(self._bars),
                "total_bars_stored": total_bars,
                "total_bars_formed": self._total_bars_formed,
                "total_ticks_processed": sum(self._tick_counts.values()),
                "symbols": list(self._bars.keys()),
            }
