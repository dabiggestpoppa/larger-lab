"""7_multiscale.scale_bridge

Scale Bridge — translates data between timeframe resolutions.

Provides bidirectional translation between tick, bar, daily, and weekly
timeframes. Aggregates (upscale) and interpolates (downscale) data
to enable cross-scale analysis and coordination between engines.
"""

import logging
import math
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.scale_bridge")


# Scale hierarchy: tick < bar < daily < weekly
SCALE_LEVELS = ["tick", "bar", "daily", "weekly"]
SCALE_FACTORS = {
    ("tick", "bar"): 100,
    ("bar", "daily"): 288,    # 288 5-min bars in a trading day
    ("daily", "weekly"): 5,    # 5 trading days in a week
}


class ScaleTranslation(BaseModel):
    """Record of a scale translation."""
    from_scale: str
    to_scale: str
    input_count: int
    output_count: int
    method: str  # aggregate or interpolate


class ScaleBridgeConfig(BaseModel):
    """Configuration for scale_bridge."""
    enabled: bool = True
    supported_scales: List[str] = Field(default_factory=lambda: ["tick", "bar", "daily", "weekly"])
    interpolation_method: str = "linear"  # linear, nearest, cubic
    aggregation_method: str = "mean"  # mean, sum, last, ohlc


class ScaleBridgeModule:
    """Translates data between timeframe resolutions."""

    def __init__(self):
        self.config = ScaleBridgeConfig()
        self.running = False
        self._lock = Lock()
        self._translation_count: int = 0
        self._last_translation: Optional[ScaleTranslation] = None
        self._error_count: int = 0

    def start(self) -> None:
        self.running = True
        logger.info("ScaleBridgeModule started (scales: %s)", self.config.supported_scales)

    def stop(self) -> None:
        self.running = False
        logger.info("ScaleBridgeModule stopped (%d translations, %d errors)",
                     self._translation_count, self._error_count)

    def list_scales(self) -> List[str]:
        """Return list of supported scales in ascending order."""
        return list(self.config.supported_scales)

    def get_scale_factor(self, from_scale: str, to_scale: str) -> Optional[int]:
        """Get the conversion factor between two adjacent scales.

        Args:
            from_scale: Source scale.
            to_scale: Target scale.

        Returns:
            Integer factor if scales are adjacent, None otherwise.
        """
        return SCALE_FACTORS.get((from_scale, to_scale))

    def _get_scale_level(self, scale: str) -> int:
        """Get numeric level of a scale (higher = larger timeframe)."""
        try:
            return SCALE_LEVELS.index(scale)
        except ValueError:
            return -1

    def translate(self, data: List[Dict[str, Any]], from_scale: str,
                  to_scale: str) -> Tuple[List[Dict[str, Any]], ScaleTranslation]:
        """Translate data between scales.

        Automatically determines whether to aggregate (upscale) or
        interpolate (downscale) based on scale ordering.

        Args:
            data: List of data points (each a dict with at least a 'value' key).
            from_scale: Source scale.
            to_scale: Target scale.

        Returns:
            Tuple of (translated_data, translation_record).
        """
        with self._lock:
            from_level = self._get_scale_level(from_scale)
            to_level = self._get_scale_level(to_scale)

            if from_level < 0 or to_level < 0:
                self._error_count += 1
                raise ValueError(f"Invalid scale: {from_scale} or {to_scale}")

            if from_level == to_level:
                # No translation needed
                translation = ScaleTranslation(
                    from_scale=from_scale, to_scale=to_scale,
                    input_count=len(data), output_count=len(data), method="identity",
                )
                return data, translation

            if from_level < to_level:
                result = self._aggregate(data, from_scale, to_scale, from_level, to_level)
                method = "aggregate"
            else:
                result = self._interpolate(data, from_scale, to_scale, from_level, to_level)
                method = "interpolate"

            translation = ScaleTranslation(
                from_scale=from_scale, to_scale=to_scale,
                input_count=len(data), output_count=len(result), method=method,
            )
            self._translation_count += 1
            self._last_translation = translation

            logger.debug("Translated %d points from %s to %s -> %d points (%s)",
                         len(data), from_scale, to_scale, len(result), method)
            return result, translation

    def _aggregate(self, data: List[Dict[str, Any]], from_scale: str,
                   to_scale: str, from_level: int, to_level: int) -> List[Dict[str, Any]]:
        """Aggregate data to a larger timeframe."""
        if not data:
            return []

        # Calculate total aggregation factor
        total_factor = 1
        for i in range(from_level, to_level):
            factor = SCALE_FACTORS.get((SCALE_LEVELS[i], SCALE_LEVELS[i + 1]), 1)
            total_factor *= factor

        result = []
        agg_method = self.config.aggregation_method

        for i in range(0, len(data), total_factor):
            chunk = data[i:i + total_factor]
            if not chunk:
                continue

            if agg_method == "mean":
                values = [p.get("value", 0) for p in chunk if isinstance(p.get("value"), (int, float))]
                agg_value = sum(values) / len(values) if values else 0
            elif agg_method == "sum":
                values = [p.get("value", 0) for p in chunk if isinstance(p.get("value"), (int, float))]
                agg_value = sum(values)
            elif agg_method == "last":
                agg_value = chunk[-1].get("value", 0)
            elif agg_method == "ohlc":
                values = [p.get("value", 0) for p in chunk if isinstance(p.get("value"), (int, float))]
                agg_value = {
                    "open": values[0] if values else 0,
                    "high": max(values) if values else 0,
                    "low": min(values) if values else 0,
                    "close": values[-1] if values else 0,
                }
            else:
                agg_value = chunk[-1].get("value", 0)

            agg_point = {"value": agg_value, "source_count": len(chunk)}
            # Carry forward timestamp if available
            if "timestamp" in chunk[-1]:
                agg_point["timestamp"] = chunk[-1]["timestamp"]
            if "timestamp" in chunk[0]:
                agg_point["start_timestamp"] = chunk[0]["timestamp"]

            result.append(agg_point)

        return result

    def _interpolate(self, data: List[Dict[str, Any]], from_scale: str,
                     to_scale: str, from_level: int, to_level: int) -> List[Dict[str, Any]]:
        """Interpolate data to a smaller timeframe."""
        if not data:
            return []

        # Calculate total expansion factor
        total_factor = 1
        for i in range(to_level, from_level):
            factor = SCALE_FACTORS.get((SCALE_LEVELS[i], SCALE_LEVELS[i + 1]), 1)
            total_factor *= factor

        result = []
        interp_method = self.config.interpolation_method

        for i in range(len(data)):
            result.append(data[i])

            # Insert interpolated points between data[i] and data[i+1]
            if i < len(data) - 1:
                v1 = data[i].get("value", 0)
                v2 = data[i + 1].get("value", 0)

                if not isinstance(v1, (int, float)) or not isinstance(v2, (int, float)):
                    # Non-numeric: just duplicate
                    for _ in range(total_factor - 1):
                        result.append(data[i])
                    continue

                for j in range(1, total_factor):
                    t = j / total_factor
                    if interp_method == "linear":
                        interp_value = v1 + t * (v2 - v1)
                    elif interp_method == "nearest":
                        interp_value = v1 if t < 0.5 else v2
                    else:
                        interp_value = v1 + t * (v2 - v1)  # default linear

                    result.append({"value": round(interp_value, 6), "interpolated": True})

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get scale bridge statistics."""
        with self._lock:
            return {
                "translation_count": self._translation_count,
                "error_count": self._error_count,
                "supported_scales": self.config.supported_scales,
                "last_translation": self._last_translation.model_dump() if self._last_translation else None,
                "aggregation_method": self.config.aggregation_method,
                "interpolation_method": self.config.interpolation_method,
            }
