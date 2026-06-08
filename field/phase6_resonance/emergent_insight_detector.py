"""
6_resonance.emergent_insight_detector
=======================================
Detects emergent insights from cross-agent pattern analysis.

Monitors agent interactions, belief changes, and message patterns
to detect when new insights emerge that no single agent produced alone.

Insight types: correlation, contradiction, synthesis, prediction, anomaly.
Confidence scoring via multi-signal aggregation.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.resonance.emergent_insight")


class EmergentInsightDetectorConfig(BaseModel):
    """Configuration for emergent_insight_detector."""
    enabled: bool = True
    detection_window: int = 50
    min_confidence: float = 0.6
    max_insights: int = 1000
    correlation_threshold: float = 0.7


class Insight(BaseModel):
    """A detected emergent insight."""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    insight_type: str  # correlation, contradiction, synthesis, prediction, anomaly
    source_agents: List[str] = Field(default_factory=list)
    description: str = ""
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Signal(BaseModel):
    """A signal that may contribute to insight detection."""
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str
    signal_type: str  # belief_shift, message_burst, agreement_spike, disagreement_spike, pattern_match
    magnitude: float = 0.0  # 0.0 to 1.0
    context: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EmergentInsightDetectorModule:
    """Detects emergent insights from cross-agent patterns."""

    def __init__(self):
        self.config = EmergentInsightDetectorConfig()
        self.running = False
        self._lock = Lock()
        self._insights: List[Insight] = []
        self._signals: List[Signal] = []
        self._agent_signal_counts: Dict[str, int] = defaultdict(int)
        self._type_counts: Dict[str, int] = defaultdict(int)

    def start(self) -> None:
        """Start the detector."""
        self.running = True
        logger.info("EmergentInsightDetector started")

    def stop(self) -> None:
        """Stop the detector."""
        self.running = False
        logger.info("EmergentInsightDetector stopped")

    def submit_signal(self, agent_id: str, signal_type: str,
                      magnitude: float = 0.5, context: str = "") -> Optional[Insight]:
        """
        Submit a signal from an agent. May trigger insight detection.

        Args:
            agent_id: The agent submitting the signal.
            signal_type: Type of signal (belief_shift, message_burst, etc.).
            magnitude: Signal strength 0.0-1.0.
            context: Human-readable context.

        Returns:
            An Insight if one was detected, None otherwise.
        """
        signal = Signal(
            agent_id=agent_id,
            signal_type=signal_type,
            magnitude=max(0.0, min(1.0, magnitude)),
            context=context,
        )

        with self._lock:
            self._signals.append(signal)
            self._agent_signal_counts[agent_id] += 1

            # Trim signals
            if len(self._signals) > self.config.detection_window * 20:
                self._signals = self._signals[-self.config.detection_window:]

            # Try to detect insight
            insight = self._try_detect_insight(signal)
            if insight:
                self._insights.append(insight)
                self._type_counts[insight.insight_type] += 1

                # Trim insights
                if len(self._insights) > self.config.max_insights:
                    self._insights = self._insights[-self.config.max_insights:]

                logger.info("Insight detected: %s (%.2f) — %s",
                            insight.insight_type, insight.confidence, insight.description[:80])
                return insight

        return None

    def _try_detect_insight(self, new_signal: Signal) -> Optional[Insight]:
        """Try to detect an emergent insight from recent signals."""
        window = self.config.detection_window
        recent = self._signals[-window:] if len(self._signals) >= window else self._signals

        # Count unique agents in recent signals
        agents_in_window = set(s.agent_id for s in recent)
        if len(agents_in_window) < 2:
            return None

        # Count signal types
        type_counts: Dict[str, int] = defaultdict(int)
        for s in recent:
            type_counts[s.signal_type] += 1

        # Detection heuristics
        # 1. Correlation: multiple agents show same signal type
        for stype, count in type_counts.items():
            if count >= 3:
                affected = list(set(s.agent_id for s in recent if s.signal_type == stype))
                avg_magnitude = sum(s.magnitude for s in recent if s.signal_type == stype) / count
                confidence = min(1.0, avg_magnitude * (count / len(recent)) * len(affected))

                if confidence >= self.config.min_confidence:
                    return Insight(
                        insight_type="correlation",
                        source_agents=affected,
                        description=f"Correlated {stype} across {len(affected)} agents (n={count})",
                        confidence=round(confidence, 3),
                        evidence=[s.signal_id for s in recent if s.signal_type == stype][:5],
                    )

        # 2. Contradiction: disagreement spike + belief_shift
        if type_counts.get("disagreement_spike", 0) >= 2 and type_counts.get("belief_shift", 0) >= 2:
            agents = list(agents_in_window)
            confidence = 0.6 + (0.1 * min(len(agents), 4))
            return Insight(
                insight_type="contradiction",
                source_agents=agents,
                description=f"Contradiction detected: disagreement + belief shifts across {len(agents)} agents",
                confidence=round(min(1.0, confidence), 3),
                evidence=[s.signal_id for s in recent[-10:]],
            )

        # 3. Synthesis: agreement spike after disagreement
        if type_counts.get("agreement_spike", 0) >= 2 and any(
            s.signal_type == "disagreement_spike" for s in recent[:len(recent) // 2]
        ):
            agents = list(agents_in_window)
            return Insight(
                insight_type="synthesis",
                source_agents=agents,
                description=f"Synthesis emerging: agreement after prior disagreement across {len(agents)} agents",
                confidence=0.7,
                evidence=[s.signal_id for s in recent[-5:]],
            )

        # 4. Anomaly: unusual signal magnitude
        if new_signal.magnitude > 0.9:
            return Insight(
                insight_type="anomaly",
                source_agents=[new_signal.agent_id],
                description=f"Anomalous {new_signal.signal_type} from {new_signal.agent_id}: magnitude={new_signal.magnitude:.2f}",
                confidence=new_signal.magnitude,
                evidence=[new_signal.signal_id],
            )

        return None

    def get_insights(self, insight_type: Optional[str] = None,
                     min_confidence: Optional[float] = None,
                     limit: int = 50) -> List[Dict]:
        """
        Get detected insights, optionally filtered.

        Args:
            insight_type: Filter by type.
            min_confidence: Minimum confidence threshold.
            limit: Max results.

        Returns:
            List of insight dicts.
        """
        with self._lock:
            results = list(self._insights)
            if insight_type:
                results = [i for i in results if i.insight_type == insight_type]
            if min_confidence is not None:
                results = [i for i in results if i.confidence >= min_confidence]
            return [i.model_dump() for i in results[-limit:]]

    def get_insight_by_id(self, insight_id: str) -> Optional[Dict]:
        """Get a specific insight by ID."""
        with self._lock:
            for i in self._insights:
                if i.insight_id == insight_id:
                    return i.model_dump()
            return None

    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        with self._lock:
            return {
                "total_insights": len(self._insights),
                "total_signals": len(self._signals),
                "signals_per_agent": dict(self._agent_signal_counts),
                "insights_by_type": dict(self._type_counts),
                "active_agents": len(self._agent_signal_counts),
            }
