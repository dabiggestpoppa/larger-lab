"""
Structural Decay Monitor — Crypto Asset Integrity Tracker
==========================================================
Monitors live DEX/CEX data for structural degradation.
If an asset loses its 'foundational' liquidity profile, it is auto-blacklisted.

This is the "No Trash" continuous filter from the lab expansion plan.
Runs parallel to the trading engine — does NOT care about price action,
only the liquidity and volume profile that makes atomic structure possible.

Usage:
    from .structural_decay_monitor import StructuralDecayMonitor, DecayConfig

    monitor = StructuralDecayMonitor(config)
    result = monitor.evaluate_live_integrity(order_book, ticker, funding_rate)
    # result = {"action": "HOLD"|"PAUSE"|"BLACKLIST", "reason": "..."}
"""

import json
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

@dataclass
class DecayConfig:
    """Configuration for structural decay monitoring per asset."""
    name: str
    min_order_book_depth_pct: float = 0.005    # 0.5% of market cap
    min_daily_volume_usd: float = 10_000_000   # $10M minimum
    max_funding_rate: float = 0.001            # 0.1% absolute
    min_age_days: int = 30
    depth_violation_threshold: int = 3         # consecutive hours of thin book
    volume_decay_pct: float = 0.40             # 40% below 7-day avg = decay
    funding_mania_multiplier: float = 1.5       # 1.5x max = mania
    pause_duration_hours: int = 2


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────────

@dataclass
class DecayState:
    """Tracks decay state for a single asset over time."""
    asset_name: str
    depth_violations: int = 0
    last_volume_check: float = 0.0
    seven_day_avg_volume: float = 0.0
    is_paused: bool = False
    pause_until: Optional[datetime] = None
    is_blacklisted: bool = False
    blacklist_reason: str = ""
    last_evaluation: Optional[datetime] = None
    evaluation_history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "asset_name": self.asset_name,
            "depth_violations": self.depth_violations,
            "is_paused": self.is_paused,
            "is_blacklisted": self.is_blacklisted,
            "blacklist_reason": self.blacklist_reason,
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation else None,
        }


@dataclass
class DecayResult:
    """Result of a single decay evaluation."""
    action: str          # "HOLD" | "PAUSE" | "BLACKLIST"
    reason: str
    metrics: dict        # raw metrics that drove the decision
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─── MONITOR ─────────────────────────────────────────────────────────────────

class StructuralDecayMonitor:
    """
    Monitors live DEX/CEX data for structural degradation.
    If an asset loses its 'foundational' liquidity profile, auto-blacklists it.
    """

    def __init__(self, configs: list[DecayConfig], state_file: Optional[Path] = None):
        self.configs = {c.name: c for c in configs}
        self.state_file = state_file or Path(__file__).parent / "decay_state.json"
        self.states: dict[str, DecayState] = {}
        self._load_state()

    def _load_state(self):
        """Load persistent decay state from disk."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                for name, s in data.items():
                    self.states[name] = DecayState(
                        asset_name=s["asset_name"],
                        depth_violations=s.get("depth_violations", 0),
                        is_paused=s.get("is_paused", False),
                        is_blacklisted=s.get("is_blacklisted", False),
                        blacklist_reason=s.get("blacklist_reason", ""),
                    )
            except Exception as e:
                logger.warning(f"Could not load decay state: {e}")

    def _save_state(self):
        """Persist decay state to disk."""
        data = {name: s.to_dict() for name, s in self.states.items()}
        self.state_file.write_text(json.dumps(data, indent=2))

    def _get_or_create_state(self, asset_name: str) -> DecayState:
        if asset_name not in self.states:
            self.states[asset_name] = DecayState(asset_name=asset_name)
        return self.states[asset_name]

    def evaluate_live_integrity(
        self,
        asset_name: str,
        order_book: dict,
        ticker: dict,
        funding_rate: float,
    ) -> DecayResult:
        """
        Evaluate a single asset's structural integrity.

        Args:
            asset_name: e.g. "BTC/USD"
            order_book: {"bids": [[price, qty], ...], "asks": [[price, qty], ...]}
            ticker: {"quote_volume_24h": float, "market_cap": float, ...}
            funding_rate: current 8h funding rate (e.g. 0.0005 = 0.05%)

        Returns:
            DecayResult with action (HOLD/PAUSE/BLACKLIST) and reason
        """
        config = self.configs.get(asset_name)
        if config:
            cfg = config
        else:
            cfg = DecayConfig(name=asset_name)

        state = self._get_or_create_state(asset_name)
        state.last_evaluation = datetime.now(timezone.utc)

        # ── CHECK 1: Already blacklisted ────────────────────────────────────
        if state.is_blacklisted:
            return DecayResult(
                action="BLACKLIST",
                reason=f"Already blacklisted: {state.blacklist_reason}",
                metrics={},
            )

        # ── CHECK 2: Currently paused ───────────────────────────────────────
        if state.is_paused and state.pause_until:
            if datetime.now(timezone.utc) < state.pause_until:
                remaining = (state.pause_until - datetime.now(timezone.utc)).total_seconds() / 3600
                return DecayResult(
                    action="PAUSE",
                    reason=f"Paused for {remaining:.1f} more hours",
                    metrics={"pause_until": state.pause_until.isoformat()},
                )
            else:
                # Pause expired — resume
                state.is_paused = False
                state.pause_until = None
                logger.info(f"[{asset_name}] Pause expired — resuming monitoring")

        metrics = {}

        # ── CHECK 3: Order Book Depth ───────────────────────────────────────
        try:
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])
            if bids and asks:
                mid_price = (float(bids[0][0]) + float(asks[0][0])) / 2
                top_bid_depth = sum(float(b[1]) * float(b[0]) for b in bids[:3])
                top_ask_depth = sum(float(a[1]) * float(a[0]) for a in asks[:3])
                total_depth = top_bid_depth + top_ask_depth
                market_cap = float(ticker.get("market_cap", 0))

                if market_cap > 0:
                    depth_pct = (total_depth * mid_price) / market_cap
                    metrics["depth_pct"] = depth_pct
                    metrics["min_depth_pct"] = cfg.min_order_book_depth_pct

                    if depth_pct < (cfg.min_order_book_depth_pct * 0.6):
                        state.depth_violations += 1
                        metrics["depth_violations"] = state.depth_violations

                        if state.depth_violations >= cfg.depth_violation_threshold:
                            state.is_blacklisted = True
                            state.blacklist_reason = (
                                f"Structural decay — order book thin for "
                                f"{state.depth_violations} consecutive checks"
                            )
                            self._save_state()
                            logger.warning(f"[{asset_name}] BLACKLISTED: {state.blacklist_reason}")
                            return DecayResult(
                                action="BLACKLIST",
                                reason=state.blacklist_reason,
                                metrics=metrics,
                            )
                    else:
                        state.depth_violations = 0
        except (KeyError, IndexError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"[{asset_name}] Error checking order book depth: {e}")

        # ── CHECK 4: Volume Decay ───────────────────────────────────────────
        try:
            volume_24h = float(ticker.get("quote_volume_24h", 0))
            metrics["volume_24h"] = volume_24h
            metrics["min_volume"] = cfg.min_daily_volume_usd

            if volume_24h < cfg.min_daily_volume_usd:
                state.is_blacklisted = True
                state.blacklist_reason = (
                    f"Volume dried up: ${volume_24h:,.0f} < "
                    f"${cfg.min_daily_volume_usd:,.0f} minimum"
                )
                self._save_state()
                logger.warning(f"[{asset_name}] BLACKLISTED: {state.blacklist_reason}")
                return DecayResult(
                    action="BLACKLIST",
                    reason=state.blacklist_reason,
                    metrics=metrics,
                )

            # Check 7-day average decay
            if state.seven_day_avg_volume > 0:
                if volume_24h < (state.seven_day_avg_volume * (1 - cfg.volume_decay_pct)):
                    state.is_blacklisted = True
                    state.blacklist_reason = (
                        f"Volume decayed {((1 - volume_24h/state.seven_day_avg_volume)*100):.0f}% "
                        f"below 7-day avg"
                    )
                    self._save_state()
                    logger.warning(f"[{asset_name}] BLACKLISTED: {state.blacklist_reason}")
                    return DecayResult(
                        action="BLACKLIST",
                        reason=state.blacklist_reason,
                        metrics=metrics,
                    )

            # Update rolling average
            if state.seven_day_avg_volume == 0:
                state.seven_day_avg_volume = volume_24h
            else:
                state.seven_day_avg_volume = (state.seven_day_avg_volume * 6 + volume_24h) / 7

        except (ValueError, TypeError) as e:
            logger.warning(f"[{asset_name}] Error checking volume: {e}")

        # ── CHECK 5: Funding Rate Mania ──────────────────────────────────────
        metrics["funding_rate"] = funding_rate
        metrics["max_funding"] = cfg.max_funding_rate

        if abs(funding_rate) > (cfg.max_funding_rate * cfg.funding_mania_multiplier):
            state.is_paused = True
            state.pause_until = datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            )
            # Add pause_duration_hours
            from datetime import timedelta
            state.pause_until += timedelta(hours=cfg.pause_duration_hours)
            self._save_state()
            logger.info(
                f"[{asset_name}] PAUSED: Funding rate {funding_rate:.4f} exceeds "
                f"mania threshold. Resuming at {state.pause_until.isoformat()}"
            )
            return DecayResult(
                action="PAUSE",
                reason=(
                    f"Extreme funding mania — structure broken. "
                    f"Rate={fundance_rate:.4f}, threshold={cfg.max_funding_rate * cfg.funding_mania_multiplier:.4f}"
                ),
                metrics=metrics,
            )

        # ── ALL CHECKS PASSED ───────────────────────────────────────────────
        self._save_state()
        return DecayResult(action="HOLD", reason="Integrity sustained", metrics=metrics)

    def get_blacklist(self) -> list[str]:
        """Return list of blacklisted asset names."""
        return [name for name, s in self.states.items() if s.is_blacklisted]

    def get_paused(self) -> list[str]:
        """Return list of currently paused asset names."""
        return [name for name, s in self.states.items() if s.is_paused]

    def get_status_report(self) -> dict:
        """Full status report for dashboard."""
        return {
            "monitored": list(self.configs.keys()),
            "blacklisted": self.get_blacklist(),
            "paused": self.get_paused(),
            "states": {name: s.to_dict() for name, s in self.states.items()},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
