"""
CEREBUS FX v4.0 — Crypto Execution Engine
=========================================

Wraps the Symmetry Trap (Model B) and P90 Kinetic (Model A) engines
from quant-lab/engines/ for crypto asset backtesting and live deployment.

Supported assets: BTCUSD, ETHUSD (extensible via CRYPTO_PRESETS).
Engine logic is NOT rewritten — engines are imported and wrapped.

Asset config pattern mirrors CEREBUS_AssetPresets.cs (tradovate/):
  crypto (k=0.52) follows the same k-factor hierarchy as FX majors.

Usage:
  from CEREBUS_Crypto_Engine import CryptoEngine, CRYPTO_PRESETS
  engine = CryptoEngine(symbol="BTCUSD", mode="backtest")
  engine.load_data(bars)
  results = engine.run_session(asian_high, asian_low)

Author: CEREBUS Track B — Crypto Integration (MAD 2026-05-31)
"""

from __future__ import annotations

import csv
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Engine Imports ────────────────────────────────────────────────────────
# Add quant-lab/engines to path so we can import directly
_QUANT_LAB_ENGINES = str(Path(__file__).resolve().parent.parent / "quant-lab" / "engines")
if _QUANT_LAB_ENGINES not in sys.path:
    sys.path.insert(0, _QUANT_LAB_ENGINES)

try:
    from symmetry_trap import (
        SymmetryTrapEngine,
        Bar as STBar,
        TradeSignal as STTradeSignal,
    )
    from p90_engine import (
        P90Engine,
        Bar as P90Bar,
        P90Signal,
    )
except ImportError as _ie:
    # Fallback import path
    _PARENT = str(Path(__file__).resolve().parent.parent)
    if _PARENT not in sys.path:
        sys.path.insert(0, _PARENT)
    from quant_lab.engines.symmetry_trap import (
        SymmetryTrapEngine,
        Bar as STBar,
        TradeSignal as STTradeSignal,
    )
    from quant_lab.engines.p90_engine import (
        P90Engine,
        Bar as P90Bar,
        P90Signal,
    )


# ─── CRYPTO ASSET PRESETS ────────────────────────────────────────────────
# Mirrors CEREBUS_AssetPresets.cs — Crypto class (k=0.52)
# PipValue and thresholds calibrated per CEREBUS ontology for crypto

CRYPTO_PRESETS: Dict[str, dict] = {
    "BTCUSD": {
        "name": "BTC/USD",
        "k_factor": 0.52,
        "pip_value": 1.0,            # 1 unit = 1 "pip" for BTC
        "h3": 650.0, "h4": 600.0, "h5": 550.0, "h6": 510.0,
        "h7": 470.0, "h8": 440.0, "h9": 410.0, "h10": 380.0, "h11": 350.0,
        "t1_ar": 2600.0, "t1_au": 1300.0, "t1_trigger": 1560.0,
        "t2_ar": 3900.0, "t2_au": 1560.0, "t2_trigger": 1950.0,
        "t3_ar": 5200.0, "t3_au": 1950.0, "t3_trigger": 2600.0,
    },
    "ETHUSD": {
        "name": "ETH/USD",
        "k_factor": 0.52,
        "pip_value": 0.01,           # 0.01 = 1 "pip" for ETH
        "h3": 26.0, "h4": 24.0, "h5": 22.0, "h6": 20.5,
        "h7": 19.0, "h8": 18.0, "h9": 17.0, "h10": 16.0, "h11": 15.0,
        "t1_ar": 100.0, "t1_au": 50.0, "t1_trigger": 60.0,
        "t2_ar": 150.0, "t2_au": 60.0, "t2_trigger": 75.0,
        "t3_ar": 200.0, "t3_au": 75.0, "t3_trigger": 100.0,
    },
}


def _build_tier_config(preset: dict) -> Dict[str, Dict[str, float]]:
    """Convert CRYPTO_PRESETS dict to engine tier_config format."""
    return {
        "T1": {"ar_max": preset["t1_ar"], "au": preset["t1_au"], "trigger": preset["t1_trigger"]},
        "T2": {"ar_max": preset["t2_ar"], "au": preset["t2_au"], "trigger": preset["t2_trigger"]},
        "T3": {"ar_max": preset["t3_ar"], "au": preset["t3_au"], "trigger": preset["t3_trigger"]},
    }


def _build_p90_config(preset: dict) -> Dict[int, float]:
    """Convert per-hour thresholds from preset to p90_config format."""
    return {
        3: preset["h3"], 4: preset["h4"], 5: preset["h5"],
        6: preset["h6"], 7: preset["h7"], 8: preset["h8"],
        9: preset["h9"], 10: preset["h10"], 11: preset["h11"],
    }


# ─── Unified Bar ─────────────────────────────────────────────────────────

def make_bar(timestamp: datetime, open_: float, high: float, low: float, close: float) -> STBar:
    """Create a Bar compatible with both ST and P90 engines."""
    bar = STBar(timestamp=timestamp, open=open_, high=high, low=low, close=close)
    return bar


# ─── Trade Result ─────────────────────────────────────────────────────────

@dataclass
class CryptoTradeResult:
    """Unified trade result from either engine."""
    engine: str                 # "ST" or "P90"
    event: str                  # "ENTRY", "TP_HIT", "SL_HIT", "KILL_SWITCH", "EWS_EXIT"
    direction: str              # "LONG", "SHORT", "FLAT"
    entry_price: Optional[float]
    exit_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    pnl_pips: float
    timestamp: Optional[datetime]
    symbol: str
    reason: str


# ─── CSV Data Loader ─────────────────────────────────────────────────────

def load_csv_data(filepath: str, symbol: str = "") -> List[STBar]:
    """
    Load M5 OHLCV CSV data into Bar objects.

    Expected CSV columns: timestamp, open, high, low, close, volume (optional)
    Timestamp format: YYYY-MM-DD HH:MM:SS
    """
    bars: List[STBar] = []
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.strptime(row["timestamp"].strip(), "%Y-%m-%d %H:%M:%S")
                bar = STBar(
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                )
                bars.append(bar)
            except (KeyError, ValueError) as e:
                logging.warning(f"Skipping malformed row in {symbol}: {e}")
                continue

    logging.info(f"Loaded {len(bars)} bars from {filepath}")
    return bars


def compute_asian_range(bars: List[STBar]) -> Tuple[float, float]:
    """
    Compute Asian session high/low from loaded bars.
    Asian session: 19:00 - 03:00 EST (approximated from the session bars).

    For simplicity, uses session max high / session min low.
    In production, this would filter to Asian hours only.
    """
    if not bars:
        return 0.0, 0.0
    session_high = max(b.high for b in bars)
    session_low = min(b.low for b in bars)
    return session_high, session_low


# ─── Crypto Engine (Unified) ──────────────────────────────────────────────

class CryptoEngine:
    """
    Unified crypto execution engine.
    Runs both Symmetry Trap and P90 engines on the same data.
    Supports backtest and live modes.

    Args:
        symbol: Asset symbol (e.g., "BTCUSD", "ETHUSD")
        mode: "backtest" or "live"
    """

    def __init__(self, symbol: str = "BTCUSD", mode: str = "backtest"):
        self.symbol = symbol.upper()
        self.mode = mode
        self.logger = logging.getLogger(f"cerebus.crypto.{symbol}")

        if self.symbol not in CRYPTO_PRESETS:
            raise ValueError(
                f"Unknown crypto symbol: {symbol}. "
                f"Supported: {list(CRYPTO_PRESETS.keys())}"
            )

        preset = CRYPTO_PRESETS[self.symbol]
        tier_config = _build_tier_config(preset)
        p90_config = _build_p90_config(preset)
        config = {
            "name": preset["name"],
            "pip_value": preset["pip_value"],
            "tiers": tier_config,
        }

        # Initialize both engines
        self.st_engine = SymmetryTrapEngine(
            pip_size=preset["pip_value"],
            tier_config=tier_config,
            symbol=symbol,
            config=config,
        )
        self.p90_engine = P90Engine(
            pip_size=preset["pip_value"],
            p90_config=p90_config,
            tier_config=tier_config,
            symbol=symbol,
            config=config,
        )

        self.trade_results: List[CryptoTradeResult] = []
        self.bars: List[STBar] = []

    def load_data(self, filepath: str) -> None:
        """Load M5 CSV data from file."""
        self.bars = load_csv_data(filepath, self.symbol)
        self.logger.info(f"[{self.symbol}] Loaded {len(self.bars)} bars for {self.mode}")

    def load_bars(self, bars: List[STBar]) -> None:
        """Load bars directly (for programmatic use)."""
        self.bars = bars

    def run_session(
        self,
        asian_high: Optional[float] = None,
        asian_low: Optional[float] = None,
    ) -> List[CryptoTradeResult]:
        """
        Run both ST and P90 engines on loaded data.

        If asian_high/low not provided, computed from full dataset
        (production would use prior-day Asian session range).

        Returns:
            List of CryptoTradeResult for all trades
        """
        if not self.bars:
            raise ValueError("No data loaded. Call load_data() or load_bars() first.")

        # Compute Asian range if not provided
        if asian_high is None or asian_low is None:
            # Use first ~288 bars (24h of M5) as Asian session proxy
            session_bars = self.bars[:288] if len(self.bars) > 288 else self.bars
            asian_high, asian_low = compute_asian_range(session_bars)
            self.logger.info(
                f"[{self.symbol}] Asian range computed: high={asian_high}, low={asian_low}"
            )

        # Initialize both engines
        self.st_engine.initialize_session(asian_high, asian_low)
        self.p90_engine.initialize_session(asian_high, asian_low)

        results: List[CryptoTradeResult] = []
        pip_size = CRYPTO_PRESETS[self.symbol]["pip_value"]

        for bar in self.bars:
            # ── Symmetry Trap ───────────────────────────────────────
            st_signal = self.st_engine.process_bar(bar)
            if st_signal and st_signal.event in ("ENTRY", "TP_HIT", "SL_HIT"):
                result = self._convert_st_signal(st_signal, pip_size)
                results.append(result)

            # ── P90 Engine ──────────────────────────────────────────
            p90_bar = P90Bar(
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
            )
            p90_signal = self.p90_engine.process_bar(p90_bar)
            if p90_signal and p90_signal.event in ("ENTRY", "TP_HIT", "SL_HIT", "EWS_EXIT"):
                result = self._convert_p90_signal(p90_signal, pip_size)
                results.append(result)

        self.trade_results = results
        self.logger.info(
            f"[{self.symbol}] Session complete: {len(results)} trade events"
        )
        return results

    def _convert_st_signal(self, sig: STTradeSignal, pip_size: float) -> CryptoTradeResult:
        """Convert ST TradeSignal → CryptoTradeResult."""
        direction = sig.direction.name if sig.direction else "FLAT"
        pnl_pips = 0.0
        exit_price = None

        if sig.event == "TP_HIT" and sig.entry_price and sig.tp_price:
            exit_price = sig.tp_price
            pnl_pips = abs(sig.tp_price - sig.entry_price) / pip_size
        elif sig.event == "SL_HIT" and sig.entry_price and sig.sl_price:
            exit_price = sig.sl_price
            pnl_pips = -abs(sig.sl_price - sig.entry_price) / pip_size
        elif sig.event == "ENTRY":
            exit_price = None
            pnl_pips = 0.0

        return CryptoTradeResult(
            engine="ST",
            event=sig.event,
            direction=direction,
            entry_price=sig.entry_price,
            exit_price=exit_price,
            sl_price=sig.sl_price,
            tp_price=sig.tp_price,
            pnl_pips=round(pnl_pips, 2),
            timestamp=sig.timestamp,
            symbol=self.symbol,
            reason=sig.reason,
        )

    def _convert_p90_signal(self, sig: P90Signal, pip_size: float) -> CryptoTradeResult:
        """Convert P90Signal → CryptoTradeResult."""
        direction = sig.direction.name if sig.direction else "FLAT"
        pnl_pips = 0.0
        exit_price = None

        if sig.event == "TP_HIT" and sig.entry_price and sig.tp_price:
            exit_price = sig.tp_price
            pnl_pips = abs(sig.tp_price - sig.entry_price) / pip_size
        elif sig.event == "SL_HIT" and sig.entry_price and sig.sl_price:
            exit_price = sig.sl_price
            pnl_pips = -abs(sig.sl_price - sig.entry_price) / pip_size
        elif sig.event == "EWS_EXIT" and sig.entry_price:
            exit_price = sig.entry_price  # EWS force-closed at market
            pnl_pips = 0.0  # Unknown PnL without actual close price
        elif sig.event == "ENTRY":
            exit_price = None
            pnl_pips = 0.0

        return CryptoTradeResult(
            engine="P90",
            event=sig.event,
            direction=direction,
            entry_price=sig.entry_price,
            exit_price=exit_price,
            sl_price=sig.sl_price,
            tp_price=sig.tp_price,
            pnl_pips=round(pnl_pips, 2),
            timestamp=sig.timestamp,
            symbol=self.symbol,
            reason=sig.reason,
        )

    def get_summary(self) -> Dict:
        """Generate summary of all trade results."""
        entries = [r for r in self.trade_results if r.event == "ENTRY"]
        exits = [r for r in self.trade_results if r.event in ("TP_HIT", "SL_HIT", "EWS_EXIT")]
        wins = [r for r in exits if r.pnl_pips > 0]
        losses = [r for r in exits if r.pnl_pips < 0]

        total_pnl = sum(r.pnl_pips for r in exits)

        return {
            "symbol": self.symbol,
            "total_bars": len(self.bars),
            "total_entries": len(entries),
            "total_exits": len(exits),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": round(len(wins) / max(len(exits), 1) * 100, 1),
            "total_pnl_pips": round(total_pnl, 2),
            "avg_win_pips": round(sum(r.pnl_pips for r in wins) / max(len(wins), 1), 2),
            "avg_loss_pips": round(sum(r.pnl_pips for r in losses) / max(len(losses), 1), 2),
        }


# ─── Standalone Test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    print("CEREBUS Crypto Engine — BTCUSD smoke test")

    engine = CryptoEngine(symbol="BTCUSD")
    data_path = Path(__file__).resolve().parent.parent / "quant-lab" / "data" / "BTCUSD_M5.csv"
    if data_path.exists():
        engine.load_data(str(data_path))
        results = engine.run_session()
        summary = engine.get_summary()
        print(f"  Bars: {summary['total_bars']}")
        print(f"  Entries: {summary['total_entries']}")
        print(f"  Exits: {summary['total_exits']}")
        print(f"  WR: {summary['win_rate_pct']}%")
        print(f"  PnL: {summary['total_pnl_pips']} pips")
    else:
        print(f"  Data file not found: {data_path}")
        print("  Engine initialized OK — data file needed for full test")
