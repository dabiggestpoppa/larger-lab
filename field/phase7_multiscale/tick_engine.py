"""
7.2 Tick Engine — Micro-Temporal Processing
=============================================
Processes tick-level data streams for real-time field awareness.

Aggregates tick data into configurable micro-bars, computes
real-time statistics (spread, imbalance, momentum), and emits
tick events to the field.

Tick → MicroBar → Bar → Daily → Weekly pipeline entry point.
"""

import logging
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.tick")


class TickRecord(BaseModel):
    """A single market tick."""
    tick_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str
    price: float
    size: int
    side: str  # buy, sell
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    spread: float = 0.0


class TickStats(BaseModel):
    """Aggregated tick statistics for a symbol."""
    symbol: str
    tick_count: int = 0
    total_volume: int = 0
    avg_spread: float = 0.0
    last_price: float = 0.0
    buy_imbalance: float = 0.0  # -1.0 to 1.0
    momentum: float = 0.0  # price change velocity
    vwap: float = 0.0


class TickEngineConfig(BaseModel):
    """Configuration for tick_engine."""
    enabled: bool = True
    max_ticks_per_symbol: int = 10000
    momentum_window: int = 20
    imbalance_window: int = 50


class TickEngineModule:
    """Micro-temporal tick data processor."""

    def __init__(self):
        self.config = TickEngineConfig()
        self.running = False
        self._lock = Lock()
        self._ticks: Dict[str, deque] = defaultdict(deque)  # symbol -> deque[TickRecord]
        self._stats: Dict[str, TickStats] = {}  # symbol -> TickStats
        self._total_ticks: int = 0

    def start(self) -> None:
        """Start the tick engine."""
        self.running = True
        logger.info("TickEngine started")

    def stop(self) -> None:
        """Stop the tick engine."""
        self.running = False
        logger.info("TickEngine stopped")

    def ingest_tick(self, symbol: str, price: float, size: int, side: str,
                    spread: float = 0.0) -> str:
        """
        Ingest a single market tick.

        Args:
            symbol: Trading symbol.
            price: Tick price.
            size: Tick size/volume.
            side: 'buy' or 'sell'.
            spread: Bid-ask spread at time of tick.

        Returns:
            tick_id of the ingested tick.
        """
        tick = TickRecord(symbol=symbol, price=price, size=size, side=side, spread=spread)
        max_t = self.config.max_ticks_per_symbol

        with self._lock:
            self._ticks[symbol].append(tick)
            self._total_ticks += 1

            # Evict oldest if over limit
            while len(self._ticks[symbol]) > max_t:
                self._ticks[symbol].popleft()

            # Update stats
            self._recompute_stats(symbol)

        return tick.tick_id

    def _recompute_stats(self, symbol: str) -> None:
        """Recompute tick statistics for a symbol."""
        ticks = self._ticks.get(symbol, deque())
        if not ticks:
            return

        tick_list = list(ticks)
        n = len(tick_list)
        total_vol = sum(t.size for t in tick_list)
        avg_spread = sum(t.spread for t in tick_list) / n if n > 0 else 0.0

        # Buy imbalance: ratio of buy volume to total
        buy_vol = sum(t.size for t in tick_list[-self.config.imbalance_window:] if t.side == "buy")
        recent_vol = sum(t.size for t in tick_list[-self.config.imbalance_window:])
        imbalance = (2.0 * buy_vol / recent_vol - 1.0) if recent_vol > 0 else 0.0

        # Momentum: price change over momentum window
        window = self.config.momentum_window
        if n >= window:
            old_price = tick_list[-window].price
            new_price = tick_list[-1].price
            momentum = (new_price - old_price) / old_price if old_price != 0 else 0.0
        else:
            momentum = 0.0

        # VWAP
        vwap = sum(t.price * t.size for t in tick_list) / total_vol if total_vol > 0 else 0.0

        self._stats[symbol] = TickStats(
            symbol=symbol,
            tick_count=n,
            total_volume=total_vol,
            avg_spread=round(avg_spread, 6),
            last_price=tick_list[-1].price,
            buy_imbalance=round(imbalance, 4),
            momentum=round(momentum, 6),
            vwap=round(vwap, 4),
        )

    def get_stats(self, symbol: str) -> Optional[TickStats]:
        """Get current tick statistics for a symbol."""
        with self._lock:
            return self._stats.get(symbol)

    def get_all_stats(self) -> Dict[str, TickStats]:
        """Get tick statistics for all symbols."""
        with self._lock:
            return dict(self._stats)

    def get_recent_ticks(self, symbol: str, n: int = 100) -> List[Dict]:
        """Get the most recent N ticks for a symbol."""
        with self._lock:
            ticks = list(self._ticks.get(symbol, deque()))[-n:]
            return [t.model_dump() for t in ticks]

    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine-wide statistics."""
        with self._lock:
            return {
                "total_ticks_processed": self._total_ticks,
                "symbols_tracked": len(self._ticks),
                "ticks_per_symbol": {s: len(t) for s, t in self._ticks.items()},
                "running": self.running,
            }
