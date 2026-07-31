"""
Shared Memory Bridge — connects consensus layer to shared memory.

Provides access to vault, event fabric, and structural memory for
context injection during spawn planning.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.consensus.shared_memory_bridge")


class SharedMemoryBridge:
    """
    Bridge to shared memory systems for context injection.

    Provides read-only access to:
    - Vault entries
    - Event fabric
    - Structural memory
    """

    def __init__(self):
        self._vault_entries: List[Dict[str, Any]] = []
        self._event_cache: List[Dict[str, Any]] = []

    def get_vault_context(self, query: str, max_entries: int = 10) -> List[Dict[str, Any]]:
        """Get relevant vault entries for a query."""
        # Return cached entries or empty list
        return self._vault_entries[:max_entries]

    def get_event_context(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events for context."""
        return self._event_cache[-limit:]

    def get_structural_memory(self, layer: str = "WORK") -> List[Dict[str, Any]]:
        """Get entries from a structural memory layer."""
        return []

    def inject_context(self, context: Dict[str, Any]) -> None:
        """Inject context into the bridge."""
        self._vault_entries.extend(context.get("vault", []))
        self._event_cache.extend(context.get("events", []))

    def clear(self) -> None:
        """Clear cached context."""
        self._vault_entries.clear()
        self._event_cache.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status."""
        return {
            "vault_entries": len(self._vault_entries),
            "event_cache_size": len(self._event_cache),
        }