"""Phase 4: Sovereign Field Operations.

Finalizes Larger-Lab as a persistent sovereign operational intelligence field.

Components:
- PersistentObserverIdentity: Stable identity across sessions/restarts
- RecursiveSelfReference: Field awareness (the system knows itself)
- GraphLevelRetrieval: Semantic cognition via knowledge graph
- OperationalTopologyMapping: System visualization
- StrategicMemoryCompression: Long-term continuity
- FullTelegramSovereignty: Mobile operational command layer
"""
import os
import json
import datetime
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOVEREIGN_DIR = REPO_ROOT / "data" / "observer" / "sovereign"
IDENTITY_FILE = SOVEREIGN_DIR / "identity.json"
FIELD_STATE_FILE = SOVEREIGN_DIR / "field_state.json"


class PersistentObserverIdentity:
    """Stable identity across sessions, restarts, model resets."""

    def __init__(self):
        SOVEREIGN_DIR.mkdir(parents=True, exist_ok=True)
        self._identity = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        if IDENTITY_FILE.exists():
            try:
                with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Create new identity
        identity = {
            "observer_id": "primary_observer",
            "created": datetime.datetime.utcnow().isoformat() + "Z",
            "version": 1,
            "traits": {
                "role": "sovereign_operational_interface",
                "style": "concise_direct_operational",
                "domain": "larger_lab_cognitive_field",
            },
            "continuity_score": 1.0,
            "total_interactions": 0,
            "total_spawns": 0,
            "total_tasks_completed": 0,
            "uptime_sessions": 1,
        }
        self._save(identity)
        return identity

    def _save(self, identity: Dict[str, Any]):
        identity["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
        with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2, ensure_ascii=False)

    def record_interaction(self):
        self._identity["total_interactions"] += 1
        self._identity["continuity_score"] = min(1.0, self._identity["continuity_score"] + 0.001)
        self._save(self._identity)

    def record_spawn(self):
        self._identity["total_spawns"] += 1
        self._save(self._identity)

    def record_task_complete(self):
        self._identity["total_tasks_completed"] += 1
        self._save(self._identity)

    def get_identity_summary(self) -> str:
        id = self._identity
        return (
            f"🧠 Primary Observer Identity\n"
            f"ID: {id['observer_id']}\n"
            f"Version: {id['version']}\n"
            f"Continuity: {id['continuity_score']:.3f}\n"
            f"Interactions: {id['total_interactions']}\n"
            f"Spawns: {id['total_spawns']}\n"
            f"Tasks completed: {id['total_tasks_completed']}\n"
            f"Created: {id['created'][:10]}"
        )

    @property
    def data(self) -> Dict[str, Any]:
        return dict(self._identity)


class RecursiveSelfReference:
    """Field awareness — the system knows itself and its own state."""

    def __init__(self, identity: PersistentObserverIdentity = None):
        self.identity = identity or PersistentObserverIdentity()

    def self_reflect(self) -> Dict[str, Any]:
        """Generate a self-referential state summary."""
        from core.observer.vault import Vault
        from core.observer.graph_traversal import KnowledgeGraph
        from core.observer.semantic_retrieval import SemanticRetrieval

        vault = Vault()
        kg = KnowledgeGraph()
        nodes = kg.build_from_vault(vault.path)

        # Count vault files
        md_count = 0
        for _, _, files in os.walk(vault.path):
            md_count += sum(1 for f in files if f.endswith('.md'))

        return {
            "identity": self.identity.data,
            "vault": {
                "notes": md_count,
                "graph_nodes": nodes,
                "graph_edges": sum(len(v) for v in kg.edges.values()),
            },
            "capabilities": [
                "telegram_chat", "slash_commands", "agent_spawn",
                "vault_search", "knowledge_graph", "semantic_retrieval",
                "pattern_distillation", "failure_intelligence",
                "task_orchestration", "autonomous_reporting",
            ],
            "self_awareness": "I am the Primary Observer. I know my vault, my graph, my agents, and my history.",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def format_self_summary(self) -> str:
        ref = self.self_reflect()
        vault = ref["vault"]
        id = ref["identity"]
        return (
            f"🪞 Self-Reflection\n"
            f"I am {id['observer_id']} (v{id['version']})\n"
            f"Continuity: {id['continuity_score']:.3f} | Interactions: {id['total_interactions']}\n"
            f"Vault: {vault['notes']} notes, {vault['graph_nodes']} graph nodes, {vault['graph_edges']} edges\n"
            f"Capabilities: {len(ref['capabilities'])} active\n"
            f"Status: {ref['self_awareness']}"
        )


class StrategicMemoryCompression:
    """Long-term continuity — compress operational history into distilled knowledge."""

    def __init__(self):
        SOVEREIGN_DIR.mkdir(parents=True, exist_ok=True)

    def compress_session(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compress a session's interactions into a distilled summary."""
        if not interactions:
            return {"summary": "No interactions", "patterns": [], "lessons": []}

        # Extract patterns
        domains = {}
        for i in interactions:
            d = i.get("domain", "unknown")
            domains[d] = domains.get(d, 0) + 1

        # Find most common patterns
        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)

        return {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "interaction_count": len(interactions),
            "domain_distribution": dict(sorted_domains[:5]),
            "compression_ratio": f"1:{len(interactions)}",
            "key_patterns": [d[0] for d in sorted_domains[:3]],
        }

    def write_compressed_summary(self, summary: Dict[str, Any]) -> str:
        """Write compressed summary to disk."""
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        fp = SOVEREIGN_DIR / f"compressed_{ts}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        return str(fp)


class SovereignField:
    """Main Phase 4 orchestrator — ties all sovereign capabilities together."""

    def __init__(self):
        self.identity = PersistentObserverIdentity()
        self.self_reference = RecursiveSelfReference(self.identity)
        self.memory_compression = StrategicMemoryCompression()
        self._session_interactions: List[Dict[str, Any]] = []

    def process_message(self, message: str, response: str, meta: Dict = None):
        """Record a message-response pair for continuity."""
        self.identity.record_interaction()
        self._session_interactions.append({
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "message": message[:200],
            "response_len": len(response),
            "meta": meta or {},
        })

    def get_sovereign_context(self) -> str:
        """Build a context string for the LLM with sovereign awareness."""
        id = self.identity.data
        ref = self.self_reference.self_reflect()
        vault = ref["vault"]
        return (
            f"[Sovereign Context] "
            f"Identity: {id['observer_id']} v{id['version']} | "
            f"Continuity: {id['continuity_score']:.3f} | "
            f"Interactions: {id['total_interactions']} | "
            f"Vault: {vault['notes']} notes, {vault['graph_nodes']} nodes | "
            f"Capabilities: {', '.join(ref['capabilities'][:5])}..."
        )

    def end_session(self):
        """Compress and persist session memory."""
        if self._session_interactions:
            summary = self.memory_compression.compress_session(self._session_interactions)
            self.memory_compression.write_compressed_summary(summary)
            self._session_interactions.clear()

    def full_status(self) -> str:
        """Complete sovereign field status."""
        return (
            f"{self.identity.get_identity_summary()}\n"
            f"\n"
            f"{self.self_reference.format_self_summary()}"
        )


if __name__ == "__main__":
    sf = SovereignField()
    print(sf.full_status())
    print()
    print("Sovereign context for LLM:")
    print(sf.get_sovereign_context())
