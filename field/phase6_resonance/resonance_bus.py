"""
6_resonance.resonance_bus
==========================
Inter-agent communication bus for resonant cognition.

Enables message passing between agents for collaborative thinking.
Message types: thought, hypothesis, evidence, challenge, synthesis, consensus_request.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.resonance.bus")


class ResonanceBusConfig(BaseModel):
    """Configuration for resonance_bus."""
    enabled: bool = True
    max_messages: int = 50000
    message_ttl_sec: int = 3600
    max_threads: int = 1000


class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    thread_id: str = ""
    from_agent: str
    to_agent: str  # "broadcast" for broadcast messages
    msg_type: str  # thought, hypothesis, evidence, challenge, synthesis, consensus_request
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResonanceBusModule:
    """Inter-agent communication bus for resonant cognition."""

    def __init__(self):
        self.config = ResonanceBusConfig()
        self.running = False
        self._messages: List[Message] = []
        self._threads: Dict[str, List[str]] = defaultdict(list)  # thread_id -> [message_id, ...]
        self._agent_inboxes: Dict[str, List[str]] = defaultdict(list)  # agent_id -> [message_id, ...]
        self._stats: Dict[str, int] = defaultdict(int)  # msg_type -> count
        self._lock = Lock()

    def start(self) -> None:
        """Start the resonance bus."""
        self.running = True
        logger.info("ResonanceBus started")

    def stop(self) -> None:
        """Stop the resonance bus."""
        self.running = False
        logger.info("ResonanceBus stopped")

    def send_message(self, from_agent: str, to_agent: str, msg_type: str,
                     content: str, thread_id: str = "", **metadata) -> str:
        """Send a message from one agent to another (or broadcast).

        Returns the message_id.
        """
        with self._lock:
            msg = Message(
                thread_id=thread_id or str(uuid.uuid4())[:8],
                from_agent=from_agent,
                to_agent=to_agent,
                msg_type=msg_type,
                content=content,
                metadata=metadata,
            )
            self._messages.append(msg)
            self._stats[msg_type] += 1
            self._threads[msg.thread_id].append(msg.message_id)

            if to_agent == "broadcast":
                # Don't add to specific inbox
                pass
            else:
                self._agent_inboxes[to_agent].append(msg.message_id)

            # Evict oldest if over max
            if len(self._messages) > self.config.max_messages:
                self._evict_oldest(1000)

            logger.debug("Message %s: %s -> %s [%s]", msg.message_id, from_agent, to_agent, msg_type)
            return msg.message_id

    def broadcast(self, from_agent: str, msg_type: str, content: str,
                  thread_id: str = "", **metadata) -> str:
        """Broadcast a message to all agents."""
        return self.send_message(from_agent, "broadcast", msg_type, content, thread_id, **metadata)

    def get_messages(self, agent_id: str, since: str = "") -> List[Dict]:
        """Get messages for an agent (inbox + broadcast), optionally since a timestamp."""
        with self._lock:
            msg_ids = set(self._agent_inboxes.get(agent_id, []))
            # Also include broadcast messages
            result = []
            for msg in self._messages:
                if msg.to_agent == "broadcast" or msg.message_id in msg_ids:
                    if not since or msg.timestamp >= since:
                        result.append(msg.model_dump())
            return result[-1000:]  # Cap at 1000

    def get_conversation(self, thread_id: str) -> List[Dict]:
        """Get all messages in a conversation thread."""
        with self._lock:
            msg_ids = self._threads.get(thread_id, [])
            return [m.model_dump() for m in self._messages if m.message_id in msg_ids]

    def get_bus_stats(self) -> Dict[str, Any]:
        """Get bus statistics."""
        with self._lock:
            return {
                "total_messages": len(self._messages),
                "total_threads": len(self._threads),
                "agent_inboxes": {k: len(v) for k, v in self._agent_inboxes.items()},
                "messages_by_type": dict(self._stats),
                "max_messages": self.config.max_messages,
                "running": self.running,
            }

    def _evict_oldest(self, count: int) -> None:
        """Evict the oldest messages."""
        if count >= len(self._messages):
            self._messages.clear()
            self._threads.clear()
            self._agent_inboxes.clear()
        else:
            evicted = self._messages[:count]
            self._messages = self._messages[count:]
            evicted_ids = {m.message_id for m in evicted}
            # Clean up threads
            for tid in list(self._threads.keys()):
                self._threads[tid] = [mid for mid in self._threads[tid] if mid not in evicted_ids]
                if not self._threads[tid]:
                    del self._threads[tid]
            # Clean up inboxes
            for aid in self._agent_inboxes:
                self._agent_inboxes[aid] = [mid for mid in self._agent_inboxes[aid] if mid not in evicted_ids]
