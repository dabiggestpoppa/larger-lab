"""
9_emergence.field_consciousness
=================================
Field-wide consciousness monitor — global workspace tracker.

Implements a simplified Global Workspace Theory (GWT) model for the field.
Multiple specialized modules compete for access to a shared "consciousness"
workspace. The winning coalition becomes the field's current conscious state.

The consciousness workspace acts as a blackboard where:
- Specialized processors (field modules) submit content
- Attention mechanisms select the most relevant coalition
- The winning coalition broadcasts globally
- Conscious state history tracks the flow of awareness

This enables the field to maintain a unified situational awareness
from the many parallel activities of its constituent modules.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.emergence.consciousness")


class ConsciousContent(BaseModel):
    """A piece of content competing for consciousness."""
    content_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_module: str
    content_type: str  # perception, goal, alert, insight, memory, plan
    data: Dict[str, Any] = Field(default_factory=dict)
    activation: float = 0.5  # salience / urgency 0-1
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    coalition_id: Optional[str] = None


class Coalition(BaseModel):
    """A coalition of content that gains conscious access."""
    coalition_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    content_ids: List[str] = Field(default_factory=list)
    total_activation: float = 0.0
    broadcast_count: int = 0
    formed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dissolved_at: Optional[str] = None


class ConsciousnessState(BaseModel):
    """Snapshot of the current conscious state."""
    current_coalition_id: Optional[str] = None
    active_content: List[str] = Field(default_factory=list)
    attention_focus: str = ""
    arousal_level: float = 0.5  # 0=calm, 1=high alert
    workspace_load: float = 0.0  # 0=empty, 1=saturated
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FieldConsciousnessConfig(BaseModel):
    """Configuration for field_consciousness."""
    enabled: bool = True
    max_workspace_size: int = 50
    competition_rounds: int = 3
    activation_decay: float = 0.9
    coalition_threshold: float = 0.6
    broadcast_history_limit: int = 1000
    attention_decay_interval: int = 10  # rounds between attention decay


class FieldConsciousnessModule:
    """Field-wide consciousness monitor — global workspace tracker."""

    def __init__(self):
        self.config = FieldConsciousnessConfig()
        self.running = False
        self._lock = Lock()
        self._workspace: Dict[str, ConsciousContent] = {}
        self._coalitions: Dict[str, Coalition] = {}
        self._current_coalition_id: Optional[str] = None
        self._broadcast_history: List[Dict[str, Any]] = []
        self._attention_focus: str = ""
        self._arousal_level: float = 0.5
        self._round_count: int = 0
        self._submissions_total: int = 0
        self._coalitions_formed: int = 0

    def start(self) -> None:
        """Start the consciousness module."""
        self.running = True
        self._arousal_level = 0.3  # start calm
        logger.info("FieldConsciousness started")

    def stop(self) -> None:
        """Stop the consciousness module."""
        self.running = False
        # Dissolve current coalition
        if self._current_coalition_id and self._current_coalition_id in self._coalitions:
            self._coalitions[self._current_coalition_id].dissolved_at = (
                datetime.now(timezone.utc).isoformat()
            )
        logger.info("FieldConsciousness stopped — %d coalitions formed total",
                     self._coalitions_formed)

    def submit_content(self, source_module: str, content_type: str,
                       data: Dict[str, Any], activation: float = 0.5) -> str:
        """
        Submit content to the global workspace for competition.

        Args:
            source_module: The module submitting content.
            content_type: Type of content (perception, goal, alert, insight, memory, plan).
            data: The content payload.
            activation: Salience/urgency score 0.0-1.0.

        Returns:
            The content_id.
        """
        content = ConsciousContent(
            source_module=source_module,
            content_type=content_type,
            data=data,
            activation=max(0.0, min(1.0, activation)),
        )

        with self._lock:
            # Evict oldest if workspace is full
            if len(self._workspace) >= self.config.max_workspace_size:
                oldest_id = min(self._workspace,
                                key=lambda k: self._workspace[k].timestamp)
                del self._workspace[oldest_id]
                logger.debug("Evicted oldest content: %s", oldest_id)

            self._workspace[content.content_id] = content
            self._submissions_total += 1

            # Adjust arousal based on activation
            if content.activation > 0.8:
                self._arousal_level = min(1.0, self._arousal_level + 0.1)
            elif content.activation < 0.3:
                self._arousal_level = max(0.0, self._arousal_level - 0.05)

        logger.debug("Content submitted by %s: %s (activation=%.2f)",
                      source_module, content.content_id, content.activation)
        return content.content_id

    def run_competition(self) -> Optional[str]:
        """
        Run a competition round to select the next conscious coalition.

        Content items compete based on activation scores. The highest-activated
        content forms a coalition with related content, and wins conscious access.

        Returns:
            The winning coalition_id, or None if no competition was decisive.
        """
        with self._lock:
            if not self._workspace:
                return None

            self._round_count += 1

            # Sort content by activation
            sorted_content = sorted(
                self._workspace.values(),
                key=lambda c: c.activation,
                reverse=True
            )

            # Top content becomes coalition seed
            winner = sorted_content[0]

            # Gather coalition: content from compatible sources with similar activation
            coalition_members = [winner.content_id]
            for content in sorted_content[1:]:
                if (content.activation >= self.config.coalition_threshold * winner.activation
                        and len(coalition_members) < 10):
                    coalition_members.append(content.content_id)

            total_activation = sum(
                self._workspace[cid].activation for cid in coalition_members
                if cid in self._workspace
            )

            # Form coalition
            coalition = Coalition(
                content_ids=coalition_members,
                total_activation=round(total_activation, 4),
            )

            # Dissolve previous coalition
            if self._current_coalition_id and self._current_coalition_id in self._coalitions:
                self._coalitions[self._current_coalition_id].dissolved_at = (
                    datetime.now(timezone.utc).isoformat()
                )

            self._coalitions[coalition.coalition_id] = coalition
            self._current_coalition_id = coalition.coalition_id
            self._coalitions_formed += 1

            # Update content with coalition reference
            for cid in coalition_members:
                if cid in self._workspace:
                    self._workspace[cid].coalition_id = coalition.coalition_id

            # Set attention focus to winning content type
            self._attention_focus = winner.content_type

            # Record broadcast
            broadcast = {
                "coalition_id": coalition.coalition_id,
                "content_ids": coalition_members,
                "total_activation": coalition.total_activation,
                "focus": self._attention_focus,
                "arousal": round(self._arousal_level, 3),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._broadcast_history.append(broadcast)
            if len(self._broadcast_history) > self.config.broadcast_history_limit:
                self._broadcast_history = self._broadcast_history[-self.config.broadcast_history_limit:]

            # Periodic attention decay
            if self._round_count % self.config.attention_decay_interval == 0:
                self._apply_decay()

            logger.info("Coalition %s won — focus=%s, activation=%.3f, members=%d",
                         coalition.coalition_id, self._attention_focus,
                         coalition.total_activation, len(coalition_members))
            return coalition.coalition_id

    def _apply_decay(self) -> None:
        """Apply activation decay to workspace content."""
        decay = self.config.activation_decay
        to_remove = []
        for cid, content in self._workspace.items():
            content.activation *= decay
            if content.activation < 0.05:
                to_remove.append(cid)
        for cid in to_remove:
            del self._workspace[cid]
        if to_remove:
            logger.debug("Decay removed %d low-activation content items", len(to_remove))

    def get_state(self) -> Dict[str, Any]:
        """Get the current consciousness state."""
        with self._lock:
            current_coalition = (
                self._coalitions.get(self._current_coalition_id)
                if self._current_coalition_id else None
            )
            return {
                "current_coalition_id": self._current_coalition_id,
                "active_content": (
                    current_coalition.content_ids if current_coalition else []
                ),
                "attention_focus": self._attention_focus,
                "arousal_level": round(self._arousal_level, 3),
                "workspace_load": round(
                    len(self._workspace) / self.config.max_workspace_size, 3
                ),
                "workspace_size": len(self._workspace),
                "total_coalitions_formed": self._coalitions_formed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_broadcast_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent consciousness broadcast history."""
        with self._lock:
            return list(reversed(self._broadcast_history[-limit:]))

    def set_arousal(self, level: float) -> None:
        """Manually set arousal level (e.g., from external alert)."""
        with self._lock:
            self._arousal_level = max(0.0, min(1.0, level))
        logger.info("Arousal level set to %.2f", self._arousal_level)

    def get_stats(self) -> Dict[str, Any]:
        """Get consciousness statistics."""
        with self._lock:
            content_types: Dict[str, int] = defaultdict(int)
            for c in self._workspace.values():
                content_types[c.content_type] += 1
            return {
                "running": self.running,
                "workspace_size": len(self._workspace),
                "workspace_capacity": self.config.max_workspace_size,
                "total_submissions": self._submissions_total,
                "total_coalitions_formed": self._coalitions_formed,
                "current_coalition": self._current_coalition_id,
                "attention_focus": self._attention_focus,
                "arousal_level": round(self._arousal_level, 3),
                "content_type_distribution": dict(content_types),
                "competition_rounds": self._round_count,
            }
