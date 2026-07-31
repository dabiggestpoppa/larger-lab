"""
Phase 1.6.5 — Memory-Aware Execution (Context Injection)

Injects semantic memory into agent execution so agents pull context
before acting, rather than operating statelessly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.memory")


@dataclass
class ContextPacket:
    """A packet of context injected into agent execution."""
    source: str  # "vector", "graph", "vault", "prior_output"
    content: str
    relevance_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextInjector:
    """
    Injects semantic memory into agent execution.
    
    Before an agent runs, this retrieves relevant context from:
    - Vector memory (semantic search)
    - Knowledge graph (topology context)
    - Vault (persistent memory)
    - Prior outputs (execution continuity)
    """

    def __init__(self, vector_store=None, graph_store=None, vault=None):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.vault = vault
        self._context_history: List[ContextPacket] = []

    def inject(
        self,
        query: str,
        agent_type: str = "general",
        max_contexts: int = 5,
    ) -> List[ContextPacket]:
        """
        Build context for an agent execution.
        
        Args:
            query: The task/query to build context for
            agent_type: Type of agent (affects what context is prioritized)
            max_contexts: Maximum number of context packets
            
        Returns:
            List of ContextPacket objects, ranked by relevance
        """
        contexts: List[ContextPacket] = []

        # 1. Vector memory search
        if self.vector_store:
            try:
                results = self.vector_store.search(query, limit=max_contexts)
                for r in results:
                    contexts.append(ContextPacket(
                        source="vector",
                        content=r.get("text", str(r)),
                        relevance_score=r.get("score", 0.5),
                    ))
            except Exception as e:
                logger.debug(f"Vector context failed: {e}")

        # 2. Knowledge graph context
        if self.graph_store:
            try:
                graph_context = self._get_graph_context(query)
                if graph_context:
                    contexts.append(ContextPacket(
                        source="graph",
                        content=graph_context,
                        relevance_score=0.6,
                    ))
            except Exception as e:
                logger.debug(f"Graph context failed: {e}")

        # 3. Vault/prior memory
        if self.vault:
            try:
                vault_context = self._get_vault_context(query)
                if vault_context:
                    contexts.append(ContextPacket(
                        source="vault",
                        content=vault_context,
                        relevance_score=0.4,
                    ))
            except Exception as e:
                logger.debug(f"Vault context failed: {e}")

        # Sort by relevance and limit
        contexts.sort(key=lambda c: c.relevance_score, reverse=True)
        selected = contexts[:max_contexts]

        self._context_history.extend(selected)
        logger.info(f"Injected {len(selected)} context packets for '{query[:50]}'")
        return selected

    def _get_graph_context(self, query: str) -> str:
        """Get context from knowledge graph."""
        # Placeholder — would query graph store for related entities
        return ""

    def _get_vault_context(self, query: str) -> str:
        """Get context from vault/persistent memory."""
        # Placeholder — would search vault for related notes
        return ""

    def format_context(self, packets: List[ContextPacket]) -> str:
        """Format context packets into a string for agent consumption."""
        if not packets:
            return "(no relevant context found)"

        parts = []
        for i, packet in enumerate(packets, 1):
            source_label = packet.source.upper()
            parts.append(f"[{source_label}] {packet.content[:500]}")

        return "\n\n".join(parts)

    def get_history(self, limit: int = 10) -> List[ContextPacket]:
        """Get recent context injection history."""
        return self._context_history[-limit:]

    def clear_history(self):
        """Clear context history."""
        self._context_history.clear()
