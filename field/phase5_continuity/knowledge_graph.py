"""5_continuity.knowledge_graph

Field Knowledge Graph — entities, relationships, and facts in the field.

Maintains an in-memory graph of field knowledge with optional JSON persistence.
Supports entities with typed relationships, subgraph queries, and neighbor traversal.
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.knowledge_graph")

DATA_DIR = Path(__file__).parent.parent / "data"


class KnowledgeGraphConfig(BaseModel):
    """Configuration for knowledge_graph."""
    enabled: bool = True
    max_entities: int = 100000
    max_relationships: int = 500000
    persist_path: str = "data/knowledge_graph.json"


class Entity(BaseModel):
    entity_id: str
    entity_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


class Relationship(BaseModel):
    from_id: str
    to_id: str
    rel_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""


class KnowledgeGraphModule:
    """knowledge_graph field module — field knowledge graph management."""

    def __init__(self):
        self.config = KnowledgeGraphConfig()
        self.running = False
        self._lock = Lock()
        self._entities: Dict[str, Entity] = {}
        self._relationships: List[Relationship] = []
        self._adjacency: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # entity_id -> [(to_id, rel_type)]
        self._reverse_adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # entity_id -> [(from_id, rel_type)]
        self._type_index: Dict[str, Set[str]] = defaultdict(set)  # entity_type -> {entity_ids}
        self._persist_file = DATA_DIR / "knowledge_graph.json"

    def start(self) -> None:
        """Start the module and load persisted graph if available."""
        self.running = True
        if self._persist_file.exists():
            self._load()
            logger.info("KnowledgeGraph started with %d entities, %d relationships",
                        len(self._entities), len(self._relationships))
        else:
            logger.info("KnowledgeGraph started (empty)")

    def stop(self) -> None:
        """Stop the module and persist graph."""
        if self.running:
            self._save()
        self.running = False
        logger.info("KnowledgeGraph stopped")

    def add_entity(self, entity_id: str, entity_type: str, properties: Optional[Dict[str, Any]] = None) -> Entity:
        """Add or update an entity in the graph."""
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            if entity_id in self._entities:
                entity = self._entities[entity_id]
                entity.properties.update(properties or {})
                entity.updated_at = now
                logger.debug("Updated entity: %s", entity_id)
            else:
                if len(self._entities) >= self.config.max_entities:
                    raise RuntimeError(f"Max entities ({self.config.max_entities}) reached")
                entity = Entity(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    properties=properties or {},
                    created_at=now,
                    updated_at=now,
                )
                self._entities[entity_id] = entity
                logger.debug("Added entity: %s (%s)", entity_id, entity_type)
            self._type_index[entity_type].add(entity_id)
            return entity

    def add_relationship(self, from_id: str, to_id: str, rel_type: str,
                         properties: Optional[Dict[str, Any]] = None) -> Relationship:
        """Add a relationship between two entities."""
        with self._lock:
            if len(self._relationships) >= self.config.max_relationships:
                raise RuntimeError(f"Max relationships ({self.config.max_relationships}) reached")
            now = datetime.now(timezone.utc).isoformat()
            rel = Relationship(
                from_id=from_id, to_id=to_id, rel_type=rel_type,
                properties=properties or {}, created_at=now,
            )
            self._relationships.append(rel)
            self._adjacency[from_id].append((to_id, rel_type))
            self._reverse_adj[to_id].append((from_id, rel_type))
            logger.debug("Added relationship: %s -[%s]-> %s", from_id, rel_type, to_id)
            return rel

    def query(self, entity_type: str, filters: Optional[Dict[str, Any]] = None) -> List[Entity]:
        """Query entities by type with optional property filters."""
        with self._lock:
            ids = self._type_index.get(entity_type, set())
            results = [self._entities[eid] for eid in ids if eid in self._entities]
            if filters:
                results = [
                    e for e in results
                    if all(e.properties.get(k) == v for k, v in filters.items())
                ]
            return results

    def get_neighbors(self, entity_id: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get neighbors of an entity, optionally filtered by relationship type."""
        with self._lock:
            neighbors = []
            for tid, rtype in self._adjacency.get(entity_id, []):
                if rel_type and rtype != rel_type:
                    continue
                if tid in self._entities:
                    neighbors.append({
                        "entity": self._entities[tid],
                        "direction": "outgoing",
                        "rel_type": rtype,
                    })
            for fid, rtype in self._reverse_adj.get(entity_id, []):
                if rel_type and rtype != rel_type:
                    continue
                if fid in self._entities:
                    neighbors.append({
                        "entity": self._entities[fid],
                        "direction": "incoming",
                        "rel_type": rtype,
                    })
            return neighbors

    def get_subgraph(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get a subgraph centered on an entity up to a given depth."""
        with self._lock:
            visited = set()
            nodes = []
            edges = []

            def _traverse(eid: str, d: int):
                if eid in visited or d > depth:
                    return
                visited.add(eid)
                if eid in self._entities:
                    nodes.append(self._entities[eid])
                for tid, rtype in self._adjacency.get(eid, []):
                    edges.append({"from": eid, "to": tid, "type": rtype})
                    _traverse(tid, d + 1)
                for fid, rtype in self._reverse_adj.get(eid, []):
                    edges.append({"from": fid, "to": eid, "type": rtype})
                    _traverse(fid, d + 1)

            _traverse(entity_id, 0)
            return {"nodes": nodes, "edges": edges, "center": entity_id, "depth": depth}

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        with self._lock:
            type_counts = {t: len(ids) for t, ids in self._type_index.items()}
            rel_type_counts: Dict[str, int] = {}
            for rel in self._relationships:
                rel_type_counts[rel.rel_type] = rel_type_counts.get(rel.rel_type, 0) + 1
            return {
                "total_entities": len(self._entities),
                "total_relationships": len(self._relationships),
                "entity_types": type_counts,
                "relationship_types": rel_type_counts,
            }

    def _save(self):
        """Persist graph to JSON."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "entities": {eid: e.model_dump() for eid, e in self._entities.items()},
                "relationships": [r.model_dump() for r in self._relationships],
            }
            with open(self._persist_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("KnowledgeGraph saved to %s", self._persist_file)
        except Exception as exc:
            logger.error("Failed to save knowledge graph: %s", exc)

    def _load(self):
        """Load graph from JSON."""
        try:
            with open(self._persist_file, "r") as f:
                data = json.load(f)
            for eid, edata in data.get("entities", {}).items():
                self._entities[eid] = Entity(**edata)
                self._type_index[edata["entity_type"]].add(eid)
            for rdata in data.get("relationships", []):
                rel = Relationship(**rdata)
                self._relationships.append(rel)
                self._adjacency[rel.from_id].append((rel.to_id, rel.rel_type))
                self._reverse_adj[rel.to_id].append((rel.from_id, rel.rel_type))
            logger.debug("KnowledgeGraph loaded from %s", self._persist_file)
        except Exception as exc:
            logger.error("Failed to load knowledge graph: %s", exc)
