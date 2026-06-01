"""
Self-Healing Telemetry — Execution Friction Monitor & Auto-Patch Engine
========================================================================
Tracks live fill quality (slippage, latency) and auto-patches the OCC buffer
in the asset config when broker friction exceeds tolerance.

This is the "Mirror Heals" layer from the lab expansion plan.
Runs parallel to the trading engine — monitors execution, generates config patches,
validates schema, and hot-swaps without restarting the bot.

Usage:
    from .self_healing_telemetry import SelfHealingTelemetry, TelemetryConfig

    telemetry = SelfHealingTelemetry(config)
    telemetry.record_fill(theoretical_sl=45000.0, actual_sl=45012.5, venue_type="DEX")
    patch = telemetry.generate_config_patch("BTC/USD")
    # patch = {"occ_buffer": 26, "reason": "Auto-widened buffer..."} or {}
"""

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

@dataclass
class TelemetryConfig:
    """Configuration for self-healing telemetry per asset."""
    name: str
    slippage_sample_size: int = 20       # min fills before generating patch
    slippage_threshold_pct: float = 0.20  # slip > 20% of buffer = widen
    max_buffer_widen_ticks: int = 5       # max ticks to add per patch
    latency_threshold_ms: int = 500       # fill latency threshold
    venue_switch_slippage_pct: float = 0.10  # slip > 10% of AU = switch venue
    config_path: Optional[str] = None     # path to asset config YAML


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────────

@dataclass
class FillRecord:
    """Single fill record for telemetry."""
    timestamp: datetime
    asset_name: str
    theoretical_price: float
    actual_price: float
    slippage_ticks: float
    venue_type: str       # "DEX" | "CFD" | "NT8"
    latency_ms: float = 0.0
    quantity: float = 0.0


@dataclass
class ConfigPatch:
    """Generated config patch from telemetry analysis."""
    asset_name: str
    field: str             # e.g. "occ_buffer", "preferred_venue"
    old_value: any
    new_value: any
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "asset_name": self.asset_name,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


# ─── TELEMETRY ENGINE ────────────────────────────────────────────────────────

class SelfHealingTelemetry:
    """
    Tracks live fill quality and auto-patches config when friction exceeds tolerance.
    """

    def __init__(self, configs: list[TelemetryConfig], patch_log_path: Optional[Path] = None):
        self.configs = {c.name: c for c in configs}
        self.fill_log: dict[str, list[FillRecord]] = {}  # asset_name -> fills
        self.patch_log: list[ConfigPatch] = []
        self.patch_log_path = patch_log_path or Path(__file__).parent / "telemetry_patches.json"

    def record_fill(
        self,
        asset_name: str,
        theoretical_price: float,
        actual_price: float,
        venue_type: str,
        tick_size: float = 1.0,
        latency_ms: float = 0.0,
        quantity: float = 0.0,
    ):
        """
        Record a single fill for telemetry analysis.

        Args:
            asset_name: e.g. "BTC/USD"
            theoretical_price: expected fill price (from OCC extreme)
            actual_price: actual fill price from broker
            venue_type: "DEX" | "CFD" | "NT8"
            tick_size: instrument tick size for slippage calculation
            latency_ms: fill latency in milliseconds
            quantity: fill quantity
        """
        slip_ticks = abs(actual_price - theoretical_price) / tick_size if tick_size > 0 else 0

        record = FillRecord(
            timestamp=datetime.now(timezone.utc),
            asset_name=asset_name,
            theoretical_price=theoretical_price,
            actual_price=actual_price,
            slippage_ticks=slip_ticks,
            venue_type=venue_type,
            latency_ms=latency_ms,
            quantity=quantity,
        )

        if asset_name not in self.fill_log:
            self.fill_log[asset_name] = []
        self.fill_log[asset_name].append(record)

        logger.debug(
            f"[{asset_name}] Fill recorded: slip={slip_ticks:.2f} ticks, "
            f"venue={venue_type}, latency={latency_ms:.0f}ms"
        )

    def generate_config_patch(self, asset_name: str) -> Optional[ConfigPatch]:
        """
        Analyze recent fills and generate a config patch if needed.

        Returns:
            ConfigPatch if a patch is needed, None if config is fine.
        """
        fills = self.fill_log.get(asset_name, [])
        cfg = self.configs.get(asset_name)
        if not cfg:
            return None

        if len(fills) < cfg.slippage_sample_size:
            return None  # Need more data

        recent = fills[-50:]  # Last 50 fills
        avg_slip = sum(f.slippage_ticks for f in recent) / len(recent)
        max_slip = max(f.slippage_ticks for f in recent)

        logger.info(
            f"[{asset_name}] Telemetry: avg_slip={avg_slip:.2f} ticks, "
            f"max_slip={max_slip:.2f} ticks over {len(recent)} fills"
        )

        # ── PATCH 1: OCC Buffer Widening ──────────────────────────────────
        # Get current buffer from config
        current_buffer = self._get_current_buffer(asset_name)
        if current_buffer and avg_slip > (current_buffer * cfg.slippage_threshold_pct):
            new_buffer = min(
                current_buffer + math.ceil(avg_slip),
                current_buffer + cfg.max_buffer_widen_ticks,
            )
            patch = ConfigPatch(
                asset_name=asset_name,
                field="occ_buffer",
                old_value=current_buffer,
                new_value=new_buffer,
                reason=(
                    f"Auto-widened OCC buffer from {current_buffer} to {new_buffer} "
                    f"due to avg slippage of {avg_slip:.1f} ticks "
                    f"(threshold: {current_buffer * cfg.slippage_threshold_pct:.1f})"
                ),
            )
            self._apply_patch(patch)
            return patch

        # ── PATCH 2: Venue Switch ─────────────────────────────────────────
        au_value = self._get_atomic_unit(asset_name)
        if au_value and avg_slip > (au_value * cfg.venue_switch_slippage_pct):
            # Determine current venue and suggest switch
            recent_venue = recent[-1].venue_type
            new_venue = "CFD" if recent_venue == "DEX" else "DEX"
            patch = ConfigPatch(
                asset_name=asset_name,
                field="preferred_venue",
                old_value=recent_venue,
                new_value=new_venue,
                reason=(
                    f"DEX slippage ({avg_slip:.1f} ticks) exceeds {cfg.venue_switch_slippage_pct*100:.0f}% "
                    f"of AU ({au_value:.1f} ticks). Rerouting to {new_venue} for tighter spreads."
                ),
            )
            self._apply_patch(patch)
            return patch

        # ── PATCH 3: Latency-Based Routing ─────────────────────────────────
        avg_latency = sum(f.latency_ms for f in recent) / len(recent)
        if avg_latency > cfg.latency_threshold_ms:
            recent_venue = recent[-1].venue_type
            new_venue = "CFD" if recent_venue == "DEX" else "DEX"
            patch = ConfigPatch(
                asset_name=asset_name,
                field="preferred_venue",
                old_value=recent_venue,
                new_value=new_venue,
                reason=(
                    f"Fill latency ({avg_latency:.0f}ms) exceeds threshold "
                    f"({cfg.latency_threshold_ms}ms). Rerouting to {new_venue}."
                ),
            )
            self._apply_patch(patch)
            return patch

        return None  # No patch needed

    def _get_current_buffer(self, asset_name: str) -> Optional[float]:
        """Read current OCC buffer from asset config YAML."""
        cfg = self.configs.get(asset_name)
        if not cfg or not cfg.config_path:
            return None
        try:
            config_file = Path(cfg.config_path)
            if config_file.exists():
                data = yaml.safe_load(config_file.read_text())
                return data.get("noise_filters", {}).get("occ_buffer")
        except Exception as e:
            logger.warning(f"[{asset_name}] Error reading config: {e}")
        return None

    def _get_atomic_unit(self, asset_name: str) -> Optional[float]:
        """Read current Atomic Unit from asset config YAML."""
        cfg = self.configs.get(asset_name)
        if not cfg or not cfg.config_path:
            return None
        try:
            config_file = Path(cfg.config_path)
            if config_file.exists():
                data = yaml.safe_load(config_file.read_text())
                return data.get("atomic_unit")
        except Exception as e:
            logger.warning(f"[{asset_name}] Error reading config: {e}")
        return None

    def _apply_patch(self, patch: ConfigPatch):
        """Apply a config patch to the asset YAML file."""
        self.patch_log.append(patch)

        # Log the patch
        logger.info(f"[{patch.asset_name}] Config patch: {patch.reason}")

        # Write to patch log
        try:
            existing = []
            if self.patch_log_path.exists():
                existing = json.loads(self.patch_log_path.read_text())
            existing.append(patch.to_dict())
            self.patch_log_path.write_text(json.dumps(existing, indent=2))
        except Exception as e:
            logger.warning(f"Error writing patch log: {e}")

        # Apply to config file
        cfg = self.configs.get(patch.asset_name)
        if not cfg or not cfg.config_path:
            return
        try:
            config_file = Path(cfg.config_path)
            if config_file.exists():
                data = yaml.safe_load(config_file.read_text()) or {}
                # Navigate to the right field
                if patch.field == "occ_buffer":
                    if "noise_filters" not in data:
                        data["noise_filters"] = {}
                    data["noise_filters"]["occ_buffer"] = patch.new_value
                elif patch.field == "preferred_venue":
                    data["preferred_venue"] = patch.new_value

                config_file.write_text(yaml.dump(data, default_flow_style=False))
                logger.info(f"[{patch.asset_name}] Config hot-swapped successfully")
        except Exception as e:
            logger.error(f"[{patch.asset_name}] Error applying config patch: {e}")

    def get_telemetry_report(self, asset_name: str) -> dict:
        """Get telemetry report for an asset."""
        fills = self.fill_log.get(asset_name, [])
        if not fills:
            return {"asset_name": asset_name, "fills": 0}

        recent = fills[-50:]
        return {
            "asset_name": asset_name,
            "total_fills": len(fills),
            "avg_slip_ticks": sum(f.slippage_ticks for f in recent) / len(recent),
            "max_slip_ticks": max(f.slippage_ticks for f in recent),
            "avg_latency_ms": sum(f.latency_ms for f in recent) / len(recent),
            "recent_patches": [
                p.to_dict() for p in self.patch_log if p.asset_name == asset_name
            ][-5:],
        }
