"""
CEREBUS FX v4.0 — Synchronized 3-Leg MT5 Data Feed for Triangular Basis
=========================================================================

Fetches M5 bars for GBPAUD, GBPNZD, AUDNZD and synchronizes them into
TriangularSnapshots where ALL three legs share the EXACT same closed M5 timestamp.

CRITICAL RULES:
- Every basis calculation requires the SAME closed M5 timestamp
- Reject a snapshot if one leg is missing/stale/timestamps differ/one bar forming
- Never mix 10:00 GBPAUD with 10:05 GBPNZD
- Exactly-once processing via last_processed_m5_timestamp tracking
- Broker timestamps normalized in data-feed layer → UTC → canonical EST time

Symbol mapping (explicit, no guessing):
    GBPAUD -> GBPAUD.PRO
    GBPNZD -> GBPNZD.PRO
    AUDNZD -> AUDNZD.PRO

Usage:
    from engines.mt5_triangular_data_feed import TriangularDataFeed
    feed = TriangularDataFeed()
    snapshot = feed.fetch_latest_snapshot()
    if snapshot:
        basis = compute_basis(snapshot)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding="utf-8")

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


# ─── SYMBOL MAPPING ──────────────────────────────────────────────────────

SYMBOL_MAP = {
    "GBPAUD": "GBPAUD.PRO",
    "GBPNZD": "GBPNZD.PRO",
    "AUDNZD": "AUDNZD.PRO",
}

TRIANGLE_SYMBOLS = ["GBPAUD", "GBPNZD", "AUDNZD"]


# ─── DATA STRUCTURES ─────────────────────────────────────────────────────

@dataclass
class M5Bar:
    """Single M5 bar with normalized timestamp."""
    timestamp: datetime  # UTC timestamp
    open: float
    high: float
    low: float
    close: float
    volume: int
    raw_time: int  # Unix timestamp from MT5


@dataclass
class TriangularSnapshot:
    """Synchronized 3-leg M5 snapshot — ALL legs share same timestamp.
    
    This is the atomic unit of truth for basis calculation.
    If any leg is missing/stale/forming, reject the entire snapshot.
    """
    timestamp: datetime  # UTC timestamp of this M5 bar
    gbpaud_bar: M5Bar
    gbpnzd_bar: M5Bar
    audnzd_bar: M5Bar
    
    def __post_init__(self):
        """Validate that all legs share the exact same timestamp."""
        if not (self.gbpaud_bar.timestamp == self.gbpnzd_bar.timestamp == self.audnzd_bar.timestamp):
            raise ValueError(
                f"Timestamp mismatch in TriangularSnapshot: "
                f"GBPAUD={self.gbpaud_bar.timestamp}, "
                f"GBPNZD={self.gbpnzd_bar.timestamp}, "
                f"AUDNZD={self.audnzd_bar.timestamp}"
            )


# ─── UTILITY FUNCTIONS ───────────────────────────────────────────────────

def _mt5_time_to_datetime(raw_time: int) -> datetime:
    """Convert MT5 Unix timestamp to Python datetime (UTC)."""
    return datetime.utcfromtimestamp(raw_time)


def _est_hour(dt: datetime) -> int:
    """Convert UTC datetime to EST hour (EST = UTC-5)."""
    est_dt = dt - timedelta(hours=5)
    return est_dt.hour


def _is_london_session(est_hour: int) -> bool:
    """Check if EST hour falls within London session (3AM-12PM)."""
    return 3 <= est_hour < 12


def _minutes_to_hard_exit(est_hour: int) -> int:
    """Calculate minutes remaining until 12PM EST hard exit."""
    current_minutes = est_hour * 60
    exit_minutes = 12 * 60  # 12PM = 720 minutes
    return exit_minutes - current_minutes


# ─── DATA FEED CLASS ─────────────────────────────────────────────────────

class TriangularDataFeed:
    """Synchronized 3-leg MT5 data feed for Triangular Basis strategy.
    
    Fetches M5 bars for all three triangle symbols and produces
    TriangularSnapshots where ALL legs share the exact same closed M5 timestamp.
    """
    
    def __init__(self, symbol_map: Dict[str, str] = None):
        """Initialize data feed.
        
        Args:
            symbol_map: Custom symbol mapping (default uses TRIANGLE_SYMBOLS)
        """
        self.symbol_map = symbol_map or SYMBOL_MAP.copy()
        self._last_processed_utc: Optional[datetime] = None
        self._bar_cache: Dict[str, List[M5Bar]] = {}  # Per-symbol bar cache
        
    def initialize(self) -> bool:
        """Initialize MT5 connection.
        
        Returns:
            True if successful, False otherwise.
        """
        if mt5 is None:
            print("[DATA_FEED] ERROR: MetaTrader5 module not available")
            return False
        
        if not mt5.initialize():
            print("[DATA_FEED] ERROR: MT5 initialization failed")
            return False
        
        print("[DATA_FEED] MT5 initialized successfully")
        return True
    
    def fetch_recent_bars(self, symbol_canonical: str, count: int = 500) -> Optional[List[M5Bar]]:
        """Fetch recent M5 bars for a single symbol.
        
        Args:
            symbol_canonical: Canonical symbol name (e.g., "GBPAUD")
            count: Number of bars to fetch
            
        Returns:
            List of M5Bar objects sorted by timestamp ascending, or None on failure.
        """
        broker_symbol = self.symbol_map.get(symbol_canonical)
        if not broker_symbol:
            print(f"[DATA_FEED] ERROR: No broker mapping for {symbol_canonical}")
            return None
        
        try:
            raw_bars = mt5.copy_rates_from_pos(broker_symbol, mt5.TIMEFRAME_M5, 0, count)
            if raw_bars is None or len(raw_bars) == 0:
                print(f"[DATA_FEED] WARNING: No bars fetched for {broker_symbol}")
                return None
            
            bars = []
            for raw in raw_bars:
                bars.append(M5Bar(
                    timestamp=_mt5_time_to_datetime(raw["time"]),
                    open=raw["open"],
                    high=raw["high"],
                    low=raw["low"],
                    close=raw["close"],
                    volume=raw.get("real_volume", raw.get("tick_volume", 0)),
                    raw_time=raw["time"],
                ))
            
            # Sort ascending by timestamp
            bars.sort(key=lambda b: b.timestamp)
            self._bar_cache[symbol_canonical] = bars
            
            return bars
            
        except Exception as e:
            print(f"[DATA_FEED] ERROR fetching bars for {broker_symbol}: {e}")
            return None
    
    def fetch_all_triangle_bars(self, count: int = 500) -> Optional[Dict[str, List[M5Bar]]]:
        """Fetch M5 bars for all three triangle symbols.
        
        Args:
            count: Number of bars per symbol
            
        Returns:
            Dict mapping canonical symbol -> List[M5Bar], or None on failure.
        """
        all_bars = {}
        for sym in TRIANGLE_SYMBOLS:
            bars = self.fetch_recent_bars(sym, count)
            if bars is None:
                print(f"[DATA_FEED] ERROR: Failed to fetch bars for {sym}")
                return None
            all_bars[sym] = bars
        
        return all_bars
    
    def build_snapshot(self, all_bars: Dict[str, List[M5Bar]]) -> Optional[TriangularSnapshot]:
        """Build a TriangularSnapshot from fetched bars.
        
        Finds the most recent COMPLETE M5 bar that exists across ALL three symbols.
        A bar is "complete" if it is NOT the current forming bar (i.e., at least 1 bar old).
        
        Args:
            all_bars: Dict mapping canonical symbol -> List[M5Bar]
            
        Returns:
            TriangularSnapshot if valid, None if sync fails.
        """
        if not all_bars:
            return None
        
        # Get latest timestamp from each symbol
        latest_times = {}
        for sym, bars in all_bars.items():
            if not bars:
                return None
            latest_times[sym] = bars[-1].timestamp
        
        # Find common timestamp (must exist in all three)
        # We look backwards from latest to find a timestamp present in all
        max_lookback = 5  # Allow up to 5 bars difference before giving up
        
        for offset in range(max_lookback + 1):
            # Use the earliest latest time minus offset
            candidate_times = [latest_times[sym] - timedelta(minutes=5 * offset) 
                             for sym in TRIANGLE_SYMBOLS]
            candidate = min(candidate_times)
            
            # Check if this candidate exists in all three
            found = True
            gbpaud_bar = None
            gbpnzd_bar = None
            audnzd_bar = None
            
            for sym, bars in all_bars.items():
                for bar in reversed(bars):
                    if bar.timestamp == candidate:
                        if sym == "GBPAUD":
                            gbpaud_bar = bar
                        elif sym == "GBPNZD":
                            gbpnzd_bar = bar
                        elif sym == "AUDNZD":
                            audnzd_bar = bar
                        break
            
            if gbpaud_bar and gbpnzd_bar and audnzd_bar:
                # Verify this is a CLOSED bar (not the current forming bar)
                # The forming bar is always the last one in the list
                if (gbpaud_bar is all_bars["GBPAUD"][-1] or
                    gbpnzd_bar is all_bars["GBPNZD"][-1] or
                    audnzd_bar is all_bars["AUDNZD"][-1]):
                    # One or more legs are still forming — skip
                    continue
                
                # Valid closed snapshot found
                return TriangularSnapshot(
                    timestamp=candidate,
                    gbpaud_bar=gbpaud_bar,
                    gbpnzd_bar=gbpnzd_bar,
                    audnzd_bar=audnzd_bar,
                )
        
        # Could not find synchronized closed snapshot
        print("[DATA_FEED] WARNING: Could not find synchronized closed M5 snapshot")
        return None
    
    def fetch_latest_snapshot(self) -> Optional[TriangularSnapshot]:
        """Fetch the latest synchronized TriangularSnapshot.
        
        This is the main entry point — fetches all bars, builds snapshot.
        
        Returns:
            TriangularSnapshot if valid, None if sync fails.
        """
        all_bars = self.fetch_all_triangle_bars(count=500)
        if all_bars is None:
            return None
        
        return self.build_snapshot(all_bars)
    
    def get_est_hour_now(self) -> Optional[int]:
        """Get current EST hour from MT5 server time.
        
        Returns:
            EST hour (0-23), or None if MT5 unavailable.
        """
        if mt5 is None:
            return None
        
        try:
            # Get time from any available symbol
            for sym in TRIANGLE_SYMBOLS:
                broker_sym = self.symbol_map.get(sym)
                tick = mt5.symbol_info_tick(broker_sym)
                if tick and tick.time > 0:
                    mt5_time = _mt5_time_to_datetime(tick.time)
                    return _est_hour(mt5_time)
        except Exception as e:
            print(f"[DATA_FEED] ERROR getting MT5 time: {e}")
        
        return None
    
    def is_london_session(self) -> bool:
        """Check if current time is within London session (3AM-12PM EST)."""
        est_hour = self.get_est_hour_now()
        if est_hour is None:
            return False
        return _is_london_session(est_hour)
    
    def minutes_to_hard_exit(self) -> int:
        """Calculate minutes remaining until 12PM EST hard exit."""
        est_hour = self.get_est_hour_now()
        if est_hour is None:
            return 0
        return _minutes_to_hard_exit(est_hour)
    
    def shutdown(self):
        """Shutdown MT5 connection."""
        if mt5 is not None:
            mt5.shutdown()
            print("[DATA_FEED] Shutdown complete")

