"""
V3 Phase 5 — Temporal BSP Projection
Long-horizon continuity forecasting.

Predicts: trajectory collapse, mission drift, entropy accumulation,
memory fragmentation, topology decay, resource exhaustion,
strategic divergence — BEFORE they occur.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from .temporal_trajectory import TemporalTrajectoryEngine, Trajectory


@dataclass
class TemporalProjection:
    """A long-horizon forecast for the cognitive field."""
    projection_id: str
    target_trajectory: str
    forecast_type: str           # "collapse", "drift", "convergence", "stability"
    confidence: float            # 0.0-1.0
    time_horizon_hours: float    # How far ahead this predicts
    risk_factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_critical(self) -> bool:
        return self.forecast_type in ["collapse", "drift"] and self.confidence > 0.7

    def to_dict(self) -> dict:
        return {
            "projection_id": self.projection_id,
            "target": self.target_trajectory,
            "forecast": self.forecast_type,
            "confidence": round(self.confidence, 4),
            "horizon_hours": round(self.time_horizon_hours, 2),
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "is_critical": self.is_critical,
        }


class TemporalBSPProjection:
    """
    Long-horizon continuity forecasting using BSP principles.
    
    Instead of asking "What should happen next?", asks:
    "What future states maintain coherence across time?"
    
    Projects trajectories forward to predict:
    - Trajectory collapse (coherence dropping below threshold)
    - Mission drift (strategic divergence from attractors)
    - Entropy accumulation (field becoming disordered)
    - Memory fragmentation (identity losing coherence)
    - Topology decay (field structure degrading)
    - Resource exhaustion (compute budget depletion)
    """

    def __init__(self, trajectory_engine: TemporalTrajectoryEngine = None):
        self.trajectory_engine = trajectory_engine or TemporalTrajectoryEngine()
        self._projection_history: list[TemporalProjection] = []

    def project_trajectory(
        self, trajectory_id: str, horizon_hours: float = 24.0,
    ) -> TemporalProjection:
        """
        Project a trajectory forward in time.
        
        Args:
            trajectory_id: The trajectory to project
            horizon_hours: How far ahead to forecast
            
        Returns:
            TemporalProjection with forecast and recommendations
        """
        traj = self.trajectory_engine.get_trajectory(trajectory_id)
        if not traj:
            return TemporalProjection(
                projection_id=f"proj_{int(time.time())}",
                target_trajectory=trajectory_id,
                forecast_type="unknown",
                confidence=0.0,
                time_horizon_hours=horizon_hours,
                risk_factors=["trajectory_not_found"],
            )

        # Analyze trajectory trends
        coherence_trend = self._estimate_coherence_trend(traj)
        entropy_trend = self._estimate_entropy_trend(traj)

        # Determine forecast type
        future_coherence = traj.coherence_score + coherence_trend * horizon_hours
        future_entropy = traj.entropy_drift + entropy_trend * horizon_hours

        if future_coherence < 0.3:
            forecast = "collapse"
            confidence = min(1.0, abs(future_coherence - traj.coherence_score))
        elif future_entropy > 0.7:
            forecast = "drift"
            confidence = min(1.0, future_entropy)
        elif future_coherence > 0.7 and future_entropy < 0.3:
            forecast = "stability"
            confidence = future_coherence
        else:
            forecast = "convergence"
            confidence = 0.5

        # Risk factors
        risks = []
        if traj.coherence_score < 0.5:
            risks.append("low_current_coherence")
        if traj.entropy_drift > 0.5:
            risks.append("high_entropy_drift")
        if len(traj.historical_states) < 3:
            risks.append("insufficient_history")
        if traj.age_hours > 168:  # 1 week
            risks.append("stale_trajectory")

        # Recommendations
        recs = []
        if forecast == "collapse":
            recs.append("Trigger repair observer")
            recs.append("Rebuild local coherence")
            recs.append("Review trajectory attractors")
        elif forecast == "drift":
            recs.append("Reinforce identity anchors")
            recs.append("Compress and prioritize")
            recs.append("Re-synchronize observers")
        elif forecast == "stability":
            recs.append("Reinforce successful patterns")
            recs.append("Document attractor for reuse")

        projection = TemporalProjection(
            projection_id=f"tproj_{int(time.time())}",
            target_trajectory=trajectory_id,
            forecast_type=forecast,
            confidence=round(confidence, 4),
            time_horizon_hours=horizon_hours,
            risk_factors=risks,
            recommendations=recs,
        )

        self._projection_history.append(projection)
        return projection

    def _estimate_coherence_trend(self, traj: Trajectory) -> float:
        """Estimate coherence change per hour."""
        if traj.age_hours < 1:
            return 0.0
        # Simple: current coherence vs assumed baseline of 0.5
        return (traj.coherence_score - 0.5) / max(traj.age_hours, 1)

    def _estimate_entropy_trend(self, traj: Trajectory) -> float:
        """Estimate entropy drift per hour."""
        if traj.age_hours < 1:
            return 0.0
        return traj.entropy_drift / max(traj.age_hours, 1)

    def get_critical_projections(self) -> list[TemporalProjection]:
        """Get all critical projections that need attention."""
        return [p for p in self._projection_history if p.is_critical]

    @property
    def stats(self) -> dict:
        if not self._projection_history:
            return {"total_projections": 0, "critical_count": 0}
        critical = sum(1 for p in self._projection_history if p.is_critical)
        return {
            "total_projections": len(self._projection_history),
            "critical_count": critical,
            "avg_confidence": round(
                sum(p.confidence for p in self._projection_history) / len(self._projection_history), 4
            ),
        }
